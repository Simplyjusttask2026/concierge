"""SJT repair core. No network, account writes, sends or threads at import time.
Deployment requires an owner-configured persistent state directory. Live effects
are disabled until separately enabled; tests inject transports and temporary state.
"""
import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
STOP = re.compile(r'\b(?:stop|unsubscribe|opt[ -]?out|do not contact)\b', re.I)
STAMP = re.compile(r'\[SJT(?:_FOLLOWUP | followup due=)(\d{4}-\d\d-\d\d)\]')


def enabled(name):
    return os.environ.get(name, '').lower() in ('1', 'true')


def authorized(expected, supplied):
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def now_et():
    return dt.datetime.now(NY)


def stopped(lead):
    return bool(STOP.search(str(lead.get('Description') or '')))


def mail_address(lead):
    email = str(lead.get('Email') or '').strip().lower()
    if not re.fullmatch(r'[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+', email):
        return ''
    if email.rsplit('@', 1)[-1] in ('example.com', 'example.net', 'example.org', 'test.com', 'invalid.com'):
        return ''
    if re.search(r'\b(?:test|testy|sample|mctesterson)\b', str(lead.get('Full_Name') or ''), re.I):
        return ''
    return email


def response_error(resp):
    if not isinstance(resp, dict):
        return 'invalid provider response'
    if resp.get('error') or resp.get('successful') is False:
        return 'provider rejected request'
    status = resp.get('status')
    if isinstance(status, dict) and int(status.get('code') or 200) >= 300:
        return 'provider returned failure status'
    if str(resp.get('status', '')).lower() == 'error':
        return 'provider returned error'
    return ''


def records(resp):
    """Accept native and Composio wrappers, reject error objects, never fake zero."""
    node = resp
    for _ in range(5):
        err = response_error(node)
        if err:
            raise RuntimeError(err)
        if isinstance(node.get('data'), list):
            return node['data'], node.get('info') or {}
        if isinstance(node.get('data'), dict):
            node = node['data']
        else:
            if node.get('info', {}).get('count') == 0:
                return [], node.get('info') or {}
            raise RuntimeError('provider omitted records array')
    raise RuntimeError('unrecognized record wrapper')


def fetch_leads(execute):
    fields = 'id,First_Name,Last_Name,Full_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time'
    args = {'module_api_name': 'Leads', 'fields': fields, 'per_page': 200,
            'sort_by': 'Created_Time', 'sort_order': 'asc', 'page': 1}
    result, seen_pages, seen_ids = [], set(), set()
    for _ in range(100):
        rows, info = records(execute('ZOHO_GET_ZOHO_RECORDS', dict(args)))
        signature = tuple(str(row.get('id')) for row in rows)
        if signature in seen_pages and (rows or info.get('more_records')):
            raise RuntimeError('repeated CRM page; refusing incomplete processing')
        seen_pages.add(signature)
        for row in rows:
            ident = str(row.get('id') or '')
            if not ident:
                raise RuntimeError('CRM record missing id')
            if ident not in seen_ids:
                seen_ids.add(ident)
                result.append(row)
        if not info.get('more_records'):
            return result
        token = info.get('next_page_token')
        if token:
            args.pop('page', None)
            args['page_token'] = token
        elif 'page_token' in args:
            raise RuntimeError('CRM continuation token missing')
        else:
            args['page'] += 1
    raise RuntimeError('CRM pagination limit reached; no partial success')


def followup_due(lead, today):
    matches = STAMP.findall(str(lead.get('Description') or ''))
    if not matches:
        return False
    return dt.date.fromisoformat(matches[-1]) <= today


