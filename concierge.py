import os, time, json, datetime, re
# Keys come from environment variables (set on Render) - safe!

import requests
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import crewai.llm as _crew_llm_mod
from composio import Composio
from composio_crewai import CrewAIProvider

# ====== FIX: strip 'cache_breakpoint' markers that Groq rejects ======
_orig_fmt = _crew_llm_mod.LLM._format_messages_for_provider

def _fmt_no_cache_breakpoint(self, messages):
    if messages:
        messages = [
            {k: v for k, v in m.items() if k != "cache_breakpoint"}
            for m in messages
        ]
    return _orig_fmt(self, messages)

_crew_llm_mod.LLM._format_messages_for_provider = _fmt_no_cache_breakpoint

# ====== Config ======
CAL_API_KEY = os.environ.get("CAL_API_KEY", "")
CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (consultations)
CAL_LINK = "https://cal.com/simply-justtask/simplybook"
CAL_HOME_VISIT_EVENT_TYPE_ID = 7554154  # Home Visit / Estimate (45/60)
CAL_HOME_VISIT_LINK = "https://cal.com/simply-justtask/home-visit"
COMPOSIO_USER_ID = os.environ.get("COMPOSIO_USER_ID", "default")
REPORT_EMAIL = os.environ.get("REPORT_EMAIL", "tasksupport@simplyjusttask.com")
REPORT_CC = os.environ.get("REPORT_CC", "a.quinones@simplyjusttask.com")
ZOHO_MAIL_ACCOUNT_ID = os.environ.get("ZOHO_MAIL_ACCOUNT_ID", "8048488000000008002")  # tasksupport mailbox
# Direct Zoho CRM bypass (owner-entered in Render only; never in chat/code).
ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/")
ZOHO_CRM_API_URL = os.environ.get("ZOHO_CRM_API_URL", "https://www.zohoapis.com").rstrip("/")
_zoho_direct_token = {"value": "", "expires_at": 0}
ZOHO_FROM = os.environ.get("ZOHO_FROM_ADDRESS", "tasksupport@simplyjusttask.com")
CAL_HEADERS = {
    "Authorization": "Bearer " + CAL_API_KEY,
    "Content-Type": "application/json",
}

composio = Composio(provider=CrewAIProvider())

def _zoho_direct_configured():
    return bool(ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN)

def _zoho_direct_access_token():
    now = time.time()
    if _zoho_direct_token["value"] and _zoho_direct_token["expires_at"] > now + 60:
        return _zoho_direct_token["value"]
    r = requests.post(ZOHO_ACCOUNTS_URL + "/oauth/v2/token", data={"grant_type": "refresh_token", "client_id": ZOHO_CLIENT_ID, "client_secret": ZOHO_CLIENT_SECRET, "refresh_token": ZOHO_REFRESH_TOKEN}, timeout=30)
    d = r.json() if r.content else {}
    token = d.get("access_token")
    if not token:
        raise Exception("Direct Zoho token failed HTTP %s: error=%s" % (r.status_code, str(d.get("error") or "unknown")[:80]))
    _zoho_direct_token["value"] = token
    _zoho_direct_token["expires_at"] = now + int(d.get("expires_in") or 3600)
    return token

def _zoho_direct_norm_data(rows):
    out = []
    for row in rows or []:
        if not isinstance(row, dict):
            out.append(row)
            continue
        r2 = dict(row)
        for k, v in list(r2.items()):
            if isinstance(v, dict) and v.get("id") and "module" in v:
                r2[k] = {"id": str(v["id"])}
                if k in ("What_Id", "Who_Id", "Parent_Id"):
                    r2["$se_module"] = str(v["module"])
        out.append(r2)
    return out

def _zoho_direct_exec(slug, args):
    if slug == "ZOHO_MAIL_MESSAGES_SEND_EMAIL":
        return {"error": "Direct Zoho bypass v1 is CRM-only; mail still needs Composio"}
    if not _zoho_direct_configured():
        return {"error": "Direct Zoho bypass not configured in Render env"}
    module = str((args or {}).get("module_api_name") or "")
    if not module:
        return {"error": "Direct Zoho bypass: module_api_name missing"}
    try:
        headers = {"Authorization": "Zoho-oauthtoken " + _zoho_direct_access_token()}
        base = ZOHO_CRM_API_URL + "/crm/v8/" + module
        method, url, params, body = "GET", base, {}, None
        if slug == "ZOHO_SEARCH_ZOHO_RECORDS":
            url = base + "/search"
            params = {k: args[k] for k in ("email", "phone", "word", "criteria", "fields", "per_page", "page") if args.get(k) not in (None, "")}
        elif slug == "ZOHO_GET_ZOHO_RECORDS":
            params = {k: args[k] for k in ("fields", "per_page", "page", "sort_by", "sort_order") if args.get(k) not in (None, "")}
            if args.get("ids"):
                params["ids"] = args["ids"]
        elif slug == "ZOHO_CREATE_ZOHO_RECORD":
            method, url, body = "POST", base, {"data": _zoho_direct_norm_data(args.get("data") or [])}
        elif slug == "ZOHO_UPDATE_ZOHO_RECORD":
            method, url, body = "PUT", base, {"data": _zoho_direct_norm_data(args.get("data") or [])}
        else:
            return {"error": "Direct Zoho bypass does not support slug " + str(slug)}
        r = requests.request(method, url, headers=headers, params=params, json=body, timeout=30)
        if r.status_code == 204:
            return {"data": {"data": [], "info": {}}, "successful": True, "via": "direct_zoho"}
        d = r.json() if r.content else {}
        if r.status_code >= 400:
            return {"error": "Direct Zoho HTTP %s: %s" % (r.status_code, json.dumps(d)[:300])}
        return {"data": d, "successful": True, "via": "direct_zoho"}
    except Exception as e:
        return {"error": "Direct Zoho bypass failed: " + str(e)[:300]}

def _composio_failed(resp):
    if not isinstance(resp, dict):
        return True
    if resp.get("error"):
        return True
    txt = json.dumps(resp, default=str)[:2000]
    return "No connected account found" in txt or "ActionExecute_ConnectedAccountNotFound" in txt

def zoho_exec(slug, args):
    try:
        resp = composio.tools.execute(slug=slug, arguments=args, user_id=COMPOSIO_USER_ID, dangerously_skip_version_check=True)
    except TypeError:
        try:
            resp = composio.tools.execute(slug, args, COMPOSIO_USER_ID)
        except Exception as e:
            resp = {"error": str(e)}
    except Exception as e:
        resp = {"error": str(e)}
    if _composio_failed(resp) and slug.startswith("ZOHO_") and "MAIL" not in slug:
        direct = _zoho_direct_exec(slug, args)
        if not (isinstance(direct, dict) and direct.get("error")):
            print("ZOHO VIA DIRECT BYPASS:", slug)
            return direct
        return {"error": "Direct bypass failed (%s); Composio failed (%s)" % (str(direct.get("error"))[:220], json.dumps(resp, default=str)[:80])}
    return resp
def zoho_ok(resp):
    return isinstance(resp, dict) and not resp.get("error") and resp.get("successful", True)

@tool("save_lead")
def save_lead(full_name: str, email: str, phone: str, address: str,
              service_needed: str, grade: str) -> str:
    """Save a new lead to the Zoho CRM Leads module.
    Args: full_name, email, phone, property address/city, service_needed,
    grade = 'A' (high intent) or 'B' (browsing)."""
    parts = full_name.strip().split()
    first, last = parts[0], (parts[-1] if len(parts) > 1 else parts[0])
    # Dedupe by email
    try:
        existing = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS",
                             {"module_api_name": "Leads", "email": email,
                              "fields": "id,Full_Name,Email", "per_page": 1})
        data = (existing.get("data") or {}).get("data") if isinstance(existing, dict) else None
        if data:
            return "SUCCESS: lead already exists in CRM with id " + str(data[0].get("id"))
    except Exception:
        pass
    desc = ("Address: %s | Service: %s | Grade: %s | Source: Website Concierge" %
            (address, service_needed, grade.upper()))
    resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {
        "module_api_name": "Leads",
        "data": [{
            "First_Name": first, "Last_Name": last,
            "Email": email, "Phone": phone,
            "Company": address or "Residential",
            "City": address,
            "Description": desc,
            "Lead_Source": "Chat",
            "Lead_Status": "Not Contacted",
        }],
    })
    try:
        recs = (resp.get("data") or {}).get("data") or []
        if recs and recs[0].get("code") == "SUCCESS":
            return "SUCCESS: lead saved to Zoho CRM with id " + str(recs[0]["details"]["id"])
        return "ERROR: lead save failed: " + json.dumps(resp)[:300]
    except Exception:
        return "ERROR: lead save failed: " + json.dumps(resp)[:300]

