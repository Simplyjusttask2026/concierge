"""Fail-closed reliability core: no external service calls at import."""
from contextlib import contextmanager
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
import uuid
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York')

def response_ok(v):
    if not isinstance(v,dict) or v.get('error') or v.get('successful') is False:return False
    d=v.get('data',{})
    if isinstance(d,dict):
        status=d.get('status',{})
        if isinstance(status,dict) and isinstance(status.get('code'),int) and status['code']>=400:return False
        if d.get('error') or d.get('status') in ('error','failure'):return False
        rows=d.get('data',[])
    else:rows=d
    return not (isinstance(rows,list) and any(isinstance(x,dict) and (x.get('status')=='error' or x.get('code') not in (None,'SUCCESS')) for x in rows))

def rows_and_info(v):
    if not response_ok(v):raise RuntimeError('CRM read failed; not zero leads')
    d=v.get('data',{})
    if isinstance(d,list):return d,v.get('info',{})
    if not isinstance(d,dict):raise RuntimeError('Unexpected CRM shape')
    return d.get('data',[]),d.get('info',{})

def opted_out(row):return bool(re.search(r'\bSTOP\b|\bOPT[ -]?OUT\b|\bUNSUBSCRIB',str(row.get('Description') or ''),re.I))

def due(row,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    status=row.get('Lead_Status') or ''
    if opted_out(row):return False
    if status in ('Not Contacted','Pre-Qualified','','-None-'):return True
    if status not in ('Recycled','Contact in Future','Attempted to Contact'):return False
    explicit=re.search(r'\[SJT followup due=(\d{4}-\d{2}-\d{2})\]',str(row.get('Description') or ''))
    try:
        when=dt.datetime.fromisoformat(explicit.group(1)).replace(tzinfo=dt.timezone.utc) if explicit else dt.datetime.fromisoformat(row['Modified_Time'])+dt.timedelta(days=3 if status=='Attempted to Contact' else 30)
        if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
        return now>=when
    except (ValueError,KeyError):return False

def pending_leads(execute,batch=50,now=None,exclude=None):
    found=[];seen=set();tokens=set();page=1;token=None
    while True:
        a={'module_api_name':'Leads','fields':'First_Name,Last_Name,Full_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time,Modified_Time','sort_by':'Created_Time','sort_order':'asc','per_page':200}
        a['page_token' if token else 'page']=token or page
        rows,info=rows_and_info(execute('ZOHO_GET_ZOHO_RECORDS',a))
        if not isinstance(rows,list):raise RuntimeError('Unexpected rows')
        for row in rows:
            if not isinstance(row,dict):continue
            ident=str(row.get('id') or '')
            if not ident or ident in seen:continue
            seen.add(ident)
            if ident not in (exclude or set()) and due(row,now):found.append(row)
        if not info.get('more_records'):break
        nxt=info.get('next_page_token')
        if nxt:
            if nxt in tokens:raise RuntimeError('Repeated CRM token')
            tokens.add(nxt);token=nxt
        elif token:raise RuntimeError('Pagination token disappeared')
        else:
            page+=1
            if page>10:raise RuntimeError('Token pagination required past 2000')
        if not rows:raise RuntimeError('Pagination made no progress')
    return sorted(found,key=lambda r:(str(r.get('Created_Time') or ''),str(r.get('id') or '')))[:batch]

def quota_exhausted(status,text):return status in (402,429) or any(x in str(text).lower() for x in ('monthly execution limit','credits depleted','insufficient credits'))
def check_token(expected,provided):return bool(expected and provided) and hmac.compare_digest(str(expected),str(provided))
def scheduler_due(now,scheduled=True,manual_approved=False):return (9<=now.astimezone(NY).hour<21) if scheduled else manual_approved

class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

@contextmanager
def database():
    path=os.environ.get('SJT_STATE_PATH','')
    if not os.path.isabs(path):raise RuntimeError('An absolute owner-configured SJT_STATE_PATH is required')
    c=sqlite3.connect(path,timeout=30)
    try:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,daykey TEXT UNIQUE,kind TEXT,status TEXT,started TEXT,finished TEXT,detail TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY,fingerprint TEXT UNIQUE,channel TEXT,recipient TEXT,subject TEXT,body TEXT,lead_id TEXT,status TEXT,created TEXT,result TEXT)')
        with c:yield c
    finally:c.close()

