#!/usr/bin/env python3
"""Frankenstein Part 3 (owner go 2026-10-20): real confirmed appointments only.
Safe patch for concierge.py - marker/exact-match only, idempotent, syntax check
before write. Rules locked by owner:
- Concierge may book ALL appointment types: consultation by phone, virtual,
  or in person, AND Home Visit / Estimate.
- Only REAL appointments: real name/email/phone, REAL full street address
  (house number + street + city + FL + ZIP), customer explicitly confirms the
  exact type/date/time/address first. Both parties aware: customer gets Cal
  confirmation, human gets Cal calendar + Zoho Task.
- Only if Cal returns a real booking UID and a re-fetch proves status
  accepted + correct event + correct attendee + correct time + address on
  the Cal record: then Zoho Lead -> Appointment Set + human Zoho Task.
- If Cal/Zoho fails: NOT BOOKED / NOT CONFIRMED / BOOKED_BUT_ZOHO_SYNC_FAILED
  out loud. No silent except: pass. No fake test booking.
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

rep('import os, time, json, datetime',
    'import os, time, json, datetime, re', "import re")
rep('import requests\n',
    'import requests\ntry:\n    from zoneinfo import ZoneInfo\nexcept Exception:\n    ZoneInfo = None\n',
    "import ZoneInfo")
rep('CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (30 min)\nCAL_LINK = "https://cal.com/simply-justtask/simplybook"',
    'CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (consultations)\nCAL_LINK = "https://cal.com/simply-justtask/simplybook"\nCAL_HOME_VISIT_EVENT_TYPE_ID = 7554154  # Home Visit / Estimate (45/60)\nCAL_HOME_VISIT_LINK = "https://cal.com/simply-justtask/home-visit"',
    "cal config home visit")

NEW_BOOKING_BLOCK = r'''
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

'''

if "PART3_REAL_APPOINTMENTS_V1" in text:
    print("booking block: already patched - idempotent skip")
else:
    _bs = text.index('@tool("check_availability")')
    _be = text.index('# ====== Business brain ======')
    text = text[:_bs] + NEW_BOOKING_BLOCK + text[_be:]
    print("booking block: patched")

rep('BOOKING LINK (fallback): """ + CAL_LINK + MASTER_KNOWLEDGE + """',
    'CONSULTATION LINK (fallback only, never claim booked from a link): """ + CAL_LINK + """\nHOME VISIT / ESTIMATE LINK (fallback only): """ + CAL_HOME_VISIT_LINK + MASTER_KNOWLEDGE + """',
    "booking links in prompt")
rep('Collect: full name, email, phone, property address or city, and the service\nthey need.',
    'Collect: full name, real email, real phone, REAL full street address\n(house number, street, city, FL and ZIP - no booking without it), and the\nservice they need. A city alone is NOT a real address.',
    "step2 real address")

_s5s = text.index("STEP 5 - QUALIFY & BOOK (Grade A leads)")
_s5e = text.index("GRADE B leads:", _s5s)
_new_s5 = '''STEP 5 - QUALIFY & BOOK REAL APPOINTMENTS (Grade A leads, or any guest who explicitly asks to book)
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

'''
text = text[:_s5s] + _new_s5 + text[_s5e:]
print("step5: patched")

rep('tools = [save_lead, check_availability, book_estimate, lookup_lead]',
    'tools = [save_lead, check_availability, book_appointment, lookup_lead]',
    "tools list")
rep('""" + CAL_LINK + """ and phone (888) 566-7570',
    '""" + CAL_LINK + """ (consultation) or """ + CAL_HOME_VISIT_LINK + """ (home visit) and phone (888) 566-7570',
    "outreach links")
rep('"Booking link: " + CAL_LINK + MASTER_KNOWLEDGE[:1500]',
    '"Booking link: " + CAL_LINK + " | Home Visit link: " + CAL_HOME_VISIT_LINK + MASTER_KNOWLEDGE[:1500]',
    "social booking links")
rep('"leads": [], "outreach": [], "errors": []}',
    '"leads": [], "outreach": [], "errors": [], "cal_sync": {}}',
    "daily report cal_sync field")

if "_sync_recent_cal_bookings" not in text.split("def run_daily_pipeline")[1].split("def run_social_pipeline")[0]:
    rep('    for ld in leads:\n        status = ld.get("Lead_Status")',
        '    try:\n        report["cal_sync"] = _sync_recent_cal_bookings()\n        report["errors"].extend(report["cal_sync"].get("errors", []))\n    except Exception as e:\n        report["errors"].append("cal sync: " + str(e)[:200])\n    for ld in leads:\n        status = ld.get("Lead_Status")',
        "daily cal sync call")
else:
    print("daily cal sync call: already patched")

rep('"", "=== LEADS ==="]',
    '"", "Cal sync: " + json.dumps(report.get("cal_sync", {}), default=str)[:1200], "", "=== LEADS ==="]',
    "daily report cal sync line")
rep('''    return jsonify({
        "crm": "zoho",
        "cal_key_loaded": bool(CAL_API_KEY),
    })''',
    '''    return jsonify({
        "crm": "zoho",
        "cal_key_loaded": bool(CAL_API_KEY),
        "cal_consultation_event_id": CAL_EVENT_TYPE_ID,
        "cal_home_visit_event_id": CAL_HOME_VISIT_EVENT_TYPE_ID,
        "cal_booking_sync": "part3-v1-real-confirmed-only",
    })''',
    "debug part3 marker")

if '"/sync-cal-bookings"' not in text:
    rep('@app.route("/ping")',
        '''@app.route("/sync-cal-bookings", methods=["POST"])
def sync_cal_bookings():
    if MACHINE_TOKEN and request.headers.get("x-machine-token") != MACHINE_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    result = _sync_recent_cal_bookings()
    return jsonify(result), (200 if not result.get("errors") else 207)


@app.route("/ping")''',
        "sync-cal-bookings route")
else:
    print("sync-cal-bookings route: already patched")

ast.parse(text)
print("syntax OK")
p.write_text(text, encoding="utf-8")
print(f"concierge.py chars after: {len(text)}")
print("PATCH OK")
