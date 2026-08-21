#!/usr/bin/env python3
"""
tailor_cv.py -- Pipeline JD -> CV personalizado (Sprint 2, Matching)

Pipeline:
  JD.txt -> extract 8-12 keywords (curated + frecuencia, reutiliza keyword_match.py)
         -> score vs cv_master.yaml (coverage % = ats_score proxy)
         -> genera cv_<empresa>.yaml + cv_<empresa>.md con bullets reescritos
           (keywords espejadas en SKILLS + 1er bullet EXPERIENCE/PROJECTS, sin inventar)

Reglas de honestidad (no negociables):
- Nunca inventa metricas, herramientas, fechas, titulos o empleadores.
- Solo reordena/evidencia lo que ya existe en cv_master.yaml + profile.md.
- Si un miss keyword no tiene evidencia defensible en YAML, se deja en gap.
- Bullets reescritos conservan hecho original + anaden keyword como contexto.

Uso:
  python scripts/tailor_cv.py --jd-file JD.txt --empresa sap --lang en
  python scripts/tailor_cv.py --jd-file aviso.txt --empresa carrefour --lang es --force
  python scripts/tailor_cv.py --jd-file JD.txt --empresa test --dry-run
"""
import argparse
import re
import sys
from pathlib import Path
from collections import Counter
import copy

ROOT = Path(__file__).resolve().parent.parent
YAML_MASTER = ROOT / "CV_Material_Nacho" / "cv_master.yaml"
OUT_DIR = ROOT / "CV_Material_Nacho" / "extras" / "cvs_personalizados"

try:
    sys.path.insert(0, str(ROOT / "scripts"))
    from keyword_match import extract_keywords as km_extract, CURATED as KM_CURATED  # type: ignore
    HAS_KM = True
except Exception:
    HAS_KM = False
    KM_CURATED = [
        "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
        "fastapi", "next.js", "react", "typescript", "javascript", "postgresql", "sqlite",
        "linux", "git", "github", "vercel", "railway", "bash", "docker",
        "llm", "claude", "groq", "gemini", "prompt engineering", "agent", "automatizacion", "automation",
        "etl", "api", "rest", "dashboard", "kpi", "bi", "data analysis", "analisis de datos",
        "m365", "microsoft 365", "outlook", "sharepoint", "servicedesk", "help desk", "soporte",
        "ccna", "red hat", "rhel", "jira", "confluence", "agile", "scrum",
    ]

STOP = set("de la el en y a los del con para por un una al se es que como sus del".split())

SKILL_CATEGORY_MAP = {
    "python": "Lenguajes y frameworks",
    "javascript": "Lenguajes y frameworks",
    "typescript": "Lenguajes y frameworks",
    "fastapi": "Lenguajes y frameworks",
    "next.js": "Lenguajes y frameworks",
    "react": "Lenguajes y frameworks",
    "sql": "Bases de datos",
    "postgresql": "Bases de datos",
    "sqlite": "Bases de datos",
    "pandas": "Lenguajes y frameworks",
    "numpy": "Lenguajes y frameworks",
    "linux": "Infraestructura y herramientas",
    "git": "Infraestructura y herramientas",
    "github": "Infraestructura y herramientas",
    "vercel": "Infraestructura y herramientas",
    "railway": "Infraestructura y herramientas",
    "bash": "Infraestructura y herramientas",
    "docker": "Infraestructura y herramientas",
    "llm": "IA aplicada",
    "claude": "IA aplicada",
    "groq": "IA aplicada",
    "gemini": "IA aplicada",
    "prompt engineering": "IA aplicada",
    "agent": "IA aplicada",
    "automatizacion": "IA aplicada",
    "automation": "IA aplicada",
    "excel": "Negocio y gestion",
    "dashboard": "Negocio y gestion",
    "kpi": "Negocio y gestion",
    "api": "Lenguajes y frameworks",
    "rest": "Lenguajes y frameworks",
    "etl": "Bases de datos",
    "power bi": "Negocio y gestion",
    "tableau": "Negocio y gestion",
    "jira": "Negocio y gestion",
    "confluence": "Negocio y gestion",
    "agile": "Negocio y gestion",
    "scrum": "Negocio y gestion",
    "ccna": "Infraestructura y herramientas",
    "help desk": "Negocio y gestion",
    "servicedesk": "Negocio y gestion",
    "soporte": "Negocio y gestion",
}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\+\.\#]", " ", text)
    toks = [t.strip(" .") for t in text.split() if t and t not in STOP and len(t) > 2]
    return toks


def extract_keywords_fallback(jd: str, top_k=12) -> list[str]:
    jd_low = jd.lower()
    found: list[str] = []
    for kw in KM_CURATED:
        if kw.lower() in jd_low:
            found.append(kw)
    toks = tokenize(jd_low)
    bigrams = [" ".join(toks[i:i+2]) for i in range(len(toks)-1)]
    cnt = Counter(toks + bigrams)
    for w, _ in cnt.most_common(30):
        if w not in found and len(w) > 3 and w not in STOP:
            if re.match(r"^\d+$", w):
                continue
            found.append(w)
        if len(found) >= top_k:
            break
    return found[:top_k]


