"""Regression tests for evidence-separated job discovery and source reporting."""

import unittest
from datetime import date

from scripts.cafedev_audit import audit
from scripts.opportunity_pipeline import review_route
from scripts.source_coverage import new_report
from scripts.source_inventory import MULTIPLE_DAILY, WEEKLY, build_inventory
from scripts.source_coverage import load_sources
from scripts.strategic_intelligence import build_report
from scripts.opportunity_rank import rank


class ReviewRouteTests(unittest.TestCase):
    def test_undated_promising_listing_is_kept_for_research(self):
        route, action = review_route({"closed": False}, {"eligibility": "uncertain", "freshness": "unverified", "fit_score": 4.2})
        self.assertEqual(route, "potential_research")
        self.assertIn("verificar", action)

    def test_recent_verified_fit_gets_priority_without_guessing(self):
        route, _ = review_route({}, {"eligibility": "eligible", "freshness": "primary", "fit_score": 4.6})
        self.assertEqual(route, "apply_priority")

    def test_mandatory_gap_and_closed_status_are_not_promoted(self):
        self.assertEqual(review_route({}, {"eligibility": "ineligible", "freshness": "primary", "fit_score": 5})[0], "no_compatible")
        self.assertEqual(review_route({"closed": True}, {"eligibility": "eligible", "freshness": "primary", "fit_score": 5})[0], "no_compatible")

    def test_senior_sounding_title_requires_description_review_not_automatic_veto(self):
        assessment = rank({
            "title": "Senior Security Engineer", "description": "Linux and Python security.",
            "location": "Argentina Remote", "closed": False,
        }, today=date(2026, 10, 18))
        self.assertNotEqual(assessment["eligibility"], "ineligible")
        self.assertTrue(any("seniority del título" in item for item in assessment["confirm"]))


class SourceInventoryTests(unittest.TestCase):
    def test_inventory_covers_catalog_once_and_has_explicit_cadence(self):
        sources = load_sources()
        inventory = build_inventory(sources)
        self.assertEqual(inventory["source_count"], 38)
        self.assertEqual(len({row["id"] for row in inventory["sources"]}), 38)
        for row in inventory["sources"]:
            self.assertTrue(row["method"])
            self.assertTrue(row["frequency"])
        self.assertTrue(any(row["id"] == "cafedev" and row["last_attempt_count"] == 711 for row in inventory["sources"]))
        self.assertTrue(any(row["id"] == "silver_dev" and row["frequency"] == "Diaria" for row in inventory["sources"]))

    def test_weekly_sources_are_deferred_on_sunday_but_due_on_monday(self):
        sources = load_sources()
        sunday = new_report("2026-10-18", sources)
        monday = new_report("2026-10-19", sources)
        self.assertTrue(WEEKLY)
        self.assertTrue(MULTIPLE_DAILY)
        for source_id in WEEKLY:
            self.assertEqual(sunday["sources"][source_id]["status"], "not_due")
            self.assertEqual(monday["sources"][source_id]["status"], "pending")
        for source_id in MULTIPLE_DAILY:
            self.assertEqual(sunday["sources"][source_id]["status"], "pending")


class CafeDevAuditTests(unittest.TestCase):
    def test_missing_date_and_description_remain_unknown_not_incompatible(self):
        result = audit([{
            "portal": "cafedev", "job_id": "job-1", "titulo": "Data Analyst",
            "empresa": "Acme", "ubicacion": "Remote (elegibilidad por confirmar)",
            "modalidad": "Remoto", "fecha": "", "descripcion": "Categoría: Data; Tecnologías/skills: Python, SQL",
            "url": "https://cafedev.co/empleos/job-1/",
        }], run_date="2026-10-18")
        self.assertEqual(result["records_audited"], 1)
        self.assertEqual(result["experience_unknown"], 1)
        self.assertEqual(result["original_dates_verified_in_snapshot"], 0)
        self.assertEqual(result["incompatible_confirmed_from_snapshot"], 0)
        self.assertEqual(result["candidates_without_verified_original_date"][0]["id"], "job-1")

    def test_unrelated_rows_are_not_counted_as_cafedev(self):
        result = audit([{"portal": "lever", "titulo": "Python Intern"}], run_date="2026-10-18")
        self.assertEqual(result["records_audited"], 0)


class StrategicIntelligenceTests(unittest.TestCase):
    def test_funding_signal_is_not_promoted_to_job_without_job_url(self):
        report = build_report([{
            "record_type": "startup_signal", "company": "Acme", "signal_type": "funding_round",
            "evidence_url": "https://company.example/news/round", "signal_date": "2026-10-17",
        }], run_date="2026-10-18")
        item = report["startup_research"][0]
        self.assertEqual(item["claim_level"], "verified_signal_not_hiring")
        self.assertIn("does not prove hiring", item["must_not_infer"])

    def test_networking_and_content_stay_separate_and_unpublished(self):
        report = build_report([
            {"record_type": "networking_lead", "person_or_team": "Recruiter", "public_profile_url": "https://linkedin.com/in/person", "why_relevant": "Hiring for entry IT"},
            {"record_type": "content_idea", "topic": "What I learned", "evidence_ref": "commit abc123"},
        ], run_date="2026-10-18")
        self.assertEqual(report["networking"][0]["status"], "draft_only")
        self.assertFalse(report["networking"][0]["message_sent"])
        self.assertFalse(report["content_calendar"][0]["published"])
        self.assertEqual(report["messages_sent"], 0)


if __name__ == "__main__":
    unittest.main()
