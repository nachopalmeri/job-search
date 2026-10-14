#!/usr/bin/env python3
"""Checklist auditable de fuentes para cada pasada diaria.

No consulta portales ni convierte un fallo de acceso en cero resultados.
"""

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
CATALOG = Path(__file__).with_name("search_sources.json")
STATUSES = {"pending", "consulted_with_results", "consulted_no_results", "blocked", "not_applicable"}


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
    date.fromisoformat(day)
    return {
        "date": day,
        "sources": {source["id"]: {"status": "pending", "count": 0, "note": ""} for source in sources},
    }


def mark_source(report, source_id, status, count=0, note=""):
    if source_id not in report["sources"]:
        raise ValueError(f"Fuente desconocida: {source_id}")
    if status not in STATUSES or status == "pending":
        raise ValueError(f"Estado inválido: {status}")
    if count < 0:
        raise ValueError("El conteo no puede ser negativo")
    if status == "consulted_with_results" and count < 1:
        raise ValueError("Un resultado positivo requiere count >= 1")
    if status != "consulted_with_results" and count != 0:
        raise ValueError("Solo consulted_with_results admite count > 0")
    if status in {"blocked", "not_applicable"} and not note.strip():
        raise ValueError("Un bloqueo o exclusión requiere motivo")
    report["sources"][source_id] = {"status": status, "count": count, "note": note.strip()}


def pending_sources(report):
    return [source_id for source_id, item in report["sources"].items() if item["status"] == "pending"]


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
                    report["sources"][source["id"]] = {"status": "pending", "count": 0, "note": ""}
                    added += 1
            if added:
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Reporte existente preservado: {output}; fuentes nuevas: {added}")
            return 0
        report = new_report(args.date, sources)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Checklist creado: {len(sources)} fuentes en {output}")
        return 0
    if not output.exists():
        parser.error(f"No existe {output}; ejecutá --init primero")
    report = json.loads(output.read_text(encoding="utf-8"))
    if args.mark:
        if not args.status:
            parser.error("--mark requiere --status")
        try:
            mark_source(report, args.mark, args.status, args.count, args.note)
        except ValueError as exc:
            parser.error(str(exc))
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{args.mark}: {args.status} ({args.count})")
        return 0
    missing = [source["id"] for source in sources if source["id"] not in report["sources"]]
    pending = pending_sources(report) + missing
    blocked = [source_id for source_id, item in report["sources"].items() if item["status"] == "blocked"]
    results = sum(item["count"] for item in report["sources"].values())
    print(f"Fuentes: {len(report['sources'])}; resultados: {results}; pendientes: {len(pending)}; bloqueadas: {len(blocked)}")
    if pending:
        print("Pendientes: " + ", ".join(pending))
    if blocked:
        print("Bloqueadas: " + ", ".join(blocked))
    return 1 if pending or blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