def select_leads(rows, today):
    return [r for r in rows if not stopped(r) and (
        r.get('Lead_Status') in (None, '', '-None-', 'Not Contacted', 'Pre-Qualified') or
        (r.get('Lead_Status') in ('Recycled', 'Contact in Future') and followup_due(r, today)))]


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class State:
    """Transactional same-host lock/ledger. Deployment MUST use persistent storage.
    Claims survive crash; uncertain sends are NEVER automatically retried.
    """
    def __init__(self, directory):
        path = Path(directory).resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.path = str(path / 'sjt-state.sqlite3')
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, job_key TEXT UNIQUE, kind TEXT, status TEXT,
              created TEXT, result TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS deliveries (
              delivery_key TEXT PRIMARY KEY, day TEXT, channel TEXT, status TEXT,
              provider_id TEXT NOT NULL DEFAULT '');
            ''')

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30, factory=ClosingConnection)
        conn.row_factory = sqlite3.Row
        return conn

    def claim_job(self, key, kind):
        ident = uuid.uuid4().hex
        with self.connect() as c:
            try:
                c.execute('INSERT INTO jobs(id,job_key,kind,status,created) VALUES(?,?,?,?,?)',
                          (ident, key, kind, 'queued', dt.datetime.now(dt.timezone.utc).isoformat()))
                return ident, True
            except sqlite3.IntegrityError:
                return c.execute('SELECT id FROM jobs WHERE job_key=?', (key,)).fetchone()['id'], False

    def job(self, ident):
        with self.connect() as c:
            row = c.execute('SELECT * FROM jobs WHERE id=?', (ident,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result['result'] = json.loads(result['result'])
        return result

    def finish(self, ident, status, result):
        with self.connect() as c:
            c.execute('UPDATE jobs SET status=?,result=? WHERE id=?',
                      (status, json.dumps(result, default=str), ident))

    def reserve_delivery(self, key, day, cap=10, channel='outreach'):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute('SELECT 1 FROM deliveries WHERE delivery_key=?', (key,)).fetchone():
                return 'already_claimed'
            count = c.execute('SELECT COUNT(*) FROM deliveries WHERE day=? AND channel=?',
                              (day, channel)).fetchone()[0]
            if count >= cap:
                return 'daily_cap'
            c.execute('INSERT INTO deliveries(delivery_key,day,channel,status) VALUES(?,?,?,?)',
                      (key, day, channel, 'reserved'))
            return 'reserved'

    def delivered(self, key, status, provider_id=''):
        with self.connect() as c:
            c.execute('UPDATE deliveries SET status=?,provider_id=? WHERE delivery_key=?',
                      (status, provider_id, key))


def configured_state():
    directory = os.environ.get('SJT_STATE_DIR', '').strip()
    if not directory or not Path(directory).is_absolute() or not enabled('SJT_DURABLE_STATE_ACK'):
        raise RuntimeError('Configure an absolute persistent SJT_STATE_DIR and acknowledge durable storage before enabling jobs')
    return State(directory)


def write_ok(resp):
    try:
        rows, _ = records(resp)
        return bool(rows) and all(row.get('code') == 'SUCCESS' for row in rows)
    except RuntimeError:
        return False


def mail_receipt(resp):
    node = resp
    for _ in range(5):
        if response_error(node):
            return ''
        data = node.get('data')
        for key in ('messageId', 'message_id'):
            if node.get(key):
                return str(node[key])
        if not isinstance(data, dict):
            return ''
        node = data
    return ''


def delivery_key(lead_id, sequence, recipient):
    return hashlib.sha256(f'{lead_id}|{sequence}|{recipient.lower()}'.encode()).hexdigest()


def deliver(execute, state, lead, subject, body, cfg, sequence='initial'):
    recipient = mail_address(lead)
    if not recipient or stopped(lead):
        return {'status': 'suppressed'}
    if not cfg.get('outreach_enabled'):
        return {'status': 'held_outreach_disabled'}
    now = now_et()
    if not 8 <= now.hour < 21:
        return {'status': 'held_quiet_hours'}
    key = delivery_key(lead['id'], sequence, recipient)
    claim = state.reserve_delivery(key, now.date().isoformat(), cfg.get('daily_cap', 10))
    if claim != 'reserved':
        return {'status': claim}
    try:
        response = execute('ZOHO_MAIL_MESSAGES_SEND_EMAIL', {
            'accountId': cfg['mail_account'], 'fromAddress': cfg['mail_from'],
            'toAddress': recipient, 'subject': subject, 'content': body, 'mailFormat': 'plaintext'})
        receipt = mail_receipt(response)
        if not receipt:
            state.delivered(key, 'uncertain')
            return {'status': 'uncertain_do_not_retry'}
        state.delivered(key, 'provider_accepted', receipt)
        return {'status': 'provider_accepted', 'message_id': receipt}
    except Exception:
        state.delivered(key, 'uncertain')
        return {'status': 'uncertain_do_not_retry'}


def mark(execute, lead, status, note):
    old = str(lead.get('Description') or '')
    # Preserve newest operational marker rather than silently clipping it off.
    description = old[-max(0, 2000-len(note)-2):] + '\n' + note
    response = execute('ZOHO_UPDATE_ZOHO_RECORD', {'module_api_name': 'Leads',
        'data': [{'id': str(lead['id']), 'Lead_Status': status, 'Description': description[-2000:]}]})
    if not write_ok(response):
        raise RuntimeError('CRM update not acknowledged; no success claimed')


def daily(execute, llm_json, qualify_prompt, outreach_prompt, state, cfg):
    today = now_et().date()
    rows = fetch_leads(execute)
    eligible = select_leads(rows, today)
    report = {'mode': 'apply' if cfg.get('crm_writes') else 'read_only',
              'total_leads': len(rows), 'eligible': len(eligible), 'outcomes': [], 'errors': []}
    if not cfg.get('crm_writes'):
        report['outcomes'] = [{'id': str(r['id']), 'status': 'eligible_no_write'} for r in eligible]
        return report
    for lead in eligible:
        ident = str(lead['id'])
        try:
            status = lead.get('Lead_Status')
            if status != 'Pre-Qualified':
                if not mail_address(lead):
                    report['outcomes'].append({'id': ident, 'status': 'needs_contact_review'})
                    continue
                q = llm_json(qualify_prompt, json.dumps(lead, default=str)[:4000])
                raw = q.get('status')
                allowed = {'Pre-Qualified', 'Not Qualified', 'Recycled', 'Junk Lead', 'Not Contacted'}
                if raw not in allowed:
                    raise RuntimeError('invalid qualifier status')
                status = 'Recycled' if raw == 'Not Qualified' else raw
                note = '[AI Qualifier %s] Score %s/100. %s' % (today, q.get('score'), str(q.get('notes') or '')[:600])
                if status == 'Recycled':
                    note += ' [SJT_FOLLOWUP %s]' % (today+dt.timedelta(days=30)).isoformat()
                mark(execute, lead, status, note)
            if status != 'Pre-Qualified':
                report['outcomes'].append({'id': ident, 'status': status})
                continue
            # Queue remains Pre-Qualified when disabled, quiet, capped or failed.
            if not cfg.get('outreach_enabled'):
                report['outcomes'].append({'id': ident, 'status': 'held_outreach_disabled'})
                continue
            m = llm_json(outreach_prompt, json.dumps(lead, default=str)[:2500])
            subject, body = str(m.get('subject') or '').strip(), str(m.get('body') or '').strip()
            if not subject or not body or '\n' in subject or '\r' in subject:
                raise RuntimeError('empty or invalid email draft')
            if 'stop' not in body.lower():
                body += '\nReply STOP to opt out.'
            match = STAMP.findall(str(lead.get('Description') or ''))
            sequence = 'recycle:'+match[-1] if match else 'initial'
            outcome = deliver(execute, state, lead, subject, body, cfg, sequence)
            if outcome['status'] == 'provider_accepted':
                mark(execute, lead, 'Attempted to Contact', '[SJT_MAIL_ACCEPTED %s] %s' % (today, outcome['message_id']))
            report['outcomes'].append({'id': ident, **outcome, 'recipient': mail_address(lead), 'subject': subject, 'body': body})
        except Exception as exc:
            # No provider payload, token, email body or recipient in public log.
            report['errors'].append({'id': ident, 'error': type(exc).__name__})
    return report


def report_mail(execute, state, report, cfg, key):
    if not cfg.get('reports_enabled'):
        return {'status': 'held_reports_disabled', 'persisted_in_job': True}
    claim = state.reserve_delivery(key, now_et().date().isoformat(), 20, 'owner_report')
    if claim != 'reserved':
        return {'status': claim, 'persisted_in_job': True}
    try:
        response = execute('ZOHO_MAIL_MESSAGES_SEND_EMAIL', {
            'accountId': cfg['mail_account'], 'fromAddress': cfg['mail_from'],
            'toAddress': cfg['report_email'], 'ccAddress': cfg.get('report_cc', ''),
            'subject': 'SJT verified job report - '+key[:80],
            'content': json.dumps(report, indent=2, default=str), 'mailFormat': 'plaintext'})
        receipt = mail_receipt(response)
        state.delivered(key, 'provider_accepted' if receipt else 'uncertain', receipt)
        return {'status': 'provider_accepted' if receipt else 'uncertain_do_not_retry', 'persisted_in_job': True}
    except Exception:
        state.delivered(key, 'uncertain')
        return {'status': 'uncertain_do_not_retry', 'persisted_in_job': True}


def cal_bookings(fetch):
    result, skip, seen = [], 0, set()
    for _ in range(100):
        payload = fetch({'take': 100, 'skip': skip, 'sortStart': 'asc'})
        if payload.get('status') not in ('success', 'ok') or not isinstance(payload.get('data'), list):
            raise RuntimeError('Cal list failed or omitted bookings')
        page = payload['data']
        for booking in page:
            key = str(booking.get('uid') or booking.get('id') or '')
            if not key or key in seen:
                raise RuntimeError('invalid/repeated Cal pagination')
            seen.add(key)
            result.append(booking)
        pagination = payload.get('pagination') or {}
        if pagination.get('hasNextPage') is False or (not pagination and len(page)<100):
            return result
        if not page:
            raise RuntimeError('empty Cal page with next page indicated')
        skip += len(page)
    raise RuntimeError('Cal pagination limit; refusing partial success')
