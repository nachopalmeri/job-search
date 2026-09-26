"""Genera el tracker de postulaciones en Excel (se sube a Drive y se guarda como Google Sheets).

Lee tracker/postulaciones.csv (espejo de la Google Sheet) y tracker/contactos.csv.
Uso:  python scripts/tracker_xlsx.py [salida.xlsx]      (requiere openpyxl)
No depende de Claude: el archivo resultante es de Nacho y funciona sin suscripción.
"""
import csv, datetime, sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule, ColorScaleRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as L
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
POST_CSV = ROOT / "tracker" / "postulaciones.csv"
CONTACTS_CSV = ROOT / "tracker" / "contactos.csv"
OUT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "tracker" / "Postulaciones_Ignacio_Palmeri.xlsx")
with open(POST_CSV, encoding="utf-8", newline="") as fh:
    docs = list(csv.DictReader(fh))
MAXR = 400  # filas preparadas con fórmulas y validaciones

INK, MUTED, LINE, BG = "17201D", "5E6B66", "DEE3DF", "F3F4F1"
ACCENT, ACCENT_SOFT = "2F55D4", "E6ECFF"
C = {"ok": ("1D7A4E", "E1F3E9"), "warn": ("A85E00", "FDF0DC"), "bad": ("B42F2F", "FBE4E2"),
     "info": ("6146B8", "EEE9FB"), "idle": ("5E6B66", "ECEFEC"), "acc": (ACCENT, ACCENT_SOFT)}
fill = lambda h: PatternFill("solid", start_color=h, end_color=h)
thin = Side(style="thin", color=LINE)
F = "Arial"

ESTADOS = ["Para postular", "Postulada", "Contactado", "Entrevista", "Prueba técnica", "Oferta", "Rechazada", "Descartada", "Retirada"]
CANALES = ["Postulación directa", "Recomendación", "Networking", "Mensaje en frío"]
FUENTES = ["LinkedIn", "Portal UADE", "Portal empresa", "BecasIT", "Startups Argentina", "Referido", "Bumeran",
           "Computrabajo", "Universia", "FirstJob", "Email", "YC / Speedrun", "Otro"]
MODALIDADES = ["Remoto", "Híbrido", "Presencial", "No informado"]
PRIORIDADES = ["Alta", "Media", "Baja"]

def d(iso):
    return datetime.date.fromisoformat(iso) if iso else None

wb = Workbook()

# ---------------- Listas ----------------
wl = wb.active
wl.title = "Listas"
for ci, (h, vals) in enumerate([("Estados", ESTADOS), ("Canal", CANALES), ("Fuente", FUENTES),
                                ("Modalidad", MODALIDADES), ("Prioridad", PRIORIDADES),
                                ("Días para follow-up", [3]), ("Días para 'sin movimiento'", [14])], 1):
    wl.cell(1, ci, h).font = Font(name=F, bold=True)
    for ri, v in enumerate(vals, 2):
        wl.cell(ri, ci, v).font = Font(name=F)
    wl.column_dimensions[L(ci)].width = 24
wl.sheet_properties.tabColor = "C9D0CB"

