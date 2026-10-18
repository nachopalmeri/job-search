"""Conservative ranking aligned with ``rubric-fit.md``.

Eligibility is a separate hard gate. The weighted fit score is a decision aid,
not a probability of being hired; uncertain evidence remains visible.
"""

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

try:
    from scripts.calendar_fit import parse_jornada, score_compat
    from scripts.opportunity_identity import canonical_url, identity_key, observation
except ImportError:  # direct execution from scripts/
    from calendar_fit import parse_jornada, score_compat
    from opportunity_identity import canonical_url, identity_key, observation


TECH_ROLES = re.compile(
    r"\b(?:it|sistemas?|tecnolog\w*|software|support|soporte|qa|testing|cloud|devops|data|datos|analytics|bi|automation|automat\w*|rpa|infra\w*|redes|network\w*|ai|ia|product\w*|producto\w*|cybersecurity|ciberseguridad|erp|sap|business systems|sistemas de negocio|digital transformation|transformaci[oó]n digital)\b",
    re.I,
)
BUSINESS_TECH = re.compile(
    r"business technology|negocios digitales|tecnolog.{0,30}negocio|transformaci[oó]n digital|business analyst|analista funcional|product operations|\bpmo\b|automatizaci[oó]n",
    re.I,
)
ROLE_EVIDENCE = re.compile(
    r"\b(?:sql|python|java|data analyst|data engineer|data analytics|analista de datos|ingenier[ií]a de datos|software engineer|software developer|desarrollador(?:a)?|programmer|qa|quality analyst|testing|service desk|help desk|it support|technical support|soporte t[eé]cnico|soporte inform[aá]tico|soporte\s+(?:it|inform[aá]tico)|cloud|devops|cybersecurity|ciberseguridad|networking|tcp/ip|linux|red hat|automation|automatizaci[oó]n|rpa|ai adoption|ai operations|inteligencia artificial|machine learning|business systems|erp|sap|business technology|transformaci[oó]n digital)\b",
    re.I,
)
ENTRY = re.compile(r"\b(?:pasant\w*|intern\w*|trainee|pr[aá]ctic\w*|aprendiz\w*|graduate|j[oó]venes|junior|jr|sin experiencia|primer empleo)\b", re.I)
SENIOR_TITLE = re.compile(r"\b(?:senior|sr\.?|staff|principal|lead|director|manager|head of)\b", re.I)
ADVANCED = re.compile(r"(?:[uú]ltimos? (?:dos|2) a[nñ]os|[uú]ltimo a[nñ]o|estudiante avanzado|3(?:er|ro|°) a[nñ]o)", re.I)
HIGH_ENGLISH = re.compile(r"(?:ingl[eé]s|english).{0,40}(?:avanzado|fluido|biling[uü]e|c1|c2|advanced|fluent|native)", re.I)
NATIVE_ENGLISH = re.compile(r"\b(?:near[- ]native|native)\s+(?:level\s+)?english\b|\benglish\s+(?:near[- ]native|native)\b", re.I)
MANDATORY = re.compile(r"excluyente|mandatory|required|must have|requisito obligatorio|requisito excluyente|solo se consider", re.I)
EXPERIENCE = re.compile(
    r"(?:at\s+least\s+|minimum\s+|min(?:imum)?\.?\s+|m[ií]nimo\s+)?"
    r"(\d+)\s*(?:[-–]\s*(\d+)\s*)?(?:\+\s*)?(?:a[nñ]os?|years?)\b"
    r"(?:\s+(?:of|de)\b)?[\w\s,;/()&+-]{0,70}?\b(?:experience|experiencia)\b"
    r"|(?:de|of)\s+(\d+)\s+(?:a[nñ]os?|years?)\s+experiencia",
    re.I,
)
MONTHS_EXPERIENCE = re.compile(
    r"(?:at\s+least\s+|minimum\s+|min(?:imum)?\.?\s+|m[ií]nimo\s+)?"
    r"(\d+)\s*(?:months?|meses?)\b[\w\s,;/()&+-]{0,70}?\b(?:experience|experiencia)\b|"
    r"(?:experience|experiencia)[\w\s,;/()&+-]{0,40}?"
    r"(?:at\s+least\s+|minimum\s+|m[ií]nimo\s+)?(\d+)\s*(?:months?|meses?)\b",
    re.I,
)
US_ONLY = re.compile(r"(?:us|usa|united states)\s+only|authorized to work in (?:the )?(?:us|usa|united states)", re.I)