@tool("lookup_lead")
def lookup_lead(email_or_phone: str) -> str:
    """Look up a returning customer in Zoho CRM by email or phone to remember past
    interactions, notes, and AI qualification. Use when a guest gives contact info."""
    for key in ({"email": email_or_phone}, {"phone": email_or_phone}):
        try:
            args = {"module_api_name": "Leads",
                    "fields": "Full_Name,Email,Phone,City,Lead_Status,Description"}
            args.update(key)
            r = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", args)
            data = (r.get("data") or {}).get("data") if isinstance(r, dict) else None
            if data:
                d = data[0]
                return ("FOUND returning lead: %s | status %s | notes: %s" %
                        (d.get("Full_Name"), d.get("Lead_Status"),
                         (d.get("Description") or "")[:400]))
        except Exception:
            pass
    return "No existing record - brand new guest."


# ====== Frankenstein Part 3: REAL CONFIRMED APPOINTMENTS ONLY (owner go 2026-10-20) ======
# PART3_REAL_APPOINTMENTS_V1
# Concierge may book: consultation by phone / virtual / in person (event
# 7325379 simplybook) AND Home Visit / Estimate (event 7554154 home-visit).
# A booking only counts when Cal returns a real UID and a re-fetch proves
# status accepted + right event + right attendee + right time + real address
# on the record. Only then: Zoho Lead -> Appointment Set + human Zoho Task.
try:
    ET_ZONE = ZoneInfo("America/New_York") if ZoneInfo else datetime.timezone(datetime.timedelta(hours=-4))
except Exception:
    ET_ZONE = datetime.timezone(datetime.timedelta(hours=-4))

def _clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()

def _is_real_address(address):
    a = _clean(address)
    low = a.lower()
    if len(a) < 16 or "@" in a:
        return False
    bad = ("tbd", "to be determined", "unknown", "n/a", "none", "no address",
           "test address", "fake", "example", "online", "virtual", "phone only",
           "p.o. box", "po box")
    if any(x in low for x in bad):
        return False
    if not re.match(r"^\d+[A-Za-z]?\s+", a):
        return False
    suffix = r"(?:street|st|avenue|ave|boulevard|blvd|road|rd|lane|ln|drive|dr|court|ct|circle|cir|way|trail|trl|place|pl|parkway|pkwy|loop|terrace|ter|highway|hwy|point|pt)\.?"
    if not re.search(r"\b" + suffix + r"(?:\s|,|$)", low):
        return False
    if not re.search(r"\b(fl|florida)\b", low):
        return False
    if not re.search(r"\b\d{5}(?:-\d{4})?\b", a):
        return False
    return len(re.findall(r"[A-Za-z]+", a)) >= 5

def _is_email(v):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", _clean(v)))

def _is_phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return len(d) == 10 and len(set(d)) > 1 and d not in ("1234567890",)

def _parse_dt(v):
    try:
        dt = datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET_ZONE)
    return dt

def _appt_config(appointment_type, consultation_mode="phone"):
    k = re.sub(r"[^a-z0-9]+", "_", str(appointment_type or "consultation").lower()).strip("_")
    m = re.sub(r"[^a-z0-9]+", "_", str(consultation_mode or "phone").lower()).strip("_")
    if k in ("home_visit", "home", "estimate", "home_visit_estimate", "in_home", "in_home_visit"):
        return {"kind": "home_visit", "event_type_id": CAL_HOME_VISIT_EVENT_TYPE_ID,
                "slug": "home-visit", "label": "Home Visit / Estimate",
                "link": CAL_HOME_VISIT_LINK, "durations": (45, 60), "default": 60,
                "mode": "in_person", "mode_label": "in person at customer home"}
    if k in ("phone", "virtual", "video", "online", "in_person", "inperson", "face_to_face"):
        m = k
        k = "consultation"
    if k in ("consultation", "consult", "simplybook", "appointment"):
        modes = {"phone": "phone", "call": "phone", "telephone": "phone",
                 "virtual": "virtual", "video": "virtual", "online": "virtual",
                 "zoom": "virtual", "meet": "virtual", "remote": "virtual",
                 "in_person": "in_person", "inperson": "in_person",
                 "face_to_face": "in_person", "person": "in_person"}
        mode = modes.get(m, "phone")
        labels = {"phone": "Phone Consultation", "virtual": "Virtual Consultation",
                  "in_person": "In-Person Consultation"}
        return {"kind": "consultation", "event_type_id": CAL_EVENT_TYPE_ID,
                "slug": "simplybook", "label": labels[mode],
                "link": CAL_LINK, "durations": (30, 45, 60, 120), "default": 30,
                "mode": mode, "mode_label": mode.replace("_", " ")}
    return None

def _duration(cfg, value):
    try:
        d = int(value or 0)
    except Exception:
        return None
    if d == 0:
        return cfg["default"]
    return d if d in cfg["durations"] else None

def _resp_data(payload):
    return payload.get("data") if isinstance(payload, dict) else None

def _booking_info(raw):
    if not isinstance(raw, dict):
        return {}
    ev = raw.get("eventType") if isinstance(raw.get("eventType"), dict) else {}
    emails = []
    attendees = raw.get("attendees") or []
    if isinstance(attendees, list):
        for a in attendees:
            if isinstance(a, dict) and a.get("email"):
                emails.append(str(a["email"]).lower())
    att = raw.get("attendee") if isinstance(raw.get("attendee"), dict) else {}
    if att.get("email"):
        emails.append(str(att["email"]).lower())
    return {"uid": str(raw.get("uid") or raw.get("bookingUid") or ""),
            "id": raw.get("id"),
            "status": str(raw.get("status") or "").lower(),
            "event_type_id": raw.get("eventTypeId") or ev.get("id"),
            "start": raw.get("start") or raw.get("startTime") or "",
            "end": raw.get("end") or raw.get("endTime") or "",
            "emails": emails, "raw": raw}

def _cal_get_booking(ref):
    last = ""
    for ver in ("2024-08-13", "2024-09-04"):
        try:
            r = requests.get("https://api.cal.com/v2/bookings/" + str(ref),
                             headers={**CAL_HEADERS, "cal-api-version": ver}, timeout=30)
            try:
                d = r.json()
            except Exception:
                d = {}
            info = _booking_info(_resp_data(d))
            if r.status_code in (200, 201) and info.get("uid"):
                return info, ""
            last = "Cal verify HTTP %s: %s" % (r.status_code, json.dumps(d)[:200])
        except Exception as e:
            last = "Cal verify error: " + str(e)[:200]
    return {}, last

def _zoho_rows(resp):
    if not isinstance(resp, dict):
        return []
    data = resp.get("data")
    if isinstance(data, dict):
        rows = data.get("data")
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    return rows if isinstance(rows, list) else []

def _zoho_write_id(resp):
    rows = _zoho_rows(resp)
    if rows and isinstance(rows[0], dict) and rows[0].get("code") == "SUCCESS":
        details = rows[0].get("details") or {}
        return str(details.get("id") or rows[0].get("id") or "")
    return ""

def _zoho_write_ok(resp):
    if _zoho_write_id(resp):
        return True
    rows = _zoho_rows(resp)
    if rows:
        return isinstance(rows[0], dict) and rows[0].get("code") == "SUCCESS"
    return zoho_ok(resp)

def _find_lead(email, phone):
    for key, val in (("email", email), ("phone", phone)):
        if not val:
            continue
        resp = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS",
                         {"module_api_name": "Leads", key: val,
                          "fields": "id,Full_Name,Email,Phone,Description,Lead_Status",
                          "per_page": 1})
        if isinstance(resp, dict) and resp.get("error"):
            return None, str(resp.get("error"))[:250]
        rows = _zoho_rows(resp)
        if rows:
            return rows[0], ""
    return None, ""

