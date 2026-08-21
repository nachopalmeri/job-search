# Matching Spec — Sprint 2 (JD→CV tailoring + rúbrica + tracker)

> Fecha: 2026-08-21 · Agente: Matching · Repo: `job-search` · Sprint 2/4
> Fuente única: `CV_Material_Nacho/cv_master.yaml` · Stack: `keyword_match.py` + `validate_ats.py v2` + `yaml_to_md.py` + `generate_cv_files.py v2`

---

## 1. Auditoría — gaps para tailoring automático

### 1.1 `cv_master.yaml` (`CV_Material_Nacho/cv_master.yaml:1`)

**Estado:** fuente única correcta (21/08/2026, 5 proyectos, 5 skills cats, honestidad verificable). No hay drift vs `cv_master_*.md` (generado por `yaml_to_md.py`).

**Gaps detectados:**

| # | Gap | Impacto ATS 2026 | Evidencia |
|---|---|---|---|
| G1 | **Sin campo `ats_keywords` / `tailoring_hints` por bloque** — no hay dónde anclar keywords por proyecto sin tocar bullets | Tailoring manual propenso a stuffing wall | `cv_master.yaml:51-110` projects tienen `keywords` pero son tech stack, no ATS mirror |
| G2 | **Bullets sin métricas densas** — Grido/experiencia 10h/sem ok, pero JobBot/FranquiYA/Prode sin números (commits, 10k sims sí están) pero no en formato SAR (Situación-Acción-Resultado) | ATS premia evidencia en bullets, no paredes | `highlights` líneas 34-38, 61-66 |
| G3 | **Sin `aliases` para sinónimos ATS** — `automatización`≠`automation`, `M365`≠`Microsoft 365` no mapeados | Falla keyword_match si JD usa variante | `keyword_match.py:CURATED` sí tiene ambos, pero YAML no normaliza |
| G4 | **Fecha solo año en proyectos** — `startDate: "2026"` sin mes | Orden cronológico ambiguo para parsers | `projects[].startDate` |
| G5 | **Sin `availability` estructurada por horas/modalidad** — texto libre | Rúbrica Jornada 25% no puede validarse programáticamente | `availability:es` línea 145 |

**No es gap:** contenido honesto, sin claims prohibidos (`profile.md` Claims prohibidos), inglés B1+/B2 correcto.

### 1.2 `yaml_to_md.py` (`CV_Material_Nacho/yaml_to_md.py:1`)

**Estado:** genera ES/EN determinista, `--check` anti-drift OK.

**Gaps:**

| # | Gap | Propuesta |
|---|---|---|
| G6 | **No expone `render_es/render_en` como lib** — `tailor_cv.py` hoy duplica import vía `importlib` | Hacer `from yaml_to_md import render_es` canónico (ya funciona, pero no documentado) |
| G7 | **Sin modo `--yaml-tailored` → MD** — solo lee master | `tailor_cv.py` suple generando MD vía render; no bloquear |
| G8 | **Headings hardcoded en ES/EN** — duplicado con `validate_ats.py` | Centralizar `REQUIRED_HEADINGS` en const compartida (Sprint 3) |

### 1.3 `keyword_match.py` (`scripts/keyword_match.py:1`)

**Estado:** extractor 8-12 keywords (curated 40 términos + bigrams frecuencia) + coverage correcto. Sin LLM, heurística rápida OK.

**Gaps:**

| # | Gap | Impacto pipeline |
|---|---|---|
| G9 | **No output JSON** — solo `print` humano | Pipeline JD→CV no puede consumir score programáticamente → `tailor_cv.py` duplica lógica |
| G10 | **STOP list corta (22 palabras)** + bigrams sin filtro técnico | Bigrams ruidosos en JD largos (ej. "últimos años") |
| G11 | **Sin lematización ni alias map** — `automatización` vs `automation` tratados como distintos si JD trae uno solo | Coverage subestimado |
| G12 | **Lee CV como texto plano**, no por sección | No sabe si miss está en SKILLS vs PROJECTS |
| G13 | **Sin `ats_score`** — coverage ≠ ats_score (ATS también mira headings, tamaño, etc.) | Tracker no puede guardar score único |