# This list is intentionally limited to evidence in profile.md and the user's
# stated target profile. Skills not listed here are not credited as experience.
PROFILE_SKILLS = {
    "python": r"\bpython\b",
    "java": r"\bjava\b",
    "sql": r"\bsql\b",
    "linux": r"\blinux\b|\bcli\b|red hat",
    "networks": r"network|redes|tcp/ip|ccna",
    "api": r"\bapi\b|\brest\b|integraci[oó]n",
    "automation": r"automatiz|automation|\brpa\b|jobbot",
    "data": r"\bdata\b|datos|analytics|estad[ií]stic|monte carlo|prode",
    "git": r"\bgit\b|github|versionado",
    "cloud": r"\bcloud\b|nube|vercel",
    "web": r"web|javascript|typescript|react|html|css|portfolio|portfolio",
    "operations": r"operaciones?|atenci[oó]n al cliente|caja|customer service",
    "excel": r"\bexcel\b",
    # Foundational training supports entry-level support work but is not
    # treated as prior professional service-desk experience.
    "support": r"red hat|rh124|ccna|linux|soporte (?:it|inform[aá]tico)",
    "windows_m365": r"windows|microsoft\s*365|office\s*365|m365",
}
SKILL_TERMS = {
    "python": r"\bpython\b",
    "java": r"\bjava\b",
    "sql": r"\bsql\b|bases? de datos|databases?",
    "linux": r"\blinux\b|\brhel\b|red hat",
    "networks": r"networking|tcp/ip|ccna|redes? inform[aá]ticas?",
    "api": r"\bapi\b|\brest\b|integraciones?",
    "automation": r"automati[sz]|\brpa\b|automation",
    "data": r"data|datos|analytics|an[aá]lisis|reporting|\bbi\b",
    "git": r"\bgit\b|github|control de versiones",
    "cloud": r"\bcloud\b|nube|vercel|aws|azure",
    "web": r"web development|desarrollo web|javascript|typescript|react|html|css|node\.js",
    "support": r"service desk|help desk|it support|technical support|soporte t[eé]cnico|soporte inform[aá]tico|microinform[aá]tica",
    "qa": r"\bqa\b|quality analyst|testing|test automation",
    "power_bi": r"power\s*bi",
    "tableau": r"tableau",
    "sap": r"\bsap\b",
    "snowflake": r"snowflake",
    "docker": r"docker",
    "aws": r"\baws\b|amazon web services",
    "excel": r"\bexcel\b",
    "windows_m365": r"windows|microsoft\s*365|office\s*365|m365",
}

PROFILE_PATH = Path(__file__).resolve().parent.parent / "profile.md"
try:
    PROFILE_TEXT = PROFILE_PATH.read_text(encoding="utf-8")
except OSError:
    PROFILE_TEXT = ""

WEIGHTS = {
    "evidencia_cv": 0.40,
    "jornada": 0.25,
    "compatibilidad_calendar": 0.15,
    "carrera": 0.15,
    "demanda": 0.05,
}
SATISFIED = {"met", "satisfied", "eligible", "confirmed", "passed", "open", "current", "verified_satisfied"}
UNMET = {"unmet", "not_met", "failed", "unsatisfied", "ineligible", "not_eligible"}


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", value).strip()


def _dimension(score, reason):
    score = round(max(1.0, min(5.0, float(score))), 2)
    return {"score": score, "weight": WEIGHTS.get("_active", 0), "reason": reason}


def _requirement_key(value):
    text = _norm(value)
    if re.search(r"date|publicaci|posted|fecha original|publication", text): return "publication_date"
    if re.search(r"vigencia|status|cierre|cerrad|open|active|current", text): return "validity"
    if re.search(r"ubicaci|location|country|pa[ií]s|argentina|remote|remoto", text): return "location"
    if re.search(r"horario|jornada|schedule|availability|disponibilidad|hours", text): return "schedule"
    if re.search(r"career|carrera|academic|estudiante|a[nñ]o|degree", text): return "academic"
    if re.search(r"experien|seniority|seniority", text): return "experience"
    if re.search(r"english|ingl[eé]s", text): return "english"
    if re.search(r"role|funciones|tareas|responsabil", text): return "role"
    return text


