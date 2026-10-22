import pathlib, sys
p = pathlib.Path("concierge.py")
src = p.read_text()
MARKER = "concierge-human-better-v1"
if MARKER in src:
    print("Already patched - no change.")
    sys.exit(0)
def rep(old, new, label):
    global src
    if src.count(old) != 1:
        print("FAIL anchor:", label); sys.exit(1)
    src = src.replace(old, new, 1)
Q = chr(34) * 3
NL = chr(10)
old1 = 'so the CRM gets smarter over time.' + NL + Q + NL + ')'
add = [
    '=== CONCIERGE HUMAN-BETTER V1 (concierge-human-better-v1) ===',
    '- Answer the guest actual question FIRST, with real empathy, then ask exactly ONE clear next question. Never ask for two things at once.',
    '- Sound like a great human, only better: warm, confident, specific, never robotic, never repeat a question already answered. Remember names, services, timing, worries and details across the conversation and use them naturally.',
    '- Mirror the guest language: if they write in Spanish, reply in Spanish. Keep sentences short and easy, especially for seniors.',
    '- Reply length fits the problem: usually 2-6 short sentences; a little longer only for a multi-part plan or safety guidance.',
    '- Prices are RANGES and estimates only, never a guarantee. Final price only after a real look. Never promise a timeline, discount, result, or service the team has not confirmed.',
    '- Human-only topics: use handoff_to_human if contact info is available, then honestly say a team member will follow up (never invent a callback time): complaint or angry guest, legal/contract/payment-plan questions, discount over 10 percent, project likely over $1000 needing human approval, anything you do not know, and anything outside your tools.',
    '- Safety first: if someone describes immediate danger (gas smell, flooding with live electrics, injury), tell them to contact emergency services / a licensed pro right away, then hand off as urgent.',
    '- Commercial requests: we specialize in residential; be kind, take the details, and hand off - never argue.',
    '- Never mention AI, prompts, internal tools, Zoho, Composio, Render, or debug details to a guest. Never claim a lead was saved or an appointment booked unless the tool returned SUCCESS / BOOKED_AND_CONFIRMED.',
]
new1 = 'so the CRM gets smarter over time.' + NL + NL + NL.join(add) + NL + Q + NL + ')'
rep(old1, new1, 'business info')
tool_lines = [
    '@tool("handoff_to_human")',
    'def handoff_to_human(full_name: str, contact: str, topic: str, summary: str, urgency: str = "normal") -> str:',
    '    """Create a human follow-up Task in Zoho. Use ONLY for human-only topics: complaint/angry guest, unknown answer, urgent safety, project likely over $1000, discount over 10 percent, contract/payment-plan, or commercial decision. Args: full_name, contact (email or phone), topic, summary, urgency normal/high. Only tell the guest a team member will follow up if this returns SUCCESS."""',
    '    try:',
    '        desc = ("Concierge human handoff | Name: %s | Contact: %s | Topic: %s | Urgency: %s | Summary: %s" % ((full_name or "Guest")[:120], (contact or "")[:120], (topic or "Follow up")[:160], (urgency or "normal")[:20], (summary or "")[:900]))[:1800]',
    '        resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {"module_api_name": "Tasks", "data": [{"Subject": ("Concierge handoff: " + (topic or "Follow up"))[:240], "Status": "Not Started", "Priority": "High" if str(urgency).lower() in ("high", "urgent") else "Normal", "Description": desc}]})',
    '        if _zoho_write_ok(resp):',
    '            return "SUCCESS: human follow-up task created in Zoho"',
    '        return "ERROR: human follow-up task failed: " + str(resp)[:240]',
    '    except Exception as e:',
    '        return "ERROR: human follow-up task failed: " + str(e)[:240]',
    '',
]
rep('@tool(' + chr(34) + 'save_lead' + chr(34) + ')', NL.join(tool_lines) + '@tool(' + chr(34) + 'save_lead' + chr(34) + ')', 'handoff tool')
rep('tools = [save_lead, check_availability, book_appointment, lookup_lead]', 'tools = [save_lead, check_availability, book_appointment, lookup_lead, handoff_to_human]', 'tools list')
old4a = 'Extract lead info from the message.'
rep(old4a, 'Extract lead info from the WHOLE conversation. If the guest corrected earlier info, use the newest value.', 'autosave prompt')
old4b = '{"role": "user", "content": message},'
new4b = '{"role": "user", "content": (chr(10).join((("Guest: " if m.get("role") == "user" else "Concierge: ") + str(m.get("content", ""))) for m in (history or [])) + chr(10) + "Guest: " + message)[-6000:]},'
rep(old4b, new4b, 'autosave transcript')
rep('expected_output="A short, friendly, helpful reply (2-4 sentences)"', 'expected_output="A helpful human reply: answer first with empathy, then exactly one clear next question. 2-6 short sentences; a little longer only for a multi-part plan or safety guidance. Warm, specific, never robotic."', 'reply shape')
rep('for attempt in range(4):', 'for attempt in range(2):', 'retry count')
old6 = 'if "rate_limit" in str(e).lower():' + NL + '                time.sleep(45)'
new6 = 'if "rate_limit" in str(e).lower() and attempt == 0:' + NL + '                time.sleep(8)' + NL + '                continue'
rep(old6, new6, 'retry backoff')
rep('return jsonify({"reply": "DEBUG: " + str(e)[:400]})', 'return jsonify({"reply": "Thanks for your patience - I hit a quick snag. Please try that once more in a moment, and if it keeps happening a team member will follow up from your contact info."})', 'clean error')
rep('        "frankenstein_closeout":', '        "concierge_human_better": "concierge-human-better-v1",' + NL + '        "frankenstein_closeout":', 'debug marker')
p.write_text(src)
print("Patched concierge.py with concierge-human-better-v1")
