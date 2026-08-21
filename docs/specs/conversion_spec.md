# Conversion Sprint 3 — Spec v1 (2026-08-21)

> Agente Conversion — Nacho Palmeri, Sprint 3/4. Repo `job-search`, ATS supremo v2 hecho, 3 cartas en `extras/cartas_presentacion/`, portfolio `ignaciopalmeri.vercel.app`, tracker sin CRM.

## 1. Auditoría cartas_presentacion/ (3)

**Archivos:** `CV_Material_Nacho/extras/cartas_presentacion/carta_{lotba_investigacion,analista_procesos,paid_media}.{md,pdf,docx}` (9 archivos, 3 MD fuente).

| Carta | Target tracker | Estructura | Honestidad | Gap |
|---|---|---|---|---|
| `carta_lotba_investigacion.md:1` | LOTBA 2026-1884 OSINT | 3 párrafos: P1 presentación UADE 2º Q4 8.2 + encaje OSINT; P2 metodología trazable + Excel/SQL/Python + informes; P3 cierre entrevista + portfolio links | OK — cita sistema trazable verificable en `cv_lotba_investigacion.md:32-36`, no inventa métricas | Bien modelo — usar como plantilla |
| `carta_analista_procesos.md:1` | 2026-1855 Procesos/Adquisiciones | P1 gestión=core carrera; P2 dashboard franquicia real + Excel; P3 afín Económicas no excluyente | OK — proyecto FranquiYA 57 commits verificable `profile.md:35` | Párrafo 2 podría citar indicadores/KPI verbatim del JD para ATS keyword mirroring |
| `carta_paid_media.md:1` | 2026-1885 Paid Media | P1 perfil analítico + curiosidad digital; P2 pipelines/reportes/BI + Excel + IA; P3 ganas de aprender paid | OK pero es el más débil en evidencia — no tiene móvil pagos/campañas, lo declara como aprendizaje (honesto) | No infla — correcto |

**Patrón común (positivo):** encabezado `Buenos Aires, 19 ago 2026` + `Estimados/as` + cierre con **Ignacio Palmeri** + tel/email + `ignaciopalmeri.vercel.app · github.com/nachopalmeri · linkedin.com/in/ignaciopalmeri`. Consistente con `profile.md:6-12` (sin inventar). Longitud 180-220 palabras → ideal para email body + PDF 1 pág.

**Gaps auditoría (no bloqueantes):**
- No hay placeholders parametrizables (`{empresa}`, `{rol}`, `{por_que_empresa}`) — cada carta es copia manual. Riesgo drift si se hacen 20 más.
- No incluye `Asunto:` ni `filename.pdf` canónico (`Ignacio_Palmeri_<Empresa>_Carta.pdf`).
- No hay validación anti-invención (ej: si JD pide "Looker Studio" y no existe en YAML, la carta debe dejar gap explícito, no espejar).
- Las 3 cartas usan "Adjunto mi CV y enlaces" — bien, pero no citan `/cv` ruta directa (ver §3).

## 2. Auditoría portfolio `ignaciopalmeri.vercel.app` (fetch 2026-08-21)

**Fetch:** `GET https://ignaciopalmeri.vercel.app` (Vercel, SPA, `lang=es data-theme=dark`, ~21KB HTML shell + `style.css`).

| Check SEO/GEO | Estado | Evidencia |
|---|---|---|
| `<title>` | OK | `ignaciopalmeri - Junior AI Automation & Product Engineer` |
| `meta description` | OK (débil) | `Portfolio de ignaciopalmeri: automatización, producto...` (97 chars, sin keywords "pasantía/IT/Buenos Aires/UADE") |
| `canonical` | **FAIL** | `rel="canonical"` ausente |
| `og:url` / `og:image` | **FAIL** | solo `og:title/description`, sin `og:url`, `og:type`, `og:image` |
| `twitter:card` | **FAIL** | ausente |
| `application/ld+json` | **FAIL** | ningún `schema.org` |
| `Person` schema | **FAIL** | no hay `Person` |
| `JobPosting` schema | **FAIL** | no aplica en home (bien ausente); sí debería en `/empleo` si existiera |
| `sitemap.xml` / `robots.txt` | **FAIL** | no linkeado, `fetch /sitemap.xml` → 404 probable (Vercel static sin file) |
| `/cv` ruta | **FAIL** | no existe; CV solo como file en repo, no URL citable en carta |
| `<h1>` | OK | 1 H1 presente |
| `alt` / a11y | Parcial | `aria-label` en nav ok, pero faltan `alt` en proyectos |
| i18n | OK | toggle ES/EN con `data-lang-btn` |
| Backlinks GitHub → portfolio | Parcial | repos tienen `vercel.app` en description pero README.md de `jobbot`/`FranquiYA` no tienen badge/link prominente arriba del fold |

