"""Genera cv_master_es.md y cv_master_en.md desde cv_master.yaml (fuente única).

Uso:
  python CV_Material_Nacho/yaml_to_md.py
  python CV_Material_Nacho/yaml_to_md.py --check  # solo valida sin escribir

Mantiene honestidad: no inventa, solo reordena YAML.
"""
import sys
from pathlib import Path
import yaml  # type: ignore

BASE = Path(__file__).resolve().parent
YAML_PATH = BASE / "cv_master.yaml"
ES_OUT = BASE / "cv_master_es.md"
EN_OUT = BASE / "cv_master_en.md"


def render_es(data) -> str:
    b = data["basics"]
    lines = []
    lines.append("# CV MAESTRO — Español (Ignacio Palmeri)")
    lines.append("")
    lines.append("> Versión maestra generada desde `cv_master.yaml` (21/08/2026). Datos verificables.")
    lines.append("> Regla: honestidad verificable. Solo lo defendible en entrevista.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**{b['name']}**")
    lines.append(f"{b['location']} | {b['phone']} | {b['email']} | " + " | ".join(p["username"] for p in b["profiles"]))
    lines.append("")
    lines.append("## PERFIL PROFESIONAL")
    lines.append("")
    lines.append(f"{b['label']}. Construyo proyectos propios que combinan Python, APIs REST, bases de datos e integraciones con LLMs, y uso herramientas de IA para prototipar, revisar, testear y documentar — siempre validando el resultado. Sumo experiencia en atención al cliente y operaciones de alto tráfico, lo que me da criterio para entender problemas reales de soporte y procesos antes de automatizarlos. Busco una pasantía part-time (20 h semanales) en IA, automatización o IT donde pueda aprender construyendo.")
    lines.append("")
    lines.append("## EDUCACIÓN")
    lines.append("")
    for e in data["education"]:
        lines.append(f"**{e['area']} — {e['institution']}** | {e['startDate']} – {e['endDate']}")
        if "status" in e:
            lines.append(f"- {e['status']}. Promedio: {e.get('gpa','')}.")
        else:
            lines.append(f"- Promedio: {e.get('gpa','')}.")
        if e.get("details"):
            lines.append(f"- {e['details']}.")
        lines.append("")
    lines.append("## EXPERIENCIA")
    lines.append("")
    for x in data["experience"]:
        lines.append(f"**{x['position']} — {x['company']}** | {x['startDate']} – {x['endDate']}")
        for h in x["highlights"]:
            lines.append(f"- {h}.")
        lines.append("")
    lines.append("## PROYECTOS")
    lines.append("")
    for p in data["projects"]:
        lines.append(f"**{p['name']} — {p['role']}** | {p['startDate']}{(' – ' + p['endDate']) if p.get('endDate') else ''}")
        lines.append(" · ".join(p["keywords"]))
        for h in p["highlights"]:
            lines.append(f"- {h}.")
        if p.get("url"):
            lines.append(f"- Repositorio: {p['url']}")
        if p.get("demo"):
            lines.append(f"- Demo: {p['demo']}")
        lines.append("")
    lines.append("## PORTFOLIO")
    lines.append("")
    lines.append("- ignaciopalmeri.vercel.app — portfolio con proyectos, CV descargable y bitácora.")
    lines.append("- github.com/nachopalmeri — 28+ repos públicos.")
    lines.append("")
    lines.append("## COMPETENCIAS TÉCNICAS")
    lines.append("")
    for s in data["skills"]:
        lines.append(f"- **{s['category']}:** " + ", ".join(s["keywords"]))
    lines.append("")
    lines.append("## CERTIFICACIONES")
    lines.append("")
    for c in data["certifications"]:
        st = f" — {c['status']}" if c.get("status") else ""
        lines.append(f"- **{c['name']}** — {c['issuer']}, {c['date']}{st}.")
    lines.append(f"- Inglés: {data['languages'][1]['fluency']} (EF SET opcional).")
    lines.append("")
    lines.append("## IDIOMAS")
    lines.append("")
    for l in data["languages"]:
        lines.append(f"- {l['language']}: {l['fluency']}")
    lines.append("")
    lines.append("## DISPONIBILIDAD")
    lines.append("")
    lines.append(f"- {data['availability']['es']}")
    lines.append("")
    return "\n".join(lines)


