"""One owner-activated catch-up schedule; HTTP 202 never means delivered."""
import datetime as dt
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from reliability import scheduler_due

def run_job(session,base,headers,kind):
    response=session.post(base+'/run-'+kind,headers=headers,timeout=60)
    response.raise_for_status();ident=response.json().get('job_id')
    if not ident:raise RuntimeError('Missing tracked job ID')
    deadline=time.monotonic()+1200
    while True:
        response=session.get(base+'/jobs/'+ident,headers=headers,timeout=30)
        response.raise_for_status();outcome=response.json().get('status')
        if outcome=='needs_owner_review':
            print(kind+': prepared for owner review; not posted, sent or delivered');return
        if outcome in ('failed','uncertain'):raise RuntimeError(kind+' job failed; inspect protected status')
        if time.monotonic()>=deadline:raise RuntimeError(kind+' completion unconfirmed; do not replay actions')
        time.sleep(10)

def main():
    if os.environ.get('SJT_AUTOMATION_ENABLED')!='true':raise RuntimeError('Jobs disabled pending owner activation; nothing triggered')
    if not scheduler_due(dt.datetime.now(dt.timezone.utc)):
        print('Outside daylight catch-up window; no job claimed');return
    token=os.environ.get('MACHINE_TOKEN','')
    if not token:raise RuntimeError('MACHINE_TOKEN missing; nothing triggered')
    base=os.environ.get('CONCIERGE_URL','https://sjt-concierge.onrender.com').rstrip('/')
    if not base.startswith('https://'):raise RuntimeError('HTTPS required')
    headers={'x-machine-token':token};errors=[]
    with requests.Session() as session:
        response=session.get(base+'/ping',timeout=60);response.raise_for_status()
        for kind in ('daily','social'):
            try:run_job(session,base,headers,kind)
            except Exception as ex:errors.append(kind+': '+type(ex).__name__)
    if errors:raise RuntimeError('; '.join(errors))

if __name__=='__main__':main()