def _find_task(booking_uid):
    try:
        resp = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS",
                         {"module_api_name": "Tasks", "word": booking_uid,
                          "fields": "id,Subject,Description,Status", "per_page": 5})
        for row in _zoho_rows(resp):
            if booking_uid in (str(row.get("Subject") or "") + str(row.get("Description") or "")):
                return str(row.get("id") or "")
    except Exception:
        pass
    try:
        resp = zoho_exec("ZOHO_GET_ZOHO_RECORDS",
                         {"module_api_name": "Tasks",
                          "fields": "Subject,Description,What_Id,Status",
                          "sort_by": "Modified_Time", "sort_order": "desc", "per_page": 200})
        for row in _zoho_rows(resp):
            if booking_uid in (str(row.get("Subject") or "") + str(row.get("Description") or "")):
                return str(row.get("id") or "")
    except Exception:
        pass
    return ""

def _sync_confirmed_booking(full_name, email, phone, address, service_needed,
                            start_iso, appointment_label, booking_uid):
    result = {"lead_id": "", "task_id": "", "already_synced": False, "errors": []}
    lead, err = _find_lead(email, phone)
    if err:
        result["errors"].append("Zoho lead search failed: " + err)
        return result
    if not lead:
        parts = full_name.strip().split()
        first = parts[0] if parts else "Customer"
        last = parts[-1] if len(parts) > 1 else first
        desc0 = ("Address: %s | Service: %s | Source: Website Concierge confirmed %s"
                 % (address, service_needed, appointment_label))
        resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {
            "module_api_name": "Leads",
            "data": [{"First_Name": first, "Last_Name": last, "Email": email,
                      "Phone": phone, "Company": address or "Residential",
                      "City": address, "Address": address, "Description": desc0,
                      "Lead_Source": "Chat", "Lead_Status": "Not Contacted"}]})
        lead_id = _zoho_write_id(resp)
        if not lead_id:
            result["errors"].append("Zoho lead create failed: " + json.dumps(resp, default=str)[:300])
            return result
        lead = {"id": lead_id, "Description": desc0, "Lead_Status": "Not Contacted"}
    lead_id = str(lead.get("id") or "")
    result["lead_id"] = lead_id
    if not lead_id:
        result["errors"].append("Zoho lead has no id")
        return result
    marker = "[Cal " + booking_uid + "]"
    old_desc = str(lead.get("Description") or "")
    task_id = _find_task(booking_uid)
    if task_id and marker in old_desc and str(lead.get("Lead_Status") or "") == "Appointment Set":
        result["task_id"] = task_id
        result["already_synced"] = True
        return result
    if not task_id:
        try:
            due = _parse_dt(start_iso).astimezone(ET_ZONE).date().isoformat()
        except Exception:
            due = str(start_iso)[:10]
        subject = ("%s: %s - %s [Cal %s]" % (appointment_label, full_name, due, booking_uid))[:240]
        tdesc = "\n".join([
            "REAL CONFIRMED APPOINTMENT - human must handle this appointment.",
            "Type: " + appointment_label,
            "When (as booked): " + str(start_iso),
            "Customer: %s | %s | %s" % (full_name, email, phone),
            "Real address: " + address,
            "Service needed: " + service_needed,
            "Cal booking UID: " + booking_uid,
            "Customer explicitly confirmed this exact appointment before booking.",
            "Customer is aware via Cal confirmation. Human is aware via Cal calendar + this Zoho Task.",
            "Home Visit is booked ONLY when Type is Home Visit / Estimate. Otherwise human decides next steps at the consultation.",
        ])
        resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {
            "module_api_name": "Tasks",
            "data": [{"Subject": subject, "Status": "Not Started", "Priority": "High",
                      "Due_Date": due, "Description": tdesc,
                      "What_Id": {"id": lead_id, "module": "Leads"}}]})
        task_id = _zoho_write_id(resp)
        if not task_id:
            result["errors"].append("Zoho Task create failed: " + json.dumps(resp, default=str)[:300])
            return result
    result["task_id"] = task_id
    note = ("\n%s %s CONFIRMED in Cal for %s at %s. Customer confirmed exact "
            "appointment. Zoho Task %s. Human: handle this real appointment."
            % (marker, appointment_label, start_iso, address, task_id))
    new_desc = old_desc if marker in old_desc else (old_desc + note)[:2000]
    resp = zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
        "module_api_name": "Leads",
        "data": [{"id": lead_id, "Lead_Status": "Appointment Set",
                  "Description": new_desc}]})
    if not _zoho_write_ok(resp):
        result["errors"].append("Zoho Lead Appointment Set update failed: "
                                 + json.dumps(resp, default=str)[:300])
    return result

def _sync_recent_cal_bookings(limit=50):
    result = {"checked": 0, "synced": 0, "already_synced": 0, "skipped": [], "errors": []}
    if not CAL_API_KEY:
        result["errors"].append("CAL_API_KEY not loaded")
        return result
    try:
        r = requests.get("https://api.cal.com/v2/bookings",
                         headers={**CAL_HEADERS, "cal-api-version": "2024-08-13"},
                         params={"take": int(limit), "skip": 0, "sortStart": "asc"},
                         timeout=30)
        try:
            d = r.json()
        except Exception:
            d = {}
        if r.status_code not in (200, 201):
            result["errors"].append("Cal bookings list HTTP %s: %s"
                                     % (r.status_code, json.dumps(d)[:250]))
            return result
    except Exception as e:
        result["errors"].append("Cal bookings list failed: " + str(e)[:250])
        return result
    data = _resp_data(d)
    bookings = data if isinstance(data, list) else []
    if isinstance(data, dict):
        bookings = data.get("data") or data.get("bookings") or []
    now = datetime.datetime.now(datetime.timezone.utc)
    for b in bookings if isinstance(bookings, list) else []:
        info = _booking_info(b)
        if info["status"] not in ("accepted", "confirmed"):
            continue
        try:
            ev_id = int(info.get("event_type_id") or 0)
        except Exception:
            ev_id = 0
        if ev_id not in (CAL_EVENT_TYPE_ID, CAL_HOME_VISIT_EVENT_TYPE_ID):
            continue
        sdt = _parse_dt(info.get("start"))
        if sdt and sdt < now - datetime.timedelta(hours=1):
            continue
        result["checked"] += 1
        uid = info.get("uid")
        attendees = b.get("attendees") or []
        att = attendees[0] if attendees and isinstance(attendees[0], dict) else {}
        name = _clean(att.get("name") or "")
        email = _clean(att.get("email") or "").lower()
        bfr = b.get("bookingFieldsResponses") or {}
        meta = b.get("metadata") or {}
        phone = _clean(att.get("phoneNumber") or bfr.get("attendeePhoneNumber") or meta.get("phone") or "")
        address = ""
        loc = b.get("location")
        if isinstance(loc, str):
            address = loc
        if not _is_real_address(address):
            loc_resp = bfr.get("location") or {}
            if isinstance(loc_resp, dict):
                address = _clean(loc_resp.get("optionValue") or "")
        if not _is_real_address(address):
            address = _clean(meta.get("address") or "")
        if not uid or not name or not _is_email(email) or not _is_phone(phone):
            result["skipped"].append({"uid": uid, "reason": "missing real name/email/phone"})
            continue
        if not _is_real_address(address):
            result["skipped"].append({"uid": uid, "reason": "missing real address - not synced as solid appointment"})
            continue
        if ev_id == CAL_HOME_VISIT_EVENT_TYPE_ID:
            label = "Home Visit / Estimate"
        else:
            blob = (str(bfr.get("cunsultation-Tyoe") or "") + " " + str(meta.get("consultation_mode") or "")).lower()
            if "virtual" in blob or "video" in blob or "online" in blob:
                label = "Virtual Consultation"
            elif "phone" in blob:
                label = "Phone Consultation"
            elif "person" in blob:
                label = "In-Person Consultation"
            else:
                label = "Consultation"
        service = _clean(meta.get("service") or bfr.get("notes") or b.get("description") or label)
        sync = _sync_confirmed_booking(name, email, phone, address, service,
                                       str(info.get("start") or ""), label, uid)
        if sync["errors"]:
            result["errors"].append({"uid": uid, "errors": sync["errors"]})
        elif sync.get("already_synced"):
            result["already_synced"] += 1
        else:
            result["synced"] += 1
    return result

