"""Genera PDF y DOCX para cada CV personalizado en extras/cvs_personalizados/*.md.

Uso: python generate_cv_files.py            (procesa todos los *.md de la carpeta)
Requisitos: reportlab, python-docx.
Fuente: adaptado de regenerate_cv_docx.py / regenerate_cv_pdf.py (maestro).
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
from docx.shared import Pt

BASE = Path(__file__).resolve().parent.parent
CVS_DIR = BASE / "extras" / "cvs_personalizados"

FONTS_DIR = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("CVSans", str(FONTS_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("CVSans-Bold", str(FONTS_DIR / "arialbd.ttf")))

REVISAR_RE = re.compile(r"\s*\[REVISAR:[^\]]*\]\s*", re.UNICODE)

S_NAME = ParagraphStyle("name", fontName="CVSans-Bold", fontSize=17, leading=20, spaceAfter=2)
S_CONTACT = ParagraphStyle("contact", fontName="CVSans", fontSize=9, leading=12, spaceAfter=6)
S_HEAD = ParagraphStyle("head", fontName="CVSans-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
S_PARA = ParagraphStyle("para", fontName="CVSans", fontSize=10, leading=13.5, spaceAfter=3)
S_BULLET = ParagraphStyle("bullet", fontName="CVSans", fontSize=10, leading=13.5, spaceAfter=2, leftIndent=12, bulletIndent=2)


def clean_text(raw: str) -> str:
    return REVISAR_RE.sub(" ", raw).replace("**", "")


def make_pdf(src: Path, out: Path) -> None:
    lines = [l.rstrip("\n") for l in src.read_text(encoding="utf-8").splitlines()]
    flow = []
    for line in lines:
        raw = line.strip()
        if not raw or raw == "---" or raw.startswith("# ") or raw.startswith("> "):
            continue
        if raw.startswith("## "):
            flow.append(Paragraph(raw[3:].upper(), S_HEAD))
            continue
        text = clean_text(raw)
        if raw.startswith("- "):
            flow.append(Paragraph(text[2:], S_BULLET, bulletText="\u2022"))
        else:
            flow.append(Paragraph(text, S_PARA))
    flow.insert(0, Spacer(1, 2))

    doc = SimpleDocTemplate(
        str(out), pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.3 * cm, bottomMargin=1.3 * cm,
        title=f"CV - Ignacio Palmeri", author="Ignacio Palmeri",
    )
    doc.build(flow)
    print(f"OK PDF  -> {out.name}")


def make_docx(src: Path, out: Path) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    lines = [l.rstrip("\n") for l in src.read_text(encoding="utf-8").splitlines()]
    for line in lines:
        raw = line.strip()
        if not raw or raw == "---" or raw.startswith("# ") or raw.startswith("> "):
            continue
        if raw.startswith("## "):
            p = doc.add_paragraph()
            r = p.add_run(raw[3:].upper())
            r.bold = True
            continue
        text = clean_text(raw)
        if raw.startswith("- "):
            doc.add_paragraph(text[2:], style="List Bullet")
        else:
            doc.add_paragraph(text)

    doc.save(out)
    print(f"OK DOCX -> {out.name}")


def main() -> None:
    targets = sorted(CVS_DIR.glob("*.md")) if len(sys.argv) < 2 else [Path(sys.argv[1])]
    for src in targets:
        if not src.exists():
            print(f"SKIP (no existe): {src}")
            continue
        make_pdf(src, src.with_suffix(".pdf"))
        make_docx(src, src.with_suffix(".docx"))


if __name__ == "__main__":
    main()