**Impacto GEO/AEO:** sin `Person` schema, ChatGPT/Perplexity no extraen `sameAs: [github,linkedin,vercel]` ni `alumniOf: UADE`. Sin `sitemap`, Vercel indexa lento. Sin `/cv`, la carta no puede linkear `vercel.app/cv` como CTA trackeable.

## 3. Generador cover letter automático

**Entrega:** `scripts/generate_cover_letter.py` (ver archivo).

**Diseño:**
- Input: cada `CV_Material_Nacho/extras/cvs_personalizados/cv_*.md` (fuente tailoreada) + `cv_master.yaml` (truth) + `tracker/applications.csv` (metadata empresa) o `--empresa`/`--jd-file` manual.
- Output: `CV_Material_Nacho/extras/cartas_presentacion/cover_letter_<empresa>.txt` (plain text email-ready) + `.md` opcional.
- Plantilla 3 párrafos (sin inventar):
  1. **Por qué vos:** `Soy {name}, estudiante {area UADE} Q4 8.2/10` + 1-2 proyectos reales del MD fuente (párrafo PROJECTS 1er bullet) + disponibilidad 20hs. Solo si MD contiene keyword, la cita.
  2. **Por qué empresa:** si `jd_text` provisto, extrae 1 frase del aviso (primer oración del JD) o `empresa`+`titulo` del tracker. Si no hay JD, usa genérico honesto: "la búsqueda de {titulo} en {empresa} combina {skills del MD} con {ubicacion/modalidad}". Nunca inventa mission/valores.
  3. **Cierre con portfolio:** "Quedo a disposición para entrevista. Portfolio: https://ignaciopalmeri.vercel.app/cv — CV adjunto {filename profesional}. Contacto: {email} {tel} | {linkedin} | {github}". CTA trackeable a `/cv`.
- Reglas anti-invención: `ALLOWLIST` = texto de `cv_master.yaml` flatten + MD fuente. Si JD keyword no está en allowlist, no se espeja; se deja gap. Bloquea `BILINGUE/ADVANCED/RHCSA/CCNA certificado/DApp/Web3` (profile.md:41-44).
- CLI: `python scripts/generate_cover_letter.py --all` barre `cvs_personalizados/cv_*.md` → genera `cover_letter_*.txt` si no existe o con `--force`. Soporta `--empresa sap --jd-file aviso.txt --lang en`. Valida `len(parrafos)==3` y `portfolio` presente.

**Integración ATS:** tras generar, el flujo sugiere `python CV_Material_Nacho/extras/generate_cv_files.py <md>` + `validate_ats.py` antes de enviar.

## 4. Portfolio SEO mejoras (spec implementación)

**Target:** `ignaciopalmeri.vercel.app` (Vercel, repo privado `portfolio` — asumir Next.js o HTML estático según `style.css` existente).

### 4.1 `<head>` meta

```html
<link rel="canonical" href="https://ignaciopalmeri.vercel.app/">
<meta name="author" content="Ignacio Palmeri">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ignaciopalmeri.vercel.app/">
<meta property="og:image" content="https://ignaciopalmeri.vercel.app/og-cover.jpg"> <!-- 1200x630 -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:creator" content="@nachopalmeri"> <!-- si existe, sino omitir -->
<link rel="alternate" hreflang="es" href="https://ignaciopalmeri.vercel.app/">
<link rel="alternate" hreflang="en" href="https://ignaciopalmeri.vercel.app/en">
```