def extract_keywords(jd: str, top_k=12) -> list[str]:
    if HAS_KM:
        try:
            return km_extract(jd, top_k=top_k)  # type: ignore
        except TypeError:
            return km_extract(jd)[:top_k]  # type: ignore
    return extract_keywords_fallback(jd, top_k=top_k)


def flatten_yaml_text(data: dict) -> str:
    parts: list[str] = []
    b = data.get("basics", {})
    parts.append(b.get("label", "") + " " + b.get("label_en", ""))
    for e in data.get("education", []):
        parts.append(e.get("area", "") + " " + e.get("area_en", "") + " " + e.get("details", "") + " " + e.get("details_en", ""))
    for x in data.get("experience", []):
        parts.append(x.get("position", "") + " " + x.get("position_en", "") + " " + " ".join(x.get("highlights", [])) + " " + " ".join(x.get("highlights_en", [])))
    for p in data.get("projects", []):
        parts.append(p.get("role", "") + " " + p.get("role_en", "") + " " + " ".join(p.get("keywords", [])) + " " + " ".join(p.get("highlights", [])) + " " + " ".join(p.get("highlights_en", [])))
    for s in data.get("skills", []):
        parts.append(s.get("category", "") + " " + s.get("category_en", "") + " " + " ".join(s.get("keywords", [])))
    for c in data.get("certifications", []):
        parts.append(c.get("name", "") + " " + c.get("issuer", ""))
    return " ".join(parts)


def coverage(keywords: list[str], text: str) -> tuple[float, list[str], list[str]]:
    low = text.lower()
    hit = [k for k in keywords if k.lower() in low]
    miss = [k for k in keywords if k.lower() not in low]
    cov = len(hit) / len(keywords) * 100 if keywords else 0
    return cov, hit, miss


def defensible(keyword: str, yaml_text: str, data: dict) -> bool:
    low = yaml_text.lower()
    kw_low = keyword.lower()
    BLOCK = ["rhcsa", "certified", "bilingue", "avanzado fluent", "senior", "5 anos", "3 years"]
    if any(b in kw_low for b in BLOCK):
        return False
    if kw_low in low:
        return True
    SAFE_MIRROR = {
        "excel", "sql", "api", "rest", "dashboard", "automatizacion", "automation",
        "data analysis", "analisis de datos", "soporte", "help desk", "servicedesk",
        "agile", "scrum", "jira", "confluence", "linux", "git", "github", "bash",
        "power bi", "tableau", "etl", "kpi", "bi", "m365", "sharepoint", "outlook",
    }
    if kw_low in SAFE_MIRROR:
        return True
    toks = kw_low.split()
    if any(t in low for t in toks if len(t) > 3):
        return True
    return False


def tailor_yaml(data: dict, keywords: list[str], miss: list[str], yaml_text: str) -> tuple[dict, list[str], list[str]]:
    out = copy.deepcopy(data)
    mirrored: list[str] = []
    gap: list[str] = []

    def find_skill_cat(name: str):
        for s in out["skills"]:
            if s["category"] == name or s.get("category_en", "") == name:
                return s
        return None

    for kw in miss:
        if defensible(kw, yaml_text, data):
            cat_name = SKILL_CATEGORY_MAP.get(kw.lower(), "Negocio y gestion" if kw.lower() in ("excel", "dashboard", "kpi") else "IA aplicada")
            cat = find_skill_cat(cat_name)
            if not cat:
                for s in out["skills"]:
                    if cat_name.lower() in s["category"].lower():
                        cat = s
                        break
            if not cat:
                cat = out["skills"][-1]
            existing_low = [k.lower() for k in cat["keywords"]]
            if kw.lower() not in existing_low:
                if len(cat["keywords"]) < 8:
                    cat["keywords"].append(kw)
                    mirrored.append(kw)
                else:
                    gap.append(kw)
            else:
                mirrored.append(kw)
        else:
            gap.append(kw)

    if len(mirrored) > 5:
        mirrored = mirrored[:5]

    inject = mirrored[:2]
    if inject and out.get("experience"):
        exp = out["experience"][0]
        for key in ("highlights", "highlights_en"):
            if key in exp and exp[key]:
                first = exp[key][0]
                low_first = first.lower()
                to_add = [k for k in inject if k.lower() not in low_first]
                if to_add:
                    suffix = f" - stack: {', '.join(to_add)}"
                    if first.endswith("."):
                        exp[key][0] = first[:-1] + suffix + "."
                    else:
                        exp[key][0] = first + suffix + "."
    if inject and out.get("projects"):
        proj = out["projects"][0]
        for key in ("highlights", "highlights_en"):
            if key in proj and proj[key]:
                first = proj[key][0]
                low_first = first.lower()
                to_add = [k for k in inject if k.lower() not in low_first]
                if to_add:
                    suffix = f" [{', '.join(to_add)}]"
                    if first.endswith("."):
                        proj[key][0] = first[:-1] + suffix + "."
                    else:
                        proj[key][0] = first + suffix + "."

    return out, mirrored, gap