def render_en(data) -> str:
    b = data["basics"]
    lines = []
    lines.append("# CV MASTER — English (Ignacio Palmeri)")
    lines.append("")
    lines.append("> Master generated from `cv_master.yaml` (21/08/2026). Verifiable facts only.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**{b['name']}**")
    lines.append(f"{b['location']} | {b['phone']} | {b['email']} | " + " | ".join(p["username"] for p in b["profiles"]))
    lines.append("")
    lines.append("## PROFILE")
    lines.append("")
    lines.append(f"{b['label_en']}. I build projects combining Python, REST APIs, databases and LLM integrations, and I use AI tools to prototype, review, test and document — always validating the result. I bring high-traffic customer-facing experience, which gives me judgment for real support and process problems before automating them. Seeking a part-time internship (20 h/week) in AI, automation or IT where I can learn by building.")
    lines.append("")
    lines.append("## EDUCATION")
    lines.append("")
    for e in data["education"]:
        area = e.get("area_en", e["area"])
        lines.append(f"**{area} — {e['institution']}** | {e['startDate']} – {e['endDate']}")
        status = e.get("status_en", e.get("status", ""))
        if status:
            lines.append(f"- {status}. GPA: {e.get('gpa','')}.")
        if e.get("details_en"):
            lines.append(f"- {e['details_en']}.")
        lines.append("")
    lines.append("## EXPERIENCE")
    lines.append("")
    for x in data["experience"]:
        pos = x.get("position_en", x["position"])
        lines.append(f"**{pos} — {x['company']}** | {x['startDate']} – {x['endDate']}")
        for h in x.get("highlights_en", x["highlights"]):
            lines.append(f"- {h}.")
        lines.append("")
    lines.append("## PROJECTS")
    lines.append("")
    for p in data["projects"]:
        role = p.get("role_en", p["role"])
        lines.append(f"**{p['name']} — {role}** | {p['startDate']}{(' – ' + p['endDate']) if p.get('endDate') else ''}")
        lines.append(" · ".join(p["keywords"]))
        for h in p.get("highlights_en", p["highlights"]):
            lines.append(f"- {h}.")
        if p.get("url"):
            lines.append(f"- Repo: {p['url']}")
        if p.get("demo"):
            lines.append(f"- Demo: {p['demo']}")
        lines.append("")
    lines.append("## TECHNICAL SKILLS")
    lines.append("")
    for s in data["skills"]:
        cat = s.get("category_en", s["category"])
        lines.append(f"- **{cat}:** " + ", ".join(s["keywords"]))
    lines.append("")
    lines.append("## CERTIFICATIONS")
    lines.append("")
    for c in data["certifications"]:
        st = f" — {c['status']}" if c.get("status") else ""
        lines.append(f"- **{c['name']}** — {c['issuer']}, {c['date']}{st}.")
    lines.append(f"- English: {data['languages'][1].get('fluency_en', data['languages'][1]['fluency'])}.")
    lines.append("")
    lines.append("## LANGUAGES")
    lines.append("")
    for l in data["languages"]:
        flu = l.get("fluency_en", l["fluency"])
        name = "Spanish" if l["language"] == "Español" else l["language"]
        lines.append(f"- {name}: {flu}")
    lines.append("")
    lines.append("## AVAILABILITY")
    lines.append("")
    lines.append(f"- {data['availability']['en']}")
    lines.append("")
    return "\n".join(lines)


def main():
    check_only = "--check" in sys.argv
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    es = render_es(data)
    en = render_en(data)
    if check_only:
        # Validar que no haya drift sin escribir
        cur_es = ES_OUT.read_text(encoding="utf-8") if ES_OUT.exists() else ""
        cur_en = EN_OUT.read_text(encoding="utf-8") if EN_OUT.exists() else ""
        if cur_es != es or cur_en != en:
            print("DRIFT: cv_master.yaml != cv_master_*.md — corré yaml_to_md.py sin --check")
            sys.exit(1)
        print("OK — YAML y MD en sync")
        return
    ES_OUT.write_text(es, encoding="utf-8")
    EN_OUT.write_text(en, encoding="utf-8")
    print(f"OK -> {ES_OUT.name} ({len(es)} chars)")
    print(f"OK -> {EN_OUT.name} ({len(en)} chars)")

if __name__ == "__main__":
    main()
