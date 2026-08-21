#!/usr/bin/env python3
"""
migrate_tracker_add_ats_score.py -- anade columna ats_score (11a) a tracker/applications.csv
Idempotente, BOM-safe, no rompe compatibilidad (10 -> 11 cols, default "").
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "tracker" / "applications.csv"
EXPECTED_HEADER_10 = "fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas"
EXPECTED_HEADER_11 = EXPECTED_HEADER_10 + "|ats_score"


def migrate(path: Path, check_only: bool = False) -> int:
    if not path.exists():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        return 2
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    if not lines:
        print("ERROR: CSV vacio", file=sys.stderr)
        return 2
    header_idx = None
    for i, l in enumerate(lines):
        if not l.strip():
            continue
        if l.strip().startswith("#"):
            continue
        header_idx = i
        break
    if header_idx is None:
        print("ERROR: no se encontro header", file=sys.stderr)
        return 2
    header = lines[header_idx].strip()
    if header == EXPECTED_HEADER_11:
        print(f"OK - {path.name} ya tiene ats_score (11 columnas). Nada que hacer.")
        return 0
    if header != EXPECTED_HEADER_10:
        cols = [c.strip() for c in header.split("|")]
        if "ats_score" in cols:
            print(f"OK - {path.name} ya contiene ats_score en header: {header}")
            return 0
        if len(cols) == 10 and cols[-1] == "notas":
            pass
        else:
            print(f"WARN: header inesperado ({len(cols)} cols): {header}", file=sys.stderr)
            print(f"      esperado 10: {EXPECTED_HEADER_10}", file=sys.stderr)
            if "ats_score" in header:
                return 0
    if check_only:
        print(f"DRIFT: {path.name} necesita migracion - header actual 10 cols, falta ats_score")
        print(f"  actual : {header}")
        print(f"  esperado: {EXPECTED_HEADER_11}")
        return 1
    out_lines: list[str] = []
    for i, l in enumerate(lines):
        if i < header_idx:
            out_lines.append(l)
            continue
        if i == header_idx:
            out_lines.append(EXPECTED_HEADER_11)
            continue
        if not l.strip() or l.strip().startswith("#"):
            out_lines.append(l)
            continue
        if l.count("|") >= 10:
            out_lines.append(l)
            continue
        if l.endswith("|"):
            out_lines.append(l + "")
        else:
            out_lines.append(l + "|")
    out_text = "\n".join(out_lines) + "\n"
    if has_bom:
        path.write_bytes(b"\xef\xbb\xbf" + out_text.encode("utf-8"))
    else:
        path.write_text(out_text, encoding="utf-8")
    print(f"OK - migrado {path} : 10 -> 11 columnas (ats_score default \"\")")
    new_header = out_lines[header_idx]
    assert new_header == EXPECTED_HEADER_11, f"header post-migracion inesperado: {new_header}"
    return 0


def main():
    ap = argparse.ArgumentParser(description="Migra tracker a 11 columnas con ats_score")
    ap.add_argument("--path", default=str(DEFAULT_CSV))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    sys.exit(migrate(Path(args.path), check_only=args.check))


if __name__ == "__main__":
    main()
