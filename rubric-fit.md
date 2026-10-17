# Rúbrica de fit — evaluación de postulaciones

Adaptada del framework ai-job-search (MadsLorentzen). Cada oportunidad se puntúa 1-5 en 5 dimensiones. Deal-breakers veto.

## Dimensiones (peso) — v2 life-context (21/08/2026)

| Dimensión | Peso | Qué mira |
|---|---|---|
| Evidencia en bullets | 40% | ¿Tus bullets muestran verb+resultado+keyword JD? (ATS 2026 parsea bullets, no walls) |
| Jornada | 25% | Part-time 20hs Lun-Vie mañana/tarde = 5. Full-time NO es veto (v3, 25/09/2026): puntúa 2-3 según flexibilidad (remoto/horario flexible > presencial rígido) y se **marca el choque con UADE 18:45** en `gap_principal`. Si el aviso es muy bueno (rol IA/automatización, junior real, buen pago, sin exigir experiencia) se evalúa igual |
| Compatibilidad horaria real | 15% | vs Calendar: UADE 18:45-22:15 veto, Psicóloga Lun 14:15 -30, Ritual Vie 10-12:30 -20 (`scripts/calendar_fit.py:1`) |
| Carrera | 15% | ¿Es IA/data/IT escalable a puesto real? |
| Demanda | 5% | Señal externa ruidosa, solo ordena backlog |

## Deal-breakers (veto directo, score final 0)

- Exige inglés certificado avanzado/fluent (tengo B1 sin cert).
- ~~Exige full-time sin opción part-time~~ (ya no es deal-breaker; ver Jornada y regla v3).
- Exige título o 3er año (puede pedir "últimos años" → revisar con cuidado, ver IBM).
- Fuera de AMBA sin remoto.
- Empresa/rol que exigiría mentir en CV para postular.

## Escala

- 4.5–5.0 → Aplicar YA (hoy)
- 4.0–4.4 → Aplicar esta semana
- 3.0–3.9 → Aplicar solo si sobra tiempo / plan B
- <3.0 → Descartar o marcar "seguir de lejos"

## Output por oportunidad evaluada (para tracker)

```
fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas
```

estado: aplicada, aplicando, descartada, pendiente, entrevista, oferta, rechazo, silencio

## Implementación del ranking (14/10/2026)

`scripts/opportunity_rank.py` aplica estas cinco dimensiones como promedio ponderado de 1 a 5 y devuelve `fit_score` (0 cuando un veto obligatorio aplica). `compatibility` se conserva como porcentaje 0–100 por compatibilidad con reportes previos; la columna `Fit` debe recibir `fit_score`, nunca `priority`.

- **Evidencia en bullets (40%)**: extrae competencias del aviso y las busca por separado en el perfil real (`profile.md`, o `profile_text` explícito para una evaluación). El texto del aviso nunca puede servir como evidencia de que el candidato ya domina una competencia. Es una preselección por palabras clave; revisar los bullets reales del CV antes de postular.
- **Jornada (25%)**: 20 h part-time = 5; part-time sin carga confirmada = 4; full-time flexible = 3; full-time rígido = 2; desconocido = 3. Full-time no es veto automático.
- **Compatibilidad Calendar (15%)**: usa `scripts/calendar_fit.py`; un horario explícitamente superpuesto con UADE es veto de elegibilidad. Sin horario, valor neutral y pendiente de revisión.
- **Carrera (15%)**: relación del puesto con IT, datos, IA o tecnología-negocio. Una carrera cuyo nombre no coincida literalmente con UADE no constituye un veto automático.
- **Demanda (5%)**: señal explícita `demand_score` de 1 a 5; sin señal se utiliza 3 neutral.

`priority` es solo orden de revisión: pondera `fit_score` por elegibilidad y antigüedad confirmada. No sustituye el score 1–5 ni convierte una señal de fecha en publicación original.

El parser horario acepta rangos `HH-HH`, `HH:MM-HH:MM`, guion en dash/em dash y “a/hasta”; si el formato no se puede interpretar, la compatibilidad queda pendiente y neutral.

### Evidencia y elegibilidad

- `publication_date_verified: true` solo se establece cuando el pipeline encuentra una fecha válida en una fuente de fecha original (`greenhouse`, `lever`, `uade`, `ashby`, `workday` o `smartrecruiters`). El agregador conserva fecha y URL como evidencia, pero no demuestra publicación original.
- `verified_requirements` admite un mapa o una lista. Cada registro puede incluir `requirement`, `status`, `met`, `evidence`, `source`, `source_url` y `verified_at`. Solo `met: true`/`satisfied: true` o estados `met`, `satisfied`, `eligible`, `open` y `current` acreditan cumplimiento. `status: verified` confirma que se revisó el hecho, no que el candidato cumpla el requisito.
- `mandatory_gaps` siempre veta salvo que el mismo requisito tenga evidencia verificada de cumplimiento.
- `closed: true` o un `posting_status` explícitamente cerrado veta. Los estados de la postulación propia se guardan aparte y no determinan el estado del aviso.
- La respuesta separa `verification.confirmed`, `verification.inferred` y `verification.pending`; ninguna inferencia reemplaza la lectura del aviso original.

### Identidad y deduplicación

El pipeline prioriza ID estable con espacio de nombres por fuente; luego admite una URL canónica exacta y, si faltan ambas, un fingerprint que también incorpora fuente, fecha y descripción completa. Empresa+título+ubicación por sí solos nunca fusionan avisos. Los registros fusionados conservan URLs, IDs, observaciones y evidencia de fecha. El libro de ciclo de vida migra su estado anterior a la clave nueva y deja una referencia `migrated_to`, sin sobrescribir el estado manual.
