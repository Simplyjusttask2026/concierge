import ast
import datetime as dt
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import reliability as r

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'SJT_STATE_PATH':str(Path(self.tmp.name)/'state.db'),'SJT_STATE_PERSISTENT_CONFIRMED':'true'})
        self.env.start()
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def test_nested_provider_failure(self):self.assertFalse(r.response_ok({'data':{'status':{'code':401}}}))
    def test_success_false(self):self.assertFalse(r.response_ok({'successful':False}))
    def test_none_failure(self):self.assertFalse(r.response_ok(None))
    def test_crm_partial_failure(self):self.assertFalse(r.response_ok({'data':{'data':[{'code':'INVALID_DATA','status':'error'}]}}))
    def test_crm_success(self):self.assertTrue(r.response_ok({'data':{'data':[{'code':'SUCCESS'}]}}))
    def test_missing_token_fails_closed(self):self.assertFalse(r.check_token('',''))
    def test_wrong_token_fails(self):self.assertFalse(r.check_token('abc','xyz'))
    def test_exact_token(self):self.assertTrue(r.check_token('abc','abc'))
    def test_stop_punctuation(self):self.assertTrue(r.opted_out({'Description':'STOP.'}))
    def test_optout_hyphen(self):self.assertTrue(r.opted_out({'Description':'opt-out'}))
    def test_optout_never_due(self):self.assertFalse(r.due({'Lead_Status':'Pre-Qualified','Description':'STOP!'}))
    def test_prequalified_is_eligible(self):self.assertTrue(r.due({'Lead_Status':'Pre-Qualified'}))
    def test_booked_not_due(self):self.assertFalse(r.due({'Lead_Status':'Appointment Set'}))
    def test_recycle_future(self):self.assertFalse(r.due({'Lead_Status':'Recycled','Description':'[SJT followup due=2099-01-01]'}))
    def test_recycle_past(self):self.assertTrue(r.due({'Lead_Status':'Recycled','Description':'[SJT followup due=2020-01-01]'}))
    def test_recycle_no_date_not_due(self):self.assertFalse(r.due({'Lead_Status':'Recycled'}))
    def test_103_old_waiting_leads_reached(self):
        rows=[{'id':str(i),'Created_Time':f'2026-10-{1+i//30:02}T00:00:00Z','Lead_Status':'Not Contacted' if i<103 else 'Attempted to Contact'} for i in range(162)]
        fake=lambda *a:{'data':{'data':rows,'info':{'more_records':False}}}
        out=r.pending_leads(fake)
        self.assertEqual(len(out),50);self.assertTrue(all(x['Lead_Status']=='Not Contacted' for x in out))
    def test_token_pagination_and_queued_skip(self):
        calls=[]
        def fake(slug,args):
            calls.append(args)
            if len(calls)==1:return {'data':{'data':[{'id':'1','Lead_Status':'Pre-Qualified'}],'info':{'more_records':True,'next_page_token':'next'}}}
            return {'data':{'data':[{'id':'2','Lead_Status':'Not Contacted'}],'info':{'more_records':False}}}
        out=r.pending_leads(fake,exclude={'1'})
        self.assertEqual(out[0]['id'],'2');self.assertEqual(calls[1]['page_token'],'next');self.assertNotIn('page',calls[1])
    def test_read_error_not_zero(self):
        with self.assertRaises(RuntimeError):r.pending_leads(lambda *a:{'error':'auth failed'})
    def test_repeated_pagination_fails(self):
        with self.assertRaises(RuntimeError):r.pending_leads(lambda *a:{'data':{'data':[{'id':'1'}],'info':{'more_records':True,'next_page_token':'same'}}})
    def test_delayed_daylight_job_can_catch_up(self):self.assertTrue(r.scheduler_due(dt.datetime(2026,10,28,19,tzinfo=dt.timezone.utc)))
    def test_overnight_no_outreach(self):self.assertFalse(r.scheduler_due(dt.datetime(2026,10,28,3,tzinfo=dt.timezone.utc)))
    def test_manual_not_implicitly_approved(self):self.assertFalse(r.scheduler_due(dt.datetime.now(dt.timezone.utc),False))
    def test_quota_429(self):self.assertTrue(r.quota_exhausted(429,''))
    def test_quota_402(self):self.assertTrue(r.quota_exhausted(402,''))
    def test_monthly_limit(self):self.assertTrue(r.quota_exhausted(400,'Monthly execution limit reached'))
    def test_normal_status_not_quota(self):self.assertFalse(r.quota_exhausted(200,'ok'))
    def draft(self,channel='facebook',lead=''):
        ident=r.save_draft(channel,'recipient','subject','exact body',lead)
        with r.database() as c:fp=c.execute('SELECT fingerprint FROM drafts WHERE id=?',(ident,)).fetchone()[0]
        return ident,'go send '+ident+' '+fp
    def test_exact_draft_dedup(self):
        self.assertEqual(self.draft()[0],self.draft()[0])
    def test_wrong_confirmation_no_claim(self):
        ident,_=self.draft()
        with self.assertRaises(ValueError):r.claim_draft(ident,'yes')
    def test_body_change_changes_fingerprint(self):
        self.assertNotEqual(self.draft()[0],r.save_draft('facebook','recipient','subject','changed'))
    def test_one_attempt(self):
        ident,confirm=self.draft();r.claim_draft(ident,confirm)
        with self.assertRaises(ValueError):r.claim_draft(ident,confirm)
    def test_uncertain_never_replayed(self):
        ident,confirm=self.draft();r.claim_draft(ident,confirm);r.finish_draft(ident,'uncertain')
        with self.assertRaises(ValueError):r.claim_draft(ident,confirm)
    def test_social_one_per_day(self):
        ident,confirm=self.draft();r.claim_draft(ident,confirm)
        ident2=r.save_draft('facebook','recipient','','different')
        with r.database() as c:fp=c.execute('SELECT fingerprint FROM drafts WHERE id=?',(ident2,)).fetchone()[0]
        with self.assertRaises(ValueError):r.claim_draft(ident2,'go send '+ident2+' '+fp)
    def test_persistence_gate(self):
        ident,confirm=self.draft()
        with patch.dict(os.environ,{'SJT_STATE_PERSISTENT_CONFIRMED':'false'}):
            with self.assertRaises(ValueError):r.claim_draft(ident,confirm)
    def test_queued_lead_does_not_starve_backlog(self):
        self.draft('email','lead123');self.assertIn('lead123',r.queued_lead_ids())
    def test_expired_draft(self):
        ident,confirm=self.draft()
        with r.database() as c:c.execute("UPDATE drafts SET created='2020-01-01T00:00:00+00:00' WHERE id=?",(ident,))
        with self.assertRaises(ValueError):r.claim_draft(ident,confirm)
    def test_account_global_ten_cap(self):
        now=dt.datetime.now(dt.timezone.utc).replace(hour=17)
        day=now.astimezone(r.NY).date().isoformat()
        with r.database() as c:
            c.execute('CREATE TABLE deliveries(draft_id TEXT PRIMARY KEY,day TEXT,channel TEXT,lead_id TEXT)')
            c.executemany('INSERT INTO deliveries VALUES(?,?,?,?)',[(str(i),day,'email',str(i)) for i in range(10)])
        ident,confirm=self.draft('email','new')
        with self.assertRaises(ValueError):r.claim_draft(ident,confirm,now)