def _verified_map(job):
    raw = job.get("verified_requirements") or {}
    entries = []
    if isinstance(raw, dict):
        entries = [{"requirement": key, **(value if isinstance(value, dict) else {"met": value})} for key, value in raw.items()]
    elif isinstance(raw, list):
        entries = [item if isinstance(item, dict) else {"requirement": item, "status": "verified"} for item in raw]
    result = {}
    for entry in entries:
        key = _requirement_key(entry.get("requirement") or entry.get("name") or entry.get("key") or "")
        state = _norm(entry.get("status") or "")
        met = entry.get("met", entry.get("satisfied"))
        if met is True or state in SATISFIED:
            result[key] = "met"
        elif met is False or state in UNMET:
            result[key] = "unmet"
        elif key:
            result[key] = "verified_fact"
    return result


def _verification_records(job):
    raw = job.get("verified_requirements") or {}
    entries = []
    if isinstance(raw, dict):
        entries = [{"requirement": key, **(value if isinstance(value, dict) else {"met": value})} for key, value in raw.items()]
    elif isinstance(raw, list):
        entries = [item if isinstance(item, dict) else {"requirement": item, "status": "verified"} for item in raw]
    fields = ("requirement", "name", "key", "status", "met", "satisfied", "evidence", "source", "source_url", "verified_at")
    return [{key: item[key] for key in fields if key in item} for item in entries]


def _freshness(job, today):
    posted_raw = str(job.get("fecha") or job.get("published_date") or "")[:10]
    try:
        posted = date.fromisoformat(posted_raw)
    except ValueError:
        return None, "unverified"
    # A checked fact is not proof that the date came from the original posting.
    # Only the explicit pipeline flag (backed by source evidence) qualifies.
    date_verified = job.get("publication_date_verified") is True
    if not date_verified or posted > today:
        return None, "unverified"
    age = (today - posted).days
    return age, "primary" if age <= 3 else ("secondary" if age <= 14 else "outside_window")


def _closed(job):
    if job.get("closed") is True:
        return True
    if isinstance(job.get("closed"), str) and _norm(job["closed"]) in {"true", "yes", "1", "closed", "expired", "filled", "cerrado", "vencido", "cubierto"}:
        return True
    status = _norm(job.get("posting_status") or job.get("job_status") or job.get("estado_aviso") or "")
    return status in {"closed", "expired", "filled", "cerrado", "vencido", "cubierto", "no longer accepting applications"}


def _work_hours_score(job, text):
    hours = _norm(f"{job.get('jornada') or job.get('schedule') or ''} {text[:3000]}")
    if re.search(r"20\s*(?:h|horas)|4\s*horas?\s*diarias|part[- ]?time.{0,40}(?:20|4\s*horas)", hours):
        return 5.0, "Part-time de ~20 h; coincide con la disponibilidad objetivo"
    if re.search(r"part[- ]?time|media jornada|6\s*horas?\s*diarias", hours):
        return 4.0, "Part-time; falta confirmar cantidad/distribución de horas"
    if re.search(r"full[- ]?time|jornada completa|8\s*horas?\s*diarias", hours):
        remote_flexible = re.search(r"remote|remoto|flexible|flexibilidad", hours)
        return (3.0 if remote_flexible else 2.0), "Full-time no es veto; considerar el choque con cursada y traslados"
    return 3.0, "Jornada no publicada o no verificada"


def _evidence_score(text, target_role, profile_text):
    requirements = [key for key, pattern in SKILL_TERMS.items() if re.search(pattern, text, re.I)]
    if not requirements:
        return (3.0 if target_role else 1.0), "El aviso no identifica competencias concretas para comparar"
    # Job requirements and candidate evidence must be matched across separate
    # documents. Searching the job description for its own keywords inflated
    # every role that mentioned a skill.
    evidenced = [
        key for key in requirements
        if key in PROFILE_SKILLS and re.search(PROFILE_SKILLS[key], profile_text, re.I)
    ]
    ratio = len(evidenced) / len(requirements)
    score = 1 + 4 * ratio
    reason = f"Evidencia alineada: {', '.join(evidenced) or 'ninguna'}; requisitos detectados: {', '.join(requirements)}"
    return score, reason