# ---------------- Postulaciones ----------------
ws = wb.create_sheet("Postulaciones", 0)
COLS = [  # (encabezado, clave, ancho, tipo)
    ("N°", "n", 5, "n"),
    ("Empresa", "empresa", 24, "t"),
    ("Puesto", "puesto", 38, "w"),
    ("Estado", "estado", 15, "t"),
    ("Seguimiento", None, 18, "f_seg"),
    ("Fecha postulación", "fecha_postulacion", 13, "d"),
    ("Última interacción", "ultima_interaccion", 13, "d"),
    ("Días sin mov.", None, 9, "f_dias"),
    ("Próxima acción", "proxima_accion", 34, "w"),
    ("Link del aviso", "link", 30, "url"),
    ("Dónde la encontré", "fuente", 17, "t"),
    ("Canal", "canal", 18, "t"),
    ("Recomendado por / networking", "referido", 26, "w"),
    ("Descripción del puesto", "descripcion", 48, "w"),
    ("CV usado", "cv", 32, "w"),
    ("Ruta / link del CV", "cv_ruta", 40, "w"),
    ("Mensaje o carta", "carta", 28, "w"),
    ("Modalidad", "modalidad", 12, "t"),
    ("Ubicación", "ubicacion", 22, "w"),
    ("Jornada / horario", "jornada", 24, "w"),
    ("Remuneración", "remuneracion", 22, "w"),
    ("Fit (1-5)", "fit", 8, "fit"),
    ("Prioridad", "prioridad", 10, "t"),
    ("Área", "area", 26, "w"),
    ("Fecha límite", "fecha_limite", 12, "d"),
    ("Contacto", "contacto.nombre", 20, "t"),
    ("Cargo del contacto", "contacto.cargo", 20, "t"),
    ("Email / LinkedIn contacto", "contacto.email", 26, "t"),
    ("Etapa / resultado", "etapa", 30, "w"),
    ("Historial", "historial", 44, "w"),
    ("Notas", "notas", 44, "w"),
    ("Motivo de cierre", "motivo_cierre", 26, "w"),
]
idx = {h: i + 1 for i, (h, *_ ) in enumerate(COLS)}
col = lambda h: L(idx[h])
HDR = 3

ws["A1"] = "Postulaciones · Ignacio Palmeri"
ws["A1"].font = Font(name=F, size=18, bold=True, color=INK)
ws["A2"] = ("Una fila por postulación. Completá Estado, fechas, Link, Dónde la encontré, Canal y CV. "
            "Seguimiento y Días sin movimiento se calculan solos (follow-up a los 3 días, 'sin movimiento' a los 14).")
ws["A2"].font = Font(name=F, size=10, color=MUTED)
ws.row_dimensions[1].height = 30

for i, (h, key, w, typ) in enumerate(COLS, 1):
    c = ws.cell(HDR, i, h)
    c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
    c.fill = fill(INK)
    c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.column_dimensions[L(i)].width = w
ws.row_dimensions[HDR].height = 32

def val(p, key):
    if key == "historial":  # en el CSV: una línea por movimiento, "AAAA-MM-DD · texto"
        out = []
        for line in (p.get("historial") or "").splitlines():
            f_, _, t = line.partition(" · ")
            try:
                f_ = datetime.date.fromisoformat(f_.strip()).strftime("%d/%m/%y")
            except ValueError:
                pass
            out.append(f"{f_} · {t}" if t else line)
        return "\n".join(out) or None
    if key.startswith("contacto."):
        return p.get("contacto_" + key.split(".")[1]) or None
    if key == "fit":
        return float(p["fit"]) if p.get("fit") else None
    return p.get(key) or None

# orden: más reciente primero, igual que lo usarías
def last_touch(p):
    return max(filter(None, [p.get("fecha_postulacion"), p.get("ultima_interaccion")]), default="")
docs.sort(key=lambda p: (last_touch(p), -int(p.get("n") or 0)), reverse=True)

