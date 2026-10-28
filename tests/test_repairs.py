import ast
import datetime as dt
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import sjt_reliability as r
import sjt_web_jobs as web


def lead(i=1, status='Not Contacted'):
    return {'id':str(i),'Full_Name':'Local Resident','Email':'resident%s@household.net'%i,
            'Lead_Status':status,'Description':''}


def response(rows, more=False, token=None):
    return {'successful':True,'data':{'data':rows,'info':{'more_records':more,'next_page_token':token}}}


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.state=r.State(self.tmp.name)
        self.cfg={'crm_writes':True,'outreach_enabled':False,'mail_account':'mock',
            'mail_from':'owner@household.net','daily_cap':10}
        self.clock=patch.object(r,'now_et',return_value=dt.datetime(2026,10,28,10,tzinfo=r.NY))
        self.clock.start()
    def tearDown(self): self.clock.stop();self.tmp.cleanup()
    def test_backlog_all_103_reached(self):
        rows=[lead(i,'Recycled' if i<59 else 'Not Contacted') for i in range(162)]
        self.assertEqual(103,len(r.select_leads(r.fetch_leads(lambda *a:response(rows)),dt.date(2026,10,28))))
    def test_oldest_first_pagination(self):
        calls=[]
        def ex(slug,args):
            calls.append(args)
            return response([lead(1)],True,'tok') if len(calls)==1 else response([lead(2)])
        self.assertEqual(2,len(r.fetch_leads(ex)))
        self.assertEqual('asc',calls[0]['sort_order'])
        self.assertNotIn('page',calls[1]);self.assertEqual('tok',calls[1]['page_token'])
    def test_repeat_page_fails(self):
        with self.assertRaises(RuntimeError):r.fetch_leads(lambda *a:response([lead()],True,'tok'))
    def test_provider_error_not_zero(self):
        with self.assertRaises(RuntimeError):r.records({'error':'rejected'})
    def test_native_records(self):self.assertEqual(1,len(r.records({'data':[lead()]})[0]))
    def test_prequalified_remains_eligible(self):self.assertEqual(1,len(r.select_leads([lead(status='Pre-Qualified')],dt.date.today())))
    def test_future_recycle_held(self):
        x=lead(status='Recycled');x['Description']='[SJT_FOLLOWUP 2026-11-28]'
        self.assertFalse(r.select_leads([x],dt.date(2026,10,28)))
    def test_due_recycle_selected(self):
        x=lead(status='Recycled');x['Description']='[SJT_FOLLOWUP 2026-10-27]'
        self.assertEqual(1,len(r.select_leads([x],dt.date(2026,10,28))))
    def test_stop_variants(self):
        for msg in ['STOP.','Please unsubscribe','opt-out','do not contact']:
            x=lead();x['Description']=msg
            self.assertTrue(r.stopped(x));self.assertFalse(r.select_leads([x],dt.date.today()))
    def test_test_email_suppressed(self):
        x=lead();x['Email']='one@example.com';self.assertFalse(r.mail_address(x))
    def test_sample_name_suppressed(self):
        x=lead();x['Full_Name']='Test Lead';self.assertFalse(r.mail_address(x))
    def test_global_cap_across_instances(self):
        for i in range(10):self.assertEqual('reserved',self.state.reserve_delivery(str(i),'today'))
        other=r.State(self.tmp.name);self.assertEqual('daily_cap',other.reserve_delivery('eleven','today'))
    def test_delivery_replay_rejected(self):
        self.state.reserve_delivery('same','today');self.assertEqual('already_claimed',self.state.reserve_delivery('same','tomorrow'))
    def test_job_daily_dedupe(self):
        a,created=self.state.claim_job('daily:2026-10-28','daily')
        b,again=self.state.claim_job('daily:2026-10-28','daily')
        self.assertTrue(created);self.assertFalse(again);self.assertEqual(a,b)
    def test_failed_report_does_not_erase_result(self):
        ident,_=self.state.claim_job('k','daily');self.state.finish(ident,'partial',{'eligible':103})
        self.assertEqual(103,self.state.job(ident)['result']['eligible'])
    def test_missing_job_not_found(self):self.assertIsNone(self.state.job('none'))
    def test_no_implicit_state_directory(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(RuntimeError):r.configured_state()
    def test_persistent_state_requires_ack(self):
        with patch.dict(os.environ,{'SJT_STATE_DIR':self.tmp.name},clear=True):
            with self.assertRaises(RuntimeError):r.configured_state()
    def test_absent_token_fails_closed(self):self.assertFalse(r.authorized('',''))
    def test_wrong_token_rejected(self):self.assertFalse(r.authorized('expected','wrong'))
    def test_correct_token(self):self.assertTrue(r.authorized('expected','expected'))
    def test_provider_receipt_required(self):self.assertFalse(r.mail_receipt({'successful':True,'data':{}}))
    def test_provider_nested_failure_rejected(self):self.assertFalse(r.mail_receipt({'data':{'status':{'code':400},'data':{'messageId':'fake'}}}))
    def test_provider_receipt_accepted(self):self.assertEqual('m1',r.mail_receipt({'successful':True,'data':{'status':{'code':200},'data':{'messageId':'m1'}}}))
    def test_email_disabled_no_transport(self):
        ex=Mock();self.assertEqual('held_outreach_disabled',r.deliver(ex,self.state,lead(),'s','b',self.cfg)['status']);ex.assert_not_called()
    def test_quiet_hours_rechecked(self):
        cfg={**self.cfg,'outreach_enabled':True};ex=Mock()
        with patch.object(r,'now_et',return_value=dt.datetime(2026,10,28,22,tzinfo=r.NY)):
            self.assertEqual('held_quiet_hours',r.deliver(ex,self.state,lead(),'s','b',cfg)['status'])
        ex.assert_not_called()
    def test_uncertain_email_no_retry(self):
        cfg={**self.cfg,'outreach_enabled':True};ex=Mock(side_effect=TimeoutError())
        self.assertEqual('uncertain_do_not_retry',r.deliver(ex,self.state,lead(),'s','b',cfg)['status'])
        self.assertEqual('already_claimed',r.deliver(ex,self.state,lead(),'s','b',cfg)['status']);self.assertEqual(1,ex.call_count)
    def test_write_requires_crm_receipt(self):
        with self.assertRaises(RuntimeError):r.mark(lambda *a:{'data':{'data':[{'code':'INVALID_DATA'}]}},lead(),'Pre-Qualified','note')
    def test_read_only_never_calls_llm_or_send(self):
        ex=Mock(return_value=response([lead()]));llm=Mock()
        out=r.daily(ex,llm,'q','m',self.state,{**self.cfg,'crm_writes':False})
        self.assertEqual('read_only',out['mode']);self.assertEqual(1,ex.call_count);llm.assert_not_called()
    def test_held_prequalified_not_marked_contacted(self):
        ex=Mock(return_value=response([lead(status='Pre-Qualified')]))
        out=r.daily(ex,Mock(),'q','m',self.state,self.cfg)
        self.assertEqual('held_outreach_disabled',out['outcomes'][0]['status']);self.assertEqual(1,ex.call_count)
    def test_failed_send_not_marked_contacted(self):
        calls=[]
        def ex(slug,args):
            calls.append(slug)
            return response([lead(status='Pre-Qualified')]) if slug=='ZOHO_GET_ZOHO_RECORDS' else {'successful':False}
        out=r.daily(ex,lambda *a:{'subject':'hello','body':'Reply STOP'},'q','m',self.state,{**self.cfg,'outreach_enabled':True})
        self.assertEqual('uncertain_do_not_retry',out['outcomes'][0]['status']);self.assertNotIn('ZOHO_UPDATE_ZOHO_RECORD',calls)
    def test_mail_success_then_contact_status(self):
        calls=[]
        def ex(slug,args):
            calls.append(slug)
            if slug=='ZOHO_GET_ZOHO_RECORDS':return response([lead(status='Pre-Qualified')])
            if slug=='ZOHO_MAIL_MESSAGES_SEND_EMAIL':return {'data':{'data':{'messageId':'receipt'}}}
            return response([{'code':'SUCCESS'}])
        out=r.daily(ex,lambda *a:{'subject':'hello','body':'Reply STOP'},'q','m',self.state,{**self.cfg,'outreach_enabled':True})
        self.assertEqual('provider_accepted',out['outcomes'][0]['status'])
        self.assertLess(calls.index('ZOHO_MAIL_MESSAGES_SEND_EMAIL'),calls.index('ZOHO_UPDATE_ZOHO_RECORD'))
    def test_social_disabled_no_calls(self):
        ex=Mock();out=web.social({'SOCIAL_SERVICES':[('Cleaning','Help','tag','')],'_social_exec':ex},self.state,{'social_enabled':False})
        self.assertEqual('read_only',out['mode']);ex.assert_not_called()
    def test_social_text_fallback_no_generator(self):
        calls=[]
        def ex(slug,args):calls.append(slug);return {'data':{'id':'post'}}
        with patch.dict(os.environ,{},clear=True):
            out=web.social({'SOCIAL_SERVICES':[('Cleaning','Help','tag','')],'_social_exec':ex,'SOCIAL_FB_PAGE_ID':'page'},self.state,{'social_enabled':True})
        self.assertEqual(['FACEBOOK_CREATE_POST'],calls);self.assertIn('Michael Sabo',out['caption'])
        self.assertEqual('held_real_image_required',out['outcomes'][1]['status'])
    def test_reports_disabled_persisted_only(self):
        ex=Mock();out=r.report_mail(ex,self.state,{},self.cfg,'k');ex.assert_not_called();self.assertTrue(out['persisted_in_job'])
    def test_cal_follows_next_page(self):
        fetch=Mock(side_effect=[{'status':'success','data':[{'uid':'1'}],'pagination':{'hasNextPage':True}}, {'status':'success','data':[{'uid':'2'}],'pagination':{'hasNextPage':False}}])
        self.assertEqual(2,len(r.cal_bookings(fetch)));self.assertEqual(1,fetch.call_args_list[1].args[0]['skip'])
    def test_cal_repeated_page_rejected(self):
        with self.assertRaises(RuntimeError):r.cal_bookings(lambda a:{'status':'success','data':[{'uid':'1'}],'pagination':{'hasNextPage':True}})
    def test_source_uses_token_pagination(self):
        source=Path('concierge.py').read_text();self.assertIn('"page_token", "sort_by"',source);ast.parse(source)
    def test_widget_sends_prior_history(self):
        source=Path('widget.js').read_text();self.assertIn('history: prior',source);self.assertIn('if (!r.ok)',source)
    def test_runner_does_not_kickoff_crewai(self):
        source=Path('scripts/daily_job.py').read_text();self.assertNotIn('/kickoff',source);self.assertNotIn('|| true',source)


@unittest.skipUnless(importlib.util.find_spec('flask'),'Flask unavailable')
class HTTPTests(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        self.app=Flask(__name__)
        self.app.add_url_rule('/run-daily','run_daily',lambda:'legacy',methods=['GET','POST'])
        self.app.add_url_rule('/run-social','run_social',lambda:'legacy',methods=['GET','POST'])
        self.app.add_url_rule('/ping','ping',lambda:'ok')
        web.install(self.app,{})
        self.client=self.app.test_client()
    def test_missing_token_503(self):
        with patch.dict(os.environ,{},clear=True):self.assertEqual(503,self.client.post('/run-daily').status_code)
    def test_bad_token_401(self):
        with patch.dict(os.environ,{'MACHINE_TOKEN':'test'},clear=True):self.assertEqual(401,self.client.post('/run-daily').status_code)
    def test_get_cannot_start_job(self):
        with patch.dict(os.environ,{'MACHINE_TOKEN':'test'},clear=True):self.assertEqual(405,self.client.get('/run-daily',headers={'x-machine-token':'test'}).status_code)
    def test_no_persistent_state_no_job(self):
        with patch.dict(os.environ,{'MACHINE_TOKEN':'test'},clear=True):self.assertEqual(503,self.client.post('/run-daily',headers={'x-machine-token':'test'}).status_code)
    def test_ping_public(self):self.assertEqual(200,self.client.get('/ping').status_code)

if __name__=='__main__':unittest.main()
