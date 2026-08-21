#!/usr/bin/env python3
"""
migrate_tracker_add_crm.py -- CRM follow-up: anade contacto_interno + fecha_followup (+7d) a tracker/applications.csv
Idempotente, BOM-safe, no rompe compat (10 -> 11 -> 13 cols).

Header target:
  fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|contacto_interno|fecha_followup|ats_score

- contacto_interno: texto libre "Nombre (rol) <whatsapp/email>" (ej Fátima)
- fecha_followup: ISO YYYY-MM-DD = fecha +7d habiles (finde->lunes), solo si estado in (aplicada,entrevista,a enviar,aplicar YA,verificar,pendiente)
- ats_score: si falta, anade (compat con migrate_tracker_add_ats_score.py)

Uso:
  python scripts/migrate_tracker_add_crm.py --check
  python scripts/migrate_tracker_add_crm.py --backfill
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "tracker" / "applications.csv"
HEADER_10 = "fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas"
HEADER_13 = HEADER_10 + "|contacto_interno|fecha_followup|ats_score"
FOLLOWUP_STATES = {"aplicada", "entrevista", "a enviar", "aplicar ya", "verificar", "pendiente", "aplicar ya", "a_enviar"}

def add_business_days(d: datetime, days: int = 7) -> datetime:
    nd = d + timedelta(days=days)
    # si cae sab/dom -> lunes
    if nd.weekday() == 5:
        nd += timedelta(days=2)
    elif nd.weekday() == 6:
        nd += timedelta(days=1)
    return nd

def migrate(path: Path, check_only: bool = False, backfill: bool = False) -> int:
    if not path.exists():
        print(f"ERROR: no existe {path}", file=sys.stderr); return 2
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    # header idx
    header_idx = None
    for i, l in enumerate(lines):
        if not l.strip() or l.strip().startswith("#"):
            continue
        header_idx = i; break
    if header_idx is None:
        print("ERROR: no header", file=sys.stderr); return 2
    header = lines[header_idx].strip()
    cols = [c.strip() for c in header.split("|")]
    if header == HEADER_13:
        print(f"OK ya tiene 13 cols CRM: {path.name}")
        if backfill:
            return do_backfill(path, lines, header_idx, has_bom)
        return 0
    if "contacto_interno" in cols and "fecha_followup" in cols:
        print(f"OK ya contiene CRM cols: {header}"); return 0
    # necesita migracion
    if check_only:
        print(f"DRIFT: {path.name} header={header} -> esperado {HEADER_13}", file=sys.stderr); return 1
    # construir nuevas lineas con 13 cols
    out = []
    for i, l in enumerate(lines):
        if i < header_idx:
            out.append(l); continue
        if i == header_idx:
            # expandir header a 13
            if header == HEADER_10:
                out.append(HEADER_13)
            elif "ats_score" in header and "contacto_interno" not in header:
                # 11 cols ats_score -> insertar 2 antes de ats_score
                out.append(header.replace("|ats_score", "|contacto_interno|fecha_followup|ats_score"))
            else:
                # fallback: si tiene 11 o 12, completar
                cur = header
                if "contacto_interno" not in cur:
                    cur += "|contacto_interno"
                if "fecha_followup" not in cur:
                    cur += "|fecha_followup"
                if "ats_score" not in cur:
                    cur += "|ats_score"
                out.append(cur)
            continue
        if not l.strip() or l.strip().startswith("#"):
            out.append(l); continue
        # data line: asegurar que tenga separadores para nuevas cols
        parts = l.split("|")
        # si linea ya tiene 13, dejar
        if len(parts) >= 13:
            out.append(l); continue
        # pad con vacios
        # 10 -> 13
        if len(parts) == 10:
            out.append(l + "|||")
        elif len(parts) == 11:
            # puede ser ats_score o contacto -> pad 2
            out.append(l + "||")
        elif len(parts) == 12:
            out.append(l + "|")
        else:
            out.append(l + "|" * (13 - len(parts)))
    out_text = "\n".join(out) + "\n"
    if has_bom:
        path.write_bytes(b"\xef\xbb\xbf" + out_text.encode("utf-8"))
    else:
        path.write_text(out_text, encoding="utf-8")
    print(f"OK migrado {path.name}: {len(cols)} -> 13 cols")
    if backfill:
        # recargar para backfill
        return do_backfill(path, out_text.splitlines(), header_idx, has_bom)
    return 0

def do_backfill(path: Path, lines: list[str], header_idx: int, has_bom: bool) -> int:
    # recalc fecha_followup = fecha +7d habiles para estados activos y celdas vacias
    header = lines[header_idx]
    hcols = [c.strip() for c in header.split("|")]
    try:
        idx_fecha = hcols.index("fecha")
        idx_estado = hcols.index("estado")
        idx_follow = hcols.index("fecha_followup")
    except ValueError as e:
        print(f"SKIP backfill: header sin cols esperadas: {e}", file=sys.stderr); return 0
    changed = 0
    out = list(lines)
    for i in range(header_idx+1, len(lines)):
        l = lines[i]
        if not l.strip() or l.startswith("#"):
            continue
        parts = l.split("|")
        if len(parts) < len(hcols):
            parts += [""] * (len(hcols) - len(parts))
        fecha = parts[idx_fecha].strip()
        estado = parts[idx_estado].strip().lower()
        follow = parts[idx_follow].strip() if idx_follow < len(parts) else ""
        if follow:
            continue
        # solo backfill si estado requiere followup y fecha parseable
        if estado not in FOLLOWUP_STATES and estado not in {"a enviar", "aplicar ya", "aplicada", "entrevista", "verificar", "pendiente"}:
            # estados holding como descartada/radio/backup/semana/evaluar no llevan followup
            if estado in {"descartada", "descartadas", "radar", "backup", "semana", "evaluar", "dudosa"}:
                continue
        try:
            d = datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            continue
        nf = add_business_days(d, 7).strftime("%Y-%m-%d")
        parts[idx_follow] = nf
        out[i] = "|".join(parts)
        changed += 1
    if changed:
        txt = "\n".join(out) + "\n"
        if has_bom:
            path.write_bytes(b"\xef\xbb\xbf" + txt.encode("utf-8"))
        else:
            path.write_text(txt, encoding="utf-8")
        print(f"OK backfill: {changed} filas con fecha_followup +7d")
    else:
        print("OK backfill: nada que rellenar")
    return 0

def main():
    ap = argparse.ArgumentParser(description="Migra tracker a CRM (contacto_interno, fecha_followup)")
    ap.add_argument("--path", default=str(DEFAULT_CSV))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--backfill", action="store_true", help="Rellena fecha_followup +7d donde vacio")
    args = ap.parse_args()
    rc = migrate(Path(args.path), check_only=args.check, backfill=args.backfill)
    # si check ok pero piden backfill, hacerlo
    if rc == 0 and args.backfill and not args.check:
        pass
    sys.exit(rc)

if __name__ == "__main__":
    main()