E, Fp, G, Y = col("Estado"), col("Fecha postulación"), col("Última interacción"), col("Fecha límite")
B = col("Empresa")
for r in range(HDR + 1, HDR + 1 + MAXR):
    p = docs[r - HDR - 1] if r - HDR - 1 < len(docs) else None
    for i, (h, key, w, typ) in enumerate(COLS, 1):
        c = ws.cell(r, i)
        c.font = Font(name=F, size=10, color=INK)
        c.alignment = Alignment(vertical="top", wrap_text=(typ == "w"))
        c.border = Border(bottom=thin)
        if typ == "f_seg":
            last = f"MAX({Fp}{r},{G}{r})"
            c.value = (f'=IF({B}{r}="","",IF({E}{r}="Para postular",IF(AND({Y}{r}<>"",{Y}{r}<TODAY()),"Aviso vencido","Pendiente de enviar"),'
                       f'IF(OR({E}{r}="Oferta",{E}{r}="Rechazada",{E}{r}="Descartada",{E}{r}="Retirada"),"Cerrada",'
                       f'IF({last}=0,"Falta fecha",IF(OR({E}{r}="Entrevista",{E}{r}="Prueba técnica"),'
                       f'IF(TODAY()-{last}>=Listas!$F$2,"Revisar","En curso"),'
                       f'IF(TODAY()-{last}>=Listas!$G$2,"Sin movimiento",IF(TODAY()-{last}>=Listas!$F$2,"Hacer follow-up","Esperar")))))))')
            c.font = Font(name=F, size=10, bold=True)
        elif typ == "f_dias":
            c.value = f'=IF(OR({B}{r}="",MAX({Fp}{r},{G}{r})=0),"",TODAY()-MAX({Fp}{r},{G}{r}))'
            c.alignment = Alignment(horizontal="center", vertical="top")
        elif p is not None:
            v = val(p, key)
            if typ == "d":
                v = d(v)
                c.number_format = "dd/mm/yyyy"
                c.alignment = Alignment(horizontal="center", vertical="top")
            elif typ == "fit":
                c.number_format = "0.0"
                c.alignment = Alignment(horizontal="center", vertical="top")
            elif typ == "url" and v:
                c.hyperlink = v
                c.font = Font(name=F, size=10, color=ACCENT, underline="single")
            elif typ == "n":
                c.alignment = Alignment(horizontal="center", vertical="top")
            if key == "empresa":
                c.font = Font(name=F, size=10, bold=True, color=INK)
            c.value = v if v not in ("", None) else None
        elif typ == "d":
            c.number_format = "dd/mm/yyyy"
    if p is not None:
        ws.cell(r, 1).value = r - HDR

ws.freeze_panes = ws.cell(HDR + 1, idx["Estado"])  # fija encabezado + N°/Empresa/Puesto
ws.auto_filter.ref = f"A{HDR}:{L(len(COLS))}{HDR + len(docs)}"
last_row = HDR + MAXR

def dv(formula, colname, prompt=None):
    v = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=False)
    if prompt:
        v.promptTitle, v.prompt = colname, prompt
    ws.add_data_validation(v)
    v.add(f"{col(colname)}{HDR+1}:{col(colname)}{last_row}")
dv(f"Listas!$A$2:$A${1+len(ESTADOS)}", "Estado")
dv(f"Listas!$B$2:$B${1+len(CANALES)}", "Canal")
dv(f"Listas!$C$2:$C${1+len(FUENTES)}", "Dónde la encontré")
dv(f"Listas!$D$2:$D${1+len(MODALIDADES)}", "Modalidad")
dv(f"Listas!$E$2:$E${1+len(PRIORIDADES)}", "Prioridad")
fv = DataValidation(type="decimal", operator="between", formula1="1", formula2="5", allow_blank=True)
ws.add_data_validation(fv); fv.add(f"{col('Fit (1-5)')}{HDR+1}:{col('Fit (1-5)')}{last_row}")

def cf(rng, formula, key, bold=True):
    fg, bg = C[key]
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], fill=fill(bg), font=Font(color=fg, bold=bold)))

er = f"{E}{HDR+1}:{E}{last_row}"
first = f"{E}{HDR+1}"
for est, k in [("Para postular", "acc"), ("Postulada", "idle"), ("Contactado", "info"), ("Prueba técnica", "info"),
               ("Entrevista", "ok"), ("Oferta", "ok"), ("Rechazada", "bad"), ("Descartada", "idle"), ("Retirada", "idle")]:
    cf(er, f'{first}="{est}"', k)
S = col("Seguimiento")
sr, sf = f"{S}{HDR+1}:{S}{last_row}", f"{S}{HDR+1}"
for txt, k in [("Hacer follow-up", "warn"), ("Revisar", "info"), ("Aviso vencido", "bad"), ("Pendiente de enviar", "acc"),
               ("Sin movimiento", "idle"), ("Esperar", "ok"), ("En curso", "ok"), ("Falta fecha", "warn"), ("Cerrada", "idle")]:
    cf(sr, f'{sf}="{txt}"', k)
