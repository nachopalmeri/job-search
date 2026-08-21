"""Keyword matcher ATS — compara JD vs CV y sugiere gap.

Uso:
  python scripts/keyword_match.py --jd "texto del aviso..." --cv CV_Material_Nacho/cv_master_es.md
  python scripts/keyword_match.py --jd-file aviso.txt --cv CV_Material_Nacho/extras/cvs_personalizados/cv_sap_ixp_oti.md

Extrae 8-12 keywords must-have del JD (frecuencia + lista curada IT) y calcula coverage en CV.
No usa LLM — heurística rápida; para tailoring fino usa prompt_multiagente_cv.md con Claude.
"""
import re
import sys
from pathlib import Path
from collections import Counter

# Diccionario curado IT/ATS 2026 — para no depender solo de frecuencia
CURATED = [
    "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
    "fastapi", "next.js", "react", "typescript", "javascript", "postgresql", "sqlite",
    "linux", "git", "github", "vercel", "railway", "bash", "docker",
    "llm", "claude", "groq", "gemini", "prompt engineering", "agent", "automatización", "automation",
    "etl", "api", "rest", "dashboard", "kpi", "bi", "data analysis", "analisis de datos",
    "m365", "microsoft 365", "outlook", "sharepoint", "servicedesk", "help desk", "soporte",
    "ccna", "red hat", "rhel", "jira", "confluence", "agile", "scrum",
]

STOP = set("de la el en y a los del con para por un una al se es que como sus del".split())


def tokenize(text: str) -> list[str]:
    text = text.lower()
    # Normalizar
    text = re.sub(r"[^a-z0-9áéíóúñ\+\.\#]", " ", text)
    toks = [t.strip(" .") for t in text.split() if t and t not in STOP and len(t) > 2]
    return toks


def extract_keywords(jd: str, top_k=12) -> list[str]:
    jd_low = jd.lower()
    found = []
    # 1) Curated presentes verbatim (prioridad)
    for kw in CURATED:
        if kw.lower() in jd_low:
            found.append(kw)
    # 2) Frecuencia de n-grams 1-2
    toks = tokenize(jd_low)
    bigrams = [" ".join(toks[i:i+2]) for i in range(len(toks)-1)]
    cnt = Counter(toks + bigrams)
    # Filtrar los ya encontrados y stop-bigrams repetidos
    for w, _ in cnt.most_common(30):
        if w not in found and len(w) > 3 and w not in STOP:
            # Evitar números sueltos
            if re.match(r"^\d+$", w):
                continue
            found.append(w)
        if len(found) >= top_k:
            break
    return found[:top_k]


def coverage(keywords: list[str], cv_text: str) -> tuple[float, list[str], list[str]]:
    cv_low = cv_text.lower()
    hit = [k for k in keywords if k.lower() in cv_low]
    miss = [k for k in keywords if k.lower() not in cv_low]
    cov = len(hit) / len(keywords) * 100 if keywords else 0
    return cov, hit, miss


def main():
    args = sys.argv[1:]
    jd_text = ""
    cv_path = None
    jd_file = None
    for i, a in enumerate(args):
        if a == "--jd" and i+1 < len(args):
            jd_text = args[i+1]
        if a == "--jd-file" and i+1 < len(args):
            jd_file = Path(args[i+1])
        if a == "--cv" and i+1 < len(args):
            cv_path = Path(args[i+1])
    if jd_file and jd_file.exists():
        jd_text = jd_file.read_text(encoding="utf-8")
    if not jd_text:
        print("Uso: python scripts/keyword_match.py --jd \"texto\" --cv <cv.md>  |  --jd-file aviso.txt --cv <cv.md>")
        sys.exit(1)
    if not cv_path or not cv_path.exists():
        # Fallback a master
        cv_path = Path("CV_Material_Nacho/cv_master_es.md")
        if not cv_path.exists():
            cv_path = Path("CV_Material_Nacho/cv_master.yaml")
    cv_text = Path(cv_path).read_text(encoding="utf-8") if cv_path.exists() else ""

    kws = extract_keywords(jd_text)
    cov, hit, miss = coverage(kws, cv_text)

    print(f"\nKeywords must-have ({len(kws)}): {', '.join(kws)}")
    print(f"Coverage vs {cv_path.name}: {cov:.0f}%  ({len(hit)}/{len(kws)})")
    print(f"  HIT : {', '.join(hit) if hit else '-'}")
    print(f"  MISS: {', '.join(miss) if miss else '- (todo cubierto)'}")
    print("")
    if cov < 60:
        print("[FAIL] <60% — reescribí bullets con keywords miss verbatim")
    elif cov < 80:
        print("[WARN] 60-80% — agregá 2-3 miss en skills + 1er bullet de experiencia")
    else:
        print("[PASS] 80%+ — listo para ATS (no hagas stuffing)")
    # Sugerencia tailoring
    if miss:
        print("\nSugerencia: añadí en SKILLS y en el 1er bullet de EXPERIENCIA/PROYECTOS:")
        for m in miss[:5]:
            print(f"  - ... {m} ...")
    sys.exit(0)

if __name__ == "__main__":
    main()
