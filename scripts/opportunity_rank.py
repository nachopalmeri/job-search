"""Explainable, conservative ranking for enriched job advertisements.

Discovery is intentionally separate: this module never claims a job is current
or eligible when the source does not provide enough evidence. Scores are
decision aids, not hiring probabilities.
"""

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

TECH_GROUPS = {
    "python": r"\bpython\b",
    "sql": r"\bsql\b|bases? de datos|databases?",
    "linux": r"\blinux\b|\brhel\b|red hat",
    "redes": r"networking|tcp/ip|ccna|redes? inform[aá]ticas?(?!\s+sociales)|redes\s+de\s+(?:datos|computadoras)",
    "apis": r"\bapi\b|\brest\b|integraciones?",
    "automatizacion": r"automati[sz]|\brpa\b|automation",
    "datos": r"data|datos|analytics|an[aá]lisis|reporting|\bbi\b",
    "git": r"\bgit\b|github|control de versiones",
    "cloud": r"\bcloud\b|nube|vercel",
}
UNVERIFIED_TECH = {
    "power bi": r"power\s*bi", "sap": r"\bsap\b", "tableau": r"tableau",
    "angular": r"angular", "snowflake": r"snowflake", "docker": r"docker",
    "office 365": r"office\s*365|microsoft\s*365", "aws": r"\baws\b",
}
TECH_ROLES = re.compile(r"\b(?:it|sistemas?|tecnolog\w*|software|support|soporte|qa|testing|cloud|devops|data|datos|analytics|bi|automation|automat\w*|rpa|infra\w*|redes|network\w*|ai|ia|product\w*|producto\w*|cybersecurity|ciberseguridad|erp|sap|business systems|sistemas de negocio|digital transformation|transformaci[oó]n digital)\b", re.I)
BUSINESS_TECH = re.compile(r"business technology|negocios digitales|tecnolog.{0,30}negocio|transformaci[oó]n digital|business analyst|analista funcional|product operations|\bpmo\b|automatizaci[oó]n", re.I)
ROLE_EVIDENCE = re.compile(r"\b(?:sql|python|power\s*bi|tableau|snowflake|data analyst|data engineer|data analytics|analista de datos|ingenier[ií]a de datos|software engineer|software developer|desarrollador(?:a)?|programmer|qa|quality analyst|testing|test automation|service desk|help desk|it support|technical support|soporte t[eé]cnico|soporte inform[aá]tico|cloud|devops|cybersecurity|ciberseguridad|networking|tcp/ip|linux|red hat|automation|automatizaci[oó]n|rpa|ai adoption|ai operations|inteligencia artificial|machine learning|business systems|sistemas de negocio|erp|sap|business technology|transformaci[oó]n digital)\b", re.I)
ENTRY = re.compile(r"\b(?:pasant\w*|intern\w*|trainee|pr[aá]ctic\w*|aprendiz\w*|graduate|j[oó]venes|junior|jr|sin experiencia|primer empleo)\b", re.I)
SENIOR_TITLE = re.compile(r"\b(?:senior|sr\.?|ssr|lead|principal|manager|director)\b", re.I)
ADVANCED = re.compile(r"[uú]ltimos? (?:dos|2) a[nñ]os|[uú]ltimo a[nñ]o|estudiante avanzado|3(?:er|ro|°) a[nñ]o", re.I)
HIGH_ENGLISH = re.compile(r"ingl[eé]s (?:avanzado|fluido|biling[uü]e|c1|c2)|(?:fluent|advanced|native) english|english c1", re.I)
EXPERIENCE = re.compile(r"(?:m[ií]nimo\s+)?(\d+)\s*(?:\+\s*)?(?:a[nñ]os?|years?)\s+(?:(?:de|of)\s+)?experiencia|(?:de|of)\s+(\d+)\s+(?:a[nñ]os?|years?)\s+experiencia", re.I)
US_ONLY = re.compile(r"(?:us|usa|united states)\s+only|authorized to work in (?:the )?(?:us|usa|united states)", re.I)
CUSTOMER_OPS = re.compile(r"atenci[oó]n|clientes?|customer|operaciones?|operations|caja|gesti[oó]n de procesos|crm", re.I)


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", value).strip()


def _dimension(points, maximum, reason):
    return {"points": round(points, 1), "max": maximum, "reason": reason}


