"""Stdlib-only regressions for CafeDev discovery and date provenance."""

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import buscar_portales as search
from scripts.source_coverage import mark_source, new_report


class CafeDevSourceTests(unittest.TestCase):
    def test_partial_source_is_not_counted_as_complete_coverage(self):
        report = new_report("2026-10-18", [{"id": "linkedin"}])
        mark_source(report, "linkedin", "partial", count=252, note="HTTP 429 luego de 13/31 consultas")
        self.assertEqual(report["sources"]["linkedin"]["count"], 252)
        self.assertEqual(report["sources"]["linkedin"]["status"], "partial")

    def test_candidates_keep_source_and_apply_links_but_not_indexing_as_publication(self):
        rows = [
            {
                "id": "latam-1", "title": "Junior QA Engineer", "company_name": "Acme",
                "url": "https://cafedev.co/empleos/acme-qa", "apply_url": "https://jobs.lever.co/acme/1",
                "country": "CO", "countries": ["CO", "AR"], "city": "Bogotá",
                "workplace_type": "remote", "employment_type": "full-time", "skills": ["Python"],
                "published_at": "2026-10-17", "first_seen_at": "2026-10-18T08:00:00Z",
            },
            {
                "id": "us-1", "title": "Junior Data Analyst", "company_name": "US only",
                "url": "https://cafedev.co/empleos/us-only", "apply_url": "https://example.com/apply",
                "country": "US", "countries": ["US"], "city": "Austin", "workplace_type": "remote",
            },
            {
                "id": "unknown-1", "title": "AI Intern", "company_name": "Unknown Geo",
                "url": "https://cafedev.co/empleos/unknown", "apply_url": "https://example.com/apply",
                "workplace_type": "remote", "first_seen_at": "2026-10-18T08:00:00Z",
            },
            {
                "id": "senior-title-1", "title": "Senior Security Engineer", "company_name": "Unknown seniority",
                "url": "https://cafedev.co/empleos/senior-security", "apply_url": "https://example.com/apply",
                "country": "AR", "workplace_type": "remote", "skills": ["Linux", "Python"],
            },
        ]

        def fake(url, retries=2):
            return {"items": rows, "page": 1, "pages": 1}

        with patch.object(search, "_get_json_with_retry", side_effect=fake) as request, patch.object(search.time, "sleep"):
            jobs = search.scrape_cafedev()

        self.assertEqual(request.call_count, 16)
        self.assertEqual([job["job_id"] for job in jobs], ["latam-1", "unknown-1", "senior-title-1"])
        self.assertEqual(jobs[0]["ubicacion"], "Bogotá, Colombia (acepta Argentina)")
        self.assertEqual(jobs[0]["apply_url"], "https://jobs.lever.co/acme/1")
        self.assertEqual(jobs[0]["fecha"], "")
        self.assertEqual(jobs[1]["estado"], "GEO_NO_VERIFICADA")

        with tempfile.TemporaryDirectory() as directory:
            unverified = Path(directory) / "unverified.tsv"
            fresh, secondary = search._filter_fresh(
                jobs, "cafedev", today=date(2026, 10, 18), unverified_path=unverified,
            )
            self.assertEqual(fresh, [])
            self.assertEqual(secondary, [])
            report = unverified.read_text(encoding="utf-8")
            self.assertIn("2026-10-17", report)  # Aggregator hint, not original-date evidence.
            self.assertIn("2026-10-18T08:00:00Z", report)
            self.assertIn("https://jobs.lever.co/acme/1", report)
            self.assertIn("fecha original no verificable", report)


if __name__ == "__main__":
    unittest.main()
