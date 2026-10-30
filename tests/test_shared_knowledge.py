import unittest
from shared_knowledge import assess_job_zip, load_company, shared_context

EXPECTED = {
 "32703","32712","32801","32804","32808","32810","32818","32819","32835",
 "34787","34761","32701","32714","32751","32750","32779","32746","32771","32773","32707"
}

class SharedKnowledgeTests(unittest.TestCase):
    def test_exact_owner_allowlist(self):
        cfg=load_company()
        actual={z for codes in cfg["service_area"]["cities"].values() for z in codes}
        self.assertEqual(actual,EXPECTED)
        self.assertEqual(len(cfg["service_area"]["cities"]),10)
    def test_every_allowed_zip(self):
        for code in EXPECTED:
            with self.subTest(zip=code): self.assertEqual(assess_job_zip(code)["status"],"in_area")
    def test_city_mapping(self):
        self.assertEqual(assess_job_zip("32703")["city"],"Apopka")
        self.assertEqual(assess_job_zip("32819")["city"],"Orlando")
    def test_missing_location(self):
        for value in [None,"","  "]:
            self.assertEqual(assess_job_zip(value)["status"],"needs_location")
    def test_no_city_only_assumption(self):
        self.assertEqual(assess_job_zip("Apopka")["status"],"needs_location")
    def test_no_profile_or_free_text_assumption(self):
        self.assertEqual(assess_job_zip("profile ZIP 32703")["status"],"needs_location")
    def test_conflicting_codes_require_clarification(self):
        self.assertEqual(assess_job_zip("32703 or 90210")["status"],"needs_location")
    def test_outside_area(self):
        self.assertEqual(assess_job_zip("90210")["status"],"out_of_area")
    def test_zip_plus_four(self):
        self.assertEqual(assess_job_zip("32703-1234")["city"],"Apopka")
    def test_invalid_zip(self):
        for value in ["3270","327030","(352) 849-2344"]:
            self.assertEqual(assess_job_zip(value)["status"],"needs_location")
    def test_all_roles_receive_current_business_rules(self):
        for role in ["Nextdoor","Website Concierge","Lead Qualifier","Social","Customer Service","Reporter"]:
            with self.subTest(role=role):
                context=shared_context(role)
                self.assertIn("tasksupport@simplyjusttask.com",context)
                self.assertIn("Cal.com",context)
                self.assertIn("one useful question at a time",context)
                self.assertIn("32703",context)
    def test_explicit_role_required(self):
        with self.assertRaises(ValueError): shared_context("")

if __name__=="__main__": unittest.main()