class SourceTests(unittest.TestCase):
    def test_all_python_syntax(self):
        for p in ('concierge.py','reliability.py','scripts/daily_job.py','scripts/operations_runner.py'):
            ast.parse(Path(p).read_text())
    def test_widget_sends_history(self):self.assertIn('history: prior',Path('widget.js').read_text())
    def test_server_management_token_guard(self):self.assertIn('def protect_management',Path('concierge.py').read_text())
    def test_no_get_job_routes(self):
        s=Path('concierge.py').read_text();self.assertIn("@app.route('/run-daily', methods=['POST'])",s);self.assertIn("@app.route('/run-social', methods=['POST'])",s)
    def test_no_autonomous_daily_email(self):
        tree=ast.parse(Path('concierge.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_daily_pipeline')
        self.assertNotIn('ZOHO_MAIL_MESSAGES_SEND_EMAIL',ast.get_source_segment(Path('concierge.py').read_text(),fn))
    def test_no_paid_image_generation(self):
        tree=ast.parse(Path('concierge.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_social_pipeline')
        segment=ast.get_source_segment(Path('concierge.py').read_text(),fn);self.assertNotIn('GEMINI_GENERATE_IMAGE',segment);self.assertNotIn('pollinations',segment)
    def test_hunter_quota_retry_guard(self):self.assertIn('if quota_exhausted(r.status_code, r.text)',Path('scripts/daily_job.py').read_text())
    def test_cal_pagination_present(self):self.assertIn("'hasNextPage'",Path('concierge.py').read_text())

if __name__=='__main__':unittest.main()
