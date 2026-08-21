#!/usr/bin/env python3
"""
ab_test_tracker.py — A/B test de orden CV (Sprint 4 Learning Loop, 2026-08-21)

Variantes:
  A = Proyectos primero (PROJECTS antes de SKILLS) — hipotesis: mejor callback en roles IA/data/portfolio-heavy
  B = Skills primero (SKILLS antes de PROJECTS)   — hipotesis: mejor ATS keyword-scan en roles soporte/BI

Tracker: añade columna 14 `cv_variant` (A/B/"") a tracker/applications.csv
Header target (14 cols, BOM-safe, idempotente):
  fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|contacto_interno|fecha_followup|ats_score|cv_variant

Asignacion deterministica: sha256(empresa|titulo normalizado) %2 -> A/B.
Balance: si desbalance >60/40, --rebalance asigna siguiente vacio a minoritario.

Stats: tasa entrevista = entrevista/(aplicada+entrevista+oferta+rechazo+silencio)
  Entrevista = estado.lower() in {"entrevista","oferta"}
  Enviada    = estado.lower() in {"aplicada","aplicada","entrevista","oferta","rechazo","silencio","aplicada "}
  Pendientes/radar/backup/descartada no cuentan como enviada hasta envio real.

Uso:
  python scripts/ab_test_tracker.py --check
  python scripts/ab_test_tracker.py --migrate
  python scripts/ab_test_tracker.py --assign --dry-run
  python scripts/ab_test_tracker.py --assign
  python scripts/ab_test_tracker.py --stats
  python scripts/ab_test_tracker.py --stats --json
  python scripts/ab_test_tracker.py --set 5 A   # linea 5 (1-indexed, header no cuenta)

Integracion tailor_cv / yaml_to_md:
  - csv csv_variant se lee en tailor_cv.py --variant A|B para reordenar MD.
  - yaml_to_md.py futuro flag --variant A|B reordena secciones (ver docs/specs/learning_spec.md).

No inventa entrevistas; solo mide lo registrado.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "tracker" / "applications.csv"

HEADER_13 = "fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|contacto_interno|fecha_followup|ats_score"
HEADER_14 = HEADER_13 + "|cv_variant"

FINAL_STATES_EXCLUDE = set()  # no se excluye variante
ENTREVISTA_STATES = {"entrevista", "oferta"}
ENVIADA_STATES = {"aplicada", "entrevista", "oferta", "rechazo", "silencio"}  # normalizado lower
# estados que NO cuentan como enviada (aun no enviada):
NO_ENVIADA = {"a enviar", "aplicar ya", "aplicar esta semana", "pendiente", "verificar", "evaluar", "backup", "semana", "descartada", "descartadas", "radar 2027", "radar", "dudosa", "descarta"}


def _norm(s: str) -> str:
    return s.strip().lower().replace("  ", " ")


def parse_csv(path: Path):
    if not path.exists():
        print(f"ERROR no existe {path}", file=sys.stderr)
        sys.exit(2)
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    hdr_idx = None
    for i, l in enumerate(lines):
        if not l.strip() or l.strip().startswith("#"):
            continue
        hdr_idx = i
        break
    if hdr_idx is None:
        print("ERROR no header", file=sys.stderr)
        sys.exit(2)
    header = lines[hdr_idx].strip()
    cols = [c.strip() for c in header.split("|")]
    rows = []
    for i, l in enumerate(lines):
        if i <= hdr_idx:
            continue
        if not l.strip() or l.strip().startswith("#"):
            rows.append((i, l, None))
            continue
        parts = l.split("|")
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        row = dict(zip(cols, parts))
        row["_line_idx"] = i
        row["_raw"] = l
        rows.append((i, l, row))
    return has_bom, lines, hdr_idx, header, cols, rows


def variant_for(empresa: str, titulo: str) -> str:
    key = f"{_norm(empresa)}|{_norm(titulo)}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()
    return "A" if int(h, 16) % 2 == 0 else "B"


def migrate(path: Path, check_only=False) -> int:
    has_bom, lines, hdr_idx, header, cols, rows = parse_csv(path)
    if header == HEADER_14:
        print(f"OK ya 14 cols cv_variant: {path.name}")
        return 0
    if "cv_variant" in cols:
        print(f"OK ya contiene cv_variant: {header}")
        return 0
    if check_only:
        print(f"DRIFT {path.name} header={header} -> esperado 14 cols", file=sys.stderr)
        print(f"  actual  : {header}", file=sys.stderr)
        print(f"  esperado: {HEADER_14}", file=sys.stderr)
        return 1
    # expandir header
    out = list(lines)
    if header == HEADER_13:
        out[hdr_idx] = HEADER_14
    elif "ats_score" in header and "cv_variant" not in header:
        out[hdr_idx] = header + "|cv_variant"
    else:
        # fallback completar
        cur = header
        if "contacto_interno" not in cur:
            cur += "|contacto_interno"
        if "fecha_followup" not in cur:
            cur += "|fecha_followup"
        if "ats_score" not in cur:
            cur += "|ats_score"
        if "cv_variant" not in cur:
            cur += "|cv_variant"
        out[hdr_idx] = cur
    # pad filas data
    new_cols = [c.strip() for c in out[hdr_idx].split("|")]
    for idx, raw, row in rows:
        if row is None:
            continue
        parts = raw.split("|")
        if len(parts) < len(new_cols):
            parts += [""] * (len(new_cols) - len(parts))
            out[idx] = "|".join(parts)
    text = "\n".join(out) + "\n"
    if has_bom:
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    else:
        path.write_text(text, encoding="utf-8")
    print(f"OK migrado {path.name}: {len(cols)} -> {len(new_cols)} cols (cv_variant)")
    return 0


def assign_variants(path: Path, dry_run=False, rebalance=False) -> int:
    has_bom, lines, hdr_idx, header, cols, rows = parse_csv(path)
    if "cv_variant" not in cols:
        print(f"ERROR falta cv_variant, correr --migrate primero. header={header}", file=sys.stderr)
        return 2
    idx_variant = cols.index("cv_variant")
    idx_empresa = cols.index("empresa") if "empresa" in cols else -1
    idx_titulo = cols.index("titulo") if "titulo" in cols else -1

    # contar existentes para rebalance
    existing = Counter()
    for _, _, row in rows:
        if row is None:
            continue
        v = row.get("cv_variant", "").strip().upper()
        if v in ("A", "B"):
            existing[v] += 1

    changed = 0
    out = list(lines)
    for line_idx, raw, row in rows:
        if row is None:
            continue
        v = row.get("cv_variant", "").strip().upper()
        if v in ("A", "B"):
            continue
        empresa = row.get("empresa", "") if idx_empresa >= 0 else ""
        titulo = row.get("titulo", "") if idx_titulo >= 0 else ""
        # sin empresa/titulo no asigna (radar vacio)
        if not empresa.strip() and not titulo.strip():
            continue
        det = variant_for(empresa, titulo)
        if rebalance and existing:
            total = existing["A"] + existing["B"]
            if total > 0:
                ratio_a = existing["A"] / total if total else 0.5
                # si A domina >60% y det es A, flip a B (y viceversa)
                if ratio_a > 0.60 and det == "A":
                    det = "B"
                elif ratio_a < 0.40 and det == "B":
                    det = "A"
        parts = raw.split("|")
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        parts[idx_variant] = det
        out[line_idx] = "|".join(parts)
        existing[det] += 1
        changed += 1
        print(f"  L{line_idx+1} {empresa} | {titulo[:40]} -> {det} (det)")

    if dry_run:
        print(f"[DRY-RUN] {changed} asignaciones pendientes (no escrito). Balance actual A:{existing['A']} B:{existing['B']}")
        return 0
    if changed == 0:
        print(f"OK sin asignaciones pendientes. Balance A:{existing['A']} B:{existing['B']}")
        return 0
    text = "\n".join(out) + "\n"
    if has_bom:
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    else:
        path.write_text(text, encoding="utf-8")
    print(f"OK asignadas {changed} filas. Balance final A:{existing['A']} B:{existing['B']}")
    return 0


def stats(path: Path, as_json=False) -> int:
    has_bom, lines, hdr_idx, header, cols, rows = parse_csv(path)
    if "cv_variant" not in cols:
        print(f"WARN sin cv_variant, correr --migrate --assign. header={header}", file=sys.stderr)

    # buckets por variante
    buckets = defaultdict(lambda: {"enviadas": 0, "entrevistas": 0, "ofertas": 0, "rechazos": 0, "silencio": 0, "filas": 0})
    no_variant = 0
    for _, _, row in rows:
        if row is None:
            continue
        estado_n = _norm(row.get("estado", ""))
        if not estado_n:
            continue
        variant = row.get("cv_variant", "").strip().upper() if "cv_variant" in cols else ""
        if variant not in ("A", "B"):
            no_variant += 1
            # igual cuenta para total sin variante
        vkey = variant if variant in ("A", "B") else "sin_variante"
        buckets[vkey]["filas"] += 1
        if estado_n in ENVIADA_STATES or estado_n in ENTREVISTA_STATES:
            # entrevista ya es subset de enviada pero contamos separado
            pass
        # enviada: solo si estado indica que se envio
        if estado_n in ENVIADA_STATES:
            buckets[vkey]["enviadas"] += 1
        if estado_n in ENTREVISTA_STATES:
            # entrevista cuenta como enviada tambien si no entro arriba por normalizacion
            if estado_n not in ENVIADA_STATES:
                buckets[vkey]["enviadas"] += 1
            buckets[vkey]["entrevistas"] += 1
        if estado_n == "oferta":
            buckets[vkey]["ofertas"] += 1
        if estado_n == "rechazo":
            buckets[vkey]["rechazos"] += 1
        if estado_n == "silencio":
            buckets[vkey]["silencio"] += 1

    # calcular tasas
    result = {}
    for k in sorted(buckets.keys()):
        b = buckets[k]
        env = b["enviadas"]
        ent = b["entrevistas"]
        tasa = (ent / env * 100) if env > 0 else 0.0
        b["tasa_entrevista"] = round(tasa, 1)
        # suficiencia
        suff = "suficiente" if env >= 30 else f"insuficiente (n={env}, min 30 para p<0.05)"
        b["suficiencia"] = suff
        result[k] = b

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== A/B tasa entrevista — {path.name} ===")
        for k in ["A", "B", "sin_variante"]:
            if k not in result:
                continue
            b = result[k]
            print(f"  {k}: enviadas={b['enviadas']} entrevistas={b['entrevistas']} ofertas={b['ofertas']} tasa={b['tasa_entrevista']}%  [{b['suficiencia']}] filas={b['filas']}")
        if "A" in result and "B" in result:
            da = result["A"]["tasa_entrevista"]
            db = result["B"]["tasa_entrevista"]
            delta = round(da - db, 1)
            print(f"  delta A-B: {delta:+.1f}pp  (A proyectos-primero vs B skills-primero)")
            if result["A"]["enviadas"] < 30 or result["B"]["enviadas"] < 30:
                print("  [WARN] n<30 por variante — no concluir ganadora; seguir recolectando.")
            elif abs(delta) < 5:
                print("  [INFO] delta <5pp — sin ganador practico.")
            else:
                win = "A" if delta > 0 else "B"
                print(f"  [LEAD] {win} lidera por {abs(delta):.1f}pp")
        if no_variant:
            print(f"  [NOTA] {no_variant} filas sin variante (correr --assign)")

    return 0


def set_variant(path: Path, line_no: int, variant: str) -> int:
    variant = variant.strip().upper()
    if variant not in ("A", "B", ""):
        print("ERROR variant debe ser A/B/''", file=sys.stderr)
        return 2
    has_bom, lines, hdr_idx, header, cols, rows = parse_csv(path)
    if "cv_variant" not in cols:
        print("ERROR falta cv_variant", file=sys.stderr)
        return 2
    idx_variant = cols.index("cv_variant")
    # line_no es numero de fila de datos 1-indexed (excluye header/comentarios)
    data_rows = [(i, r, row) for i, r, row in rows if row is not None]
    if line_no < 1 or line_no > len(data_rows):
        print(f"ERROR linea {line_no} fuera de rango 1..{len(data_rows)}", file=sys.stderr)
        return 2
    target_idx, _, row = data_rows[line_no - 1]
    parts = lines[target_idx].split("|")
    if len(parts) < len(cols):
        parts += [""] * (len(cols) - len(parts))
    parts[idx_variant] = variant
    lines[target_idx] = "|".join(parts)
    text = "\n".join(lines) + "\n"
    if has_bom:
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    else:
        path.write_text(text, encoding="utf-8")
    print(f"OK L{target_idx+1} cv_variant={variant} ({row.get('empresa','')})")
    return 0


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="A/B tracker CV variante A/B")
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    ap.add_argument("--check", action="store_true", help="Verifica header 14 cols")
    ap.add_argument("--migrate", action="store_true", help="Migra a 14 cols")
    ap.add_argument("--assign", action="store_true", help="Asigna A/B a filas vacias")
    ap.add_argument("--rebalance", action="store_true", help="Corrige desbalance >60/40")
    ap.add_argument("--stats", action="store_true", help="Muestra tasa entrevista por variante")
    ap.add_argument("--json", action="store_true", help="Stats en JSON")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--set", nargs=2, metavar=("LINEA", "VARIANTE"), help="Set manual: --set 5 A")
    args = ap.parse_args()

    path = Path(args.csv)

    if args.check:
        return sys.exit(migrate(path, check_only=True))
    if args.migrate:
        return sys.exit(migrate(path, check_only=False))
    if args.assign:
        return sys.exit(assign_variants(path, dry_run=args.dry_run, rebalance=args.rebalance))
    if args.stats:
        return sys.exit(stats(path, as_json=args.json))
    if args.set:
        return sys.exit(set_variant(path, int(args.set[0]), args.set[1]))

    ap.print_help()
    print("\nEjemplos:\n  python scripts/ab_test_tracker.py --migrate\n  python scripts/ab_test_tracker.py --assign --dry-run\n  python scripts/ab_test_tracker.py --assign\n  python scripts/ab_test_tracker.py --stats")
    sys.exit(1)


if __name__ == "__main__":
    main()