@tool("check_availability")
def check_availability(start_date: str, end_date: str, appointment_type: str = "consultation",
                       consultation_mode: str = "phone", duration_minutes: int = 0) -> str:
    """Check real open slots. appointment_type: consultation or home_visit.
    consultation_mode: phone, virtual, or in_person. duration_minutes:
    consultation 30/45/60/120, home_visit 45/60. Only offer slots returned here."""
    cfg = _appt_config(appointment_type, consultation_mode)
    if not cfg:
        return "ERROR: appointment_type must be consultation or home_visit."
    duration = _duration(cfg, duration_minutes)
    if not duration:
        return ("ERROR: duration must be one of %s minutes for %s."
                % ("/".join(str(x) for x in cfg["durations"]), cfg["label"]))
    if not CAL_API_KEY:
        return "ERROR: booking calendar not configured. Share the booking link instead: " + cfg["link"]
    try:
        r = requests.get(
            "https://api.cal.com/v2/slots",
            headers={**CAL_HEADERS, "cal-api-version": "2024-09-04"},
            params={"eventTypeId": cfg["event_type_id"], "start": start_date,
                    "end": end_date, "timeZone": "America/New_York",
                    "duration": duration},
            timeout=30)
        try:
            payload = r.json()
        except Exception:
            payload = {}
        if r.status_code not in (200, 201):
            return "ERROR: Cal slots HTTP %s: %s" % (r.status_code, json.dumps(payload)[:250])
    except Exception as e:
        return "ERROR: Cal slots failed: " + str(e)[:250]
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    if not data:
        return "No open slots in that range. Suggest a different week."
    lines = []
    if isinstance(data, dict):
        for day, slots in data.items():
            times = []
            for s in slots if isinstance(slots, list) else []:
                st = s.get("start") if isinstance(s, dict) else str(s)
                times.append(str(st)[11:16])
            if times:
                lines.append(day + ": " + ", ".join(times[:8]))
    if not lines:
        return "No open slots in that range. Suggest a different week."
    return ("Available %s slots (%s min, Eastern Time):\n" % (cfg["label"], duration)
            + "\n".join(lines))

@tool("book_appointment")
def book_appointment(full_name: str, email: str, phone: str, address: str,
                     service_needed: str, start_iso: str,
                     appointment_type: str = "consultation",
                     consultation_mode: str = "phone",
                     duration_minutes: int = 0,
                     customer_confirmed: bool = False) -> str:
    """Book a REAL confirmed appointment. Call ONLY after the customer explicitly
    confirms the exact appointment type/mode, date/time, duration and real
    address, and set customer_confirmed=True only then. appointment_type:
    consultation or home_visit. consultation_mode: phone/virtual/in_person.
    Returns BOOKED_AND_CONFIRMED only when Cal re-fetch proves accepted."""
    cfg = _appt_config(appointment_type, consultation_mode)
    if not cfg:
        return "NOT_BOOKED: appointment_type must be consultation or home_visit."
    duration = _duration(cfg, duration_minutes)
    if not duration:
        return ("NOT_BOOKED: duration must be one of %s minutes for %s."
                % ("/".join(str(x) for x in cfg["durations"]), cfg["label"]))
    label = cfg["label"]
    if not customer_confirmed:
        return ("NOT_BOOKED: customer has not explicitly confirmed this exact "
                + label + " appointment. Read back type, date/time, duration and "
                "real address and ask them to say yes first.")
    full_name, email, phone, address = _clean(full_name), _clean(email).lower(), _clean(phone), _clean(address)
    service_needed = _clean(service_needed)
    if len(full_name) < 3 or not any(c.isalpha() for c in full_name):
        return "NOT_BOOKED: real full customer name is required."
    if not _is_email(email):
        return "NOT_BOOKED: a real customer email is required."
    if not _is_phone(phone):
        return "NOT_BOOKED: a real 10-digit customer phone is required."
    if not _is_real_address(address):
        return ("NOT_BOOKED: a REAL full street address is required for every "
                "appointment (house number, street, city, FL and ZIP). No booking without it.")
    if len(service_needed) < 3:
        return "NOT_BOOKED: service needed is required."
    sdt = _parse_dt(start_iso)
    if not sdt:
        return "NOT_BOOKED: start time must be an exact ISO slot from check_availability."
    if sdt <= datetime.datetime.now(datetime.timezone.utc):
        return "NOT_BOOKED: that time is in the past. Offer a future real slot."
    if not CAL_API_KEY:
        return "NOT_BOOKED: booking calendar not configured. Share: " + cfg["link"]
    body = {
        "start": start_iso,
        "eventTypeId": cfg["event_type_id"],
        "attendee": {"name": full_name, "email": email,
                     "timeZone": "America/New_York", "language": "en",
                     "phoneNumber": phone},
        "metadata": {"phone": phone, "address": address, "service": service_needed,
                     "source": "website concierge", "appointment_type": cfg["kind"],
                     "consultation_mode": cfg["mode"],
                     "customer_confirmed": "explicit_exact_slot_yes"},
    }
    if duration != cfg["default"]:
        body["lengthInMinutes"] = duration
    if cfg["kind"] == "home_visit":
        body["location"] = {"type": "attendeeInPerson", "address": address}
    try:
        r = requests.post("https://api.cal.com/v2/bookings",
                          headers={**CAL_HEADERS, "cal-api-version": "2024-08-13"},
                          json=body, timeout=30)
        try:
            d = r.json()
        except Exception:
            d = {}
    except Exception as e:
        return "NOT_BOOKED: Cal booking request failed: " + str(e)[:250]
    if r.status_code not in (200, 201) or not isinstance(d, dict) or d.get("status") != "success":
        return "NOT_BOOKED: Cal.com rejected the booking: " + json.dumps(d, default=str)[:300]
    created = _booking_info(_resp_data(d))
    ref = created.get("uid") or (str(created.get("id")) if created.get("id") else "")
    if not ref:
        return "NOT_CONFIRMED: Cal.com returned no booking UID. Do not tell the customer it is booked."
    verified, verr = _cal_get_booking(ref)
    if not verified:
        return ("NOT_CONFIRMED: Cal booking ref %s could not be verified as a real "
                "appointment (%s). Do not tell the customer it is booked. Zoho untouched."
                % (ref, verr))
    uid = verified.get("uid") or ref
    if verified.get("status") not in ("accepted", "confirmed"):
        return ("NOT_CONFIRMED: Cal booking %s status is %s, not accepted. "
                "Do not tell the customer it is booked. Zoho untouched."
                % (uid, verified.get("status") or "unknown"))
    try:
        ev_ok = int(verified.get("event_type_id") or 0) == int(cfg["event_type_id"])
    except Exception:
        ev_ok = False
    if not ev_ok:
        return "NOT_CONFIRMED: Cal booking %s is for the wrong event type. Zoho untouched." % uid
    if verified.get("emails") and email not in verified["emails"]:
        return "NOT_CONFIRMED: Cal booking %s attendee email does not match. Zoho untouched." % uid
    vdt = _parse_dt(verified.get("start"))
    if vdt and abs((vdt - sdt).total_seconds()) > 180:
        return "NOT_CONFIRMED: Cal booking %s time does not match the chosen slot. Zoho untouched." % uid
    blob = json.dumps(verified.get("raw") or {}, default=str).lower()
    zipm = re.search(r"\b\d{5}(?:-\d{4})?\b", address)
    house = address.split()[0].lower() if address.split() else ""
    if house and house not in blob and (not zipm or zipm.group(0) not in blob):
        return ("NOT_CONFIRMED: Cal booking %s does not show the real address on "
                "the Cal record. Do not claim it is solid. Zoho untouched." % uid)
    sync = _sync_confirmed_booking(full_name, email, phone, address, service_needed,
                                   start_iso, label, uid)
    if sync["errors"]:
        return ("BOOKED_AND_CONFIRMED_IN_CAL_BUT_ZOHO_SYNC_FAILED: %s on %s at %s. "
                "Cal UID %s is real and accepted; customer gets Cal confirmation and "
                "the human sees the Cal calendar, but Zoho Lead/Task sync FAILED: %s "
                "Team must fix Zoho manually. Do not claim Zoho is done."
                % (label, full_name, start_iso, uid, "; ".join(sync["errors"])))
    return ("BOOKED_AND_CONFIRMED: %s for %s on %s (%s min). Cal UID %s verified "
            "accepted. Customer gets Cal confirmation. Human gets Cal calendar + "
            "Zoho Task %s. Zoho Lead %s is Appointment Set. Real address: %s"
            % (label, full_name, start_iso, duration, uid,
               sync.get("task_id"), sync.get("lead_id"), address))

