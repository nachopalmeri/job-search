"""Triage manually collected LinkedIn/X posts without mixing leads and jobs.

Social posts are discovery signals. This importer never scrapes, messages,
applies, assigns a fit score, or treats a search/index date as publication.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


HIRING = re.compile(
    r"\b(?:buscamos|estamos buscando|sumate|sumate al equipo|hiring|we.re hiring|"
    r"join our team|open role|vacante|oportunidad laboral|referidos?|referral)\b",
    re.I,
)
NETWORKING = re.compile(
    r"\b(?:referid[oa]s?|referral|recomendar|recomendaci[oó]n|contacto|dm|inbox|"
    r"conectar|networking|charlemos|te refiero)\b", re.I
)
SOCIAL_SEARCH_QUERIES = {
    "linkedin_posts": [
        '"estamos buscando" (pasantía OR trainee OR junior) (tecnología OR sistemas OR datos)',
        '"sumate al equipo" (IT OR soporte OR datos OR producto)',
        '"busco referidos" (pasantía OR trainee OR junior) tecnología Argentina',
        '"me pueden referir" (intern OR junior) (data OR software OR IT)',
    ],
    "x_latest": [
        '"estamos buscando" (pasantía OR trainee OR junior) (tecnología OR sistemas OR datos)',
        '"sumate al equipo" (IT OR soporte OR datos OR producto)',
        '"tengo referidos" (pasantía OR trainee OR junior) Argentina',
        '"busco referidos" (intern OR junior) (data OR software OR IT)',
        '"buscamos estudiantes" (sistemas OR tecnología OR datos)',
    ],
}


def _valid_http_url(value: object) -> bool:
    parsed = urlsplit(str(value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def classify_post(post: dict, *, today: date, max_age_days: int = 4) -> tuple[str, str]:
    """Return a bucket and reason; only concrete, fresh linked vacancies qualify."""
    raw_date = str(post.get("published_at") or "")[:10]
    try:
        published = date.fromisoformat(raw_date)
    except ValueError:
        return "undated", "fecha original ausente o inválida; no contar como aviso activo"
    age = (today - published).days
    if age < 0:
        return "undated", "fecha futura; verificar fecha original"
    if age > max_age_days:
        return "stale", f"publicación original de {age} días; supera el máximo de {max_age_days}"

    text = str(post.get("text") or "")
    company = str(post.get("company") or "").strip()
    title = str(post.get("job_title") or "").strip()
    apply_url = post.get("application_url")
    if HIRING.search(text) and company and title and _valid_http_url(apply_url):
        return "opportunity_candidate", "vacante concreta y enlace de postulación; verificar aviso original y elegibilidad"
    if HIRING.search(text) or NETWORKING.search(text):
        return "networking_lead", "señal social sin vacante concreta verificable; mantener separada del ranking activo"
    return "non_actionable", "sin señal de contratación o networking laboral"


def triage(posts: list[dict], *, today: date, max_age_days: int = 4) -> dict:
    buckets = {name: [] for name in ("opportunity_candidates", "networking_leads", "stale", "undated", "non_actionable")}
    for post in posts:
        bucket, reason = classify_post(post, today=today, max_age_days=max_age_days)
        row = {**post, "triage": bucket, "triage_reason": reason}
        if bucket == "opportunity_candidate":
            buckets["opportunity_candidates"].append(row)
        elif bucket == "networking_lead":
            buckets["networking_leads"].append(row)
        else:
            buckets[bucket].append(row)
    return {"run_date": today.isoformat(), "max_age_days": max_age_days, **buckets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON array of manually collected posts")
    parser.add_argument("--output", type=Path, help="output JSON; defaults to radar/social-signals-<date>.json")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--max-age-days", type=int, default=4)
    parser.add_argument("--queries", action="store_true", help="print additive LinkedIn Posts/X discovery queries")
    args = parser.parse_args()
    if args.queries:
        print(json.dumps(SOCIAL_SEARCH_QUERIES, ensure_ascii=False, indent=2))
        return
    if not args.input:
        parser.error("--input is required unless --queries is used")
    if args.max_age_days < 0:
        parser.error("--max-age-days must be non-negative")
    posts = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(posts, list) or any(not isinstance(post, dict) for post in posts):
        parser.error("input must be a JSON array of objects")
    result = triage(posts, today=args.today, max_age_days=args.max_age_days)
    out = args.output or Path(__file__).resolve().parent.parent / "radar" / f"social-signals-{args.today.isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), **{key: len(result[key]) for key in result if isinstance(result[key], list)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
