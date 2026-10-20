#!/usr/bin/env python3
"""Frankenstein Part 2 (owner go 2026-10-20): recycle pool + CrewAI source + booking sync.
Safe patch for concierge.py - exact-match only, idempotent, syntax check before write.
Changes:
1) CrewAI ingest Lead_Source Web Research -> CrewAI (owner added CrewAI to Zoho Lead_Source 2026-10-20)
2) QUALIFY prompt allows Recycled; /run-daily maps Not Qualified/Recycled -> Recycled + follow-up note (never delete; Junk stays Junk)
3) book_estimate success -> mark matching Zoho lead Appointment Set (owner added Appointment Set 2026-10-20)
No WhatsApp/text code added - templates are 0, blocked separately.
"""
from pathlib import Path
import ast, sys

p = Path("concierge.py")
text = p.read_text(encoding="utf-8")

def rep(old, new, label, required=True):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        print(f"{label}: patched")
        return
    if new in text:
        print(f"{label}: already patched - idempotent skip")
        return
    if required:
        print(f"ERROR: {label} old text not found exactly. Refusing to write.")
        sys.exit(1)
    print(f"{label}: old not found (ok, optional)")

rep(
  '# Lead_Status=Not Contacted, Lead_Source=Web Research (Zoho has no CrewAI value yet),',
  '# Lead_Status=Not Contacted, Lead_Source=CrewAI (owner added CrewAI to Zoho Lead_Source 2026-10-20 convo, verified live),',
  "crewai comment")

rep(
  '"Lead_Source": "Web Research", "Lead_Status": "Not Contacted"',
  '"Lead_Source": "CrewAI", "Lead_Status": "Not Contacted"',
  "crewai source")

old_book = '''    d = r.json()
    if r.status_code in (200, 201) and d.get("status") == "success":
        return ("BOOKED! Confirmation email sent to " + email +
                ". Booking details: " + json.dumps(d.get("data", {}))[:300])'''
new_book = '''    d = r.json()
    if r.status_code in (200, 201) and d.get("status") == "success":
        # Frankenstein Part 2: booking writes back to Zoho as Appointment Set (owner added 2026-10-20).
        try:
            got = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "email": email, "fields": "id,Full_Name,Email,Description", "per_page": 1})
            found = (got.get("data") or {}).get("data") if isinstance(got, dict) else None
            if found:
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {"module_api_name": "Leads", "data": [{"id": str(found[0]["id"]), "Lead_Status": "Appointment Set", "Description": ((found[0].get("Description") or "") + "\\n[Cal booked %s] Appointment Set via Concierge book_estimate." % start_iso)[:2000]}]})
        except Exception:
            pass
        return ("BOOKED! Confirmation email sent to " + email +
                ". Booking details: " + json.dumps(d.get("data", {}))[:300])'''
rep(old_book, new_book, "book appointment-set")

rep(
  '{"status": one of "Pre-Qualified", "Not Qualified", "Junk Lead",',
  '{"status": one of "Pre-Qualified", "Not Qualified", "Junk Lead", "Recycled",',
  "qualify prompt recycled")

old_daily = '''                new_status = q.get("status", "Not Qualified")
                entry["new_status"] = new_status
                note = "\\n\\n[AI Qualifier %s] Score %s/100. %s" % (
                    report["date"], q.get("score"), q.get("notes"))
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                    "module_api_name": "Leads",
                    "data": [{"id": str(ld["id"]), "Lead_Status": new_status,
                              "Description": (ld.get("Description") or "") + note}]})'''
new_daily = '''                raw_status = q.get("status", "Not Qualified")
                # Frankenstein Part 2 recycle pool (owner rule, 2026-10-20): Not Qualified / Recycled = keep, do not drop.
                # Owner added Zoho Lead_Status values Appointment Set + Recycled and Lead_Source values CrewAI/Nextdoor/Instagram/TikTok/YouTube/LinkedIn.
                # Junk Lead is the only true drop.
                new_status = "Recycled" if raw_status in ("Not Qualified", "Recycled") else raw_status
                entry["new_status"] = new_status
                recycled_note = ""
                if new_status == "Recycled":
                    recycled_note = " | Recycle follow-up: +30 days, never delete."
                note = "\\n\\n[AI Qualifier %s] Score %s/100. %s%s" % (
                    report["date"], q.get("score"), q.get("notes"), recycled_note)
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                    "module_api_name": "Leads",
                    "data": [{"id": str(ld["id"]), "Lead_Status": new_status,
                              "Description": ((ld.get("Description") or "") + note)[:2000]}]})'''
rep(old_daily, new_daily, "daily recycle mapping")

ast.parse(text)
print("syntax OK")
p.write_text(text, encoding="utf-8")
print(f"concierge.py chars after: {len(text)}")
print("PATCH OK")