# ====== Business brain ======
TODAY = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d")

MASTER_KNOWLEDGE = """
=== SIMPLY JUST TASK - MASTER KNOWLEDGE BASE v1.0 ===
Tagline: Reliable Help for Everyday Life.
One Call. One Contact. One Less Thing To Worry About.
We are not in the task business. We are in the peace-of-mind business.

COMPANY INFO
Website: SimplyJustTask.com | Email: tasksupport@simplyjusttask.com
Customer Service: (888) 566-7570 | Office: (321) 236-5574
Address: 2246 E Semoran Blvd, Suite 2082, Apopka, FL 32703

COMPANY STORY
Simply Just Task began in 2024 helping neighbors and community members with
errands, deliveries, projects, and everyday needs. Built on kindness and
family values; legally established in late 2025. Name inspired by the phrase
'Why don't you just ask.'

LEADERSHIP
Anthony Quinones - CEO & President, Customer Service & Client Relations
Michael Sabo - VP & Head of Operations, Dream Makers Landscape Design Division
Gary Greenawalt - CFO, Billing, Finance, Invoicing, Job & Task Assignment
Derrick McAlister - Head of Engineering & Small Engine Division

SERVICES
Concierge Services, Handyman Services, Cleaning Services, Landscape Design,
Property Services, Small Engine Services, Business Support, Administrative
Services, Appointment Scheduling, Project Coordination, AI & Technology Services.

HOURS
Mon-Fri 9:00 AM-5:00 PM ET | Sat-Sun 11:00 AM-4:00 PM ET

SOCIAL MEDIA
Facebook: Simply Just Task | Instagram: @simply_just_task | YouTube: Simply Just Task

=== PRICING RULES ===
Golden Rule 1: Always try to give a flat-rate project quote first. Customers
prefer knowing the final cost. Preferred: fixed price. Secondary: hourly.
Large projects: custom proposal.
Golden Rule 2: If scope is unclear, collect info BEFORE quoting. Ask: what
service, address, timeline, materials included, project size, photos.
Golden Rule 3: Never underprice. Travel time, fuel, experience, insurance,
and customer service all have value.

PRICING GUIDELINES (ESTIMATES ONLY - ranges, never guarantees):
CLEANING: apartment/small home $100-150 | standard house (3 bed/2 bath) $140-200 |
  deep clean $220-380 | move-in/move-out $250-450 | Airbnb turnover $100-160 |
  commercial: custom proposal (collect sqft, frequency, building type first)
HANDYMAN: TV mounting $90-180 | furniture assembly $80-250 | general repairs
  $75-120/hr | drywall/patching $100-250 | ceiling fan $125-300 | door repair
  $100-350 | half-day multi-job $250-400 | large projects: custom proposal
LAWN & LANDSCAPE: mow + edge (standard lot) $45-75/visit | full yard cleanup
  $150-350 | mulching/trimming $120-300 | consult $75-150 | design $250-1,500+
PRESSURE WASHING: driveway $100-200 | house exterior $200-400
ERRAND RUNNING: grocery run + delivery $35-55 plus store receipt | pickups and
  drop-offs $25-40 | multi-stop errand hour $35-50/hr
CONCIERGE/ADMIN: coordination from $75/project or $50-75/hr
SMALL ENGINE: diagnostic $50-100 | tune-up $100-250 | repair: quote after inspection
AI/TECH: website help $150-500 | website dev $750-5,000+ | AI setup from $250

FLEXIBLE PRICING PROMISE (use this wording):
Our pricing is FLEXIBLE and NEGOTIABLE. After giving a range, ALWAYS add warmly:
"These are honest estimates - our pricing is flexible and we work with your
budget. Your free in-person estimate is where we lock in a number that works
for you. No pressure, no hidden fees." We promise to be CLOSE to the estimate
but never guarantee exact pricing. Use every price question as a reason to book
the FREE estimate - never argue about price, always pivot to booking. If pushed
for a firm number, say a team member will work it out personally at the visit.

TRAVEL FEES: within 15 miles of Apopka: free | 15-30 miles: $20 | beyond 30: custom quote
EMERGENCY: same-day +25% | after-hours +50% | holidays: custom quote

DISCOUNTS: may offer MANAGEMENT REVIEW for seniors, veterans, first responders,
nonprofits, repeat customers. Discounts are never automatically guaranteed.

REVENUE PROTECTION: NEVER give a firm quote when materials unknown, photos
unavailable, scope unclear, multiple trades involved, or requirements change.
Instead say: 'Based on the information provided, we'd recommend a consultation
so we can provide an accurate fixed-price quote.'
When uncertain, say: 'Every project is unique, and Simply Just Task prefers
transparent flat-rate pricing whenever possible. I'd be happy to gather a few
details and connect you with our team for a customized quote.'

=== PAYMENTS ===
Accepted: Cash, Check, Credit Cards, Debit Cards, Zelle, Cash App, Venmo,
PayPal, Business Checks, Electronic Invoices, Bank Transfers (when applicable).
Terms vary by service type, project size, materials, vendors, contract,
timeline. Some projects require deposit, progress payments, materials upfront,
or final payment on completion.

PRICING DISCLAIMER: pricing examples are general guidelines; final pricing may
vary with scope, location, materials, labor, duration, travel, accessibility,
urgency, vendor costs. Never guarantee final pricing without full scope.

QUOTE AUTHORITY:
You MAY: provide ranges, starting rates, explain pricing philosophy, gather info.
You MAY NOT: approve discounts, guarantee final prices, modify contracts, override policies.
MANAGEMENT APPROVAL REQUIRED for: discounts over 10%, projects over $1,000,
commercial contracts, recurring contracts, payment arrangements, special pricing.

COMPANY POLICY: fair, honest, transparent pricing; exceptional value; reliable
service; long-term relationships, not one-time transactions.
"""

BUSINESS_INFO = (
    """You are the friendly concierge for Simply Just Task, serving Central Florida
homeowners. Be warm, concise, human, and helpful. RESIDENTIAL focus; for
commercial requests, say we specialize in residential and a team member will
follow up. If you do not know something, say so and offer to take a message.

TODAY'S DATE: """ + TODAY + """ (Eastern Time)
CONSULTATION LINK (fallback only, never claim booked from a link): """ + CAL_LINK + """
HOME VISIT / ESTIMATE LINK (fallback only): """ + CAL_HOME_VISIT_LINK + MASTER_KNOWLEDGE + """

=== CONVERSATION FLOW (from the Booking Folio - follow it!) ===

STEP 1 - WARM GREETING
Open like: "Hi! Welcome to Simply Just Task! I'm your concierge. I help
homeowners get connected with Anthony for a quick estimate. Are you looking
for help with a residential property?"

STEP 2 - COLLECT LEAD INFO (one question at a time, conversational!)
Collect: full name, real email, real phone, REAL full street address
(house number, street, city, FL and ZIP - no booking without it), and the
service they need. A city alone is NOT a real address.

STEP 3 - GRADE THE LEAD
- Grade A (high intent) if ANY: mentions a specific service or project,
  asks about pricing or timeline, has a property address ready, or says
  ASAP / urgent / ready to start.
- Grade B (lower intent): just browsing, vague on service, no address or
  timeline.

STEP 4 - SAVE THE LEAD (as soon as you have name + email + phone)
Call the save_lead tool with the collected info and the grade.
IMPORTANT: only tell the guest their info was captured if the tool returns
SUCCESS. If it returns ERROR, say a team member will follow up instead.
Do NOT mention internal systems to the visitor.

STEP 5 - QUALIFY & BOOK REAL APPOINTMENTS (Grade A leads, or any guest who explicitly asks to book)
Ask which appointment they want:
- Consultation by PHONE, VIRTUAL, or IN PERSON (Simply Stress-Free Booking)
- Home Visit / Estimate at their real home address (separate Home Visit event)
Consultation durations: 30/45/60/120 min. Home Visit durations: 45/60 min.
1. Ask their preferred day.
2. Use check_availability for that week WITH the correct appointment_type
   (consultation or home_visit), consultation_mode and duration. Offer 2-3 times.
3. Read back the EXACT appointment: type/mode, date and time (ET), duration,
   full name, email, phone, REAL full street address, and service. Ask:
   "Should I book this exact appointment?" Only if they explicitly say yes,
   call book_appointment with customer_confirmed=True. NEVER set
   customer_confirmed=True on an assumption.
4. Only say it is booked if the tool returns BOOKED_AND_CONFIRMED. If it
   returns BOOKED_AND_CONFIRMED_IN_CAL_BUT_ZOHO_SYNC_FAILED, tell them the
   calendar appointment is confirmed and the team will follow up - do NOT
   claim Zoho is done. If it returns NOT_BOOKED or NOT_CONFIRMED, do NOT say
   booked; offer the correct fallback link for that appointment type.

GRADE B leads: thank them, save the lead, and promise a friendly follow-up.

=== HOW TO THINK (partner-level reasoning) ===
You are Anthony's business partner, not a script. Before every reply, silently reason:
1) What does this person ACTUALLY need (the real job behind their words)?
2) What do I already know? If they gave an email or phone earlier, use lookup_lead
   to remember them and reference it naturally (welcome back!).
3) What is the single best next step toward a booked free estimate?
Then speak like a smart, caring human: warm, confident, concise, never robotic.
Remember details they mention within the conversation and use them later.
If you learn something new about the customer, include it when you save_lead
so the CRM gets smarter over time.
"""
)