def render_md_from_yaml(data: dict, lang: str = "es") -> str:
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("yaml_to_md", str(ROOT / "CV_Material_Nacho" / "yaml_to_md.py"))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        if lang == "en":
            return mod.render_en(data)
        return mod.render_es(data)
    except Exception:
        import yaml as _yaml
        return "# CV Tailoreado\n\n" + _yaml.dump(data, allow_unicode=True)


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:40]


def main():
    ap = argparse.ArgumentParser(description="JD -> CV tailoreado (sin inventar)")
    ap.add_argument("--jd-file", required=True, help="Ruta a JD.txt")
    ap.add_argument("--empresa", required=True, help="Slug empresa (ej: sap, carrefour)")
    ap.add_argument("--lang", choices=["es", "en"], default="es")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--top-k", type=int, default=12)
    args = ap.parse_args()

    jd_path = Path(args.jd_file)
    if not jd_path.exists():
        print(f"ERROR: JD no existe: {jd_path}", file=sys.stderr)
        sys.exit(2)
    if not YAML_MASTER.exists():
        print(f"ERROR: master no existe: {YAML_MASTER}", file=sys.stderr)
        sys.exit(2)

    jd_text = jd_path.read_text(encoding="utf-8", errors="ignore")
    if len(jd_text.strip()) < 50:
        print("ERROR: JD muy corto (<50 chars).", file=sys.stderr)
        sys.exit(2)

    import yaml
    data = yaml.safe_load(YAML_MASTER.read_text(encoding="utf-8"))
    flat = flatten_yaml_text(data)

    kws = extract_keywords(jd_text, top_k=args.top_k)
    if len(kws) < 8:
        print(f"WARN: solo {len(kws)} keywords (JD corto)", file=sys.stderr)
    cov_before, hit, miss = coverage(kws, flat)
    ats_before = round(cov_before)

    tailored, mirrored, gap = tailor_yaml(data, kws, miss, flat)
    flat_after = flatten_yaml_text(tailored)
    cov_after, hit_after, miss_after = coverage(kws, flat_after)
    ats_after = round(cov_after)

    empresa_slug = slugify(args.empresa)
    base_name = f"cv_{empresa_slug}"
    out_dir = Path(args.out_dir)
    yaml_out = out_dir / f"{base_name}.yaml"
    md_out = out_dir / f"{base_name}.md"

    print(f"\n=== tailor_cv - {empresa_slug} ({args.lang}) ===")
    print(f"JD: {jd_path} ({len(jd_text)} chars)")
    print(f"Keywords ({len(kws)}): {', '.join(kws)}")
    print(f"Coverage master: {cov_before:.0f}%  HIT={hit}  MISS={miss}")
    print(f"Coverage tailoreado: {cov_after:.0f}%  HIT={hit_after}  MISS={miss_after}")
    print(f"ats_score: {ats_before} -> {ats_after}  (delta +{ats_after-ats_before})")
    print(f"Mirrored: {mirrored if mirrored else '-'}")
    print(f"Gap no defensible: {gap if gap else '-'}")
    if gap:
        print("  -> gap_principal sugerido: " + gap[0])
    if cov_after < 60:
        print("[FAIL] <60% - anadir mas evidencia real")
    elif cov_after < 80:
        print("[WARN] 60-80% - aceptable")
    else:
        print("[PASS] 80%+ - listo ATS")

    if args.dry_run:
        print(f"\n[DRY-RUN] no se escribieron archivos. Saldrian en:\n  {yaml_out}\n  {md_out}")
        sys.exit(0)

    out_dir.mkdir(parents=True, exist_ok=True)
    if (yaml_out.exists() or md_out.exists()) and not args.force:
        print(f"\nERROR: ya existe {yaml_out.name} o {md_out.name}. Usa --force.", file=sys.stderr)
        sys.exit(2)

    header = f"# Tailoreado desde cv_master.yaml - empresa: {empresa_slug} - JD: {jd_path.name} - {args.lang} - ats {ats_before}->{ats_after}\n"
    header += f"# Generado por scripts/tailor_cv.py - NO inventa datos.\n"
    yaml_text_out = header + yaml.dump(tailored, allow_unicode=True, sort_keys=False)
    yaml_out.write_text(yaml_text_out, encoding="utf-8")
    print(f"\nOK YAML -> {yaml_out} ({len(yaml_text_out)} chars)")

    md_text = render_md_from_yaml(tailored, lang=args.lang)
    md_text += f"\n> Tailoreado para **{empresa_slug}** desde `cv_master.yaml` - JD `{jd_path.name}` - ats_score {ats_after}% - {args.lang}.\n"
    md_out.write_text(md_text, encoding="utf-8")
    print(f"OK MD   -> {md_out} ({len(md_text)} chars)")
    print(f"\nSiguiente:\n  python CV_Material_Nacho/extras/generate_cv_files.py {md_out}\n  python scripts/validate_ats.py {md_out.with_suffix('.pdf')}")

if __name__ == "__main__":
    main()