Descripciones ES/EN con keywords reclutador: `Estudiante Lic. Gestión TI UADE (2º año) — pasantía part-time 20hs IA/IT Buenos Aires | Python, SQL, LLMs | Proyectos con evidencia`.

### 4.2 Schema.org `Person` (JSON-LD en `<head>`)

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Ignacio Palmeri",
  "alternateName": "Nacho Palmeri",
  "url": "https://ignaciopalmeri.vercel.app",
  "image": "https://ignaciopalmeri.vercel.app/avatar.jpg",
  "sameAs": [
    "https://github.com/nachopalmeri",
    "https://linkedin.com/in/ignaciopalmeri",
    "https://ignaciopalmeri.vercel.app"
  ],
  "jobTitle": "Estudiante Lic. Gestión de TI — Busco pasantía part-time IA/IT",
  "alumniOf": {"@type":"CollegeOrUniversity","name":"UADE"},
  "address": {"@type":"PostalAddress","addressLocality":"Buenos Aires","addressCountry":"AR"},
  "knowsAbout": ["Python","SQL","Excel","FastAPI","Next.js","LLMs","Automatización"],
  "availableLanguage": ["es","en"],
  "seeks": {"@type":"Demand","name":"Pasantía part-time 20hs IA/IT"}
}
```

No usar `JobPosting` en home (es para el empleador). Si se crea `/empleo` para que empresas posteen, ahí sí `JobPosting`.

### 4.3 Ruta `/cv`

- Crear `public/cv/index.html` o `app/cv/page.tsx` que sirva el PDF maestro `Ignacio_Palmeri_CV_ES.pdf` embebido + botón descarga + canonical `https://ignaciopalmeri.vercel.app/cv`.
- Añadir `Link: <https://ignaciopalmeri.vercel.app/cv>; rel="canonical"` y meta `noindex` solo si es duplicado del PDF. Mejor: HTML con resumen + `embed` PDF.
- Carta y LinkedIn apuntan a `/cv` (trackeable con `?utm_source=carta&utm_campaign=<empresa>`).

### 4.4 `sitemap.xml` + `robots.txt`

```
# public/robots.txt
User-agent: *
Allow: /
Sitemap: https://ignaciopalmeri.vercel.app/sitemap.xml

# public/sitemap.xml (generado por next-sitemap o manual)
<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">
  <url><loc>https://ignaciopalmeri.vercel.app/</loc><priority>1.0</priority></url>
  <url><loc>https://ignaciopalmeri.vercel.app/cv</loc><priority>0.9</priority></url>
  <url><loc>https://ignaciopalmeri.vercel.app/en</loc><priority>0.8</priority></url>
</urlset>
```

Config Vercel: `vercel.json` con `cleanUrls: true`, `trailingSlash: false`.

### 4.5 Backlinks GitHub README

En cada repo público (`jobbot`, `FranquiYA`, `prode-mundial-2026`, `agents-system`) añadir arriba del fold:

```md
> **Portfolio:** [ignaciopalmeri.vercel.app](https://ignaciopalmeri.vercel.app) · **CV:** [vercel.app/cv](https://ignaciopalmeri.vercel.app/cv) · **LinkedIn:** [linkedin.com/in/ignaciopalmeri](https://linkedin.com/in/ignaciopalmeri)
```

Badge opcional: `[![Portfolio](https://img.shields.io/badge/portfolio-vercel-black)](https://ignaciopalmeri.vercel.app)`.

### 4.6 Métricas

Verificar con `curl -I /sitemap.xml`, `https://validator.schema.org`, `og:debug` (Facebook Sharing Debugger), y `site:ignaciopalmeri.vercel.app` en Google.

## 5. Follow-up CRM — tracker como CRM

**Estado actual:** `tracker/applications.csv:1` header 10 cols `fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas` (80 filas, `|` sep, `#` comentario). Sin `contacto_interno`, sin `fecha_followup`, sin SLA. Fuente verdad = Google Sheets `Tracker de postulaciones — Ignacio Palmeri` (ver `README.md:32`).

**Diseño target (12-13 cols):**