llm = LLM(model="groq/openai/gpt-oss-120b")
tools = [save_lead, check_availability, book_appointment, lookup_lead]

agent = Agent(
    role="Website Concierge",
    goal="Welcome guests warmly, answer questions using the master knowledge base, qualify residential leads, save them to the pipeline, and book estimate appointments",
    backstory=BUSINESS_INFO,
    tools=tools,
    llm=llm,
    verbose=True,
)

app = Flask(__name__)
CORS(app)

@app.route("/api/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()
    history = request.json.get("history", [])[-12:]
    if not message:
        return jsonify({"reply": "Please type a message! :)"})

    def _autosave():
        try:
            resp = llm.call([
                {"role": "system", "content": "Extract lead info from the message. Reply with ONLY a JSON object with keys: full_name, email, phone, address, service_needed, grade ('A' if ready to start/urgent/specific, else 'B'). Use empty string for anything missing. No markdown."},
                {"role": "user", "content": message},
            ])
            txt = str(resp).strip()
            if txt.startswith("```"):
                txt = txt.strip("`").replace("json", "", 1).strip()
            info = json.loads(txt)
            if info.get("full_name") and info.get("email") and info.get("phone"):
                print("AUTO-SAVE:", save_lead(
                    info["full_name"], info["email"], info["phone"],
                    info.get("address", ""), info.get("service_needed", ""),
                    info.get("grade", "B")))
        except Exception as ex:
            print("auto-extract skipped:", ex)

    threading.Thread(target=_autosave, daemon=True).start()

    convo = ""
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            ("Guest: " if m.get("role") == "user" else "You: ") + str(m.get("content", ""))
            for m in history) + "\n\n"
    task = Task(description=convo + "A website guest asks: " + message,
                expected_output="A short, friendly, helpful reply (2-4 sentences)",
                agent=agent)
    for attempt in range(4):
        try:
            result = Crew(agents=[agent], tasks=[task]).kickoff()
            return jsonify({"reply": str(result)})
        except Exception as e:
            if "rate_limit" in str(e).lower():
                time.sleep(45)
            else:
                return jsonify({"reply": "DEBUG: " + str(e)[:400]})

@app.route("/debug")
def debug():
    return jsonify({
        "crm": "zoho",
        "cal_key_loaded": bool(CAL_API_KEY),
        "cal_consultation_event_id": CAL_EVENT_TYPE_ID,
        "cal_home_visit_event_id": CAL_HOME_VISIT_EVENT_TYPE_ID,
        "cal_booking_sync": "part3-v1-real-confirmed-only",
        "composio_user_id": COMPOSIO_USER_ID,
        "zoho_direct_bypass_configured": _zoho_direct_configured(),
        "zoho_path": "composio-first,direct-crm-fallback-v1",
        "zoho_direct_diag": "error-code-v1",
        "frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",
        "call_center": "call-center-v2,email-gate-8-21ET,stop-line,human-call-list,whatsapp-draft",
        "nextdoor": "kernel-personal-auth,watcher-v2,draft-only",
    })

@app.route("/")
def home():
    return "Concierge is alive!"


# ================= DAILY LEAD PIPELINE (9am crew) =================
import threading

QUALIFY_PROMPT = """You are the lead qualification crew for Simply Just Task, a Central Florida
residential services company (cleaning, handyman, lawn/landscape, pressure washing,
errands, concierge, small engine, AI/tech). Score this lead and reply with ONLY JSON:
{"status": one of "Pre-Qualified", "Not Qualified", "Junk Lead", "Recycled", "Recycled",
 "score": 0-100, "notes": "2-3 sentence AI note on intent, fit, and suggested next step"}
Rules: Pre-Qualified = real person, residential service fit, reachable contact info,
some buying intent. Not Qualified = out of area/commercial/vague. Junk = spam/test/gibberish."""

OUTREACH_DAILY_CAP = int(os.environ.get("OUTREACH_DAILY_CAP", "10"))
CALL_CENTER_CAP = 10
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

OUTREACH_PROMPT = """You are the outreach crew for Simply Just Task. Write a short, warm,
plain-text follow-up email (under 120 words) from Anthony at Simply Just Task to this lead.
Mention their service need, offer a FREE no-pressure estimate, include this booking link:
""" + CAL_LINK + """ (consultation) or """ + CAL_HOME_VISIT_LINK + """ (home visit) and phone (888) 566-7570. Always end with: Reply STOP to opt out. Sign off as 'Anthony & the Simply Just Task Team'.
Reply with ONLY JSON: {"subject": "...", "body": "..."}"""

def _llm_json(system, user):
    resp = llm.call([{"role": "system", "content": system},
                     {"role": "user", "content": user}])
    txt = str(resp).strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:]
    return json.loads(txt.strip())