def rank(job, *, today=None):
    """Score against rubric-fit.md, while keeping mandatory eligibility separate.

    ``verified_requirements`` accepts a mapping or list of objects. An item is
    satisfied only with ``met: true``/``satisfied: true`` or a status such as
    ``met``, ``satisfied``, ``eligible``, ``open`` or ``current``. A bare
    ``verified`` status means the fact was checked, not that the candidate met it.
    """
    today = today or date.today()
    title = str(job.get("titulo") or job.get("title") or "")
    description = str(job.get("descripcion") or job.get("description") or "")
    text = f"{title}\n{description}"
    place = _norm(f"{job.get('ubicacion') or job.get('location') or ''} {job.get('modalidad') or job.get('modality') or ''}")
    schedule = str(job.get("jornada") or job.get("schedule") or "")
    verified = _verified_map(job)
    confirm, gaps, reasons = [], [], []
    age, freshness = _freshness(job, today)

    target_role = bool(TECH_ROLES.search(title) or BUSINESS_TECH.search(title) or ROLE_EVIDENCE.search(description))
    candidate_profile = str(job.get("profile_text") or job.get("candidate_profile") or PROFILE_TEXT)
    evidence_score, evidence_reason = _evidence_score(text, target_role, candidate_profile)
    schedule_score, schedule_reason = _work_hours_score(job, text)

    # Use the shared life-context schedule checker when the advertisement gives
    # an explicit time interval. Unknown hours remain neutral and reviewable.
    parsed_hours = parse_jornada(schedule) or parse_jornada(description[:3000])
    if parsed_hours:
        normalized_range = f"{parsed_hours[0].hour:02d}:{parsed_hours[0].minute:02d}-{parsed_hours[1].hour:02d}:{parsed_hours[1].minute:02d}"
        raw_calendar = score_compat(normalized_range)
        calendar_score = 1 + 4 * raw_calendar / 100
        calendar_reason = f"Compatibilidad calculada con calendario semanal ({raw_calendar}/100)"
        if raw_calendar == 0:
            gaps.append("horario explícitamente superpuesto con la cursada UADE")
    else:
        calendar_score, calendar_reason = 3.0, "Horario exacto sin verificar; no se presume compatibilidad"
        confirm.append("compatibilidad horaria real")

    if re.search(r"\b(?:ai|ia|data|datos|analytics|software|developer|development|qa|testing|it|sistemas?|support|soporte|cloud|devops|network|infra|business analyst|analista funcional|automatiz)\b", text, re.I):
        career_score = 5.0 if target_role else 3.5
        career_reason = "Tareas vinculadas a tecnología/datos/IA o cruce negocio-tecnología"
    else:
        career_score, career_reason = 1.0, "No aparece una relación clara con la trayectoria IT/IA"

    demand = job.get("demand_score")
    try:
        demand_score = max(1.0, min(5.0, float(demand))) if demand is not None else 3.0
        demand_reason = "Señal externa explícita; solo ordena oportunidades" if demand is not None else "Neutral: no hay señal de demanda comparable"
    except (TypeError, ValueError):
        demand_score, demand_reason = 3.0, "Señal de demanda inválida; se usa neutral"

    if age is None:
        confirm.append("fecha original de publicación")
    if SENIOR_TITLE.search(title) and not ENTRY.search(title):
        confirm.append("seniority del título sugiere experiencia; revisar los años y el carácter obligatorio en la descripción original")
    status = _norm(job.get("posting_status") or job.get("job_status") or "")
    if status not in {"open", "active", "current", "published", "accepting applications"} and job.get("closed") is not False:
        confirm.append("vigencia del aviso")
    if not place:
        confirm.append("ubicación y elegibilidad geográfica")
    elif re.search(r"remote|remoto|worldwide|latam", place) and not re.search(r"argentina|argentin|worldwide|global", place):
        confirm.append("elegibilidad geográfica para Argentina")
    if not schedule:
        confirm.append("jornada")

    required_years = [int(v) for match in EXPERIENCE.findall(description) for v in match if v]
    if required_years and max(required_years) >= 3:
        # A seniority expectation is a hard veto only when the same sentence
        # clearly makes it mandatory. Preferred/ambiguous years stay reviewable.
        year_context = " ".join(
            sentence for sentence in re.split(r"(?<=[.!?;])\s+|\n+", description)
            if EXPERIENCE.search(sentence)
        )
        preferred = re.search(r"prefer(?:red|able)?|deseable|valorad[oa]|nice to have|plus|ideal(?:mente)?", year_context, re.I)
        mandatory_years = (
            MANDATORY.search(year_context)
            or re.search(r"\b(?:require[sd]?|requires?|must have|minimum|min(?:imum)?\.?|m[ií]nimo)\b", year_context, re.I)
            or re.search(r"\d+\s*\+\s*(?:years?|a[nñ]os?)", year_context, re.I)
        )
        if mandatory_years and not preferred:
            gaps.append(f"exige {max(required_years)} años de experiencia profesional")
        else:
            confirm.append(f"confirmar si los {max(required_years)} años de experiencia son excluyentes o deseables")
    required_months = [int(v) for match in MONTHS_EXPERIENCE.findall(description) for v in match if v]
    if required_months and verified.get("experience") != "met":
        confirm.append(f"verificar experiencia relacionada de al menos {max(required_months)} meses")
    elif ADVANCED.search(description):
        if MANDATORY.search(description):
            gaps.append("exige cursar año avanzado/tercero como requisito obligatorio")
        else:
            confirm.append("si aceptan estudiante de 2.º año ante mención de año avanzado")
    if HIGH_ENGLISH.search(description) or NATIVE_ENGLISH.search(description):
        if MANDATORY.search(description):
            gaps.append("inglés avanzado/fluidо excluyente; el perfil tiene B1 autoevaluado")
        else:
            confirm.append("nivel de inglés requerido; el aviso menciona nivel avanzado")
    if US_ONLY.search(text):
        gaps.append("elegibilidad laboral/ubicación exclusiva de EE. UU.")
    if re.search(r"fuera de (?:argentina|amba)|relocation required|must relocate", text, re.I) and not re.search(r"remote|remoto", text, re.I):
        gaps.append("ubicación fuera de AMBA/Argentina sin modalidad remota")
    if _closed(job):
        gaps.append("convocatoria cerrada o vencida")

    # Verified statuses can resolve a pending check. They never erase a
    # contradictory explicit hard gap or an explicit closed flag.
    if verified.get("publication_date") == "met": confirm = [v for v in confirm if _requirement_key(v) != "publication_date"]
    resolution = {
        "validity": "vigencia", "location": "ubicación", "schedule": "jornada",
        "academic": "estudiante", "experience": "experiencia", "english": "inglés",
        "role": "tareas",
    }
    for key, needle in resolution.items():
        state = verified.get(key)
        if state == "met":
            confirm = [item for item in confirm if needle not in _norm(item)]
            if key == "schedule":
                confirm = [item for item in confirm if "horaria real" not in _norm(item)]
        elif state == "unmet":
            label = f"requisito obligatorio no cumplido: {key}"
            if label not in gaps:
                gaps.append(label)

    for item in job.get("mandatory_gaps") or []:
        label = str(item).strip()
        if not label:
            continue
        key = _requirement_key(label)
        if verified.get(key) == "met":
            continue
        if label not in gaps:
            gaps.append(label)

    dimensions = {
        "evidencia_cv": {"score": round(evidence_score, 2), "weight": WEIGHTS["evidencia_cv"], "reason": evidence_reason},
        "jornada": {"score": schedule_score, "weight": WEIGHTS["jornada"], "reason": schedule_reason},
        "compatibilidad_calendar": {"score": round(calendar_score, 2), "weight": WEIGHTS["compatibilidad_calendar"], "reason": calendar_reason},
        "carrera": {"score": career_score, "weight": WEIGHTS["carrera"], "reason": career_reason},
        "demanda": {"score": demand_score, "weight": WEIGHTS["demanda"], "reason": demand_reason},
    }
    fit_potential = round(sum(item["score"] * item["weight"] for item in dimensions.values()), 2)
    eligibility = "ineligible" if gaps else ("uncertain" if confirm else "eligible")
    fit_score = 0.0 if eligibility == "ineligible" else fit_potential
    freshness_factor = {"primary": 1.0, "secondary": 0.6, "outside_window": 0.0, "unverified": 0.35}[freshness]
    eligibility_factor = {"eligible": 1.0, "uncertain": 0.7, "ineligible": 0.0}[eligibility]
    priority = round(fit_score * 20 * freshness_factor * eligibility_factor)
    compatibility_percent = round(fit_score * 20)
    reasons.append("Fit 1–5 calculado con rubric-fit.md; no estima probabilidad de contratación")
    confirmed = _verification_records(job)
    if job.get("publication_date_verified") is True and job.get("publication_date_evidence"):
        confirmed.append({"requirement": "publication_date", "status": "verified", "evidence": job["publication_date_evidence"]})
    inferred = [
        {"field": "target_role", "value": target_role, "basis": "title/description keyword rules"},
        {"field": "skill_evidence", "value": evidence_reason, "basis": "profile-skill crosswalk; review against CV bullets"},
    ]
    return {
        "eligibility": eligibility,
        "fit_score": fit_score,
        "fit_potential": fit_potential,
        "compatibility": compatibility_percent,  # legacy 0–100 field
        "priority": priority,
        "freshness": freshness,
        "age_days": age,
        "dimensions": dimensions,
        "mandatory_gaps": gaps,
        "confirm": list(dict.fromkeys(confirm)),
        "verification": {"confirmed": confirmed, "inferred": inferred, "pending": list(dict.fromkeys(confirm))},
        "why": reasons,
    }