```
fecha|portal|titulo|empresa|ubicacion|link|fit_score|gap_principal|estado|notas|contacto_interno|fecha_followup|ats_score
```

- `contacto_interno` (antes 11): texto libre `Nombre (rol) <email|whatsapp>` ej `Fátima (Team & People) WhatsApp 5/8`.
- `fecha_followup` (antes 12): ISO `YYYY-MM-DD`, calculada `fecha +7d` hábiles (si cae finde → lunes). Vacía si `estado in (descartada,radar)`.
- `ats_score` (13): ya propuesto en `docs/ats-supremo-spec.md:54` y `migrate_tracker_add_ats_score.py:13` — conservar.
- Compatibilidad: migración idempotente, añade `||` si faltan. Sheets: insertar columnas sin mover histórico.

**Máquina de estados (columna `estado`):**

`pendiente → aplicar YA/a enviar → aplicada → entrevista → oferta/rechazo`  
`backup/semana/evaluar/descartadas/radar/verificar` son holding. `fecha_followup` solo para `aplicada|entrevista|a enviar|aplicar YA`.

**Script:** `scripts/migrate_tracker_add_crm.py` (idempotente, BOM-safe):
- Detecta header 10 vs 11 vs 12 vs 13.
- Añade `contacto_interno|fecha_followup` (y `ats_score` si falta).
- Backfill `fecha_followup = fecha +7d` para filas con `estado in (aplicada,entrevista,a enviar,aplicar YA)` y sin fecha.
- `--check` para CI, `--backfill` para rellenar.

**Bot Telegram ping (sin push, spec):**

- Nuevo `scripts/crm_followup.py` (o extensión `buscar_portales.py`):
  - Lee `tracker/applications.csv` (o Sheets API si creds).
  - Filtra `fecha_followup == hoy ±1d` y `estado not in (descartada,radar,ofertada)`.
  - Mensaje: `⏰ Follow-up hoy: {empresa} — {titulo} ({estado}) — contacto: {contacto_interno} — link: {link} — notas: {notas[:120]}`
  - Envío: `TELEGRAM_BOT_TOKEN` en `.secrets/telegram_token.json` (gitignored, ver `.gitignore:10`) + `TELEGRAM_CHAT_ID` (ASK). Usa `https://api.telegram.org/bot{token}/sendMessage` vía `urllib.request` (sin deps). Modo `DRY_RUN=1` loggea sin enviar.
  - Cron: `0 9 * * 1-5` (lun-vie 09:00 AMBA) `py scripts/crm_followup.py --check` — valida `bin/check-secrets.ps1` antes.

**Patch tracker entregado:** `scripts/migrate_tracker_add_crm.py` aplicado localmente con `--backfill` deja `applications.csv` con 13 cols. No rompe `buscar_portales.py` (lee por índice/nombre). Sheets manual: replicar columnas `K: contacto_interno`, `L: fecha_followup`, `M: ats_score`, copiar valores locales.

## 6. Archivos entregados y diff (sin push)

- `docs/specs/conversion_spec.md` (este archivo)
- `scripts/generate_cover_letter.py` (nuevo, ~180 líneas)
- `scripts/migrate_tracker_add_crm.py` (nuevo, ~110 líneas)
- `scripts/crm_followup.py` (nuevo, ~90 líneas)
- `tracker/applications.csv` (modificado: 10→13 cols, backfill +7d)
- Portfolio: spec en §4 (no se pushea código Vercel aquí; cambios en repo portfolio separado).

```bash
git diff --stat # estimado
#  docs/specs/conversion_spec.md       | 220 +++
#  scripts/generate_cover_letter.py    | 180 +++
#  scripts/migrate_tracker_add_crm.py  | 110 +++
#  scripts/crm_followup.py             |  90 +++
#  tracker/applications.csv            |   2 +- (header + backfill)
```

Validación:
- `py scripts/generate_cover_letter.py --dry-run --all` → 3 cover_letter_*.txt preview sin escribir.
- `py scripts/migrate_tracker_add_crm.py --check` → OK 13 cols.
- `py scripts/crm_followup.py --dry-run` → lista follow-ups vencidos.

No push por instrucción sprint.
