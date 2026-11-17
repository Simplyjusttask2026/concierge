"""Shared knowledge between this crew desk and the Simply Just Task website.

Both directions, so the two of her work from one head:
  * the site pulls what this desk knows      -> GET  /summer/share
  * the site hands back what it learned      -> POST /summer/share
  * this desk reads the site back into chat  -> site_context_block()

Nothing secret is written here. The token comes from the Render environment.
"""

import json
import os
import threading
import time

import requests
from flask import jsonify, request

SITE_SHARE_URL = os.environ.get(
    "SITE_SHARE_URL", "https://wwwsimplyjusttaskcom-ad20a7c4.base44.app/api/summer/share"
)
MACHINE_TOKEN = os.environ.get("MACHINE_TOKEN", "").strip()
HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "summer_shared.json")
CACHE_SECONDS = 600

_lock = threading.Lock()
_cache = {"at": 0, "digest": "", "lessons": []}


def _headers():
    if not MACHINE_TOKEN:
        return {}
    return {"Authorization": "Bearer " + MACHINE_TOKEN, "Accept": "application/json"}


def _load():
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return {
                "lessons": list(data.get("lessons") or []),
                "contacts": list(data.get("contacts") or []),
                "updated": data.get("updated", ""),
            }
    except Exception:
        pass
    return {"lessons": [], "contacts": [], "updated": ""}


def _save(store):
    try:
        with open(STORE_PATH, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2)
    except Exception as ex:
        print("[summer-bridge] could not write the shared store:", ex)


def _merge(store, lessons, contacts):
    seen = {str(item.get("lesson", "")).strip().lower() for item in store["lessons"]}
    added = 0
    for item in lessons or []:
        if isinstance(item, dict):
            text = str(item.get("lesson", "")).strip()
            topic = item.get("topic") or "other"
        else:
            text = str(item).strip()
            topic = "other"
        if len(text) < 8 or text.lower() in seen:
            continue
        store["lessons"].append({"lesson": text, "topic": topic})
        seen.add(text.lower())
        added += 1
    for person in contacts or []:
        if isinstance(person, dict) and str(person.get("name", "")).strip():
            store["contacts"].append(person)
    store["lessons"] = store["lessons"][-120:]
    store["contacts"] = store["contacts"][-120:]
    store["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return added


def _brain_excerpt(limit=4000):
    try:
        with open(os.path.join(HERE, "BRAIN.md"), "r", encoding="utf-8") as handle:
            return handle.read()[:limit]
    except Exception:
        return ""


def site_knowledge(max_age=CACHE_SECONDS):
    """What the website desk holds, kept for a few minutes at a time."""
    now = time.time()
    if _cache["at"] and now - _cache["at"] < max_age:
        return _cache
    if not MACHINE_TOKEN:
        return _cache
    try:
        res = requests.get(SITE_SHARE_URL, headers=_headers(), timeout=6)
        if res.ok:
            payload = res.json()
            _cache["at"] = now
            _cache["digest"] = str(payload.get("digest") or "")[:6000]
            _cache["lessons"] = list(payload.get("lessons") or [])[:40]
    except Exception as ex:
        print("[summer-bridge] site pull skipped:", ex)
    return _cache


def site_context_block():
    """The website desk, read into this desk's own words before it answers."""
    data = site_knowledge()
    parts = []
    if data["digest"]:
        parts.append("What your website desk holds, in her own words:\n" + data["digest"])
    if data["lessons"]:
        lines = "\n".join("- " + str(item.get("lesson", "")) for item in data["lessons"][:15])
        parts.append("What she has learned from website guests:\n" + lines)
    return "\n\n".join(parts)


def push_to_site(lessons=None, contact=None):
    """Hands what this desk worked out back to the website, so both remember it."""
    if not MACHINE_TOKEN:
        return False
    try:
        payload = {"lessons": lessons or [], "contact": contact}
        res = requests.post(
            SITE_SHARE_URL,
            headers=dict(_headers(), **{"Content-Type": "application/json"}),
            json=payload,
            timeout=8,
        )
        return bool(res.ok)
    except Exception as ex:
        print("[summer-bridge] push skipped:", ex)
        return False


def register_summer_bridge(app):
    @app.route("/summer/share", methods=["GET"])
    def summer_share_get():
        store = _load()
        return jsonify({
            "service": "sjt-concierge",
            "brain": _brain_excerpt(),
            "lessons": store["lessons"][-60:],
            "contacts_kept": len(store["contacts"]),
            "updated": store["updated"],
        })

    @app.route("/summer/share", methods=["POST"])
    def summer_share_post():
        payload = request.get_json(silent=True) or {}
        contacts = payload.get("contacts") or []
        if payload.get("contact"):
            contacts.append(payload["contact"])
        with _lock:
            store = _load()
            added = _merge(store, payload.get("lessons"), contacts)
            _save(store)
        return jsonify({"ok": True, "learned": added, "lessons": store["lessons"][-60:]})

    @app.route("/summer/lessons", methods=["POST"])
    def summer_lessons_post():
        payload = request.get_json(silent=True) or {}
        lessons = payload.get("lessons") if isinstance(payload, dict) else None
        return jsonify({"ok": True, "pushed": push_to_site(lessons=lessons)})

    print("[summer-bridge] wired: /summer/share and /summer/lessons")
    return app
