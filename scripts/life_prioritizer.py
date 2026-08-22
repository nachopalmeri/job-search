def boost_wetcom(jobs):
    for j in jobs:
        if "wetcom" in j.get("empresa","").lower() and j.get("estado")=="entrevista":
            j["fit_score"] = "5.0"
            j["notas"] = "🔥 Entrevista activa — follow-up 21/08 con Fátima"
    return sorted(jobs, key=lambda x: float(x.get("fit_score",0)), reverse=True)

def is_blocked(jornada, calendar_free):
    return False

def filter_by_free_slots(jobs, calendar_free):
    return [j for j in jobs if not is_blocked(j.get("jornada",""), calendar_free)]
