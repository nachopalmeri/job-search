#!/usr/bin/env python3
"""Checklist auditable de fuentes para cada pasada diaria.

No consulta portales ni convierte un fallo de acceso en cero resultados.
"""

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.source_inventory import cadence, write_inventory
except ImportError:  # direct execution from scripts/
    from source_inventory import cadence, write_inventory


ROOT = Path(__file__).resolve().parent.parent
CATALOG = Path(__file__).with_name("search_sources.json")
STATUSES = {"pending", "not_due", "consulted_with_results", "consulted_no_results", "partial", "blocked", "not_applicable"}


def load_sources(path=CATALOG):
    sources = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        raise ValueError("El catálogo debe ser una lista JSON")
    seen = set()
    for source in sources:
        source_id = source.get("id", "")
        if not source_id or source_id in seen:
            raise ValueError(f"ID ausente o repetido: {source_id}")
        if source.get("access") not in {"automatic", "manual"}:
            raise ValueError(f"Acceso inválido: {source_id}")
        if source.get("group") not in {"startups_ar", "local", "startups_global", "remote", "gig", "networking"}:
            raise ValueError(f"Grupo inválido: {source_id}")
        if urlparse(source.get("url", "")).scheme != "https":
            raise ValueError(f"URL inválida: {source_id}")
        seen.add(source_id)
    return sources


def new_report(day, sources):
    day_date = date.fromisoformat(day)

    entries = {}
    for source in sources:
        not_due = cadence(source["id"]) == "Semanal" and day_date.isoweekday() != 1
        entries[source["id"]] = {
            "status": "not_due" if not_due else "pending", "count": 0,
            "note": "Frecuencia semanal; próxima consulta el lunes." if not_due else "",
        }
    return {
        "date": day,
        "sources": entries,
    }


def mark_source(report, source_id, status, count=0, note="", attempted=None, total=None):
    if source_id not in report["sources"]:
        raise ValueError(f"Fuente desconocida: {source_id}")
    if status not in STATUSES or status == "pending":
        raise ValueError(f"Estado inválido: {status}")
    if count < 0:
        raise ValueError("El conteo no puede ser negativo")
    if status == "consulted_with_results" and count < 1:
        raise ValueError("Un resultado positivo requiere count >= 1")
    if status not in {"consulted_with_results", "partial"} and count != 0:
        raise ValueError("Solo consulted_with_results o partial admiten count > 0")
    if status in {"partial", "blocked", "not_applicable"} and not note.strip():
        raise ValueError("Un resultado parcial, bloqueo o exclusión requiere motivo")
    if (attempted is None) != (total is None):
        raise ValueError("La cobertura requiere --attempted y --total juntos")
    entry = {"status": status, "count": count, "note": note.strip()}
    if attempted is not None:
        if attempted < 0 or total < 1 or attempted > total:
            raise ValueError("La cobertura debe cumplir 0 <= attempted <= total y total >= 1")
        if attempted < total and status != "partial":
            raise ValueError("La cobertura incompleta requiere status=partial")
        entry["coverage"] = {"attempted": attempted, "total": total}
    report["sources"][source_id] = entry


def pending_sources(report):
    return [source_id for source_id, item in report["sources"].items() if item["status"] == "pending"]


def incomplete_sources(report):
    """Return entries whose explicit attempted/total coverage is incomplete or malformed."""
    incomplete = []
    for source_id, item in report["sources"].items():
        coverage = item.get("coverage")
        if coverage is None:
            continue  # Legacy reports have no query/page denominator.
        if not isinstance(coverage, dict):
            incomplete.append(source_id)
            continue
        attempted, total = coverage.get("attempted"), coverage.get("total")
        if (not isinstance(attempted, int) or isinstance(attempted, bool)
                or not isinstance(total, int) or isinstance(total, bool)
                or attempted < 0 or total < 1 or attempted > total or attempted < total):
            incomplete.append(source_id)
    return incomplete


def main():
    parser = argparse.ArgumentParser(description="Auditar cobertura de todas las fuentes del día")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--out", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--init", action="store_true", help="inicializar fuentes pendientes; preserva reporte existente")
    action.add_argument("--mark", metavar="ID", help="registrar estado de una fuente")
    action.add_argument("--check", action="store_true", help="salir con 1 si hay pendientes o bloqueos")
    parser.add_argument("--status", choices=sorted(STATUSES - {"pending"}))
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--note", default="")
    parser.add_argument("--attempted", type=int, help="familias/páginas consultadas dentro del total declarado")
    parser.add_argument("--total", type=int, help="total conocido de familias/páginas para esta consulta")
    args = parser.parse_args()
    output = args.out or ROOT / "radar" / f"coverage-{args.date}.json"
    sources = load_sources()
    if args.init:
        if output.exists():
            report = json.loads(output.read_text(encoding="utf-8"))
            if report.get("date") != args.date:
                parser.error(f"El reporte existente es de {report.get('date')}; usá el día correcto")
            added = 0
            for source in sources:
                if source["id"] not in report["sources"]:
                    report["sources"][source["id"]] = new_report(args.date, [source])["sources"][source["id"]]
                    added += 1
            if added:
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Reporte existente preservado: {output}; fuentes nuevas: {added}")
            write_inventory()
            return 0
        report = new_report(args.date, sources)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Checklist creado: {len(sources)} fuentes en {output}")
        write_inventory()
        return 0
    if not output.exists():
        parser.error(f"No existe {output}; ejecutá --init primero")
    report = json.loads(output.read_text(encoding="utf-8"))
    if args.mark:
        if not args.status:
            parser.error("--mark requiere --status")
        try:
            mark_source(report, args.mark, args.status, args.count, args.note,
                        args.attempted, args.total)
        except ValueError as exc:
            parser.error(str(exc))
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{args.mark}: {args.status} ({args.count})")
        write_inventory()
        return 0
    missing = [source["id"] for source in sources if source["id"] not in report["sources"]]
    pending = pending_sources(report) + missing
    partial = [source_id for source_id, item in report["sources"].items() if item["status"] == "partial"]
    blocked = [source_id for source_id, item in report["sources"].items() if item["status"] == "blocked"]
    not_due = [source_id for source_id, item in report["sources"].items() if item["status"] == "not_due"]
    incomplete = incomplete_sources(report)
    results = sum(item["count"] for item in report["sources"].values())
    print(f"Fuentes: {len(report['sources'])}; señales: {results}; pendientes: {len(pending)}; no programadas hoy: {len(not_due)}; parciales: {len(partial)}; cobertura incompleta: {len(incomplete)}; bloqueadas: {len(blocked)}")
    if pending:
        print("Pendientes: " + ", ".join(pending))
    if blocked:
        print("Bloqueadas: " + ", ".join(blocked))
    if partial:
        print("Parciales: " + ", ".join(partial))
    if incomplete:
        print("Cobertura incompleta: " + ", ".join(incomplete))
    write_inventory()
    return 1 if pending or blocked or partial or incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