# filas cerradas en gris
ws.conditional_formatting.add(f"A{HDR+1}:{L(len(COLS))}{last_row}",
    FormulaRule(formula=[f'OR(${E}{HDR+1}="Descartada",${E}{HDR+1}="Rechazada",${E}{HDR+1}="Retirada")'], font=Font(color="8A9691")))
# referidos resaltados
Lc = col("Canal")
cf(f"{Lc}{HDR+1}:{Lc}{last_row}", f'OR({Lc}{HDR+1}="Recomendación",{Lc}{HDR+1}="Networking")', "ok")
Fit = col("Fit (1-5)")
ws.conditional_formatting.add(f"{Fit}{HDR+1}:{Fit}{last_row}",
    ColorScaleRule(start_type="num", start_value=1, start_color="FBE4E2", mid_type="num", mid_value=3, mid_color="FDF0DC", end_type="num", end_value=5, end_color="E1F3E9"))
ws.sheet_properties.tabColor = ACCENT

# ---------------- Panel ----------------
wp = wb.create_sheet("Panel", 0)
wp.sheet_view.showGridLines = False
for c_, w in zip("ABCDEFGHI", [2, 26, 12, 4, 26, 12, 4, 26, 12]):
    wp.column_dimensions[c_].width = w
wp["B1"] = "Búsqueda de pasantía IT · Ignacio Palmeri"
wp["B1"].font = Font(name=F, size=20, bold=True, color=INK)
wp["B2"] = '="Actualizado al "&TEXT(TODAY(),"dd/mm/yyyy")&". Todo se calcula desde la hoja Postulaciones."'
wp["B2"].font = Font(name=F, size=10, color=MUTED)
P = "Postulaciones!"
Er = f"{P}${E}${HDR+1}:${E}${last_row}"
Sr = f"{P}${S}${HDR+1}:${S}${last_row}"
Fr = f"{P}${Fp}${HDR+1}:${Fp}${last_row}"
Cr = f"{P}${Lc}${HDR+1}:${Lc}${last_row}"
Kr = f"{P}${col('Dónde la encontré')}${HDR+1}:${col('Dónde la encontré')}${last_row}"
kpis = [
    ("Procesos activos", f'=COUNTIF({Er},"Postulada")+COUNTIF({Er},"Contactado")+COUNTIF({Er},"Entrevista")+COUNTIF({Er},"Prueba técnica")', "acc"),
    ("Para hacer follow-up hoy", f'=COUNTIF({Sr},"Hacer follow-up")+COUNTIF({Sr},"Revisar")', "warn"),
    ("Con respuesta o entrevista", f'=COUNTIF({Er},"Contactado")+COUNTIF({Er},"Entrevista")+COUNTIF({Er},"Prueba técnica")+COUNTIF({Er},"Oferta")', "ok"),
    ("Enviadas últimos 7 días", f'=COUNTIFS({Fr},">="&(TODAY()-7),{Fr},"<="&TODAY())', "info"),
    ("Pendientes de enviar", f'=COUNTIF({Er},"Para postular")', "acc"),
    ("Por recomendación o networking", f'=COUNTIF({Cr},"Recomendación")+COUNTIF({Cr},"Networking")', "ok"),
]
for i, (lbl, fml, k) in enumerate(kpis):
    rr = 4 + (i // 3) * 3
    cc = 2 + (i % 3) * 3
    fg, bg = C[k]
    a = wp.cell(rr, cc, lbl); b = wp.cell(rr + 1, cc, fml)
    for x in (a, b, wp.cell(rr, cc + 1), wp.cell(rr + 1, cc + 1)):
        x.fill = fill(bg)
    a.font = Font(name=F, size=10, color=fg, bold=True)
    b.font = Font(name=F, size=26, bold=True, color=fg)
    b.alignment = Alignment(horizontal="left")
    wp.row_dimensions[rr + 1].height = 36

def table(r0, c0, title, rows, formula_for):
    h = wp.cell(r0, c0, title); h.font = Font(name=F, size=12, bold=True, color=INK)
    for j, t in enumerate(["", "Cant.", ""]):
        pass
    for k_, name in enumerate(rows):
        r = r0 + 1 + k_
        a = wp.cell(r, c0, name); a.font = Font(name=F, size=10, color=INK); a.border = Border(bottom=thin)
        b = wp.cell(r, c0 + 1, formula_for(name)); b.font = Font(name=F, size=10, bold=True); b.border = Border(bottom=thin)
        b.alignment = Alignment(horizontal="center")
    return r0 + 1 + len(rows)

end1 = table(11, 2, "Embudo por estado", ESTADOS, lambda n: f'=COUNTIF({Er},"{n}")')
# barra visual
for k_, n in enumerate(ESTADOS):
    r = 12 + k_
    wp.cell(r, 4).value = None
table(11, 5, "Dónde las encontré", FUENTES, lambda n: f'=COUNTIF({Kr},"{n}")')
table(11, 8, "Canal", CANALES, lambda n: f'=COUNTIF({Cr},"{n}")')
wp.cell(17, 8, "Tasa de respuesta").font = Font(name=F, size=12, bold=True, color=INK)
wp.cell(18, 8, "Enviadas").font = Font(name=F, size=10)
wp.cell(18, 9, f'=COUNTA({Fr})').font = Font(name=F, size=10, bold=True)
wp.cell(19, 8, "Con respuesta").font = Font(name=F, size=10)
wp.cell(19, 9, "=H5").font = Font(name=F, size=10, bold=True)
wp.cell(20, 8, "Tasa").font = Font(name=F, size=10)
t = wp.cell(20, 9, "=IFERROR(I19/I18,0)"); t.number_format = "0%"; t.font = Font(name=F, size=10, bold=True, color=C["ok"][0])
wp.cell(22, 8, "Cómo seguir").font = Font(name=F, size=12, bold=True, color=INK)
tips = ["1. Abrí Postulaciones y filtrá Seguimiento = Hacer follow-up.",
        "2. Mandá el mensaje y cargá la fecha en Última interacción.",
        "3. Anotá lo que pasó en Historial (dd/mm/aa · texto).",
        "4. Los viernes cerrá lo que diga Sin movimiento."]
for i, tx in enumerate(tips):
    c_ = wp.cell(23 + i, 8, tx); c_.font = Font(name=F, size=10, color=MUTED)
for r in range(12, 12 + len(ESTADOS)):
    # color del estado en el embudo
    pass
wp.sheet_properties.tabColor = INK

# ---------------- Contactos ----------------
wc = wb.create_sheet("Contactos")
CH = [("Nombre", 22), ("Empresa", 22), ("Relación / cargo", 26), ("Canal", 16), ("Email / LinkedIn", 28),
      ("Último contacto", 13), ("Próximo follow-up", 13), ("Alerta", 12), ("Qué decir", 50), ("Notas", 40)]
wc["A1"] = "Contactos y networking"; wc["A1"].font = Font(name=F, size=16, bold=True, color=INK)
wc["A2"] = "Recruiters, referentes y gente de tu red. La alerta usa la misma regla de 3 días."
wc["A2"].font = Font(name=F, size=10, color=MUTED)
for i, (h, w) in enumerate(CH, 1):
    c_ = wc.cell(3, i, h); c_.font = Font(name=F, bold=True, color="FFFFFF", size=10); c_.fill = fill(INK)
    wc.column_dimensions[L(i)].width = w
with open(CONTACTS_CSV, encoding="utf-8", newline="") as fh:
    contacts = [tuple(r[k] for k in ("nombre", "empresa", "relacion", "canal", "email_linkedin", "ultimo_contacto", "que_decir", "notas"))
                for r in csv.DictReader(fh)]
for ri, (n, e, rel, can, em, last, say, notes) in enumerate(contacts, 4):
    for ci, v in enumerate([n, e, rel, can, em, d(last), None, None, say, notes], 1):
        c_ = wc.cell(ri, ci, v); c_.font = Font(name=F, size=10); c_.alignment = Alignment(vertical="top", wrap_text=ci in (3, 9, 10))
        c_.border = Border(bottom=thin)
for ri in range(4, 104):
    wc.cell(ri, 6).number_format = "dd/mm/yyyy"
    wc.cell(ri, 7, f'=IF(F{ri}="","",F{ri}+Listas!$F$2)').number_format = "dd/mm/yyyy"
    wc.cell(ri, 8, f'=IF(G{ri}="","",IF(G{ri}<=TODAY(),"Contactar","Esperar"))')
wc.conditional_formatting.add("H4:H103", FormulaRule(formula=['H4="Contactar"'], fill=fill(C["warn"][1]), font=Font(color=C["warn"][0], bold=True)))
vv = DataValidation(type="list", formula1=f"Listas!$B$2:$B${1+len(CANALES)}", allow_blank=True, showErrorMessage=False)
wc.add_data_validation(vv); vv.add("D4:D103")
wc.freeze_panes = "B4"

# ---------------- CVs ----------------
wv = wb.create_sheet("CVs")
wv["A1"] = "CVs usados"; wv["A1"].font = Font(name=F, size=16, bold=True, color=INK)
wv["A2"] = "Cada CV personalizado y dónde está. Inglés siempre B1 (intermedio)."
wv["A2"].font = Font(name=F, size=10, color=MUTED)
for i, (h, w) in enumerate([("Archivo", 50), ("Usado en", 40), ("Ruta en tu PC / link", 80)], 1):
    c_ = wv.cell(3, i, h); c_.font = Font(name=F, bold=True, color="FFFFFF", size=10); c_.fill = fill(INK)
    wv.column_dimensions[L(i)].width = w
cvs = {}
for p in docs:
    if p.get("cv"):
        cvs.setdefault(p["cv"], {"ruta": p.get("cv_ruta") or "", "usos": []})["usos"].append(p["empresa"])
for ri, (name, info) in enumerate(sorted(cvs.items(), key=lambda x: x[0].lower()), 4):
    for ci, v in enumerate([name, ", ".join(dict.fromkeys(info["usos"])), info["ruta"]], 1):
        c_ = wv.cell(ri, ci, v or None); c_.font = Font(name=F, size=10); c_.border = Border(bottom=thin)
        c_.alignment = Alignment(vertical="top", wrap_text=True)

# ---------------- Guía ----------------
wg = wb.create_sheet("Guía")
wg.column_dimensions["A"].width = 28; wg.column_dimensions["B"].width = 100
wg["A1"] = "Cómo usar este tracker"; wg["A1"].font = Font(name=F, size=16, bold=True, color=INK)
guide = [
    ("Al postular", "Agregá una fila al final de Postulaciones: Empresa, Puesto, Estado = Postulada, Fecha postulación, Link, Dónde la encontré, Canal, CV usado y Descripción."),
    ("Recomendación o networking", "En Canal elegí Recomendación o Networking y escribí quién en 'Recomendado por'. Sumalo también a Contactos."),
    ("Cada respuesta", "Cambiá la fecha de Última interacción y anotá en Historial: '26/09/26 · me escribió la recruiter'. Eso reinicia el contador."),
    ("Seguimiento", "Se calcula solo: Esperar (0-2 días) → Hacer follow-up (3-13) → Sin movimiento (14+). En entrevistas: Revisar a los 3 días."),
    ("Cierre semanal", "Los viernes filtrá Seguimiento = Sin movimiento y decidí: último mensaje o Estado = Rechazada/Retirada."),
    ("Ajustes", "Los días del follow-up (3) y de 'sin movimiento' (14) se cambian en la hoja Listas, columnas F y G."),
    ("Mensaje de follow-up", "Hola [Nombre], quería confirmar si recibiste mi postulación para [Puesto]. Quedo a disposición para una entrevista. ¡Gracias!"),
]
for ri, (a, b) in enumerate(guide, 3):
    x = wg.cell(ri, 1, a); x.font = Font(name=F, size=10, bold=True)
    y = wg.cell(ri, 2, b); y.font = Font(name=F, size=10); y.alignment = Alignment(wrap_text=True, vertical="top")
    wg.row_dimensions[ri].height = 30

wb.move_sheet("Listas", offset=10)
wb.active = 0
wb.save(OUT)
print("saved", OUT, len(docs), "postulaciones")
