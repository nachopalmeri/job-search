import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.source_coverage import load_sources, new_report, mark_source, pending_sources, incomplete_sources


ROOT = Path(__file__).resolve().parents[1]


class SourceCoverageTests(unittest.TestCase):
    def test_catalog_has_unique_sources_and_every_automatic_adapter(self):
        sources = load_sources()
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"startups", "startup_jobs_ar", "cosign", "cafedev", "uade", "linkedin_posts", "firstjob", "outlier", "appgentina"} <= set(ids))
        from scripts.buscar_portales import AUTOMATED_SOURCES
        self.assertEqual({source["id"] for source in sources if source["access"] == "automatic"}, set(AUTOMATED_SOURCES))
        vibehackers = next(source for source in sources if source["id"] == "vibehackers")
        self.assertEqual(vibehackers.get("feed_url"), "https://vibehackers.io/jobs-feed.xml")
        from scripts.buscar_portales import BASE_LINKS
        self.assertEqual(BASE_LINKS["wellfound"], "https://wellfound.com/location/argentina")

    def test_coverage_stays_incomplete_until_every_source_has_a_real_status(self):
        report = new_report("2026-10-14", [{"id": "cosign"}, {"id": "uade"}])
        self.assertEqual(pending_sources(report), ["cosign", "uade"])
        mark_source(report, "cosign", "consulted_no_results", count=0)
        with self.assertRaises(ValueError):
            mark_source(report, "uade", "blocked")
        mark_source(report, "uade", "blocked", note="sesión vencida")
        self.assertEqual(pending_sources(report), [])

    def test_coverage_cli_writes_checklist_and_returns_nonzero_for_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "coverage.json"
            init = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-14", "--out", str(output), "--init"],
                capture_output=True, text=True,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["date"], "2026-10-14")
            self.assertEqual(report["sources"]["uade"]["status"], "pending")
            check = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--out", str(output), "--check"],
                capture_output=True, text=True,
            )
            self.assertEqual(check.returncode, 1)
            self.assertIn("pendientes", check.stdout.lower())

    def test_existing_report_preserves_reviews_and_picks_up_new_catalog_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "coverage.json"
            output.write_text(json.dumps({"date": "2026-10-14", "sources": {"uade": {"status": "consulted_no_results", "count": 0, "note": ""}}}), encoding="utf-8")
            init = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-14", "--out", str(output), "--init"],
                capture_output=True, text=True,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["sources"]["uade"]["status"], "consulted_no_results")
            self.assertEqual(report["sources"]["cosign"]["status"], "pending")

    def test_query_family_counts_require_partial_status_when_not_all_were_attempted(self):
        report = new_report("2026-10-19", [{"id": "linkedin"}])
        with self.assertRaisesRegex(ValueError, "partial"):
            mark_source(report, "linkedin", "consulted_with_results", count=103,
                        note="Rate limited", attempted=7, total=31)
        mark_source(report, "linkedin", "partial", count=103, note="HTTP 429",
                    attempted=7, total=31)
        self.assertEqual(report["sources"]["linkedin"]["coverage"], {"attempted": 7, "total": 31})
        self.assertEqual(incomplete_sources(report), ["linkedin"])

    def test_check_detects_incomplete_coverage_even_if_status_was_misrecorded(self):
        report = {"date": "2026-10-19", "sources": {
            "linkedin": {"status": "consulted_with_results", "count": 103,
                         "note": "7/31 query families", "coverage": {"attempted": 7, "total": 31}}
        }}
        self.assertEqual(incomplete_sources(report), ["linkedin"])

    def test_cli_records_attempted_and_total_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "coverage.json"
            report = {"date": "2026-10-19", "sources": {
                "linkedin": {"status": "pending", "count": 0, "note": ""}
            }}
            output.write_text(json.dumps(report), encoding="utf-8")
            mark = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-19",
                 "--out", str(output), "--mark", "linkedin", "--status", "partial", "--count", "103",
                 "--note", "HTTP 429", "--attempted", "7", "--total", "31"],
                capture_output=True, text=True,
            )
            self.assertEqual(mark.returncode, 0, mark.stderr)
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["sources"]["linkedin"]["coverage"], {"attempted": 7, "total": 31})
            check = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-19",
                 "--out", str(output), "--check"], capture_output=True, text=True,
            )
            self.assertEqual(check.returncode, 1)
            self.assertIn("cobertura incompleta", check.stdout.lower())


if __name__ == "__main__":
    unittest.main()
