"""Compatibility for existing concierge imports; all new state is owner-configured."""
import json
import uuid
import os
import sqlite3
import datetime as dt
from pathlib import Path
from sjt_reliability import NY, ClosingConnection
from sjt_reliability import (authorized, configured_state, fetch_leads, now_et,
                            select_leads, stopped, response_error)


def check_token(expected, supplied):
    return authorized(expected, supplied)


def opted_out(lead):
    return stopped(lead)


def response_ok(resp):
    node = resp
    for _ in range(5):
        if response_error(node):
            return False
        data = node.get('data')
        if isinstance(data, list):
            return not any(isinstance(row, dict) and row.get('code') and row['code'] != 'SUCCESS' for row in data)
        if not isinstance(data, dict):
            return True
        node = data
    return False


def due(lead, now=None):
    today = (now or now_et()).astimezone(NY).date()
    return bool(select_leads([lead], today))


def scheduler_due(now=None, approved=True):
    return approved and 9 <= (now or now_et()).astimezone(NY).hour < 21


def quota_exhausted(status, body):
    return status in (402,429) or 'monthly execution limit' in str(body).lower()


def pending_leads(execute, batch=50, exclude=None):
    excluded=set(exclude or [])
    return [r for r in select_leads(fetch_leads(execute), now_et().date()) if str(r['id']) not in excluded][:batch]


def database():
    path=os.environ.get('SJT_STATE_PATH','').strip()
    if not path:
        path=str(Path(configured_state().path).with_name('sjt-drafts.sqlite3'))
    if not Path(path).is_absolute():
        raise RuntimeError('absolute owner-configured state path required')
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path,timeout=30,factory=ClosingConnection)
    conn.row_factory=sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS drafts (
      id TEXT PRIMARY KEY, channel TEXT, recipient TEXT, subject TEXT,
      body TEXT, status TEXT, created TEXT, lead_id TEXT, fingerprint TEXT UNIQUE)""")
    conn.commit()
    return conn


def save_draft(channel, recipient, subject, body, lead_id=''):
    import hashlib
    key = hashlib.sha256(json.dumps([channel,recipient,subject,body,lead_id]).encode()).hexdigest()
    ident = uuid.uuid4().hex
    with database() as conn:
        conn.execute('INSERT OR IGNORE INTO drafts VALUES(?,?,?,?,?,?,?,?,?)',
            (ident,channel,recipient,subject,body,'needs_owner_confirmation',now_et().isoformat(),lead_id,key))
        return conn.execute('SELECT id FROM drafts WHERE fingerprint=?',(key,)).fetchone()['id']


def record_report(subject, body):
    return save_draft('owner_report','owner',subject,body)


def job_status(ident):
    return configured_state().job(ident)


def start_job(kind, function):
    # Old dispatcher must not accidentally resume opaque background execution.
    raise RuntimeError('Use the observable owner-authenticated /ops job dispatcher')


def queued_lead_ids():
    with database() as connection:
        return {r[0] for r in connection.execute("SELECT DISTINCT lead_id FROM drafts WHERE channel='email' AND lead_id!='' AND status IN ('needs_owner_confirmation','sending','uncertain','provider_accepted','accepted_crm_sync_failed')")}


def queued_lead_ids():
    with database() as conn:
        return {str(r[0]) for r in conn.execute("SELECT lead_id FROM drafts WHERE lead_id<>'' AND status IN ('needs_owner_confirmation','claimed','uncertain')")}


def claim_draft(ident, confirmation, now=None):
    if os.environ.get('SJT_STATE_PERSISTENT_CONFIRMED') != 'true' and os.environ.get('SJT_DURABLE_STATE_ACK') not in ('1','true'):
        raise ValueError('persistent storage acknowledgement required')
    now=now or dt.datetime.now(dt.timezone.utc)
    day=now.astimezone(NY).date().isoformat()
    with database() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT * FROM drafts WHERE id=?',(ident,)).fetchone()
        if row is None or row['status']!='needs_owner_confirmation':
            raise ValueError('draft already claimed or absent')
        if confirmation!='go send '+ident+' '+row['fingerprint']:
            raise ValueError('exact action confirmation required')
        created=dt.datetime.fromisoformat(row['created'])
        if now-created>dt.timedelta(hours=24) or created>now+dt.timedelta(minutes=5):
            raise ValueError('draft expired or clock invalid')
        conn.execute('CREATE TABLE IF NOT EXISTS deliveries(draft_id TEXT PRIMARY KEY,day TEXT,channel TEXT,lead_id TEXT)')
        limit=10 if row['channel']=='email' else 1
        count=conn.execute('SELECT COUNT(*) FROM deliveries WHERE day=? AND channel=?',(day,row['channel'])).fetchone()[0]
        if count>=limit:
            raise ValueError('daily channel cap reached')
        conn.execute('INSERT INTO deliveries VALUES(?,?,?,?)',(ident,day,row['channel'],row['lead_id']))
        conn.execute("UPDATE drafts SET status='claimed' WHERE id=?",(ident,))
        return dict(row)


def finish_draft(ident, status):
    if status not in ('uncertain','provider_accepted','sent_verified','rejected'):
        raise ValueError('invalid terminal delivery state')
    with database() as conn:
        cursor=conn.execute("UPDATE drafts SET status=? WHERE id=? AND status='claimed'",(status,ident))
        if cursor.rowcount!=1:
            raise ValueError('draft was not claimed')
