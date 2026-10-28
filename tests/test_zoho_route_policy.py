import unittest
from unittest.mock import Mock
from zoho_route_policy import DirectCircuit,execute,rejected

class RoutingTests(unittest.TestCase):
    def setUp(self):self.now=100.;self.circuit=DirectCircuit(lambda:self.now)
    def call(self,slug,direct,bridge):return execute(slug,{},direct,bridge,True,self.circuit)
    def test_auth_failure_uses_existing_bridge(self):
        d=Mock(return_value={'error':'invalid_code'});b=Mock(return_value={'data':{'data':[{'id':'ok'}]}})
        self.assertEqual('ok',self.call('ZOHO_GET_ZOHO_RECORDS',d,b)['data']['data'][0]['id'])
    def test_no_repeated_bad_auth_on_every_read(self):
        d=Mock(return_value={'error':'invalid_code'});b=Mock(return_value={'data':{'data':[]}})
        self.call('ZOHO_GET_ZOHO_RECORDS',d,b);self.call('ZOHO_GET_ZOHO_RECORDS',d,b)
        self.assertEqual(d.call_count,1);self.assertEqual(b.call_count,2)
    def test_cooldown_recovers_without_key_change(self):
        d=Mock(side_effect=[{'error':'invalid_code'},{'data':{'data':[{'id':'recovered'}]}}]);b=Mock(return_value={'data':{'data':[]}})
        self.call('ZOHO_GET_ZOHO_RECORDS',d,b);self.now+=3601
        self.assertEqual('recovered',self.call('ZOHO_GET_ZOHO_RECORDS',d,b)['data']['data'][0]['id'])
    def test_healthy_direct_does_not_call_bridge(self):
        d=Mock(return_value={'data':{'data':[]}});b=Mock();self.call('ZOHO_GET_ZOHO_RECORDS',d,b);b.assert_not_called()
    def test_mail_uses_bridge_not_direct_crm(self):
        d=Mock();b=Mock(return_value={'data':{'messageId':'m'}});self.call('ZOHO_MAIL_MESSAGES_SEND_EMAIL',d,b);d.assert_not_called()
    def test_uncertain_write_is_never_replayed(self):
        d=Mock(side_effect=TimeoutError());b=Mock();self.assertTrue(self.call('ZOHO_CREATE_ZOHO_RECORD',d,b)['uncertain']);b.assert_not_called()
    def test_auth_rejected_write_can_use_bridge(self):
        d=Mock(return_value={'error':'invalid_code'});b=Mock(return_value={'data':{'data':[{'code':'SUCCESS'}]}})
        self.assertFalse(rejected(self.call('ZOHO_CREATE_ZOHO_RECORD',d,b)));b.assert_called_once()
    def test_read_timeout_can_use_bridge(self):
        d=Mock(side_effect=TimeoutError());b=Mock(return_value={'data':{'data':[]}})
        self.call('ZOHO_GET_ZOHO_RECORDS',d,b);b.assert_called_once()
    def test_partial_write_not_accepted_or_replayed(self):
        d=Mock(return_value={'data':{'data':[{'code':'SUCCESS'},{'code':'INVALID_DATA','status':'error'}]}});b=Mock()
        self.assertTrue(self.call('ZOHO_UPDATE_ZOHO_RECORD',d,b)['uncertain']);b.assert_not_called()
    def test_bridge_failure_is_visible(self):
        d=Mock(return_value={'error':'invalid_code'});b=Mock(side_effect=RuntimeError())
        self.assertIn('error',self.call('ZOHO_GET_ZOHO_RECORDS',d,b))
    def test_nested_failure_is_rejected(self):self.assertTrue(rejected({'data':{'data':{'status':{'code':401}}}}))

if __name__=='__main__':unittest.main()