def deduplicate(jobs):
    """Merge only stable IDs or exact canonical URLs; preserve all observations."""
    merged, url_index = {}, {}
    for job in jobs:
        key, confidence = identity_key(job)
        url_key = canonical_url(job.get("url") or job.get("link"))
        # The same exact posting URL can join cross-source observations, but
        # distinct IDs from one source remain distinct requisitions.
        existing_key = url_index.get(url_key) if url_key else None
        if key not in merged and existing_key:
            previous = merged[existing_key]
            old_source = _norm(previous.get("portal"))
            new_source = _norm(job.get("portal"))
            old_id, new_id = str(previous.get("job_id") or ""), str(job.get("job_id") or "")
            if old_source != new_source or old_id == new_id:
                key = existing_key
        if key not in merged:
            first = {**job}
            first["identity_confidence"] = confidence
            first["source_urls"] = list(dict.fromkeys([*(job.get("source_urls") or []), *([job.get("url")] if job.get("url") else [])]))
            first["source_job_ids"] = list(dict.fromkeys([*(job.get("source_job_ids") or []), *([str(job.get("job_id"))] if job.get("job_id") else [])]))
            first["source_records"] = [observation(job)]
            merged[key] = first
            if url_key:
                url_index[url_key] = key
            continue
        target = merged[key]
        for field in ("source_urls", "source_job_ids"):
            target.setdefault(field, [])
        url = job.get("url")
        job_id = str(job.get("job_id") or "")
        if url and url not in target["source_urls"]: target["source_urls"].append(url)
        if job_id and job_id not in target["source_job_ids"]: target["source_job_ids"].append(job_id)
        record = observation(job)
        if record not in target.setdefault("source_records", []): target["source_records"].append(record)
        if url_key:
            url_index[url_key] = key
        for field in ("descripcion", "description"):
            if len(str(job.get(field) or "")) > len(str(target.get(field) or "")):
                target[field] = job[field]
    return list(merged.values())


def main():
    parser = argparse.ArgumentParser(description="Puntuar avisos completos de forma explicable")
    parser.add_argument("--input", type=Path, required=True, help="JSON array de avisos enriquecidos")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    jobs = deduplicate(json.loads(args.input.read_text(encoding="utf-8")))
    result = [{**job, "assessment": rank(job, today=args.today)} for job in jobs]
    result.sort(key=lambda job: (job["assessment"]["priority"], job["assessment"]["fit_score"]), reverse=True)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for job in result:
        score = job["assessment"]
        print(f"{score['priority']:3} prioridad | {score['fit_score']:0.1f}/5 fit | {score['eligibility']:10} | {job.get('empresa') or 'Empresa sin verificar'} — {job.get('titulo')}")


if __name__ == "__main__":
    main()
