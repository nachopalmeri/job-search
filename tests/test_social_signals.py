import unittest
from datetime import date

from scripts.social_signals import classify_post, triage


TODAY = date(2026, 10, 17)


class SocialSignalTests(unittest.TestCase):
    def test_four_day_concrete_job_is_candidate_not_eligible_match(self):
        post = {
            "platform": "X", "published_at": "2026-10-13", "post_url": "https://x.com/recruiter/status/1",
            "text": "Estamos buscando una persona trainee", "company": "Acme",
            "job_title": "IT Trainee", "application_url": "https://acme.example/jobs/1",
        }
        bucket, reason = classify_post(post, today=TODAY)
        self.assertEqual(bucket, "opportunity_candidate")
        self.assertIn("verificar", reason)

    def test_five_day_post_is_stale(self):
        bucket, _ = classify_post({"published_at": "2026-10-12", "text": "hiring"}, today=TODAY)
        self.assertEqual(bucket, "stale")

    def test_referral_is_separate_from_active_jobs(self):
        post = {"published_at": "2026-10-17", "text": "Tengo referidos para roles trainee, escribime por DM"}
        result = triage([post], today=TODAY)
        self.assertEqual(len(result["networking_leads"]), 1)
        self.assertEqual(len(result["opportunity_candidates"]), 0)

    def test_missing_or_invalid_original_date_never_enters_fresh_buckets(self):
        result = triage([{"text": "hiring"}, {"published_at": "not-a-date", "text": "hiring"}], today=TODAY)
        self.assertEqual(len(result["undated"]), 2)
        self.assertEqual(len(result["opportunity_candidates"]), 0)

    def test_candidate_requires_company_title_and_safe_application_url(self):
        base = {"published_at": "2026-10-17", "text": "We are hiring"}
        for extra in (
            {"company": "Acme", "job_title": "Trainee", "application_url": "javascript:alert(1)"},
            {"company": "Acme", "application_url": "https://acme.example/jobs"},
        ):
            self.assertEqual(classify_post({**base, **extra}, today=TODAY)[0], "networking_lead")


if __name__ == "__main__":
    unittest.main()
