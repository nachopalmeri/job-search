"""Audit CafeDev discoveries without treating unknown dates or facts as negatives."""

from __future__ import annotations

import argparse
import csv
import time
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
RADAR = ROOT / "radar"
ENTRY = re.compile(r"\b(junior|jr\.?|trainee|intern(ship)?|pasant[ií]a|practicante|graduate|early career|entry[ -]level|associate)\b", re.I)
SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|manager|head of)\b", re.I)
YEARS = re.compile(r"(?:at least |minimum |min(?:imum)?\.? |m[ií]nimo )?(\d+)\+?\s*(?:years?|a[nñ]os?)(?: of| de)? [\w /-]{0,30}(?:experience|experiencia)", re.I)
SKILLS = {"python", "sql", "java", "linux", "network", "ccna", "automation", "api", "rest", "javascript", "typescript", "react", "html", "css", "qa", "testing", "data", "analytics", "aws", "cloud", "security", "support", "excel", "ai", "llm", "docker"}
CAFEDEV_API = "https://api.cafedev.co/v1/jobs"
DETAIL_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _seniority(title: str) -> str:
    if ENTRY.search(title or ""):
        return "junior_trainee_intern"
    if SENIOR.search(title or ""):
        return "explicit_seniority_experienced"
    return "seniority_unspecified"


def _geo(location: str) -> str:
    value = (location or "").lower()
    if "argentina" in value or "acepta argentina" in value or "argentina" == value.strip():
        return "argentina_stated_in_snapshot"
    if "no informada" in value or "por confirmar" in value or not value:
        return "unknown"
    return "other_location_requires_eligibility_check"


def _workplace(row: dict) -> str:
    value = f"{row.get('modalidad', '')} {row.get('ubicacion', '')}".lower()
    if "remoto" in value or "remote" in value:
        return "remote"
    if "hybrid" in value or "híbrido" in value or "hibrido" in value:
        return "hybrid"
    if "presencial" in value or "onsite" in value:
        return "onsite"
    return "unknown"


def _years_evidence(description: str) -> dict:
    matches = [int(match) for match in YEARS.findall(description or "")]
    full_detail = len(description or "") > 500
    return {
        "mandatory_years_found": max(matches) if matches else None,
        "experience_requirement": "possible_mandatory_years_found" if matches else ("not_found_in_full_description" if full_detail else "unknown_description_not_available"),
    }


def _potential_score(row: dict) -> tuple[float, list[str]]:
    title = (row.get("titulo") or "").lower()
    description = row.get("descripcion") or ""
    text = f"{title} {description}".lower()
    overlap = sorted(skill for skill in SKILLS if re.search(rf"\b{re.escape(skill)}\b", text))
    score = min(5.0, 1.0 + min(len(overlap), 4) * 0.45)
    seniority = _seniority(title)
    if seniority == "junior_trainee_intern":
        score += 1.2
    elif seniority == "explicit_seniority_experienced":
        score -= 0.8
    if _geo(row.get("ubicacion", "")) == "argentina_stated_in_snapshot":
        score += 0.8
    return round(min(5.0, max(0.0, score)), 2), overlap


def audit(rows: list[dict], *, run_date: str) -> dict:
    today = date.fromisoformat(run_date)
    candidates = []
    for row in rows:
        if (row.get("portal") or "").lower() != "cafedev":
            continue
        age = None
        raw = (row.get("fecha") or "")[:10]
        try:
            age = (today - date.fromisoformat(raw)).days
        except ValueError:
            pass
        score, matched = _potential_score(row)
        candidates.append({
            "id": row.get("job_id", ""), "title": row.get("titulo", ""),
            "company": row.get("empresa", ""), "url": row.get("url", ""),
            "apply_url": row.get("apply_url", ""), "seniority": _seniority(row.get("titulo", "")),
            "geography": _geo(row.get("ubicacion", "")), "workplace": _workplace(row),
            "publication_date": raw or None, "date_age_days": age,
            **_years_evidence(row.get("descripcion", "")),
            "skills_visible_in_snapshot": matched, "potential_score": score,
            "review_state": "manual_review_candidate" if score >= 1.8 else "low_affinity_sample",
            "evidence_limit": "Snapshot omits original posting description and does not verify job status, exact eligibility, or mandatory requirements.",
        })
    candidates.sort(key=lambda item: (item["potential_score"], item["seniority"] == "junior_trainee_intern"), reverse=True)
    seniority = {key: sum(item["seniority"] == key for item in candidates) for key in ("junior_trainee_intern", "seniority_unspecified", "explicit_seniority_experienced")}
    geography = {key: sum(item["geography"] == key for item in candidates) for key in ("argentina_stated_in_snapshot", "other_location_requires_eligibility_check", "unknown")}
    workplace = {key: sum(item["workplace"] == key for item in candidates) for key in ("remote", "hybrid", "onsite", "unknown")}
    dates_verified = sum(item["publication_date"] is not None for item in candidates)
    potential = [item for item in candidates if item["review_state"] == "manual_review_candidate"]
    low = [item for item in candidates if item["review_state"] == "low_affinity_sample"]
    return {
        "run_date": run_date, "records_audited": len(candidates), "seniority": seniority,
        "geography": geography, "workplace": workplace,
        "mandatory_experience_confirmed": sum(item["mandatory_years_found"] is not None for item in candidates),
        "experience_unknown": sum(item["experience_requirement"] == "unknown_description_not_available" for item in candidates),
        "original_dates_verified_in_snapshot": dates_verified,
        "candidates_missing_original_date": sum(item["date_age_days"] is None and item["review_state"] == "manual_review_candidate" for item in candidates),
        "potential_for_manual_review": len(potential), "incompatible_confirmed_from_snapshot": 0,
        "top_potential_candidates": potential[:30], "low_affinity_sample": low[:20],
        "candidates_without_verified_original_date": [item for item in potential if item["date_age_days"] is None][:10],
        "limitations": [
            "This audit uses the cached TSV snapshot only; it has no full job descriptions for most CafeDev records.",
            "A first-seen or aggregator date is not treated as original publication date.",
            "Unknown years, geography, seniority, and open/closed status remain unknown; none are counted as verified fits.",
            "The potential_score ranks records for human inspection, not application readiness.",
            "This 161-row snapshot was produced by a collector version that filtered senior-titled roles; the observed senior-title count is therefore a lower bound, not an API-wide count. The updated collector keeps these records for later review.",
        ],
    }


