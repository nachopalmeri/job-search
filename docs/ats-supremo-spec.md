# ATS Supremo — Spec v1 (21/08/2026)

## Objetivo
CVs que parsean 99% en Workday/Greenhouse/Lever/Taleo/iCIMS/Ashby, con texto 100% seleccionable, headings estándar, y keyword coverage 80%+ sin stuffing.

## Pilares (CoT)

1. **Fuente única YAML** (`CV_Material_Nacho/cv_master.yaml`): evita drift ES/EN, permite tailoring programático. `yaml_to_md.py` genera `cv_master_es.md`/`_en.md` — si editás MD a mano, CI falla (`--check`).
2. **Single-column estricto**: 1 columna, 1-2 páginas, Calibri/Arial 10pt, márgenes 1.6cm, contacto en body. Probado: 2 páginas para este perfil (proyectos = evidencia). No tablas/box-drawing (validator lo detecta).
3. **PDF etiquetado + DOCX con Heading 1/2**: `generate_cv_files.py v2` usa `SimpleDocTemplate(title,author,subject,keywords)` y `Heading 1` nativo. Taleo/Workday mapean experiencia por headings, no por bold suelto.
4. **Dual export siempre**: cada `cv_*.md` → `cv_*.pdf` (legacy) + `Ignacio_Palmeri_*.pdf` (profesional) + ambos DOCX. Subí el profesional; dejá el legacy para tracker compat.
5. **Filename profesional**: `Ignacio_Palmeri_<Empresa>_<Rol>.pdf` — el recruiter ve eso en la lista de adjuntos.
6. **Keyword mirroring**: `scripts/keyword_match.py` extrae 8-12 must-have del JD (curated IT + frecuencia) y mide coverage. Regla: espejá keywords verbatim en **SKILLS + 1er bullet de EXPERIENCE/PROJECTS**, no en wall al final.
7. **Validación pre-submit obligatoria**: `scripts/validate_ats.py --all` corre en CI y local. Score <60 = no postular. Score 60-80 = revisar. Score 80+ = ok. Chequea tamaño, páginas, texto extraíble, headings ES/EN, tablas, email/github.

## Repos de referencia evaluados (21/08/2026)

| Repo | Uso |
|---|---|
| `sb2nov/resume` (Jake) | LaTeX single-column más usado — inspiración tipográfica |
| `rendercv/rendercv` | YAML→Typst/PDF — **candidato futuro** para reemplazar ReportLab sin tocar MD |
| `denniyahh/ats_safe_resume` | Markdown→PDF/DOCX/HTML via Pandoc — alternativa 0-install |
| `xitanggg/open-resume` + `OmkarPathak/pyresparser` | Parsers para validación local |
| `hugounoclaw/awesome-ats-resume` | Curaduría completa (checkers/parsers/templates) |

## Migración Sprint 3 (cuando quieras)

- **Opción A (recomendada)**: mantener `generate_cv_files.py v2` (ReportLab) — ya es ATS-supremo. Migrar a `rendercv` solo si querés tipografía Typst pixel-perfect sin codear.
- **Opción B**: `pandoc + Eisvogel LaTeX` como en `ats_safe_resume` — requiere instalar pandoc/texlive, pero da PDF/DOCX/HTML desde un único `resume.md`.
- En ambos casos, `cv_master.yaml` ya te deja cambiar backend sin tocar contenido.

## Cómo usar hoy

```bash
# 1. Editar fuente única
code CV_Material_Nacho/cv_master.yaml
python CV_Material_Nacho/yaml_to_md.py   # regenera ES/EN

# 2. Crear personalizado (copiá master y tailoreá)
cp CV_Material_Nacho/cv_master_es.md CV_Material_Nacho/extras/cvs_personalizados/cv_empresa_rol.md
# ...editá...

# 3. Build + validación + keywords
python CV_Material_Nacho/extras/generate_cv_files.py
python scripts/validate_ats.py CV_Material_Nacho/extras/cvs_personalizados/cv_empresa_rol.pdf
python scripts/keyword_match.py --jd-file aviso.txt --cv CV_Material_Nacho/extras/cvs_personalizados/cv_empresa_rol.md

# 4. Postular con el profesional
# -> Ignacio_Palmeri_Empresa_Rol.pdf  (PDF por defecto en AR, DOCX si el portal es Taleo/Workday old)
```

## Tracker — columna futura

`tracker/applications.csv` mantiene `fecha|portal|titulo|empresa|...|estado|notas`. Propuesta v2 (no rompe compatibilidad): añadir `ats_score` como 11ª columna opcional. Cuando generes un CV, anotá `ats_score=XX` en notas o añadí columna. CI no exige header nuevo — es incremental.

## Validación manual rápida (sin script)

1. Abre el PDF → Ctrl+A, Ctrl+C → pega en Notepad → ¿sale en orden y con email/github?
2. ¿Headings en mayúsculas y en inglés/español estándar?
3. ¿1-2 páginas, <1MB, sin foto/tabla/barras?
Si las 3 son sí, pasa ATS moderno.