def rank(job, *, today=None):
    """Return eligibility, compatibility and priority with reasons.

    Supported inputs include the fields emitted by ``uade_import.py``. A
    human may add ``mandatory_gaps`` and ``verified_requirements`` after
    reading the complete original advertisement.
    """
    today = today or date.today()
    title = str(job.get("titulo") or job.get("title") or "")
    description = str(job.get("descripcion") or job.get("description") or "")
    text = f"{title}\n{description}"
    location = str(job.get("ubicacion") or job.get("location") or "")
    modality = str(job.get("modalidad") or job.get("modality") or "")
    schedule = str(job.get("jornada") or job.get("schedule") or "")
    posted_raw = str(job.get("fecha") or job.get("published_date") or "")
    reasons, gaps, unknown = [], list(job.get("mandatory_gaps") or []), []
    try:
        posted = date.fromisoformat(posted_raw[:10])
        age = (today - posted).days
        freshness = "primary" if 0 <= age <= 3 else ("secondary" if 4 <= age <= 14 else "outside_window")
    except ValueError:
        age, freshness = None, "unverified"
    if age is not None and age < 0:
        freshness = "unverified"
    if freshness == "unverified":
        unknown.append("fecha original de publicación")

    # Discovery is description-led: many student-accessible roles use generic
    # titles (operations, associate, coordinator) and mention technical work in
    # their responsibilities. Never let a title-only rule erase that evidence.
    target_role = bool(TECH_ROLES.search(title) or BUSINESS_TECH.search(title) or ROLE_EVIDENCE.search(description))
    known = [key for key, pattern in TECH_GROUPS.items() if re.search(pattern, text, re.I)]
    missing = [key for key, pattern in UNVERIFIED_TECH.items() if re.search(pattern, text, re.I)]
    tech_count = len(known) + len(missing)
    tech_points = 18 if not tech_count and target_role else (8 if not tech_count else 30 * len(known) / tech_count)
    technical = _dimension(tech_points, 30, f"Con evidencia: {', '.join(known) or 'ninguna tecnología explícita'}; por confirmar: {', '.join(missing) or 'ninguna'}")
    if missing:
        unknown.append("experiencia requerida en " + ", ".join(missing))

    if ADVANCED.search(description):
        academic = _dimension(2, 15, "El aviso menciona años finales o estudiante avanzado; Nacho cursa 2.º año")
        unknown.append("si aceptan estudiante de 2.º año")
    elif re.search(r"estudiante|universitari|carrera af[ií]n|pasant", text, re.I):
        academic = _dimension(13, 15, "Abierto a estudiantes o carreras afines; verificar carrera exacta")
        unknown.append("aceptación de Gestión de TI si no figura explícita")
    else:
        academic = _dimension(8, 15, "No se identificó requisito académico verificable")
        unknown.append("requisito académico")

    experience_years = [int(value) for match in EXPERIENCE.findall(description) for value in match if value]
    if experience_years and max(experience_years) >= 3:
        experience = _dimension(0, 10, f"Exige {max(experience_years)} años de experiencia")
        gaps.append("experiencia de 3+ años")
    elif SENIOR_TITLE.search(title) and not ENTRY.search(title):
        experience = _dimension(2, 10, "El título indica seniority alto o contradictorio; leer requisitos completos")
        unknown.append("seniority y experiencia exigida")
    elif re.search(r"sin experiencia|no se requiere experiencia|primera experiencia", description, re.I) or ENTRY.search(title):
        experience = _dimension(10, 10, "Orientado a primera experiencia")
    else:
        experience = _dimension(6, 10, "Experiencia mínima no confirmada")
        unknown.append("años de experiencia exigidos")

    learning = _dimension(10 if re.search(r"mentor|aprendizaje|capacitaci[oó]n|programa|pasant", text, re.I) else 5, 10,
                          "Programa de formación o pasantía" if re.search(r"mentor|aprendizaje|capacitaci[oó]n|programa|pasant", text, re.I) else "Aprendizaje no explicitado")
    trajectory = _dimension(10 if BUSINESS_TECH.search(text) else (8 if target_role else 0), 10,
                            "Cruce tecnología-negocio" if BUSINESS_TECH.search(text) else ("El aviso contiene evidencia de tareas IT/datos" if target_role else "Sin evidencia clara de tareas IT/datos"))

    place = _norm(f"{location} {modality}")
    if re.search(r"remote|remoto", place):
        location_dim = _dimension(10, 10, "Remoto; elegibilidad geográfica aún requiere confirmación")
    elif re.search(r"hibrid|parque patricios|caba|buenos aires", place):
        location_dim = _dimension(9, 10, "Híbrido o ubicación AMBA")
    elif re.search(r"f[aá]tima|pilar|munro|olivos", place):
        location_dim = _dimension(3, 10, "Traslado largo desde Temperley")
    else:
        location_dim = _dimension(5, 10, "Ubicación o modalidad por confirmar")
        unknown.append("ubicación y modalidad")

    hours = _norm(f"{schedule} {description[:3000]}")
    if re.search(r"20\s*(?:h|horas)|4\s*horas?\s*diarias", hours):
        schedule_dim = _dimension(10, 10, "Compatible con 20 horas semanales")
    elif re.search(r"part[- ]?time|media jornada|6\s*horas?\s*diarias", hours):
        schedule_dim = _dimension(6, 10, "Media jornada; confirmar horas y cursada")
    elif re.search(r"full[- ]?time|jornada completa|8\s*horas?\s*diarias", hours):
        schedule_dim = _dimension(2, 10, "Jornada completa; conflicto con disponibilidad ideal")
    else:
        schedule_dim = _dimension(5, 10, "Horario sin verificar")
        unknown.append("jornada")
    transfer = _dimension(5 if CUSTOMER_OPS.search(text) else 2, 5,
                          "Experiencia transferible de atención y operaciones" if CUSTOMER_OPS.search(text) else "Transferencia desde experiencia actual limitada")

    if HIGH_ENGLISH.search(description):
        unknown.append("inglés avanzado frente a B1 autoevaluado")
        if re.search(r"(?:ingl[eé]s|english).{0,35}(?:excluyente|mandatory|required)", description, re.I):
            gaps.append("inglés avanzado obligatorio")
    if US_ONLY.search(text):
        gaps.append("ubicación o autorización de trabajo exclusiva de EE. UU.")
    if job.get("closed") is True:
        gaps.append("convocatoria cerrada")

    dimensions = {
        "tecnica": technical, "academica": academic, "experiencia": experience,
        "aprendizaje": learning, "trayectoria": trajectory, "ubicacion": location_dim,
        "jornada": schedule_dim, "transferibles": transfer,
    }
    compatibility = round(sum(item["points"] for item in dimensions.values()))
    if not target_role:
        unknown.append("no se encontró evidencia de tareas IT/datos/negocio-tecnología")
    eligibility = "ineligible" if gaps else ("uncertain" if unknown else "eligible")
    eligibility_factor = {"eligible": 1.0, "uncertain": 0.7, "ineligible": 0.0}[eligibility]
    freshness_factor = {"primary": 1.0, "secondary": 0.6, "outside_window": 0.0, "unverified": 0.35}[freshness]
    # Compatibility describes fit; priority additionally reflects eligibility
    # and verified recency. Unknown role evidence remains reviewable, not zeroed.
    role_factor = 1.0 if target_role else 0.5
    priority = round(compatibility * eligibility_factor * freshness_factor * role_factor)
    reasons.append("Puntaje de compatibilidad, no probabilidad de contratación")
    return {
        "eligibility": eligibility, "compatibility": compatibility, "priority": priority,
        "freshness": freshness, "age_days": age, "dimensions": dimensions,
        "mandatory_gaps": gaps, "confirm": list(dict.fromkeys(unknown)), "why": reasons,
    }


