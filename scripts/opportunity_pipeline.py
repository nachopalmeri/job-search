"""Recall-first, checkpointed opportunity pipeline for the daily job radar.

Input TSVs stay immutable. The lifecycle ledger preserves first/last sightings,
all source URLs, reviewer status, and a structured next step between runs.
Dates from aggregators are not treated as original publication dates.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from scripts.opportunity_rank import rank
except ImportError:  # direct execution from scripts/
    from opportunity_rank import rank

ROOT = Path(__file__).resolve().parent.parent
RADAR = ROOT / "radar"
LEDGER = RADAR / "job_lifecycle.json"
ORIGINAL_DATE_SOURCES = {"greenhouse", "lever", "uade", "ashby", "workday", "smartrecruiters"}


def norm(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


def key_for(row: dict) -> str:
    portal, stable_id = norm(row.get("portal")), str(row.get("job_id") or "").strip()
    if portal == "uade" and stable_id:
        return f"uade:{stable_id}"
    url = str(row.get("url") or "").split("?", 1)[0].rstrip("/").lower()
    company, title = norm(row.get("empresa")), norm(row.get("titulo"))
    if company and title:
        return f"job:{company}|{title}|{norm(row.get('ubicacion'))}"
    return f"url:{url}" if url else f"weak:{portal}|{title}"


def load_ledger(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def build_pipeline(inputs: list[Path], *, today: date, ledger_path: Path) -> tuple[list[dict], dict]:
    ledger = load_ledger(ledger_path)
    merged: dict[str, dict] = {}
    source_counts = Counter()
    for path in inputs:
        for source_row in read_tsv(path):
            source = norm(source_row.get("portal"))
            source_counts[source] += 1
            key = key_for(source_row)
            if key not in merged:
                merged[key] = {**source_row, "source_urls": [], "source_names": [], "evidence": []}
            row = merged[key]
            url = (source_row.get("url") or "").strip()
            if url and url not in row["source_urls"]:
                row["source_urls"].append(url)
            if source and source not in row["source_names"]:
                row["source_names"].append(source)
            if source_row.get("fecha"):
                row["evidence"].append({"source": source, "publication_date": source_row["fecha"], "input": path.name})

    results, eligible_window, older_window, undated = [], 0, 0, 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for key, row in merged.items():
        prior = ledger.get(key, {}) if isinstance(ledger.get(key), dict) else {}
        source_names = row["source_names"]
        source = source_names[0] if source_names else norm(row.get("portal"))
        raw_date = str(row.get("fecha") or "")[:10]
        date_verified = bool(raw_date and source in ORIGINAL_DATE_SOURCES)
        try:
            posted = date.fromisoformat(raw_date) if date_verified else None
            age = (today - posted).days if posted else None
            if age is not None and age < 0:
                posted, age, date_verified = None, None, False
        except ValueError:
            posted, age, date_verified = None, None, False
        if age is None:
            freshness = "needs_original_date"
            undated += 1
        elif age <= 3:
            freshness = "primary"
            eligible_window += 1
        elif age <= 14:
            freshness = "secondary"
            older_window += 1
        else:
            freshness = "expired_window"
        job = {**row, "job_key": key, "published_date": posted.isoformat() if posted else "",
               "publication_date_verified": date_verified, "age_days": age, "freshness_window": freshness,
               "first_seen": prior.get("first_seen") or today.isoformat(), "last_seen": today.isoformat(),
               "state": prior.get("state") or "Found", "review_notes": prior.get("review_notes", ""),
               "enrichment_status": prior.get("enrichment_status") or "pending",
               "next_action": "Open original posting; verify publication date, requirements, location, schedule, and status"}
        assess_input = {**job, "published_date": job["published_date"]}
        assessment = rank(assess_input, today=today)
        # Keep freshness confidence from the pipeline authoritative. The ranker
        # does not know whether a date is an ATS original date or portal signal.
        if not date_verified:
            assessment["freshness"] = "unverified"
            assessment["age_days"] = None
        job["assessment"] = assessment
        results.append(job)
        prior.update({"first_seen": job["first_seen"], "last_seen": today.isoformat(),
                      "state": job["state"], "review_notes": job["review_notes"],
                      "enrichment_status": job["enrichment_status"], "source_urls": job["source_urls"],
                      "title": job.get("titulo", ""), "company": job.get("empresa", "")})
        ledger[key] = prior

    results.sort(key=lambda item: (
        item["freshness_window"] == "primary", item["assessment"]["priority"],
        item["assessment"]["compatibility"]), reverse=True)
    metrics = {
        "run_date": today.isoformat(), "inputs": [str(path) for path in inputs],
        "input_rows_by_source": dict(source_counts), "unique_opportunities": len(results),
        "original_date_verified": sum(bool(item["publication_date_verified"]) for item in results),
        "within_3_days_verified": eligible_window, "within_14_days_verified": older_window,
        "date_unverified": undated,
        "pending_enrichment": sum(item["enrichment_status"] == "pending" for item in results),
        "limitations": ["No original posting page was fetched by this pipeline.",
                        "No opportunity is marked eligible or ready to apply until enrichment is reviewed."],
    }
    return results, {"ledger": ledger, "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge, deduplicate, rank and checkpoint job opportunities")
    parser.add_argument("--input", action="append", type=Path, help="input TSV; repeat to merge daily and unverified")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--out", type=Path, help="output JSON queue; defaults to radar/enrichment-<date>.json")
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args()
    inputs = args.input or [RADAR / f"daily-{args.today.isoformat()}.tsv",
                            RADAR / f"secondary-{args.today.isoformat()}.tsv",
                            RADAR / f"unverified-{args.today.isoformat()}.tsv"]
    queue, state = build_pipeline(inputs, today=args.today, ledger_path=args.ledger)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(state["ledger"], ensure_ascii=False, indent=2), encoding="utf-8")
    out = args.out or RADAR / f"enrichment-{args.today.isoformat()}.json"
    out.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics_path = out.with_name(out.stem.replace("enrichment", "pipeline-metrics") + ".json")
    metrics_path.write_text(json.dumps(state["metrics"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state["metrics"], ensure_ascii=False, indent=2))
    print(f"Queue: {out}")
    print(f"Lifecycle ledger: {args.ledger}")


if __name__ == "__main__":
    main()