def save_draft(channel,recipient,subject,body,lead_id=''):
    fp=hashlib.sha256(json.dumps([channel,recipient,subject,body,str(lead_id),dt.datetime.now(NY).date().isoformat()],ensure_ascii=False).encode()).hexdigest();ident=fp[:24]
    with database() as c:c.execute('INSERT OR IGNORE INTO drafts VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,fp,channel,recipient,subject,body,str(lead_id),'needs_owner_confirmation',dt.datetime.now(dt.timezone.utc).isoformat(),''))
    return ident

def record_report(kind,body):return save_draft('owner_report',os.environ.get('REPORT_EMAIL','tasksupport@simplyjusttask.com'),kind,body)

def queued_lead_ids():
    cutoff=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=24)).isoformat()
    with database() as c:
        return {r[0] for r in c.execute("SELECT DISTINCT lead_id FROM drafts WHERE channel='email' AND lead_id!='' AND (status IN ('sending','uncertain','accepted_crm_sync_failed') OR (status='needs_owner_confirmation' AND created>=?))",(cutoff,))}

def start_job(kind,function):
    if os.environ.get('SJT_STATE_PERSISTENT_CONFIRMED')!='true' or not os.path.isabs(os.environ.get('SJT_STATE_PATH','')):
        raise ValueError('Verified persistent absolute SJT_STATE_PATH required before jobs')
    if os.environ.get('SJT_STATE_PERSISTENT_CONFIRMED')!='true':raise RuntimeError('Persistent state must be verified before activating jobs')
    day=dt.datetime.now(NY).date().isoformat();ident=str(uuid.uuid4())
    with database() as c:
        try:c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?)',(ident,day+':'+kind,kind,'running',dt.datetime.now(dt.timezone.utc).isoformat(),'',''))
        except sqlite3.IntegrityError:return c.execute('SELECT id,status FROM jobs WHERE daykey=?',(day+':'+kind,)).fetchone(),False
    def work():
        try:
            result=function();errors=result.get('errors',[]) if isinstance(result,dict) else ['Missing completion result'];status='failed' if errors else 'needs_owner_review';detail=json.dumps({'errors':len(errors)})
        except Exception as ex:status='failed';detail=json.dumps({'error_type':type(ex).__name__})
        with database() as c:c.execute('UPDATE jobs SET status=?,finished=?,detail=? WHERE id=?',(status,dt.datetime.now(dt.timezone.utc).isoformat(),detail,ident))
    threading.Thread(target=work,daemon=True).start()
    return (ident,'running'),True

def job_status(ident):
    with database() as c:row=c.execute('SELECT id,kind,status,started,finished,detail FROM jobs WHERE id=?',(ident,)).fetchone()
    return dict(zip(('id','kind','status','started','finished','detail'),row)) if row else None

def claim_draft(ident,confirmation,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    if os.environ.get('SJT_STATE_PERSISTENT_CONFIRMED')!='true' or not os.path.isabs(os.environ.get('SJT_STATE_PATH','')):raise ValueError('Live sends require verified durable state')
    with database() as c:
        c.execute('CREATE TABLE IF NOT EXISTS deliveries(draft_id TEXT PRIMARY KEY,day TEXT,channel TEXT,lead_id TEXT)');c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT id,fingerprint,channel,recipient,subject,body,lead_id,status,created FROM drafts WHERE id=?',(ident,)).fetchone()
        if not row:raise ValueError('Draft not found')
        d=dict(zip(('id','fingerprint','channel','recipient','subject','body','lead_id','status','created'),row))
        if confirmation!='go send '+ident+' '+d['fingerprint']:raise ValueError('Exact displayed draft confirmation required')
        if d['status']!='needs_owner_confirmation':raise ValueError('Already claimed; no replay')
        if now-dt.datetime.fromisoformat(d['created'])>dt.timedelta(hours=24):raise ValueError('Draft expired')
        day=now.astimezone(NY).date().isoformat()
        if d['channel']=='email':
            if not 8<=now.astimezone(NY).hour<21:raise ValueError('Outside contact hours')
            if c.execute("SELECT count(*) FROM deliveries WHERE day=? AND channel='email'",(day,)).fetchone()[0]>=10:raise ValueError('Daily account cap')
            if d['lead_id'] and c.execute("SELECT 1 FROM deliveries WHERE day=? AND lead_id=? AND channel='email'",(day,d['lead_id'])).fetchone():raise ValueError('Lead already claimed today')
        elif d['channel'] in ('facebook','instagram'):
            if c.execute('SELECT 1 FROM deliveries WHERE day=? AND channel=?',(day,d['channel'])).fetchone():raise ValueError('Daily post cap')
        elif d['channel']!='owner_report':raise ValueError('Unsupported channel')
        c.execute('INSERT INTO deliveries VALUES(?,?,?,?)',(ident,day,d['channel'],d['lead_id']));c.execute("UPDATE drafts SET status='sending' WHERE id=?",(ident,))
    return d

def finish_draft(ident,status,result=''):
    if status not in ('provider_accepted','published_verified','uncertain','accepted_crm_sync_failed'):raise ValueError('Bad terminal status')
    with database() as c:c.execute('UPDATE drafts SET status=?,result=? WHERE id=?',(status,str(result)[:500],ident))