def run_daily_pipeline():
    _outreach_open = _call_center_window_open()
    report = {"date": datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET"),
        "leads": [], "outreach": [], "errors": [], "cal_sync": {}, "outreach_open": _outreach_open}
    try:
        resp = zoho_exec("ZOHO_GET_ZOHO_RECORDS", {
            "module_api_name": "Leads",
            "fields": "First_Name,Last_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time",
            "sort_by": "Created_Time", "sort_order": "desc", "per_page": 50})
        print("RAW ZOHO FETCH:", json.dumps(resp, default=str)[:800])
        leads = (resp.get("data") or {}).get("data") or []
    except Exception as e:
        leads = []
        report["errors"].append("fetch leads failed: " + str(e)[:200])
    try:
        report["cal_sync"] = _sync_recent_cal_bookings()
        report["errors"].extend(report["cal_sync"].get("errors", []))
    except Exception as e:
        report["errors"].append("cal sync: " + str(e)[:200])
    for ld in leads:
        status = ld.get("Lead_Status")
        name = (ld.get("Full_Name") or ((ld.get("First_Name") or "") + " " + (ld.get("Last_Name") or ""))).strip()
        entry = {"id": ld.get("id"), "name": name, "email": ld.get("Email"),
                 "phone": ld.get("Phone"), "city": ld.get("City"),
                 "source": ld.get("Lead_Source"), "old_status": status}
        try:
            if status in ("Not Contacted", None, "-None-"):
                q = _llm_json(QUALIFY_PROMPT, json.dumps(ld, default=str)[:2000])
                entry["ai_score"] = q.get("score")
                entry["ai_notes"] = q.get("notes")
                raw_status = q.get("status", "Not Qualified")
                # Frankenstein Part 2 recycle pool (owner rule, 2026-10-20): Not Qualified / Recycled = keep, do not drop.
                # Owner added Zoho Lead_Status values Appointment Set + Recycled and Lead_Source values CrewAI/Nextdoor/Instagram/TikTok/YouTube/LinkedIn.
                # Junk Lead is the only true drop.
                new_status = "Recycled" if raw_status in ("Not Qualified", "Recycled") else raw_status
                entry["new_status"] = new_status
                recycled_note = ""
                if new_status == "Recycled":
                    recycled_note = " | Recycle follow-up: +30 days, never delete."
                note = "\n\n[AI Qualifier %s] Score %s/100. %s%s" % (
                    report["date"], q.get("score"), q.get("notes"), recycled_note)
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                    "module_api_name": "Leads",
                    "data": [{"id": str(ld["id"]), "Lead_Status": new_status,
                              "Description": ((ld.get("Description") or "") + note)[:2000]}]})
                if (new_status == "Pre-Qualified" and ld.get("Email")
                        and len(report["outreach"]) >= OUTREACH_DAILY_CAP):
                    entry["ai_notes"] = (entry.get("ai_notes") or "") + " | Outreach QUEUED for tomorrow (daily cap)"
                elif new_status == "Pre-Qualified" and ld.get("Email") and _lead_is_stopped(ld):
                    entry["outreach_suppressed"] = "STOP/opt-out in lead notes - do not contact"
                elif new_status == "Pre-Qualified" and ld.get("Email") and not _outreach_open:
                    entry["outreach_held"] = "outside 8am-9pm ET - hold for next 9AM run, no send at night"
                elif new_status == "Pre-Qualified" and ld.get("Email") and _outreach_open:
                    try:
                        m = _llm_json(OUTREACH_PROMPT, json.dumps(ld, default=str)[:1500])
                        send = zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
                            "accountId": ZOHO_MAIL_ACCOUNT_ID,
                            "fromAddress": ZOHO_FROM,
                            "toAddress": ld["Email"],
                            "subject": m.get("subject", "Your free estimate from Simply Just Task"),
                            "content": m.get("body", ""), "mailFormat": "plaintext"})
                        zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                            "module_api_name": "Leads",
                            "data": [{"id": str(ld["id"]), "Lead_Status": "Attempted to Contact"}]})
                        entry["new_status"] = "Attempted to Contact"
                        entry["outreach_sent"] = zoho_ok(send)
                        report["outreach"].append({"to": ld["Email"], "name": name,
                            "subject": m.get("subject"), "body": m.get("body"),
                            "sent": zoho_ok(send)})
                    except Exception as e:
                        report["errors"].append("outreach %s: %s" % (name, str(e)[:200]))
            else:
                entry["new_status"] = status
                entry["ai_notes"] = "Skipped - already " + str(status)
        except Exception as e:
            report["errors"].append("qualify %s: %s" % (name, str(e)[:200]))
        report["leads"].append(entry)
    # Build + send report email
    lines = ["DAILY LEAD PIPELINE REPORT - " + report["date"], "",
             "Leads reviewed: %d | Outreach sent: %d | Errors: %d" % (
                 len(report["leads"]),
                 sum(1 for o in report["outreach"] if o.get("sent")),
                 len(report["errors"])), "", "Cal sync: " + json.dumps(report.get("cal_sync", {}), default=str)[:1200], "", "=== LEADS ==="]
    for e in report["leads"]:
        lines.append("- %s | %s | %s | %s" % (e.get("name"), e.get("email"),
                                              e.get("phone"), e.get("city")))
        lines.append("  source: %s | status: %s -> %s | score: %s" % (
            e.get("source"), e.get("old_status"), e.get("new_status"), e.get("ai_score", "-")))
        lines.append("  AI notes: %s" % (e.get("ai_notes") or "-"))
    _ccp=_call_center_plan(report["leads"])
    lines += ["", "=== CALL CENTER PLAN v1 (DRAFT ONLY - SENDS NOTHING) ===", "counts=%s window=%s wa_autosend=%s" % (_ccp["counts"],_ccp["window_open_8am_9pm_et"],_ccp["whatsapp_autosend_enabled"])]
    for _c in _ccp.get("human_call_list") or []:
        lines.append("- HUMAN CALL %s (%s) | %s" % (_c.get("name"), _c.get("phone"), _c.get("script")))
    lines += ["", "=== WHATSAPP DRAFTS (DRAFT ONLY - NOT SENT) ==="]
    lines.append("WhatsApp cold text blocked until approved template + VERIFIED. Owner-send drafts only.")
    _wa = [e for e in report["leads"] if e.get("phone") and e.get("new_status") in ("Pre-Qualified", "Attempted to Contact")]
    if not _wa:
        lines.append("- none today")
    for e in _wa:
        _parts = str(e.get("name") or "").split()
        _first = _parts[0] if _parts else "there"
        lines.append("- DRAFT to %s (%s): Hello %s, this is Anthony from Simply Just Task. We received your request and can help. Reply YES to talk or STOP to opt out. Booking: %s" % (e.get("name"), e.get("phone"), _first, CAL_LINK))
    lines += ["", "=== RECYCLE CANDIDATES (DRAFT ONLY - NO SEND) ==="]
    _rc = [e for e in report["leads"] if e.get("new_status") in ("Recycled", "Contact in Future")]
    if not _rc:
        lines.append("- none in newest 50")
    for e in _rc:
        lines.append("- %s | status: %s | follow-up +30 days, never delete" % (e.get("name"), e.get("new_status")))
    lines += ["", "=== OUTREACH COPIES ==="]
    for o in report["outreach"]:
        lines.append("TO: %s (%s) | sent=%s" % (o.get("to"), o.get("name"), o.get("sent")))
        lines.append("SUBJECT: " + str(o.get("subject")))
        lines.append(str(o.get("body")))
        lines.append("---")
    if report["errors"]:
        lines += ["", "=== ERRORS ==="] + report["errors"]
    body = "\n".join(lines)
    try:
        zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
            "accountId": ZOHO_MAIL_ACCOUNT_ID, "fromAddress": ZOHO_FROM,
            "toAddress": REPORT_EMAIL, "ccAddress": REPORT_CC,
            "subject": "SJT Lead Machine Report - " + report["date"],
            "content": body, "mailFormat": "plaintext"})
    except Exception as e:
        print("report email failed:", e)
    print(body)


# ================= SOCIAL MEDIA CREW =================
SOCIAL_PLATFORMS = ["facebook", "instagram", "twitter"]  # twitter re-added 2026-10-19: @simplyjusttask connected in Composio

def run_social_pipeline():
    rep = {"date": datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET"),
        "actions": [], "errors": []}
    social_tools = []
    for tk in SOCIAL_PLATFORMS:
        try:
            t = composio.tools.get(user_id=COMPOSIO_USER_ID, toolkits=[tk])
            t = list(t)
            rep["actions"].append("%s: %d tools loaded" % (tk, len(t)))
            social_tools += t
        except Exception as e:
            rep["errors"].append("%s toolkit: %s" % (tk, str(e)[:150]))
    if not social_tools:
        rep["errors"].append("No social platforms connected in Composio for user " + COMPOSIO_USER_ID)
    else:
        social_agent = Agent(
            role="Social Media Manager",
            goal=("Run Simply Just Task social media: make one friendly daily post per connected "
                  "platform about residential services in Central Florida, check and warmly reply "
                  "to any new messages/comments, and capture anyone interested as a lead."),
            backstory="You represent Simply Just Task. Tagline: Reliable Help for Everyday Life. "
                      "Residential focus, Central Florida. Warm, human, never pushy. "
                      "Booking link: " + CAL_LINK + " | Home Visit link: " + CAL_HOME_VISIT_LINK + MASTER_KNOWLEDGE[:1500],
            tools=social_tools + [save_lead], llm=llm, verbose=True)
        tasks = [
            Task(description="Create and publish one short daily post on each connected platform "
                             "(Facebook, Instagram, Twitter/X) promoting Simply Just Task residential "
                             "services. Skip any platform whose tools are unavailable.",
                 expected_output="List of posts published with platform + post text", agent=social_agent),
            Task(description="Check for new unread messages/comments on connected platforms. Reply "
                             "warmly and helpfully. If anyone shows buying intent, collect name, email, "
                             "phone, service needed and call save_lead (grade A).",
                 expected_output="List of replies sent and any leads saved", agent=social_agent),
        ]
        try:
            result = Crew(agents=[social_agent], tasks=tasks).kickoff()
            rep["actions"].append("crew result: " + str(result)[:1500])
        except Exception as e:
            rep["errors"].append("social crew: " + str(e)[:300])
    body = "SOCIAL MEDIA CREW REPORT - " + rep["date"] + "\n\n" + \
           "\n".join(rep["actions"]) + "\n\nERRORS:\n" + "\n".join(rep["errors"])
    try:
        zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
            "accountId": ZOHO_MAIL_ACCOUNT_ID, "fromAddress": ZOHO_FROM,
            "toAddress": REPORT_EMAIL, "ccAddress": REPORT_CC,
            "subject": "SJT Social Crew Report - " + rep["date"],
            "content": body, "mailFormat": "plaintext"})
    except Exception as e:
        print("social report email failed:", e)
    print(body)

