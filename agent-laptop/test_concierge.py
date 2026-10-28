"""Offline tests only. No real accounts, browsers, calls or outreach."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from concierge_assistant import Store, classify, draft_job, confirm, DEFAULTS, worker_lock, local_draft
from concierge_adapters import allowed_url, browser_send, send_email, email_config


class ConciergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Store(Path(self.tmp.name))
        self.cfg = json.loads(json.dumps(DEFAULTS))
        self.save_config()

    def save_config(self):
        (self.s.root / 'concierge_config.json').write_text(json.dumps(self.cfg), encoding='utf-8')

    def tearDown(self):
        self.s.db.close(); self.tmp.cleanup()

    def draft(self):
        return self.s.add('Zoho Mail','email','mailto:test@example.com','test@example.com','Test body',subject='Test')

    def test_keyword_candidate(self):
        self.assertEqual(classify('Looking for a handyman in Apopka'), 'handyman work')

    def test_skip_sensitive_and_commercial(self):
        for text in ['Lost dog need help handyman', 'Need someone for commercial cleaning', 'Politics recommend handyman']:
            self.assertIsNone(classify(text))

    def test_no_intent(self):
        self.assertIsNone(classify('I am a handyman advertising services'))

    def test_callback_no_claimed_qualifications(self):
        draft = draft_job('cleaning', '(352) 849-2344')
        self.assertIn('(352) 849-2344', draft)
        self.assertNotIn('licensed', draft)

    def test_dedupe(self):
        self.assertTrue(self.s.observe('Nextdoor','https://nextdoor.com/p/1','Hello'))
        self.assertFalse(self.s.observe('Nextdoor','https://nextdoor.com/p/1','Hello'))
        self.assertTrue(self.s.observe('Nextdoor','https://nextdoor.com/p/1','Hello changed'))

    def test_replay_denied(self):
        ident = self.draft(); self.s.claim(ident)
        with self.assertRaises(ValueError): self.s.claim(ident)

    def test_expired_denied(self):
        ident = self.draft()
        self.s.db.execute('UPDATE actions SET created=? WHERE id=?', (time.time()-90000, ident)); self.s.db.commit()
        with self.assertRaises(ValueError): self.s.claim(ident)

    def test_stop(self):
        ident = self.draft(); (self.s.data / 'STOP').touch()
        with self.assertRaises(RuntimeError): self.s.claim(ident)
        self.assertEqual(self.s.action(ident)['status'], 'draft')

    def test_edit_attempted_denied(self):
        ident = self.draft(); self.s.claim(ident)
        with self.assertRaises(ValueError): self.s.edit(ident, 'Changed')

    def test_exact_confirmation(self):
        row = self.s.action(self.draft())
        self.assertFalse(confirm(row, lambda _: 'yes'))
        self.assertFalse(confirm(row, lambda _: 'go 99999'))
        self.assertTrue(confirm(row, lambda _: 'go ' + str(row['id'])))

    def test_url_validation(self):
        self.assertEqual(allowed_url('https://nextdoor.com/news_feed/'), 'nextdoor.com')
        for url in ['http://nextdoor.com','https://nextdoor.com.evil.example','https://evilnextdoor.com',
                    'https://user:pass@nextdoor.com','https://127.0.0.1/','https://nextdoor.com:9999/']:
            with self.assertRaises(ValueError): allowed_url(url)

    def test_no_browser_send_adapter(self):
        row = self.s.action(self.draft())
        with self.assertRaises(RuntimeError): browser_send(self.s, row, lambda _: True)
        self.assertEqual(self.s.action(row['id'])['status'], 'draft')

    def test_email_disabled(self):
        with self.assertRaises(RuntimeError): email_config(self.s)

    def test_offline_model_not_configured(self):
        with self.assertRaises(RuntimeError): local_draft(self.s, 'hello')

    def test_lock(self):
        with worker_lock(self.s):
            with self.assertRaises(FileExistsError):
                with worker_lock(self.s): pass
        self.assertFalse((self.s.data / 'worker.lock').exists())

    def test_mail_mock_success(self):
        self.cfg['email']['enabled'] = True; self.save_config()
        ident = self.draft()
        with patch.dict('os.environ', {'SJT_ZOHO_MAIL_PASSWORD': 'fake-test-only'}), patch('concierge_adapters.smtplib.SMTP_SSL') as smtp:
            smtp.return_value.__enter__.return_value.send_message.return_value = {}
            send_email(self.s, self.s.action(ident))
            self.assertEqual(self.s.action(ident)['status'], 'smtp_accepted')
            self.assertEqual(smtp.return_value.__enter__.return_value.send_message.call_count, 1)
            with self.assertRaises(ValueError): send_email(self.s, self.s.action(ident))
            self.assertEqual(smtp.return_value.__enter__.return_value.send_message.call_count, 1)

    def test_mail_uncertain_not_retried(self):
        self.cfg['email']['enabled'] = True; self.save_config()
        ident = self.draft()
        with patch.dict('os.environ', {'SJT_ZOHO_MAIL_PASSWORD': 'fake-test-only'}), patch('concierge_adapters.smtplib.SMTP_SSL') as smtp:
            smtp.return_value.__enter__.return_value.send_message.side_effect = TimeoutError()
            with self.assertRaises(TimeoutError): send_email(self.s, self.s.action(ident))
            self.assertEqual(self.s.action(ident)['status'], 'uncertain')

    def test_single_recipient_only(self):
        self.cfg['email']['enabled'] = True; self.save_config()
        ident = self.s.add('Zoho Mail','email','mailto:a@example.com,b@example.com','a@example.com,b@example.com','Body',subject='Subject')
        with patch.dict('os.environ', {'SJT_ZOHO_MAIL_PASSWORD': 'fake-test-only'}), patch('concierge_adapters.smtplib.SMTP_SSL') as smtp:
            with self.assertRaises(ValueError): send_email(self.s, self.s.action(ident))
            smtp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
