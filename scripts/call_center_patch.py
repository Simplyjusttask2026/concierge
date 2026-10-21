import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'call-center-plan-v1' in s:
    print('already patched'); raise SystemExit(0)
anchor = 'OUTREACH_DAILY_CAP = int(os.environ.get("OUTREACH_DAILY_CAP", "10"))' + chr(10)
assert anchor in s
helpers = anchor + '''CALL_CENTER_CAP = 10
WHATSAPP_AUTOSEND_ENABLED = os.environ.get("WHATSAPP_AUTOSEND_ENABLED", "false").lower() == "true"
def _et_now():
    try:
        if ZoneInfo is not None:
            return datetime.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        pass
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
def _call_center_window_open(now=None):
    return 8 <= (now or _et_now()).hour < 21
def _lead_is_stopped(ld):
    txt = (" " + str((ld or {}).get("Description") or "") + " ").upper()
    return " STOP " in txt or "OPT OUT" in txt
def _fn(name):
    x = str(name or "").split(); return x[0] if x else "there"
def _call_center_plan(leads, now=None):
    now = now or _et_now()
    plan = {"version":"call-center-plan-v1","generated_at_et":now.strftime("%Y-%m-%d %H:%M ET"),"window_open_8am_9pm_et":_call_center_window_open(now),"whatsapp_autosend_enabled":bool(WHATSAPP_AUTOSEND_ENABLED),"whatsapp_note":"DRAFT ONLY until approved template + VERIFIED phone","email_queue":[],"whatsapp_drafts":[],"human_call_list":[],"recycle_drafts":[],"suppressed_stop":[],"counts":{}}
    for ld in leads or []:
        name = (ld.get("Full_Name") or ((ld.get("First_Name") or "")+" "+(ld.get("Last_Name") or ""))).strip() or "Lead"
        status = ld.get("Lead_Status") or "Not Contacted"; svc = str(ld.get("Description") or "your request")[:120]
        item = {"name":name,"status":status,"email":ld.get("Email"),"phone":ld.get("Phone"),"source":ld.get("Lead_Source")}
        if _lead_is_stopped(ld): plan["suppressed_stop"].append(item); continue
        if status in ("Recycled","Contact in Future"):
            item["sequence"]=["Day3 draft","Day7 draft","Day12 draft","+30d Contact in Future - never delete"]
            item["draft"]="Hello %s, Anthony from Simply Just Task in Apopka - checking back on %s. Want a free consultation? %s Reply STOP to opt out." % (_fn(name),svc,CAL_LINK)
            if len(plan["recycle_drafts"])<10: plan["recycle_drafts"].append(item)
            continue
        if item["email"] and len(plan["email_queue"])<10:
            q=dict(item); q["channel_note"]="Day0 email via /run-daily only; plan sends nothing"; plan["email_queue"].append(q)
        if item["phone"]:
            if len(plan["whatsapp_drafts"])<10:
                w=dict(item); w["draft"]="Hello %s, this is Anthony from Simply Just Task. We received your request for %s. Reply YES to confirm or STOP to opt out." % (_fn(name),svc); plan["whatsapp_drafts"].append(w)
            if len(plan["human_call_list"])<10:
                c=dict(item); c["script"]="Hi %s, Anthony with Simply Just Task in Apopka, calling about %s. Is now ok for 2 minutes?" % (_fn(name),svc); plan["human_call_list"].append(c)
    plan["counts"]={k:len(plan[k]) for k in ("email_queue","whatsapp_drafts","human_call_list","recycle_drafts","suppressed_stop")}
    return plan
'''
s = s.replace(anchor, helpers, 1)
a2 = '    lines += ["", "=== WHATSAPP DRAFTS (DRAFT ONLY - NOT SENT) ==="]'
assert a2 in s
block = '    _ccp=_call_center_plan(report["leads"])' + chr(10) + '    lines += ["", "=== CALL CENTER PLAN v1 (DRAFT ONLY - SENDS NOTHING) ===", "counts=%s window=%s wa_autosend=%s" % (_ccp["counts"],_ccp["window_open_8am_9pm_et"],_ccp["whatsapp_autosend_enabled"])]' + chr(10)
s = s.replace(a2, block + a2, 1)
dbg = '"frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",'
assert dbg in s
s = s.replace(dbg, dbg + chr(10) + '        "call_center": "call-center-plan-v1",', 1)
route = '@app.route("/call-center", methods=["GET"])' + chr(10) + 'def call_center():' + chr(10) + '    try:' + chr(10) + '        resp = zoho_exec("ZOHO_GET_ZOHO_RECORDS", {"module_api_name":"Leads","fields":"First_Name,Last_Name,Full_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time","sort_by":"Created_Time","sort_order":"desc","per_page":50})' + chr(10) + '        leads = (resp.get("data") or {}).get("data") or []' + chr(10) + '        if not leads and resp.get("error"): return jsonify({"version":"call-center-plan-v1","error":str(resp.get("error"))[:300],"note":"Fix #3 blocks Render Zoho read; code live"}), 207' + chr(10) + '        return jsonify(_call_center_plan(leads)), 200' + chr(10) + '    except Exception as e:' + chr(10) + '        return jsonify({"version":"call-center-plan-v1","error":str(e)[:300]}), 207' + chr(10) + chr(10)
s = s.replace('@app.route("/ping")', route + '@app.route("/ping")', 1)
p.write_text(s)
print('patched', len(s))
pp = pathlib.Path('SOPS/CALL_CENTER.md'); ss = pp.read_text()
if 'call-center-plan-v1' not in ss:
    pp.write_text(ss + chr(10) + '## LIVE BUILD 2026-10-21 - call-center-plan-v1' + chr(10) + 'GET /call-center = draft-only queues (email/whatsapp/human-call/recycle Day3-Day7-Day12/STOP). Sends NOTHING. WhatsApp autosend OFF until template APPROVED + phone VERIFIED + owner enable. Human calls only 8am-9pm ET.' + chr(10))
