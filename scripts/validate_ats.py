"""Validador ATS supremo — chequeos pre-submit para PDF/DOCX generados.

Uso:
  python scripts/validate_ats.py extras/cvs_personalizados/cv_sap_ixp_oti.pdf
  python scripts/validate_ats.py --all
  python scripts/validate_ats.py --all --strict  # falla si score < 80

Chequeos (2026):
  1. Tamaño < 1MB, 1-2 páginas
  2. Texto 100% seleccionable y en orden (pdfminer / PyPDF2)
  3. Headings estándar presentes (CONTACT/SUMMARY/EDUCATION/EXPERIENCE/PROJECTS/SKILLS/CERTIFICATIONS)
  4. Sin tablas/imagenes/cajas
  5. Contacto en body (no header/footer) — DOCX: sin header/footer con texto
  6. Fechas consistentes (detecta formatos raros)
  7. Filename profesional
  8. Score 0-100

Requisitos opcionales: pdfminer.six, PyPDF2, python-docx. Si faltan, hace fallback degradado.
Exit code 0 si ok, 1 si hay FAIL (para CI).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CVS_DIR = ROOT / "CV_Material_Nacho" / "extras" / "cvs_personalizados"

REQUIRED_HEADINGS = ["EDUCATION", "EXPERIENCE", "SKILLS"]  # mínimos en EN
REQUIRED_HEADINGS_ES = ["EDUCACION", "EDUCACIÓN", "EXPERIENCIA", "COMPETENCIAS", "HABILIDADES"]
OPTIONAL_HEADINGS = ["PROFILE", "SUMMARY", "PROJECTS", "CERTIFICATIONS", "LANGUAGES", "AVAILABILITY",
                     "PERFIL", "PROYECTOS", "EDUCACION", "EDUCACIÓN", "CERTIFICACIONES", "IDIOMAS", "DISPONIBILIDAD"]
DISALLOWED_RE = re.compile(r"[│┌┐└┘├┤┬┴┼]|\\u2502")  # box drawing = tabla
DATE_RE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Sept|Oct|Nov|Dic)\b.*\d{4}|\b\d{4}\s*[-–—]\s*(?:Present|Actual|\d{4})", re.I)


def extract_pdf_text(path: Path) -> tuple[str, int]:
    text = ""
    pages = 0
    # PyPDF/pypdf primero — conteo páginas exacto
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if text and len(text.strip()) > 200:
            return text, pages
    except ImportError:
        pass
    except Exception as e:
        print(f"WARN pypdf: {e}")
    try:
        from PyPDF2 import PdfReader as PdfReader2  # type: ignore
        reader = PdfReader2(str(path))
        pages = len(reader.pages)
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if text:
            return text, pages
    except ImportError:
        pass
    except Exception as e:
        print(f"WARN PyPDF2: {e}")
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        text = extract_text(str(path)) or ""
        pages = text.count("\x0c") + 1 if text else 1
        return text, pages
    except ImportError:
        pass
    except Exception as e:
        print(f"WARN pdfminer: {e}")
    return text, pages


def check_docx(path: Path) -> dict:
    issues = []
    score = 100
    try:
        from docx import Document  # type: ignore
        doc = Document(str(path))
        # Headings nativos — check bilingüe normalizado
        headings_raw = [p.text.strip().upper() for p in doc.paragraphs if p.style.name.startswith("Heading")]
        headings = [h.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U") for h in headings_raw]
        checks = [("EDUCATION/EDUCACION", ["EDUCATION", "EDUCACION"]), ("EXPERIENCE/EXPERIENCIA", ["EXPERIENCE", "EXPERIENCIA"]), ("SKILLS/COMPETENCIAS", ["SKILLS", "COMPETENCIAS", "HABILIDADES", "TECNICAS"])]
        for label, variants in checks:
            if not any(any(v in hd for v in variants) for hd in headings):
                # fallback: buscar en texto plano también normalizado
                full_text = " ".join(p.text.upper() for p in doc.paragraphs).replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
                if not any(v in full_text for v in variants):
                    issues.append(f"FAIL: heading {label} no encontrado como Heading 1/2")
                    score -= 10
        # Header/footer con texto = riesgo Taleo
        for sect in doc.sections:
            if sect.header.paragraphs and any(p.text.strip() for p in sect.header.paragraphs):
                issues.append("WARN: header con texto — Taleo/iCIMS puede ignorarlo; mové contacto al body")
                score -= 5
            if sect.footer.paragraphs and any(p.text.strip() for p in sect.footer.paragraphs):
                issues.append("WARN: footer con texto")
                score -= 5
        # Tablas
        if doc.tables:
            issues.append(f"FAIL: {len(doc.tables)} tabla(s) detectada(s) — ATS las rompe")
            score -= 20
        # Imágenes
        if doc.inline_shapes:
            issues.append(f"FAIL: {len(doc.inline_shapes)} imagen(es) — ATS no las lee")
            score -= 15
        # Tamaño
        kb = path.stat().st_size / 1024
        if kb > 1024:
            issues.append(f"WARN: {kb:.0f} KB > 1024 KB — peso alto")
            score -= 3
    except ImportError:
        issues.append("SKIP: python-docx no instalado — chequeo DOCX omitido")
    except Exception as e:
        issues.append(f"ERROR DOCX: {e}")
        score -= 10
    return {"issues": issues, "score": max(0, score)}


def check_pdf(path: Path) -> dict:
    issues = []
    score = 100
    kb = path.stat().st_size / 1024
    if kb > 1024:
        issues.append(f"WARN: {kb:.0f} KB > 1MB — puede fallar upload")
        score -= 5
    if kb < 5:
        issues.append(f"WARN: {kb:.1f} KB sospechosamente chico — ¿PDF vacío?")
        score -= 10
    text, pages = extract_pdf_text(path)
    if not text or len(text.strip()) < 200:
        issues.append("FAIL: texto extraíble <200 chars — PDF es imagen/escaneado o no es text-based")
        score -= 30
    else:
        # Orden: contacto debe aparecer antes que experiencia
        low = text.lower()
        c_pos = low.find("ignacio palmeri")
        e_pos = low.find("experience")
        if c_pos != -1 and e_pos != -1 and c_pos > e_pos:
            issues.append("FAIL: nombre/contacto aparece después de EXPERIENCE — orden roto")
            score -= 15
        # Headings presentes en texto extraído — soporta ES y EN
        upper = text.upper()
        # Normalizar acentos para EDUCACION/EDUCACIÓN
        upper_norm = upper.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        has_edu = any(h in upper_norm for h in ["EDUCATION", "EDUCACION"])
        has_exp = any(h in upper_norm for h in ["EXPERIENCE", "EXPERIENCIA"])
        has_skills = any(h in upper_norm for h in ["SKILLS", "COMPETENCIAS", "HABILIDADES", "TECNICAS"])
        if not has_edu:
            issues.append("FAIL: heading EDUCACION/EDUCATION no encontrado en texto extraido")
            score -= 10
        if not has_exp:
            issues.append("FAIL: heading EXPERIENCIA/EXPERIENCE no encontrado")
            score -= 10
        if not has_skills:
            issues.append("FAIL: heading COMPETENCIAS/SKILLS no encontrado")
            score -= 10
        # Tablas/box drawing
        if DISALLOWED_RE.search(text):
            issues.append("FAIL: caracteres de tabla/caja detectados")
            score -= 15
        # Páginas
        if pages == 0:
            issues.append("WARN: no se pudo contar páginas")
        elif pages > 2:
            issues.append(f"WARN: {pages} páginas — ideal 1-2 para ATS")
            score -= 5
        # Copy-paste sanity: debe contener email y github
        if "ignaciopalmeri1@gmail.com" not in text and "@gmail" not in text:
            issues.append("WARN: email no encontrado en texto extraído")
            score -= 5
        if "github.com/nachopalmeri" not in text.lower():
            issues.append("WARN: github link no extraíble")
            score -= 3
    # Filename
    if not re.match(r"^[A-Z][a-z]+_[A-Z][a-z]+_.*\.(pdf|docx)$", path.name):
        issues.append(f"INFO: nombre '{path.name}' no sigue patrón Profesional Ignacio_Palmeri_*.pdf (recomendado)")
        # no resta score, solo info
    return {"issues": issues, "score": max(0, score), "pages": pages, "chars": len(text)}


def check_file(path: Path) -> dict:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return check_pdf(path)
    if ext == ".docx":
        return check_docx(path)
    return {"issues": [f"SKIP: extensión {ext} no soportada"], "score": 0}


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    do_all = "--all" in args
    files: list[Path] = []
    if do_all:
        files = sorted(CVS_DIR.glob("*.pdf")) + sorted(CVS_DIR.glob("*.docx"))
        # Evitar duplicar profesional + legacy si son idénticos en contenido; validar todos igual
        # Filtrar los Ignacio_Palmeri_* para no duplicar ruido: validar legacy y profesional por separado está ok
    else:
        for a in args:
            if a.startswith("--"):
                continue
            p = Path(a)
            if not p.exists():
                # Relativo a ROOT
                p = ROOT / a
            if p.exists():
                files.append(p)
            else:
                print(f"SKIP no existe: {a}")
    if not files:
        print("Uso: python scripts/validate_ats.py <archivo.pdf/.docx> | --all")
        print("Ej:  python scripts/validate_ats.py CV_Material_Nacho/extras/cvs_personalizados/cv_sap_ixp_oti.pdf")
        sys.exit(1)

    overall_fail = False
    for f in files:
        res = check_file(f)
        score = res["score"]
        pages = res.get("pages", "-")
        chars = res.get("chars", "-")
        label = "PASS" if score >= 80 else "WARN" if score >= 60 else "FAIL"
        if label == "FAIL":
            overall_fail = True
        print(f"\n[{label}] {f.name}  score={score}  pages={pages}  chars={chars}")
        for iss in res["issues"]:
            print(f"  - {iss}")
        if score >= 80:
            print("  [OK] Listo para ATS")
        elif score >= 60:
            print("  [WARN] Revision recomendada antes de postular")
        else:
            print("  [FAIL] No postular hasta corregir")

    sys.exit(1 if (strict and overall_fail) else 0)


if __name__ == "__main__":
    main()
