"""Normalize startup, networking, and content signals without promoting guesses."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SIGNAL_TYPES = {
    "funding_round", "market_expansion", "new_product", "talent_program",
    "team_hiring", "accelerator", "founder_hiring_signal", "other",
}


def _public_url(value: object) -> bool:
    parsed = urlsplit(str(value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def classify_record(record: dict) -> dict:
    """Keep a job, company hypothesis, contact, or content proposal in its own lane."""
    kind = str(record.get("record_type") or "").strip().lower()
    if kind == "startup_signal":
        evidence = str(record.get("evidence_url") or "").strip()
        valid = bool(record.get("company") and _public_url(evidence) and record.get("signal_type") in SIGNAL_TYPES)
        role_url = str(record.get("job_url") or "").strip()
        return {
            **record,
            "lane": "startup_opportunity" if role_url and _public_url(role_url) else "startup_research",
            "status": "needs_review" if valid else "needs_evidence",
            "claim_level": "verified_signal_not_hiring" if valid else "unverified_hypothesis",
            "must_not_infer": "A funding, expansion, or product announcement does not prove hiring.",
        }
    if kind == "networking_lead":
        profile = str(record.get("public_profile_url") or record.get("post_url") or "").strip()
        valid = bool(record.get("person_or_team") and _public_url(profile) and record.get("why_relevant"))
        return {
            **record, "lane": "networking", "status": "draft_only" if valid else "needs_context",
            "claim_level": "public_profile_evidence" if valid else "unverified",
            "message_sent": False,
        }
    if kind == "content_idea":
        evidence = str(record.get("evidence_ref") or record.get("evidence_url") or "").strip()
        valid = bool(record.get("topic") and evidence)
        return {
            **record, "lane": "content_calendar", "status": "draft_for_review" if valid else "needs_project_evidence",
            "claim_level": "evidence_linked" if valid else "unsubstantiated",
            "platforms": ["X", "LinkedIn"], "published": False,
        }
    return {**record, "lane": "unclassified", "status": "needs_review", "claim_level": "unverified"}


def build_report(records: list[dict], *, run_date: str) -> dict:
    date.fromisoformat(run_date)
    lanes = {name: [] for name in ("startup_research", "startup_opportunity", "networking", "content_calendar", "unclassified")}
    for record in records:
        item = classify_record(record)
        lanes[item["lane"]].append(item)
    return {"run_date": run_date, **lanes, "messages_sent": 0, "posts_published": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON array of sourced signals/ideas")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        parser.error("input must be a JSON array of objects")
    report = build_report(records, run_date=args.date)
    out = args.output or ROOT / "radar" / f"strategic-signals-{args.date}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), **{key: len(value) for key, value in report.items() if isinstance(value, list)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
