import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.source_coverage import load_sources, new_report, mark_source, pending_sources


ROOT = Path(__file__).resolve().parents[1]


class SourceCoverageTests(unittest.TestCase):
    def test_catalog_has_unique_sources_and_every_automatic_adapter(self):
        sources = load_sources()
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"startups", "startup_jobs_ar", "cosign", "cafedev", "uade", "linkedin_posts", "firstjob", "outlier", "appgentina"} <= set(ids))
        from scripts.buscar_portales import AUTOMATED_SOURCES
        self.assertEqual({source["id"] for source in sources if source["access"] == "automatic"}, set(AUTOMATED_SOURCES))

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


if __name__ == "__main__":
    unittest.main()
