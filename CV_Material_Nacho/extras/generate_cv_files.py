"""Genera PDF y DOCX ATS-supremo para cada CV en extras/cvs_personalizados/*.md.

v2 (21/08/2026) — sprint 1:
- Single-column, texto 100% seleccionable, sin tablas/cajas/imagenes.
- DOCX con estilos Heading 1/2 nativos (para parsers Workday/Taleo), bullets nativos, hyperlinks clickeables.
- PDF con metadata (Title/Author/Subject/Keywords), fuentes Arial embed, copy-paste ordenado.
- Filename profesional Ignacio_Palmeri_<Slug>.pdf/docx + compatibilidad con nombre legacy cv_*.pdf.
- Valida con validate_ats.py (standalone).

Uso:
  python extras/generate_cv_files.py                # todos
  python extras/generate_cv_files.py extras/cvs_personalizados/cv_sap_ixp_oti.md
Requisitos: reportlab, python-docx, pdfminer.six (opcional para validación).
"""

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = Path(__file__).resolve().parent.parent
CVS_DIR = BASE / "extras" / "cvs_personalizados"

# Fuentes — fallback a Helvetica si Arial no está (Linux/Docker)
FONTS_DIR = Path(r"C:\Windows\Fonts")
try:
    pdfmetrics.registerFont(TTFont("CVSans", str(FONTS_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("CVSans-Bold", str(FONTS_DIR / "arialbd.ttf")))
    PDF_FONT = "CVSans"
    PDF_FONT_B = "CVSans-Bold"
except Exception:
    PDF_FONT = "Helvetica"
    PDF_FONT_B = "Helvetica-Bold"

REVISAR_RE = re.compile(r"\s*\[REVISAR:[^\]]*\]\s*", re.UNICODE)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
# Profesionalizar slug: cv_sap_ixp_oti -> SAP_iXp_O2I ; cv_master_es -> Master_ES
SLUG_MAP = {"oti": "O2I", "ixp": "iXp", "sap": "SAP", "kavak": "Kavak", "tetrapak": "TetraPak"}

# Estilos PDF — 10-11pt body, 9pt contacto, jerarquía sin ruido
S_NAME = ParagraphStyle("name", fontName=PDF_FONT_B, fontSize=17, leading=20, spaceAfter=2, textColorRGB=(0.1, 0.1, 0.1))
S_CONTACT = ParagraphStyle("contact", fontName=PDF_FONT, fontSize=8.5, leading=11, spaceAfter=7, textColorRGB=(0.25, 0.25, 0.25))
S_HEAD = ParagraphStyle("head", fontName=PDF_FONT_B, fontSize=11, leading=14, spaceBefore=11, spaceAfter=4, textColorRGB=(0.15, 0.15, 0.15), keepWithNext=1)
S_PARA = ParagraphStyle("para", fontName=PDF_FONT, fontSize=10, leading=13.5, spaceAfter=3)
S_BULLET = ParagraphStyle("bullet", fontName=PDF_FONT, fontSize=9.5, leading=13, spaceAfter=2, leftIndent=14, bulletIndent=3)
S_SKILL = ParagraphStyle("skill", fontName=PDF_FONT, fontSize=9.5, leading=13, spaceAfter=2, leftIndent=14, bulletIndent=3)


def slug_to_professional(src: Path) -> str:
    """cv_sap_ixp_oti.md -> Ignacio_Palmeri_SAP_iXp_O2I"""
    stem = src.stem  # cv_sap_ixp_oti
    if stem.startswith("cv_"):
        stem = stem[3:]
    parts = stem.split("_")
    pro = []
    for p in parts:
        low = p.lower()
        if low in SLUG_MAP:
            pro.append(SLUG_MAP[low])
        elif low in ("master", "es", "en"):
            pro.append(p.capitalize() if low != "es" and low != "en" else p.upper())
        else:
            pro.append(p.capitalize())
    return "Ignacio_Palmeri_" + "_".join(pro)


def md_to_reportlab(text: str) -> str:
    """Convierte markdown inline a subset HTML que entiende reportlab Paragraph: links + bold."""
    # Links primero
    text = MD_LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = MD_BOLD_RE.sub(r"<b>\1</b>", text)
    # Escapar & suelto que rompe XML
    # reportlab Paragraph tolera <br/> pero no & sin escapar
    return text


def clean_text(raw: str) -> str:
    raw = REVISAR_RE.sub(" ", raw)
    # No strip bold aqui — lo maneja md_to_reportlab
    return raw.strip()


def is_contact_line(text: str) -> bool:
    return ("@" in text and "|" in text) or ("linkedin.com" in text.lower() and "github.com" in text.lower())


def make_pdf(src: Path, out: Path) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    flow = []
    # Titulo legible para metadata
    title = src.stem.replace("cv_", "").replace("_", " ").title()
    for line in lines:
        raw = line.strip()
        if not raw or raw == "---" or raw.startswith("# ") or raw.startswith("> "):
            continue
        if raw.startswith("## "):
            heading = raw[3:].strip()
            # Forzar verbatim headings estándar para ATS (mapeo)
            heading_up = heading.upper()
            flow.append(Paragraph(heading_up, S_HEAD))
            continue
        # Detección contacto
        cleaned = clean_text(raw)
        if not cleaned:
            continue
        rl_text = md_to_reportlab(cleaned)
        if raw.startswith("- "):
            # bullet con texto convertido
            flow.append(Paragraph(rl_text[2:] if rl_text.startswith("- ") else rl_text, S_BULLET, bulletText="•"))
        elif is_contact_line(raw):
            flow.append(Paragraph(rl_text, S_CONTACT))
        else:
            # Negrita en linea suelta (ej. **Ignacio Palmeri**) -> usar S_NAME si es primera
            if raw.startswith("**") and raw.endswith("**") and len(flow) == 0:
                inner = raw.strip("*").strip()
                flow.append(Paragraph(inner, S_NAME))
            else:
                flow.append(Paragraph(rl_text, S_PARA))
    flow.insert(0, Spacer(1, 2))
    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
        title=f"CV — Ignacio Palmeri — {title}",
        author="Ignacio Palmeri",
        subject="Curriculum Vitae — ATS single-column, text-based",
        keywords="CV, resume, ATS, Ignacio Palmeri, UADE",
        creator="job-search generate_cv_files.py v2",
    )
    doc.build(flow)
    print(f"OK PDF  -> {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def add_hyperlink(paragraph, text: str, url: str):
    """Inserta hyperlink clickeable en python-docx."""
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), "1155CC")
    rPr.append(c)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    rStyle = OxmlElement("w:rStyle")
    rStyle.set(qn("w:val"), "Hyperlink")
    rPr.append(rStyle)
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink


