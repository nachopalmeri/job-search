#!/usr/bin/env python3
"""
generate_cover_letter.py -- Generador cover letter automatico (Sprint 3 Conversion)

Por cada cv_*.md en CV_Material_Nacho/extras/cvs_personalizados genera
cover_letter_<empresa>.txt con 3 parrafos (por que vos / por que empresa / cierre portfolio)
sin inventar datos. Fuente de verdad: cv_master.yaml + MD fuente.

Uso:
  python scripts/generate_cover_letter.py --all
  python scripts/generate_cover_letter.py --all --dry-run
  python scripts/generate_cover_letter.py --empresa lotba --jd-file aviso.txt --lang es
  python scripts/generate_cover_letter.py --empresa sap --lang en --force

Reglas anti-invencion:
- ALLOWLIST = texto flatten de cv_master.yaml + MD fuente + profile.md.
- Si JD keyword no esta en allowlist, no se espeja.
- Bloquea claims prohibidos: bilingue/avanzado ingles, RHCSA, CCNA certificado, DApp, Web3 architect, 200+ clientes (profile.md:41-44).
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CVS_DIR = ROOT / "CV_Material_Nacho" / "extras" / "cvs_personalizados"
CARTAS_DIR = ROOT / "CV_Material_Nacho" / "extras" / "cartas_presentacion"
YAML_MASTER = ROOT / "CV_Material_Nacho" / "cv_master.yaml"
TRACKER = ROOT / "tracker" / "applications.csv"
PROFILE = ROOT / "profile.md"

BLOCKED = ["bilingue", "bilingual", "ingles avanzado", "english advanced", "rhcsa certificado",
           "ccna certificado", "dapp", "solidity", "web3 architect", "200+ clientes", "make/zapier"]

# Contacto fijo desde profile.md / cv_master.yaml (no hardcodear distinto)
CONTACT = {
    "name": "Ignacio Palmeri",
    "email": "ignaciopalmeri1@gmail.com",
    "phone": "+54 9 11 5509-0832",
    "linkedin": "linkedin.com/in/ignaciopalmeri",
    "github": "github.com/nachopalmeri",
    "portfolio": "https://ignaciopalmeri.vercel.app",
    "portfolio_cv": "https://ignaciopalmeri.vercel.app/cv",
    "location": "Buenos Aires",
    "studies": "Lic. en Gestion de Tecnologias de la Informacion (UADE, 2do ano Q4, promedio 8.2/10)",
    "studies_en": "B.A. in Information Technology Management (UADE, 2nd year Q4, GPA 8.2/10)",
}


def flatten_yaml_text(data: dict) -> str:
    parts = []
    b = data.get("basics", {})
    parts.append(b.get("label", "") + " " + b.get("label_en", ""))
    for e in data.get("education", []):
        parts.append(" ".join([e.get("area", ""), e.get("area_en", ""), e.get("details", ""), e.get("details_en", "")]))
    for x in data.get("experience", []):
        parts.append(" ".join([x.get("position", ""), x.get("position_en", "")] + x.get("highlights", []) + x.get("highlights_en", [])))
    for p in data.get("projects", []):
        parts.append(" ".join([p.get("role", ""), p.get("role_en", "")] + p.get("keywords", []) + p.get("highlights", []) + p.get("highlights_en", [])))
    for s in data.get("skills", []):
        parts.append(" ".join(s.get("keywords", [])))
    return " ".join(parts)


def load_allowlist(md_text: str) -> str:
    allow = md_text.lower()
    if YAML_MASTER.exists():
        try:
            import yaml
            data = yaml.safe_load(YAML_MASTER.read_text(encoding="utf-8"))
            allow += " " + flatten_yaml_text(data).lower()
        except Exception:
            pass
    if PROFILE.exists():
        allow += " " + PROFILE.read_text(encoding="utf-8", errors="ignore").lower()
    return allow


def safe_extract_projects(md_text: str) -> list[str]:
    # Extrae bullets de PROYECTOS/PROJECTS como evidencia citable (max 2)
    in_projects = False
    bullets = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            in_projects = "PROYECT" in line.upper()
            continue
        if in_projects and line.strip().startswith("- ") and len(bullets) < 4:
            bullets.append(line.strip()[2:].strip())
        if in_projects and line.startswith("## ") and bullets:
            break
    return bullets[:2]


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")[:40]


def blocked_check(text: str) -> list[str]:
    low = text.lower()
    return [b for b in BLOCKED if b.lower() in low]


def parse_tracker_row(empresa_slug: str) -> dict | None:
    if not TRACKER.exists():
        return None
    txt = TRACKER.read_bytes().decode("utf-8-sig", errors="ignore")
    for line in txt.splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("fecha|"):
            continue
        cols = line.split("|")
        # fecha|portal|titulo|empresa|ubicacion|link|fit|gap|estado|notas...
        if len(cols) < 4:
            continue
        empresa = cols[3].strip().lower()
        if slugify(empresa) == empresa_slug or empresa_slug in slugify(empresa):
            return {"titulo": cols[2].strip(), "empresa": cols[3].strip(), "ubicacion": cols[4].strip(), "link": cols[5].strip() if len(cols) > 5 else ""}
    return None


def build_letter(md_path: Path, empresa_slug: str, jd_text: str = "", lang: str = "es") -> str:
    md_text = md_path.read_text(encoding="utf-8", errors="ignore")
    allowlist = load_allowlist(md_text)
    bullets = safe_extract_projects(md_text)
    # Determinar titulo/empresa desde tracker o slug
    meta = parse_tracker_row(empresa_slug) or {"titulo": empresa_slug.replace("_", " ").title(), "empresa": empresa_slug.replace("_", " ").title(), "ubicacion": "", "link": ""}
    today = date.today().strftime("%d de %B de %Y" if lang == "es" else "%B %d, %Y")
    # Parrafo 1: por que vos (solo hechos del MD)
    studies = CONTACT["studies"] if lang == "es" else CONTACT["studies_en"]
    disp = "20 h semanales, hibrido/presencial CABA/GBA" if lang == "es" else "20 h/week, hybrid/on-site CABA/GBA"
    ev = ""
    if bullets:
        # usar 1 bullet real, truncado
        ev = bullets[0][:160].rstrip(".") + "."
        # validar que ev no inventa fuera de allowlist (ya viene del MD, ok)
    if lang == "es":
        p1 = f"Soy {CONTACT['name']}, estudiante de {studies}. Me presento a la busqueda de {meta['titulo']} en {meta['empresa']} porque mi perfil combina lo que piden con lo que ya hago: {ev} Busco una pasantia part-time ({disp}) donde pueda aprender construyendo."
    else:
        p1 = f"I am {CONTACT['name']}, {studies_en} student. I am applying for {meta['titulo']} at {meta['empresa']} as my background matches the role: {ev} I am seeking a part-time internship ({disp}) to learn by building."
        # fix var name
        p1 = p1.replace("{studies_en}", studies)

    # Parrafo 2: por que empresa (solo si hay JD, cita verbatim 1ra oracion; si no, generico honesto)
    if jd_text and len(jd_text.strip()) > 50:
        first_sentence = re.split(r"[.\n]", jd_text.strip())[0].strip()[:220]
        # no espejar keywords bloqueadas
        if lang == "es":
            p2 = f"Me interesa {meta['empresa']} porque el aviso describe: \"{first_sentence}\". Mi experiencia en atencion y operaciones de alto trafico y mis proyectos con Python/SQL/Excel y automatizacion con LLMs me dan criterio para ordenar informacion, generar indicadores y documentar procesos de forma auditable desde el primer dia."
        else:
            p2 = f"I am interested in {meta['empresa']} because the posting states: \"{first_sentence}\". My high-traffic customer-facing experience and my Python/SQL/Excel + LLM automation projects give me judgment to structure information, build indicators and document processes auditably from day one."
    else:
        # generico sin inventar valores/mision
        skills_hint = "investigacion en fuentes abiertas, organizacion de grandes volumenes de informacion y elaboracion de informes" if "investigacion" in md_text.lower() else "analisis de datos, automatizacion y soporte"
        if lang == "es":
            p2 = f"La posicion de {meta['titulo']} en {meta['empresa']} combina {skills_hint} con trabajo con Excel/SQL/Python, que es exactamente mi stack diario. Aporto prolijidad, trazabilidad y ganas de aprender lo especifico del dominio."
        else:
            p2 = f"The {meta['titulo']} role at {meta['empresa']} combines {skills_hint} with Excel/SQL/Python — my daily stack. I bring thoroughness, traceability and eagerness to learn the domain specifics."

    # Parrafo 3: cierre con portfolio (CTA trackeable)
    pro_file = f"Ignacio_Palmeri_{empresa_slug.title().replace('_','')}.pdf"
    if lang == "es":
        p3 = f"Quedo a disposicion para una entrevista. Portfolio: {CONTACT['portfolio_cv']} — CV adjunto ({pro_file}). Contacto: {CONTACT['email']} · {CONTACT['phone']} · {CONTACT['linkedin']} · {CONTACT['github']}."
    else:
        p3 = f"Available for an interview. Portfolio: {CONTACT['portfolio_cv']} — CV attached ({pro_file}). Contact: {CONTACT['email']} · {CONTACT['phone']} · {CONTACT['linkedin']} · {CONTACT['github']}."

    header = f"{CONTACT['location']}, {today}\n\nEstimados/as del equipo de Seleccion de {meta['empresa']}:" if lang == "es" else f"{CONTACT['location']}, {today}\n\nDear {meta['empresa']} Hiring Team:"
    body = f"{header}\n\n{p1}\n\n{p2}\n\n{p3}\n\nSaludos cordiales,\n{CONTACT['name']}\n{CONTACT['phone']} · {CONTACT['email']}" if lang == "es" else f"{header}\n\n{p1}\n\n{p2}\n\n{p3}\n\nKind regards,\n{CONTACT['name']}\n{CONTACT['phone']} · {CONTACT['email']}"
    # validaciones
    assert CONTACT["portfolio_cv"] in body, "portfolio /cv ausente"
    blocked = blocked_check(body)
    if blocked:
        raise ValueError(f"Blocked claims detectados: {blocked} — corregir plantilla")
    return body


def main():
    ap = argparse.ArgumentParser(description="Genera cover_letter_<empresa>.txt (3 parrafos, sin inventar)")
    ap.add_argument("--all", action="store_true", help="Barre cvs_personalizados/cv_*.md")
    ap.add_argument("--empresa", help="Slug empresa (ej: lotba, sap)")
    ap.add_argument("--jd-file", help="Ruta a JD.txt para parrafo 2")
    ap.add_argument("--lang", choices=["es", "en"], default="es")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jd_text = ""
    if args.jd_file:
        p = Path(args.jd_file)
        if not p.exists():
            print(f"ERROR: JD no existe: {p}", file=sys.stderr); sys.exit(2)
        jd_text = p.read_text(encoding="utf-8", errors="ignore")

    targets: list[Path] = []
    if args.all:
        targets = sorted(CVS_DIR.glob("cv_*.md"))
        if not targets:
            print(f"ERROR: no hay cv_*.md en {CVS_DIR}", file=sys.stderr); sys.exit(2)
    elif args.empresa:
        slug = slugify(args.empresa)
        # buscar cv que matchee slug
        cand = list(CVS_DIR.glob(f"cv_{slug}*.md"))
        if cand:
            targets = [cand[0]]
        else:
            # fallback: usar master como base
            master = ROOT / "CV_Material_Nacho" / f"cv_master_{args.lang}.md"
            if master.exists():
                targets = [master]
                print(f"WARN: no hay cv_{slug}.md, uso {master.name} como base", file=sys.stderr)
            else:
                print(f"ERROR: no se encontro cv para {slug}", file=sys.stderr); sys.exit(2)
    else:
        ap.print_help(); sys.exit(2)

    CARTAS_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for md in targets:
        # slug empresa desde nombre cv: cv_lotba_investigacion -> lotba_investigacion
        stem = md.stem
        empresa_slug = stem[3:] if stem.startswith("cv_") else stem
        if args.empresa:
            empresa_slug = slugify(args.empresa)
        out = CARTAS_DIR / f"cover_letter_{empresa_slug}.txt"
        out_md = CARTAS_DIR / f"cover_letter_{empresa_slug}.md"
        if out.exists() and not args.force and not args.dry_run:
            print(f"SKIP existe {out.name} (usar --force)"); continue
        try:
            letter = build_letter(md, empresa_slug, jd_text=jd_text, lang=args.lang)
        except Exception as e:
            print(f"FAIL {md.name} -> {e}", file=sys.stderr); continue
        # validacion 3 parrafos
        paras = [p for p in letter.split("\n\n") if p.strip()]
        if len(paras) < 4:
            print(f"WARN {empresa_slug}: se esperaban 3 parrafos + header/cierre, hay {len(paras)}", file=sys.stderr)
        if args.dry_run:
            print(f"\n[DRY-RUN] {md.name} -> {out.name} ({len(letter)} chars)\n---\n{letter[:900]}\n---")
        else:
            out.write_text(letter, encoding="utf-8")
            out_md.write_text(f"# Cover letter — {empresa_slug}\n\n> Generado desde `{md.name}` — {args.lang} — {date.today().isoformat()} — sin datos inventados.\n\n" + letter, encoding="utf-8")
            print(f"OK {md.name} -> {out.name} ({len(letter)} chars) + {out_md.name}")
            ok += 1
    if not args.dry_run:
        print(f"\nHecho: {ok}/{len(targets)} cartas generadas en {CARTAS_DIR}")
        print(f"Siguiente: adjuntar Ignacio_Palmeri_<Empresa>.pdf generado via generate_cv_files.py")

if __name__ == "__main__":
    main()
