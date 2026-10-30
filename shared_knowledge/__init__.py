"""Offline shared company context and explicit-job-ZIP validation. No I/O beyond local files."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def load_company():
    config = json.loads((ROOT / "company.json").read_text(encoding="utf-8"))
    codes = [z for values in config["service_area"]["cities"].values() for z in values]
    if len(codes) != 20 or len(codes) != len(set(codes)):
        raise ValueError("Expected exactly 20 unique owner-supplied ZIP codes")
    if any(not re.fullmatch(r"[0-9]{5}", z) for z in codes):
        raise ValueError("Invalid configured ZIP code")
    return config


def assess_job_zip(job_zip=None):
    """Accept only an explicitly supplied job ZIP, never a post/profile inference."""
    value = "" if job_zip is None else str(job_zip).strip()
    match = re.fullmatch(r"([0-9]{5})(?:-[0-9]{4})?", value)
    if match is None:
        return {"status": "needs_location", "job_zip": None, "city": None,
                "question": "What ZIP code is the job in?"}
    code = match.group(1)
    config = load_company()
    city = next((city for city, codes in config["service_area"]["cities"].items()
                 if code in codes), None)
    return {"status": "in_area" if city else "out_of_area", "job_zip": code,
            "city": city, "question": None}


def shared_context(role):
    """Provide the same current business requirements to an identified AI role.

    This helper is not yet wired into repository agents. It does not import full
    OneDrive sources, establish customer history, or grant action permissions.
    """
    if not isinstance(role, str) or not role.strip():
        raise ValueError("An explicit AI role is required")
    policy = (ROOT / "operating_requirements.md").read_text(encoding="utf-8")
    return ("AI role: " + role.strip() + "\n" + policy + "\nCompany data:\n"
            + json.dumps(load_company(), ensure_ascii=False, sort_keys=True))
