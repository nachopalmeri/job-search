import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.source_coverage import load_sources, new_report, mark_source, pending_sources


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_has_unique_sources_and_every_automatic_adapter():
    sources = load_sources()
    ids = [source["id"] for source in sources]
    assert len(ids) == len(set(ids))
    assert {"startups", "startup_jobs_ar", "cosign", "uade", "linkedin_posts", "firstjob", "outlier", "appgentina"} <= set(ids)
    from scripts.buscar_portales import AUTOMATED_SOURCES

    assert {source["id"] for source in sources if source["access"] == "automatic"} == set(AUTOMATED_SOURCES)


def test_coverage_stays_incomplete_until_every_source_has_a_real_status():
    sources = [{"id": "cosign"}, {"id": "uade"}]
    report = new_report("2026-10-14", sources)
    assert pending_sources(report) == ["cosign", "uade"]

    mark_source(report, "cosign", "consulted_no_results", count=0)
    with pytest.raises(ValueError):
        mark_source(report, "uade", "blocked")
    mark_source(report, "uade", "blocked", note="sesión vencida")
    assert pending_sources(report) == []


def test_coverage_cli_writes_checklist_and_returns_nonzero_for_pending(tmp_path):
    output = tmp_path / "coverage.json"
    init = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-14", "--out", str(output), "--init"],
        capture_output=True, text=True,
    )
    assert init.returncode == 0, init.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["date"] == "2026-10-14"
    assert report["sources"]["uade"]["status"] == "pending"
    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--out", str(output), "--check"],
        capture_output=True, text=True,
    )
    assert check.returncode == 1
    assert "pendientes" in check.stdout.lower()


def test_existing_report_preserves_reviews_and_picks_up_new_catalog_sources(tmp_path):
    output = tmp_path / "coverage.json"
    output.write_text(json.dumps({"date": "2026-10-14", "sources": {"uade": {"status": "consulted_no_results", "count": 0, "note": ""}}}), encoding="utf-8")
    init = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "source_coverage.py"), "--date", "2026-10-14", "--out", str(output), "--init"],
        capture_output=True, text=True,
    )
    assert init.returncode == 0, init.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["sources"]["uade"]["status"] == "consulted_no_results"
    assert report["sources"]["cosign"]["status"] == "pending"