**Mitigación Sprint 2:** `tailor_cv.py` reutiliza `extract_keywords` si importa bien; fallback embebido idéntico. Sprint 3: añadir `--json` a `keyword_match.py`.

### 1.4 `rubric-fit.md` (`rubric-fit.md:1`)

**Estado:** 5 dimensiones (Habilidades 30%, Exp/Edu 25%, Ubic 20%, Carrera 15%, Demanda 10%) + deal-breakers. Adaptada de `ai-job-search`.

**Gaps vs ATS 2026:**

| # | Gap | Justificación cambio |
|---|---|---|
| G14 | **Pesa Habilidades 30% como wall** — ATS 2026 no premia lista SKILLS larga, premia **evidencia en bullets** (Workday/Greenhouse parsean bullets, no walls) | Nueva rúbrica: Evidencia 40% |
| G15 | **Sin dimensión ATS/tailoring** — `fit_score` no refleja `coverage` | Añadir `ats_score` como señal, no como dimensión nueva (para no romper escala 1-5) |
| G16 | **Ubicación 20% sobreponderada** — AMBA/híbrido ya es deal-breaker (veto), no debería pesar tanto si no veta | Bajar a 10%, subir Jornada |
| G17 | **Jornada no tiene peso propio** — está dentro de Ubicación/horario 20% | Extraer Jornada 25% (20h part-time es el filtro #1 de Nacho) |
| G18 | **Demanda 10% ruidosa** — "realmente necesitan cubrir" no es medible | Bajar a 5% |

---

## 2. Pipeline JD→CV diseñado

```
JD.txt (texto aviso)
  │
  ├─→ extract 8-12 keywords  (curated 40 + frecuencia bigrams, 12 max)
  │     fuente: scripts/keyword_match.py:CURATED (prioridad verbatim)
  │     fallback: tokenize + Counter(toks+bigrams) + STOP filter
  │
  ├─→ score vs cv_master.yaml (flatten YAML → texto, coverage %)
  │     coverage = |hit| / |keywords| *100  → ats_score proxy (0-100)
  │     hit/miss por substring lower
  │
  ├─→ tailor decision (sin inventar)
  │     miss → defensible? (ver §3) → mirrored (max 5) vs gap (no espejable)
  │     defensible = ya existe en YAML o en SAFE_MIRROR allowlist
  │     blocklist: rhcsa, bilingüe, senior, años falsos → nunca espejar
  │
  ├─→ genera cv_<empresa>.yaml  (deepcopy master + inyecciones)
  │     SKILLS: añade mirrored a categoría mapeada (SKILL_CATEGORY_MAP, max 8/cat)
  │     EXPERIENCE[0].highlights[0]: append " — stack: kw1, kw2"
  │     PROJECTS[0].highlights[0]: append " [kw1, kw2]"
  │     header trazabilidad: empresa, JD, ats delta
  │
  ├─→ genera cv_<empresa>.md  (render_es/en vía yaml_to_md.py)
  │     footer: "> Tailoreado para **empresa** — ats_score XX%"
  │
  └─→ siguiente manual:
        python CV_Material_Nacho/extras/generate_cv_files.py cv_<empresa>.md
        python scripts/validate_ats.py cv_<empresa>.pdf  (score 80+)
        python scripts/keyword_match.py --jd-file JD.txt --cv cv_<empresa>.md
```

### CLI canónico

```bash
# ES (default)
python scripts/tailor_cv.py --jd-file JD.txt --empresa sap --lang en
# Sobrescribir
python scripts/tailor_cv.py --jd-file JD.txt --empresa sap --lang en --force
# Dry-run (solo reporta)
python scripts/tailor_cv.py --jd-file JD.txt --empresa test --dry-run
# Top-k custom
python scripts/tailor_cv.py --jd-file aviso.txt --empresa carrefour --top-k 10
```

**Outputs:**
- `CV_Material_Nacho/extras/cvs_personalizados/cv_<slug>.yaml`
- `CV_Material_Nacho/extras/cvs_personalizados/cv_<slug>.md`
- stdout: keywords, coverage master→tailoreado, ats_score, mirrored, gap, gap_principal sugerido

### Reglas de no-invención

1. Nunca crea métricas, fechas, empleadores, títulos.
2. Bullets reescritos conservan frase original + suffix contextual (` — stack: ...` / ` [...]`).
3. Máx 5 mirrored, 2 inyectados en 1er bullet — anti-stuffing.
4. Si `gap` no es defensible, queda para `tracker gap_principal` y `notas`, no se fuerza en CV.

---

## 3. Rúbrica propuesta — pesos nuevos

### 3.1 Tabla (escala 1-5 por dimensión, fit_score ponderado 1.0-5.0)

| Dimensión | Peso nuevo | Peso viejo | Qué mira (criterio 1-5) | Por qué cambia |
|---|---|---|---|---|
| **Evidencia en bullets** | **40%** | 30% (Habilidades wall) | ¿Cuántos must-have del JD aparecen **en bullets de EXPERIENCE/PROJECTS con verbo+resultado**, no solo en SKILLS? 5=≥80% keywords en bullets, 1=<40% | **ATS 2026**: Greenhouse/Workday/iCIMS parsean bullets; SKILLS wall sin evidencia = stuffing penalizado. Nacho tiene evidencia real (JobBot, FranquiYA 57 commits, Prode 10k sims) — hay que espejarla en bullets. |
| **Jornada** | **25%** | 20% (mezclada con Ubicación) | ¿Es part-time 20h (ideal), 12-20h, o full-time? 5=20h explícito, 3=part-time sin horas, 1=full-time sin opción | Filtro #1 de Nacho (`profile.md:Disponibilidad 20h`, `cv_master.yaml:availability`). Deal-breaker si exige full-time → veto. Merece peso propio. |
| **Carrera** | **20%** | 15% | ¿Es IA/data/IT/automatización/soporte con escalabilidad a puesto real? 5=stack directo (Python/APIs/SQL/LLMs), 1=no-IT | Alineación con objetivo `pasantía → puesto real` (`profile.md:Compatibilidades`). Sube porque filtra ruido (Kavak, SAP iXp valen más que roles genéricos). |
| **Ubicación** | **10%** | 20% | ¿AMBA híbrido/presencial o remoto? 5=AMBA híbrido o remoto AR, 3=CABA presencial, 1=fuera AMBA sin remoto | Ya es **veto** si fuera AMBA sin remoto (`rubric-fit.md:Deal-breakers`). Si no veta, no debe pesar 20% — es binario. |
| **Demanda** | **5%** | 10% | ¿Campaña activa / reclutando activo / fecha publicación <30d? 5=publicado <7d + Actively Hiring, 1=>60d sin señales | Señal ruidosa y no controlable; útil para ordenar backlog pero no para decidir fit. |

**Suma 100%.** Deal-breakers sin cambio (veto → 0).

### 3.2 Justificación corta

> ATS 2026 premia **evidencia en bullets con keywords del JD**, no paredes de skills. Por eso Evidencia sube a 40% y exige espejar keywords en **SKILLS + 1er bullet de EXPERIENCE/PROJECTS** (regla `keyword_match.py: WARN 60-80%`). Jornada se independiza a 25% porque 20h part-time es la restricción operativa real (cursada noche Lun-Vie). Carrera sube a 20% para priorizar stack IA/automatización sobre roles genéricos. Ubicación baja a 10% porque ya es veto binario. Demanda baja a 5% por ser señal externa ruidosa.

### 3.3 Migración de scores

- Scores viejos 1-5 siguen válidos; solo cambia ponderación. Para backlog: recalcular top 5 con pesos nuevos y comparar delta (no reescribir tracker histórico).

---

## 4. Tracker — migración `ats_score` (11ª columna)

**Header actual (10 cols):**
```
fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas
```

**Header nuevo (11 cols, opcional, backward-compat):**
```
fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|ats_score
```

**Compatibilidad:**
- Lectores viejos: `line.split("|")` con `maxsplit=9` sigue funcionando; `ats_score` es columna extra al final, ignorable.
- Escritores nuevos: siempre escribir 11 cols; si `ats_score` vacío → `|` final con `""`.
- Sheets maestro: añadir columna K `ats_score` (num 0-100 o vacío) sin tocar fórmulas existentes (que referencian A-J).

**Script:** `scripts/migrate_tracker_add_ats_score.py`
- Idempotente, maneja BOM, comentarios `#`, líneas vacías.
- `--check` para CI; sin flag migra in-place con default `""`.

```bash
python scripts/migrate_tracker_add_ats_score.py --check   # verifica
python scripts/migrate_tracker_add_ats_score.py            # migra
```

---

## 5. Archivos entregados (Sprint 2)

| Archivo | Descripción |
|---|---|
| `scripts/tailor_cv.py` | CLI JD→CV (extract 8-12 kw, score, genera yaml+md, sin inventar) |
| `scripts/migrate_tracker_add_ats_score.py` | Migración tracker 10→11 cols, idempotente |
| `docs/specs/matching_spec.md` | Este spec (auditoría + pipeline + rúbrica + migración) |
| `rubric-fit.md` (patch) | Patch pesos nuevos (ver §6) |

No se hace push por instrucción sprint. Archivos quedan en working tree.

---

## 6. Patch `rubric-fit.md` — aplicar

Ver `rubric-fit.patch` adjunto o aplicar manual:

```diff
-## Dimensiones (peso)
-| Habilidades | 30% | ¿Usa Python/automatización/APIs/Linux/SQL? ...
-| Experiencia/edu | 25% | ...
-| Ubicación/horario | 20% | ...
-| Alineación carrera | 15% | ...
-| Demanda del puesto | 10% | ...
+## Dimensiones (peso) — v2 2026-08-21 (ATS premia evidencia en bullets)
+| Evidencia en bullets | 40% | ¿Cuántos must-have del JD aparecen en bullets de EXPERIENCE/PROJECTS con verbo+resultado (no solo en SKILLS)? 5=≥80% en bullets, 1=<40% |
+| Jornada | 25% | ¿Part-time 20h explícito? 5=20h, 3=part-time sin horas, 1=full-time (veto) |
+| Carrera | 20% | ¿IA/data/IT/automatización/soporte escalable a puesto real? 5=stack Python/APIs/SQL/LLMs |
+| Ubicación | 10% | ¿AMBA híbrido/presencial o remoto AR? (si fuera AMBA sin remoto → veto) |
+| Demanda del puesto | 5% | ¿Campaña activa <30d / Actively Hiring? Señal ruidosa, solo ordena backlog |
```

Y añadir al final de `## Output por oportunidad`:

```
|ats_score| (11ª col opcional, 0-100, default "" si no hay CV tailoreado)
```

---

## 7. Validación

```bash
# Sintaxis
python -m py_compile scripts/tailor_cv.py && echo OK
python -m py_compile scripts/migrate_tracker_add_ats_score.py && echo OK

# Dry-run pipeline
echo "Python SQL Excel dashboard API REST Linux Git automatización prompt engineering agent" > /tmp/JD_test.txt
python scripts/tailor_cv.py --jd-file /tmp/JD_test.txt --empresa demo --dry-run --lang es

# Tracker
python scripts/migrate_tracker_add_ats_score.py --check
```

Criterio de aceptación: `tailor_cv.py --dry-run` reporta coverage y no escribe; `migrate --check` detecta drift si header 10 cols.

---

## 8. Próximos pasos (Sprint 3)

- Añadir `--json` a `keyword_match.py` para que `tailor_cv.py` no duplique lógica.
- Centralizar `REQUIRED_HEADINGS` entre `validate_ats.py` y `yaml_to_md.py`.
- Integrar `validate_ats.py` post-build en `tailor_cv.py --validate`.
- Recalcular top 5 backlog con pesos nuevos y registrar delta en `matriz_fit_postulaciones.md`.