def deduplicate(jobs):
    """Keep one logical job and preserve every observed source URL."""
    merged = {}
    for job in jobs:
        job_id = str(job.get("job_id") or "")
        if job.get("portal") == "uade" and job_id:
            key = f"uade:{job_id}"
        else:
            key = "|".join(_norm(job.get(field)) for field in ("empresa", "titulo", "ubicacion"))
            if not key.strip("|"):
                key = str(job.get("url") or "")
        if key not in merged:
            merged[key] = {**job, "source_urls": [job.get("url")] if job.get("url") else []}
        elif job.get("url") and job["url"] not in merged[key]["source_urls"]:
            merged[key]["source_urls"].append(job["url"])
    return list(merged.values())


def main():
    parser = argparse.ArgumentParser(description="Puntuar avisos completos de forma explicable")
    parser.add_argument("--input", type=Path, required=True, help="JSON array de avisos enriquecidos")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    jobs = deduplicate(json.loads(args.input.read_text(encoding="utf-8")))
    result = [{**job, "assessment": rank(job, today=args.today)} for job in jobs]
    result.sort(key=lambda job: (job["assessment"]["priority"], job["assessment"]["compatibility"]), reverse=True)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for job in result:
        score = job["assessment"]
        print(f"{score['priority']:3} prioridad | {score['compatibility']:3} encaje | {score['eligibility']:10} | {job.get('empresa') or 'Empresa sin verificar'} — {job.get('titulo')}")


if __name__ == "__main__":
    main()
