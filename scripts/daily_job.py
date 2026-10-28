"""Observable daily runner: no strict 9AM gate, no implicit CrewAI kickoff.
Default scheduled jobs require separately activated server effects and durable state.
The server deduplicates by New York day; delayed cron runs catch up safely.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo
import requests


def quota_exhausted(status, body):
    return status in (402, 429) or 'monthly execution limit' in str(body).lower()


def require_free_allowance(r):
    if quota_exhausted(r.status_code, r.text):
        raise RuntimeError('free execution allowance exhausted; stop, never buy or retry')


def run_job(session, base, token, kind, timeout=1200):
    headers = {'x-machine-token': token}
    r = session.post(base+'/run-'+kind, headers=headers, json={}, timeout=60)
    r.raise_for_status()
    body = r.json()
    ident = body.get('job_id')
    if not ident:
        raise RuntimeError('server did not return observable job id')
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        r = session.get(base+'/ops/jobs/'+ident, headers=headers, timeout=60)
        r.raise_for_status()
        job = r.json()
        status = job.get('status')
        if status == 'succeeded':
            print(json.dumps({'kind':kind,'job_id':ident,'status':status,'mode':job.get('result',{}).get('mode')}, default=str))
            return
        if status in ('failed','partial','succeeded_read_only'):
            # Print summary only, not recipients, bodies, tokens or provider errors.
            print(json.dumps({'kind':kind,'job_id':ident,'status':status,
                'mode':job.get('result',{}).get('mode'),
                'error_count':len(job.get('result',{}).get('errors',[]))}))
            raise RuntimeError('job did not complete all configured live outcomes: '+status)
        time.sleep(5)
    raise TimeoutError('job unfinished; inspect stored job before retrying')


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--kind',choices=['daily','social','health','hunt','all'],default='all')
    args=p.parse_args(argv)
    base=os.environ.get('CONCIERGE_URL','https://sjt-concierge.onrender.com').rstrip('/')
    if not base.startswith('https://'):
        raise RuntimeError('HTTPS required')
    if args.kind=='health':
        r=requests.get(base+'/ping',timeout=60);r.raise_for_status()
        print('Health only: not proof of lead processing, posting or delivery.')
        return 0
    if args.kind=='hunt':
        raise RuntimeError('CrewAI paused after monthly execution limit. No automatic retry or paid upgrade; reassess free allowance separately.')
    token=os.environ.get('MACHINE_TOKEN','').strip()
    if not token:
        raise RuntimeError('MACHINE_TOKEN missing; no jobs started')
    now=dt.datetime.now(ZoneInfo('America/New_York'))
    if os.environ.get('GITHUB_EVENT_NAME')=='schedule' and not 9 <= now.hour < 21:
        print('Outside 9AM-9PM ET; no jobs claimed. Catch-up remains eligible in the next operating window.')
        return 0
    errors=[]
    with requests.Session() as s:
        for kind in (['daily','social'] if args.kind=='all' else [args.kind]):
            try: run_job(s,base,token,kind)
            except Exception as exc:
                errors.append(kind+': '+type(exc).__name__)
    if errors:
        print('::error::'+ '; '.join(errors))
        return 1
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc:
        print('::error::'+type(exc).__name__+': '+str(exc)[:200])
        sys.exit(1)
