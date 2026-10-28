import ast
import datetime
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import reliability as r

class IntegrationTests(unittest.TestCase):
    def function(self,name):
        t=ast.parse(Path('concierge.py').read_text());n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);n.decorator_list=[]
        return compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),'selected-source','exec')
    def test_actual_daily_preserves_prequalified_until_approved(self):
        lead={'id':'backlog','Full_Name':'Customer','Email':'customer@real.invalid','Lead_Status':'Pre-Qualified','Description':''}
        execute=Mock(return_value={'data':{'data':[{'code':'SUCCESS','details':{'id':'backlog'}}]}})
        ns={'datetime':datetime,'json':json,'_call_center_window_open':lambda:True,'pending_leads':lambda *a,**k:[lead],'queued_lead_ids':lambda:set(),'zoho_exec':execute,'_sync_recent_cal_bookings':lambda:{'errors':[]},'_llm_json':lambda *a:{'subject':'Estimate','body':'Approved review candidate'},'OUTREACH_DAILY_CAP':10,'_lead_is_stopped':lambda x:False,'save_draft':Mock(return_value='draft1'),'record_report':Mock(return_value='report1'),'response_ok':r.response_ok,'OUTREACH_PROMPT':'test','QUALIFY_PROMPT':'test','CAL_LINK':'https://cal.com/example','_call_center_plan':lambda x:{'counts':{},'window_open_8am_9pm_et':True,'whatsapp_autosend_enabled':False}}
        exec(self.function('run_daily_pipeline'),ns);result=ns['run_daily_pipeline']()
        self.assertEqual(result['outreach'][0]['sent'],False)
        self.assertEqual(result['outreach'][0]['draft_id'],'draft1')
        for call in execute.call_args_list:
            self.assertNotIn('SEND_EMAIL',call.args[0]);self.assertNotEqual(call.args[1]['data'][0]['Lead_Status'],'Attempted to Contact')
    def test_actual_daily_crm_error_not_contacted(self):
        ns={'datetime':datetime,'json':json,'_call_center_window_open':lambda:True,'pending_leads':Mock(side_effect=RuntimeError('CRM failed')),'queued_lead_ids':lambda:set(),'zoho_exec':Mock(),'_sync_recent_cal_bookings':lambda:{'errors':[]},'record_report':lambda *a:'r','_call_center_plan':lambda x:{'counts':{},'window_open_8am_9pm_et':True,'whatsapp_autosend_enabled':False},'CAL_LINK':'x'}
        exec(self.function('run_daily_pipeline'),ns);result=ns['run_daily_pipeline']();self.assertTrue(result['errors']);ns['zoho_exec'].assert_not_called()
    def test_job_claim_is_idempotent_and_completion_visible(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'SJT_STATE_PATH':str(Path(tmp)/'state.db'),'SJT_STATE_PERSISTENT_CONFIRMED':'true'}):
            function=Mock(return_value={'errors':[]});row,created=r.start_job('daily',function)
            for _ in range(100):
                if r.job_status(row[0])['status']!='running':break
                time.sleep(.01)
            row2,created2=r.start_job('daily',function)
            self.assertTrue(created);self.assertFalse(created2);self.assertEqual(row2[0],row[0]);function.assert_called_once();self.assertEqual(r.job_status(row[0])['status'],'needs_owner_review')
    def test_job_error_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'SJT_STATE_PATH':str(Path(tmp)/'state.db'),'SJT_STATE_PERSISTENT_CONFIRMED':'true'}):
            row,_=r.start_job('daily',lambda:{'errors':['failed']})
            for _ in range(100):
                if r.job_status(row[0])['status']!='running':break
                time.sleep(.01)
            self.assertEqual(r.job_status(row[0])['status'],'failed')
    def test_live_jobs_require_explicit_storage_activation(self):
        with patch.dict(os.environ,{'SJT_STATE_PERSISTENT_CONFIRMED':'false'}):
            with self.assertRaises(ValueError):r.start_job('daily',lambda:{'errors':[]})
    def test_runner_uses_matching_status_endpoint(self):
        s=Path('scripts/operations_runner.py').read_text();self.assertIn("base+'/jobs/'",s);self.assertNotIn('/ops/jobs/',s)

if __name__=='__main__':unittest.main()