# ================= CREWAI STUDIO -> ZOHO BRIDGE =================
# POST /ingest-crewai-leads  {leads:[...]}  or {result: "..."} or {output: "..."}
# CrewAI Studio hunter finishes -> scripts/daily_job.py sends its result here.
# Each lead is saved to Zoho CRM (dedupe by email, then phone) as
# Lead_Status=Not Contacted, Lead_Source=CrewAI (owner added CrewAI to Zoho Lead_Source 2026-10-20 convo, verified live),
# with "Source: CrewAI Studio Lead Automation-v1" in Description.
# Optional guard: set MACHINE_TOKEN on Render + GitHub; send x-machine-token header.
MACHINE_TOKEN = os.environ.get("MACHINE_TOKEN", "")

def _crewai_norm_lead(raw):
    if not isinstance(raw, dict):
        return None
    def g(*keys):
        for k in keys:
            v = raw.get(k)
            if v:
                return str(v).strip()
        return ""
    name = g("full_name", "name", "Full_Name", "Name")
    email = g("email", "Email")
    phone = g("phone", "Phone", "mobile", "Mobile")
    if not name and not email and not phone:
        return None
    return {
        "full_name": name or "CrewAI Lead",
        "email": email, "phone": phone,
        "address": g("address", "Address", "city", "City"),
        "service_needed": g("service_needed", "service", "Service_Needed", "notes", "Notes"),
        "grade": (g("grade", "Grade") or "B").upper()[:1],
        "score": g("score", "Score"),
    }

def _crewai_extract_leads(payload):
    leads = []
    if isinstance(payload, dict):
        for key in ("leads", "data", "results", "output_leads"):
            if isinstance(payload.get(key), list):
                for item in payload[key]:
                    n = _crewai_norm_lead(item)
                    if n: leads.append(n)
                if leads: return leads
        for key in ("result", "output", "raw", "text"):
            v = payload.get(key)
            if isinstance(v, str):
                leads = _crewai_extract_leads({"_text": v})
                if leads: return leads
            elif isinstance(v, (dict, list)):
                leads = _crewai_extract_leads(v)
                if leads: return leads
    text = ""
    if isinstance(payload, dict):
        text = str(payload.get("_text") or "")
    elif isinstance(payload, str):
        text = payload
    if text:
        try:
            parsed = json.loads(text)
            return _crewai_extract_leads(parsed if isinstance(parsed, (dict, list)) else {"_text": text})
        except Exception:
            pass
        # fallback: find JSON array/object chunks in prose
        import re
        for chunk in re.findall(r"\[.*?\]|\{.*?\}", text, flags=re.S):
            try:
                parsed = json.loads(chunk)
            except Exception:
                continue
            got = _crewai_extract_leads(parsed if isinstance(parsed, (dict, list)) else {"_text": chunk})
            if got: leads.extend(got)
    if isinstance(payload, list):
        for item in payload:
            n = _crewai_norm_lead(item)
            if n: leads.append(n)
    return leads

def _crewai_save_one(lead):
    first_parts = lead["full_name"].strip().split()
    first = first_parts[0] if first_parts else "CrewAI"
    last = first_parts[-1] if len(first_parts) > 1 else first
    # dedupe email
    if lead["email"]:
        try:
            ex = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "email": lead["email"], "fields": "id,Full_Name,Email", "per_page": 1})
            data = (ex.get("data") or {}).get("data") if isinstance(ex, dict) else None
            if data:
                return "exists:" + str(data[0].get("id"))
        except Exception:
            pass
    # dedupe phone
    if lead["phone"]:
        try:
            ex = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "phone": lead["phone"], "fields": "id,Full_Name,Phone", "per_page": 1})
            data = (ex.get("data") or {}).get("data") if isinstance(ex, dict) else None
            if data:
                return "exists:" + str(data[0].get("id"))
        except Exception:
            pass
    desc = ("Address: %s | Service: %s | Grade: %s | Score: %s | Source: CrewAI Studio Lead Automation-v1" % (lead["address"], lead["service_needed"], lead["grade"] or "B", lead["score"] or "-"))
    resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {"module_api_name": "Leads", "data": [{"First_Name": first, "Last_Name": last, "Email": lead["email"], "Phone": lead["phone"], "Company": lead["address"] or "Residential", "City": lead["address"], "Description": desc, "Lead_Source": "CrewAI", "Lead_Status": "Not Contacted"}]})
    try:
        recs = (resp.get("data") or {}).get("data") or []
        if recs and recs[0].get("code") == "SUCCESS":
            return "created:" + str(recs[0]["details"]["id"])
        return "error:" + json.dumps(resp)[:300]
    except Exception:
        return "error:" + json.dumps(resp)[:300]

@app.route("/ingest-crewai-leads", methods=["POST"])
def ingest_crewai_leads():
    if MACHINE_TOKEN and request.headers.get("x-machine-token") != MACHINE_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    # also accept form/raw text
    if not payload and request.data:
        try:
            payload = json.loads(request.data.decode("utf-8", "ignore"))
        except Exception:
            payload = {"result": request.data.decode("utf-8", "ignore")}
    leads = _crewai_extract_leads(payload)
    results = []
    for lead in leads[:100]:
        results.append({"name": lead["full_name"], "email": lead["email"], "result": _crewai_save_one(lead)})
    created = sum(1 for r in results if r["result"].startswith("created:"))
    exists = sum(1 for r in results if r["result"].startswith("exists:"))
    errors = sum(1 for r in results if r["result"].startswith("error:"))
    return jsonify({"status": "ok", "received": len(leads), "created": created, "exists": exists, "errors": errors, "results": results}), 200


@app.route("/run-social", methods=["GET", "POST"])
def run_social():
    threading.Thread(target=run_social_pipeline, daemon=True).start()
    return jsonify({"status": "started",
                    "note": "social crew running; report will be emailed to " + REPORT_EMAIL}), 202

@app.route("/run-daily", methods=["GET", "POST"])
def run_daily():
    threading.Thread(target=run_daily_pipeline, daemon=True).start()
    return jsonify({"status": "started",
                    "note": "pipeline running; report will be emailed to " + REPORT_EMAIL}), 202

@app.route("/sync-cal-bookings", methods=["POST"])
def sync_cal_bookings():
    if MACHINE_TOKEN and request.headers.get("x-machine-token") != MACHINE_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    result = _sync_recent_cal_bookings()
    return jsonify(result), (200 if not result.get("errors") else 207)


@app.route("/call-center", methods=["GET"])
def call_center():
    try:
        resp = zoho_exec("ZOHO_GET_ZOHO_RECORDS", {"module_api_name":"Leads","fields":"First_Name,Last_Name,Full_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time","sort_by":"Created_Time","sort_order":"desc","per_page":50})
        leads = (resp.get("data") or {}).get("data") or []
        if not leads and resp.get("error"): return jsonify({"version":"call-center-plan-v1","error":str(resp.get("error"))[:300],"note":"Fix #3 blocks Render Zoho read; code live"}), 207
        return jsonify(_call_center_plan(leads)), 200
    except Exception as e:
        return jsonify({"version":"call-center-plan-v1","error":str(e)[:300]}), 207

@app.route("/ping")
def ping():
    return jsonify({"alive": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
