"""Build a factual inventory of configured job-search sources and recent coverage."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "scripts" / "search_sources.json"
RADAR = ROOT / "radar"
MULTIPLE_DAILY = {"linkedin_posts", "x"}
WEEKLY = {
    "startup_jobs_ar", "wellfound", "startup_jobs", "vibe_coding_jobs", "vibehackers",
    "outlier", "alignerr", "dataannotation", "prolific", "yc_events", "appgentina",
}
AUTH_REQUIRED = {"uade", "linkedin_posts", "x", "wellfound"}
METHODS = {
    "cafedev": "API REST pública (/v1/jobs); consulta automática",
    "greenhouse": "API pública de job boards; consulta automática",
    "lever": "API pública de postings; consulta automática",
    "ashby": "API pública de job boards; consulta automática",
    "uade": "Navegador con sesión del usuario; lectura manual",
    "linkedin": "Consulta web pública/guest; automática con límite HTTP 429",
    "linkedin_posts": "Navegador/sesión o índice público; lectura manual",
    "x": "Búsqueda Latest en navegador; lectura manual",
    "yc": "Listado/API pública; automática, requiere confirmar en empresa",
    "speedrun": "Listado web público; automática, requiere confirmar en empresa",
    "startup_jobs_ar": "Listado web y búsqueda manual",
    "wellfound": "Portal web; sesión/filtros pueden requerir navegador",
    "silver_dev": "Listado público de vacantes y empresas asociadas; revisión manual de elegibilidad",
    "bumeran": "Portal/búsqueda web; revisión manual",
    "zonajobs": "Portal/búsqueda web; revisión manual",
    "indeed": "Portal/búsqueda web; revisión manual",
    "jooble": "Portal/búsqueda web; revisión manual",
    "firstjob": "Portal web; revisión manual",
    "startup_jobs": "Portal web; revisión manual",
    "vibe_coding_jobs": "Portal/comunidad web; revisión manual",
    "vibehackers": "Listado web + RSS oficial /jobs-feed.xml (últimos 50 ítems); verificar vacante original",
    "yc_events": "Calendario web público; revisión manual",
    "appgentina": "Sitio de comunidad/eventos; revisión manual",
}
TYPE_BY_GROUP = {
    "local": "Portal / red social / universidad",
    "remote": "Agregador de empleo remoto",
    "startups_ar": "Portal de startups",
    "startups_global": "Startup board / ATS",
    "gig": "Plataforma de tareas, no empleo garantizado",
    "networking": "Comunidad / eventos",
}
PROFILE_BY_GROUP = {
    "local": "Pasantías, trainee y roles IT/negocio en Argentina",
    "remote": "Roles remotos; elegibilidad desde Argentina pendiente de comprobar",
    "startups_ar": "Startups argentinas y programas de talento",
    "startups_global": "Startups, ATS y talento early-career; geografía por aviso",
    "gig": "Tareas de IA/freelance; no equivalen a empleo estable",
    "networking": "Eventos, contactos y señales de networking",
}
SUCCESS = {"consulted_with_results", "consulted_no_results"}


def cadence(source_id: str) -> str:
    if source_id in MULTIPLE_DAILY:
        return "Varias veces al día (solo consultas cortas; respetar límites)"
    if source_id in WEEKLY:
        return "Semanal"
    return "Diaria"


def _coverage_reports() -> list[tuple[date, bool, Path, dict]]:
    reports = []
    for path in RADAR.glob("coverage-*.json"):
        try:
            day = date.fromisoformat(path.stem.removeprefix("coverage-")[:10])
            canonical = path.name == f"coverage-{day.isoformat()}.json"
            reports.append((day, canonical, path, json.loads(path.read_text(encoding="utf-8"))))
        except (ValueError, OSError, json.JSONDecodeError):
            continue
    return sorted(reports, key=lambda item: (item[0], item[1], item[2].name), reverse=True)


def latest_coverage() -> tuple[str, dict]:
    reports = _coverage_reports()
    if not reports:
        return "", {}
    day, _, _, payload = reports[0]
    return day.isoformat(), payload.get("sources", {})


def build_inventory(sources: list[dict]) -> dict:
    report_day, latest = latest_coverage()
    rows = []
    for source in sources:
        sid = source["id"]
        attempt = latest.get(sid, {"status": "not recorded", "count": 0, "note": ""})
        previous_success = ""
        previous_count = None
        for historical_day, _, _, report in _coverage_reports():
            item = report.get("sources", {}).get(sid, {})
            if item.get("status") in SUCCESS:
                previous_success = report.get("date", historical_day.isoformat())
                previous_count = item.get("count", 0)
                break
        rows.append({
            **source,
            "type": TYPE_BY_GROUP.get(source.get("group", ""), "Other"),
            "profile_coverage": PROFILE_BY_GROUP.get(source.get("group", ""), "Por clasificar"),
            "method": METHODS.get(source["id"], "API/scraper" if source.get("access") == "automatic" else "Web/navegador, revisión manual"),
            "frequency": cadence(sid),
            "requires_auth_or_manual": sid in AUTH_REQUIRED,
            "last_attempt_date": report_day,
            "last_attempt_status": attempt.get("status", "not recorded"),
            "last_attempt_count": attempt.get("count", 0),
            "last_attempt_note": attempt.get("note", ""),
            "last_success_date": previous_success,
            "last_success_count": previous_count,
            "eligible_count": None,
        })
    return {"source_count": len(rows), "coverage_report_date": report_day, "sources": rows}


def markdown(inventory: dict) -> str:
    lines = [
        "# Inventario de fuentes de búsqueda laboral",
        "",
        f"Fuentes configuradas: **{inventory['source_count']}** · último reporte de cobertura: **{inventory['coverage_report_date'] or 'sin reporte'}**.",
        "Los conteos del reporte son señales encontradas, no oportunidades elegibles. `eligible_count` queda sin valor porque la cobertura actual no mide elegibilidad por fuente.",
        "",
        "## Varias veces al día",
    ]
    for row in inventory["sources"]:
        if row["frequency"].startswith("Varias"):
            lines.append(f"- [{row['name']}]({row['url']}) — consultas breves; detener ante rate-limit.")
    lines.extend(["", "## Diarias"])
    for row in inventory["sources"]:
        if row["frequency"] == "Diaria":
            lines.append(f"- [{row['name']}]({row['url']})")
    lines.extend(["", "## Semanales"])
    for row in inventory["sources"]:
        if row["frequency"] == "Semanal":
            lines.append(f"- [{row['name']}]({row['url']})")
    lines.extend([
        "",
        "## Fuentes por frecuencia",
        "| Fuente | URL | Tipo | Perfiles | Método | Frecuencia | Último intento | Señales | Último éxito completo | Bloqueo / límite | Manual |",
        "|---|---|---|---|---|---|---|---:|---|---|---|",
    ])
    for row in inventory["sources"]:
        status = row["last_attempt_status"]
        attempt = f"{row['last_attempt_date']}: {status}" if row["last_attempt_date"] else status
        lines.append("| {name} | [{url}]({url}) | {type} | {profile_coverage} | {method} | {frequency} | {attempt} | {count} | {success} ({success_count}) | {note} | {manual} |".format(
            name=row["name"], url=row["url"], type=row["type"], profile_coverage=row["profile_coverage"],
            method=row["method"], frequency=row["frequency"], attempt=attempt,
            count=row["last_attempt_count"], success=row["last_success_date"] or "Sin éxito registrado",
            success_count=row["last_success_count"] if row["last_success_count"] is not None else "—",
            note=row["last_attempt_note"].replace("|", "/") or "—",
            manual="Sí" if row["requires_auth_or_manual"] or row.get("access") == "manual" else "No",
        ))
    lines.extend(["", "## Semanal / investigación", "Fuentes de exploración, gigs y eventos se revisan semanalmente para reducir consultas sin valor diario. Las que requieren login siguen marcadas como manuales.", ""])
    return "\n".join(lines)


def write_inventory(output_md: Path | None = None, output_json: Path | None = None) -> dict:
    sources = json.loads(CATALOG.read_text(encoding="utf-8"))
    inventory = build_inventory(sources)
    output_md = output_md or RADAR / "source-inventory.md"
    output_json = output_json or RADAR / "source-inventory.json"
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown(inventory), encoding="utf-8")
    output_json.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()
    result = write_inventory(args.out_md, args.out_json)
    print(f"Inventario generado: {result['source_count']} fuentes; cobertura {result['coverage_report_date'] or 'sin reporte'}")


if __name__ == "__main__":
    main()