def add_paragraph_with_links(doc, text: str, style=None):
    """Crea párrafo docx respetando [text](url) y **bold**."""
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    # Split por links
    last = 0
    for m in MD_LINK_RE.finditer(text):
        pre = text[last:m.start()]
        if pre:
            # Procesar bold dentro de pre
            add_runs_with_bold(p, pre)
        add_hyperlink(p, m.group(1), m.group(2))
        last = m.end()
    tail = text[last:]
    if tail:
        add_runs_with_bold(p, tail)
    # Si no hubo links, el párrafo ya tiene runs; si vacío por solo link, ok
    if not p.text and not p._p.xpath(".//w:hyperlink"):
        # Fallback sin links
        p.text = text
    return p


def add_runs_with_bold(paragraph, text: str):
    parts = MD_BOLD_RE.split(text)
    # split deja alternancia: texto normal, bold, normal...
    is_bold = False
    # re.split con grupo captura intercala; usamos finditer para claridad
    last = 0
    for m in MD_BOLD_RE.finditer(text):
        pre = text[last:m.start()]
        if pre:
            paragraph.add_run(pre)
        paragraph.add_run(m.group(1)).bold = True
        last = m.end()
    tail = text[last:]
    if tail:
        paragraph.add_run(tail)


def make_docx(src: Path, out: Path) -> None:
    doc = Document()
    # Estilos base ATS: Calibri 10pt, interlineado 1.0, sin decoraciones
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)
    style.paragraph_format.spaceAfter = Pt(2)
    # Asegurar Heading 1/2 existan con formato sobrio (no colores raros que confundan)
    for i in (1, 2):
        hs = doc.styles[f"Heading {i}"]
        hs.font.name = "Calibri"
        hs.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        hs.font.size = Pt(11 if i == 1 else 10)
        hs.font.bold = True
        hs.paragraph_format.spaceBefore = Pt(8)
        hs.paragraph_format.spaceAfter = Pt(3)

    core = doc.core_properties
    core.author = "Ignacio Palmeri"
    core.title = f"CV — Ignacio Palmeri — {src.stem}"
    core.subject = "Curriculum Vitae — ATS single-column"
    core.keywords = "CV, ATS, Ignacio Palmeri"

    lines = src.read_text(encoding="utf-8").splitlines()
    for line in lines:
        raw = line.rstrip("\n")
        stripped = raw.strip()
        if not stripped or stripped == "---" or stripped.startswith("# ") or stripped.startswith("> "):
            continue
        if stripped.startswith("## "):
            heading = stripped[3:].strip().upper()
            # Usar Heading 1 nativo para que Workday/Taleo lo detecte
            p = doc.add_heading(heading, level=1)
            # Compactar después
            p.paragraph_format.spaceAfter = Pt(3)
            continue
        cleaned = clean_text(raw)
        if not cleaned:
            continue
        if stripped.startswith("- "):
            # Bullet nativo ATS — sin simbolos raros
            text = cleaned[2:] if cleaned.startswith("- ") else cleaned
            # El markdown ya limpió [REVISAR]; ahora manejar links/bold
            # python-docx List Bullet no soporta hyperlinks bien si usamos style directo, creamos manual
            p = doc.add_paragraph(style="List Bullet")
            # Vaciar el párrafo creado y rellenar con runs/links
            p.clear()
            # Re-parse links/bold dentro del bullet
            last = 0
            for m in MD_LINK_RE.finditer(text):
                pre = text[last:m.start()]
                if pre:
                    add_runs_with_bold(p, pre)
                add_hyperlink(p, m.group(1), m.group(2))
                last = m.end()
            tail = text[last:]
            if tail:
                add_runs_with_bold(p, tail)
            if not p.text and not p._p.xpath(".//w:hyperlink"):
                p.text = text
        else:
            # Contacto vs párrafo normal
            if is_contact_line(stripped):
                p = add_paragraph_with_links(doc, cleaned)
                p.style = doc.styles["Normal"]
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            elif stripped.startswith("**") and stripped.endswith("**"):
                p = doc.add_paragraph()
                r = p.add_run(stripped.strip("*").strip())
                r.bold = True
                r.font.size = Pt(16)
            else:
                add_paragraph_with_links(doc, cleaned)

    doc.save(out)
    print(f"OK DOCX -> {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def main() -> None:
    targets = sorted(CVS_DIR.glob("*.md")) if len(sys.argv) < 2 else [Path(sys.argv[1])]
    for src in targets:
        if not src.exists():
            print(f"SKIP (no existe): {src}")
            continue
        # 1) Legacy names (compatibilidad tracker)
        make_pdf(src, src.with_suffix(".pdf"))
        make_docx(src, src.with_suffix(".docx"))
        # 2) Profesional names (recomendado para postular)
        pro_name = slug_to_professional(src)
        pro_pdf = src.with_name(pro_name + ".pdf")
        pro_docx = src.with_name(pro_name + ".docx")
        # Evitar duplicar si es master (ya es profesional)
        if pro_pdf != src.with_suffix(".pdf"):
            make_pdf(src, pro_pdf)
            make_docx(src, pro_docx)

if __name__ == "__main__":
    main()