def fetch_job_detail(job_id: str, *, opener=urlopen) -> dict:
    """Fetch one CafeDev detail record; never substitute its indexing date for publication."""
    if not DETAIL_ID.fullmatch(str(job_id or "")):
        raise ValueError("CafeDev job id has an invalid format")
    request = Request(
        f"{CAFEDEV_API}/{quote(job_id, safe='')}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with opener(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    if not isinstance(payload, dict) or str(payload.get("id", "")) != str(job_id):
        raise ValueError("CafeDev detail response did not match the requested id")
    return payload


def enrich_candidates(
    result: dict,
    rows: list[dict],
    *,
    fetcher=fetch_job_detail,
    detail_limit: int = 30,
    low_sample: int = 10,
    pause_seconds: float = 0.6,
    sleeper=time.sleep,
) -> dict:
    """Enrich the top N, a bounded low-affinity sample, and legacy long summaries only."""
    if not 1 <= detail_limit <= 30 or not 0 <= low_sample <= 20:
        raise ValueError("detail_limit must be 1..30 and low_sample 0..20")
    selected: list[tuple[str, str]] = []
    selected.extend((item.get("id", ""), "top_potential") for item in result.get("top_potential_candidates", [])[:detail_limit])
    selected.extend((item.get("id", ""), "low_affinity_sample") for item in result.get("low_affinity_sample", [])[:low_sample])
    selected.extend(
        (str(row.get("job_id", "")), "legacy_long_summary")
        for row in rows
        if (row.get("portal") or "").lower() == "cafedev" and len(row.get("descripcion") or "") > 500
    )
    unique: list[tuple[str, str]] = []
    seen: set[str] = set()
    for job_id, group in selected:
        if job_id and job_id not in seen:
            unique.append((str(job_id), group))
            seen.add(str(job_id))

    records, failures = [], []
    for index, (job_id, group) in enumerate(unique):
        if index and pause_seconds > 0:
            sleeper(pause_seconds)
        try:
            detail = fetcher(job_id)
            if str(detail.get("id", "")) != job_id:
                raise ValueError("detail response id mismatch")
            records.append({
                "audit_group": group,
                "id": job_id,
                "title": detail.get("title"),
                "company": detail.get("company_name"),
                "company_domain": detail.get("company_domain"),
                "skills": detail.get("skills") or [],
                "seniority": detail.get("seniority"),
                "workplace_type": detail.get("workplace_type"),
                "employment_type": detail.get("employment_type"),
                "country": detail.get("country"),
                "city": detail.get("city"),
                "countries": detail.get("countries") or [],
                "region_scope": detail.get("region_scope") or [],
                "published_at": detail.get("published_at"),
                "first_seen_at": detail.get("first_seen_at"),
                "experience_min_years": detail.get("experience_min_years"),
                "url": detail.get("url"),
                "apply_url": detail.get("apply_url"),
                "source_posting_url": detail.get("source_url") or detail.get("source_posting_url") or detail.get("ats_url"),
                "source_posting_url_verified": bool(detail.get("source_url") or detail.get("source_posting_url") or detail.get("ats_url")),
                "description": detail.get("description") or "",
            })
        except Exception as exc:  # Keep one unavailable detail from stopping the other candidates.
            failures.append({"id": job_id, "audit_group": group, "error": f"{type(exc).__name__}: {exc}"})
    result["detail_enrichment"] = {
        "endpoint": CAFEDEV_API + "/{id}",
        "requested": len(unique),
        "fetched": len(records),
        "failed": len(failures),
        "published_at_present": sum(bool(item.get("published_at")) for item in records),
        "first_seen_is_not_publication_date": True,
        "records": records,
        "failures": failures,
    }
    return result


def read_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows.extend(csv.DictReader(handle, delimiter="|"))
    return rows


def render(result: dict) -> str:
    lines = [
        f"# CafeDev: auditoría de {result['records_audited']} señales · {result['run_date']}",
        "",
        "## Lo que se puede confirmar en el snapshot",
        f"- Seniority junior/trainee/intern en el título: {result['seniority']['junior_trainee_intern']}",
        f"- Seniority no especificado: {result['seniority']['seniority_unspecified']}",
        f"- Seniority explícitamente experimentado: {result['seniority']['explicit_seniority_experienced']}",
        f"- Ubicación Argentina explícita en el snapshot: {result['geography']['argentina_stated_in_snapshot']}",
        f"- Ubicación por confirmar: {result['geography']['unknown']}",
        f"- Remoto / híbrido / presencial / desconocido: {result['workplace']['remote']} / {result['workplace']['hybrid']} / {result['workplace']['onsite']} / {result['workplace']['unknown']}",
        f"- Fechas originales comprobadas en el snapshot: {result['original_dates_verified_in_snapshot']}",
        f"- Requisito de experiencia: {result['mandatory_experience_confirmed']} con años detectables; {result['experience_unknown']} desconocidos por falta de descripción.",
        f"- Candidatos a revisión humana: {result['potential_for_manual_review']}; incompatibles confirmados en el snapshot: {result['incompatible_confirmed_from_snapshot']}.",
        "",
        "La falta de fecha no descarta estas señales; se conservan en la cola potencial. El ranking siguiente solo prioriza qué fichas abrir primero.",
        "",
        "## Candidatos con mayor prioridad de inspección",
        "| Puesto | Empresa | Seniority del título | Geo | Skills visibles | Potencial | URL |",
        "|---|---|---|---|---|---:|---|",
    ]
    for item in result["top_potential_candidates"]:
        lines.append(f"| {item['title']} | {item['company']} | {item['seniority']} | {item['geography']} | {', '.join(item['skills_visible_in_snapshot']) or '—'} | {item['potential_score']} | [ficha]({item['url']}) |")
    lines.extend(["", "## Muestra de baja afinidad visible", "No es un descarte definitivo: revisar la descripción antes de cerrar.", "", "| Puesto | Empresa | Motivo | URL |", "|---|---|---|---|"])
    for item in result["low_affinity_sample"]:
        lines.append(f"| {item['title']} | {item['company']} | Título/skills del snapshot con baja señal de encaje | [ficha]({item['url']}) |")
    lines.extend(["", "## Límites", *[f"- {value}" for value in result["limitations"]], ""])
    detail = result.get("detail_enrichment")
    if detail:
        lines.extend([
            "", "## Enriquecimiento acotado desde el endpoint de detalle",
            f"- Solicitudes planificadas: {detail['requested']}; fichas recuperadas: {detail['fetched']}; fallidas: {detail['failed']}; con `published_at`: {detail['published_at_present']}.",
            "- `first_seen_at` se conserva como fecha de indexación y nunca se convierte en fecha de publicación.",
            "- El API de detalle no expone estado de apertura ni URL directa del empleador; `apply_url` sigue siendo un proxy de CafeDev. Para confirmar vigencia, ubicación/país y fecha, se debe contrastar la página oficial de la empresa/ATS.",
        ])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, help="TSV(s), defaulting to the latest radar queues")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--out", type=Path)
    parser.add_argument("--enrich-live", action="store_true", help="consultar endpoint de detalle para top 30, 10 de baja afinidad y fichas con resumen largo")
    parser.add_argument("--detail-limit", type=int, default=30, help="máximo de candidatos potenciales; nunca supera 30")
    parser.add_argument("--low-sample", type=int, default=10, help="muestra de baja afinidad; máximo 20")
    args = parser.parse_args()
    paths = args.input or [RADAR / f"unverified-{args.date}.tsv", RADAR / f"daily-{args.date}.tsv", RADAR / f"secondary-{args.date}.tsv"]
    rows = read_rows(paths)
    result = audit(rows, run_date=args.date)
    if args.enrich_live:
        result = enrich_candidates(result, rows, detail_limit=args.detail_limit, low_sample=args.low_sample)
        detail_out = RADAR / f"cafedev-detail-enrichment-{args.date}.json"
        detail_out.write_text(json.dumps(result["detail_enrichment"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"detail_enrichment": str(detail_out), **{key: result["detail_enrichment"][key] for key in ("requested", "fetched", "failed", "published_at_present")}}, ensure_ascii=False))
    out = args.out or RADAR / f"cafedev-audit-{args.date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(result), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit": str(out), "records_audited": result["records_audited"], "potential_for_manual_review": result["potential_for_manual_review"], "incompatible_confirmed_from_snapshot": result["incompatible_confirmed_from_snapshot"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
