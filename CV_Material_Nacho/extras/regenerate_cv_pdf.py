"""Regenera Ignacio_Palmeri_CV_ES.pdf desde cv_master_es.md con encoding Unicode correcto.

Uso: python regenerate_cv_pdf.py
Requiere: reportlab (pip install reportlab). Usa Arial de Windows (registrada con TTF para unicode).
"""
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "cv_master_es.md"
OUT = BASE / "Ignacio_Palmeri_CV_ES.pdf"

FONTS_DIR = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("CVSans", str(FONTS_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("CVSans-Bold", str(FONTS_DIR / "arialbd.ttf")))

REVISAR_RE = re.compile(r"\s*\[REVISAR:[^\]]*\]\s*", re.UNICODE)

S_NAME = ParagraphStyle("name", fontName="CVSans-Bold", fontSize=17, leading=20, spaceAfter=2)
S_CONTACT = ParagraphStyle("contact", fontName="CVSans", fontSize=9, leading=12, spaceAfter=6)
S_HEAD = ParagraphStyle("head", fontName="CVSans-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
S_PARA = ParagraphStyle("para", fontName="CVSans", fontSize=10, leading=13.5, spaceAfter=3)
S_BULLET = ParagraphStyle("bullet", fontName="CVSans", fontSize=10, leading=13.5, spaceAfter=2, leftIndent=12, bulletIndent=2)


def main() -> None:
    lines = [l.rstrip("\n") for l in SRC.read_text(encoding="utf-8").splitlines()]
    flow = []
    for line in lines:
        raw = line.strip()
        if not raw or raw == "---" or raw.startswith("# ") or raw.startswith("> "):
            continue
        if raw.startswith("## "):
            flow.append(Paragraph(raw[3:].upper(), S_HEAD))
            continue
        text = REVISAR_RE.sub(" ", raw).replace("**", "")
        if raw.startswith("- "):
            flow.append(Paragraph(text[2:], S_BULLET, bulletText="\u2022"))
        else:
            flow.append(Paragraph(text, S_PARA))
    flow.insert(0, Spacer(1, 2))

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.3 * cm, bottomMargin=1.3 * cm,
        title="CV - Ignacio Palmeri",
        author="Ignacio Palmeri",
    )
    doc.build(flow)
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    main()
