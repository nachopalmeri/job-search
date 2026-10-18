"""Audit CafeDev discoveries without treating unknown dates or facts as negatives."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RADAR = ROOT / "radar"
ENTRY = re.compile(r"\b(junior|jr\.?|trainee|intern(ship)?|pasant[ií]a|practicante|graduate|early career|entry[ -]level|associate)\b", re.I)
SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|manager|head of)\b", re.I)
YEARS = re.compile(r"(?:at least |minimum |min(?:imum)?\.? |m[ií]nimo )?(\d+)\+?\s*(?:years?|a[nñ]os?)(?: of| de)? [\w /-]{0,30}(?:experience|experiencia)", re.I)
SKILLS = {"python", "sql", "java", "linux", "network", "ccna", "automation", "api", "rest", "javascript", "typescript", "react", "html", "css", "qa", "testing", "data", "analytics", "aws", "cloud", "security", "support", "excel", "ai", "llm", "docker"}


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
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, help="TSV(s), defaulting to the latest radar queues")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    paths = args.input or [RADAR / f"unverified-{args.date}.tsv", RADAR / f"daily-{args.date}.tsv", RADAR / f"secondary-{args.date}.tsv"]
    result = audit(read_rows(paths), run_date=args.date)
    out = args.out or RADAR / f"cafedev-audit-{args.date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(result), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit": str(out), "records_audited": result["records_audited"], "potential_for_manual_review": result["potential_for_manual_review"], "incompatible_confirmed_from_snapshot": result["incompatible_confirmed_from_snapshot"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
