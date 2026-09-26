# Portales argentinos — investigación 2026 (para la búsqueda diaria)

Resultado de la investigación (ago 2026) + conocimiento del mercado. Ordenados por prioridad para el perfil: pasantía IT / estudiante sistemas / part-time.

> **Fuente v2 (pestañas abiertas del usuario, 5/8/2026):** 23 pestañas clasificadas en 8 categorías al final de este archivo. Se incorporó: Portal UADE (login), FirstJob, Wellfound, Y Combinator, GoodVibeCode, Vibehackers, Appgentina, Credly, y el tracker propio en Google Sheets.

## Tier 1 — revisar TODOS los días (máxima señal)

| Portal | URL búsqueda | Notas / cómo usarlo |
|---|---|---|
| **BecasIT** | https://becasit.itechcareer.com/pasantías | El que ya usamos: 14+ pasantías IT activas (Analista IA, Python, DBA, Infra). Tiene avisos por mail directo (empleo@itechCareer.com) — estrategia: enviar email con pretensión salarial (placeholder $[MONT0]). Revisar "Pasantías IT" a diario. |
| **LinkedIn** | linkedin.com/jobs | Principal canal B2B. Configurar alertas: "pasantía", "trainee", "programa jóvenes talentos", "estudiante sistemas", "IT", "IA". Activar OpenToWork (reclutadores ven el perfil). Para scraping: endpoints guest (uso personal bajo, respetar ToS) |
| **Computrabajo** | ar.computrabajo.com/trabajo-de-tecnologia | Sección tecnología con junior/pasante. Avisos frescos "Urgente" (ej. Mesa de Ayuda JR 11-20hs, Help Desk 9-15hs, Desarrollador JAVA Junior). Los avisos con horario part-time son oro para nosotros. |

## Tier 2 — 2-3 veces por semana

| Portal | URL | Notas |
|---|---|---|
| **Bumeran** | bumeran.com.ar | Estándar argentino, integrado con reclutadoras (IBM usa Bumeran). Exige sueldo pretendido en algunos avisos → usar rango mercado ($250–500K, ajustar). Bloquea scrape (auth/Cloudflare) → links manuales. |
| **Empleos IT** | empleosit.com.ar | Bolsa especializada IT argentina desde 2011. Tiene avisos de pasantía y jr. |
| **Get on Board** | getonbrd.com.ar | Tech/startups, incluye remoto. Buenos perfiles IA/data. API pública JSON para autofetch. |
| **Jooble** | ar.jooble.org | Metabuscador — agarra avisos de todo (1657 vacantes "pasantía programador BA"). Bueno para descubrir programas (ExxonMobil Internship, YPF Pasantías, INKOMPASS Philip Morris, JEI, SeedZ, Central Puerto). Usar como radar, aplicar en el portal original. |
| **Indeed** | ar.indeed.com | Metabuscador con filtro por "pasantía". Mucho ruido, útil como radar. |

## Tier 3 — semanal o por campaña

| Portal | URL | Notas |
|---|---|---|
| **ZonaJobs** | zonajobs.com.ar | Avisos exclusivos de CABA en algunos casos. |
| **Empleos AMIA (SEA)** | empleos.amia.org.ar | Base de postulantes + empresas, tradicional de Argentina. |
| **Portal Empleo (Gob. AR)** | argentina.gob.ar/trabajo/empleo | Ofertas verificadas, programas nacionales. |
| **Jobsora** | ar.jobsora.com | Metabuscador con filtro "pasantías estudiantes BA". |
| **Google Empleos** | google.com/search?q=...&ibp=htl;jobs | Agrega todo lo anterior. Útil como búsqueda programática diaria con keywords. |
| **Universia / bolsas universitarias** | universia.net | Ofertas para estudiantes; la UADE tiene su propia bolsa (revisar campus UADE). |

## Fuentes agregadas en v3 (25/09/2026) — scrapeables en `--scrape all`

| Fuente | Cómo se scrapea | Notas |
|---|---|---|
| **Startups Argentina** `/empleos?page=N` | HTML SSR, ~400 avisos en 18 páginas (el viejo `/jobs` con `job-card` ya no existe; el parser anterior devolvía 0 en silencio) | Filtro de relevancia por título (`_relevant`) para no volcar 400 filas. Full-time ya no es veto |
| **YC Work at a Startup** `ycombinator.com/jobs/role/<rol>/remote` | HTML SSR, ~34 avisos por rol (roles: software-engineer, operations, support-success, science, product-manager) | Solo remoto alcanzable desde AR (LatAm/AR/"Remote" a secas). Cobertura parcial: el sitio pagina en JS |
| **a16z Speedrun Talent Network** `speedrun-talent-network.com/api/jobs` | API JSON (`remote=1&q=<kw>&page=N`); ojo: Cloudflare bloquea el UA completo, usar `User-Agent: Mozilla/5.0` | ~6.600 roles; "Remote" suele ser US-only: verificar a mano antes de postular |

## Radar de programas (campañas anuales — revisar mensual)

ExxonMobil Internship, YPF Pasantías, INKOMPASS (Philip Morris), Programa JEI, SeedZ (trainees), Central Puerto (pasante de datos — ¡Python + pandas! buen fit), Amazon Internships, IBM (Req 127046), Wetcom Jóvenes Talentos, BecasIT.

## Portal UADE (crítico — exclusivo de estudiantes)

| Portal | URL | Notas |
|---|---|---|
| **Portal de Empleos UADE** | https://www.empleos.uade.edu.ar/ (login con libreta universitaria) | Exclusivo alumnos y graduados. **3.600+ instituciones, 1.800 convenios de pasantía/año**, filtros por Pasantía / Efectivo / Joven Profesional, y por carrera. Obligatorio: cargar CV en PDF, **actualizar datos cada 2 meses** (si no, se inactiva el registro y no sos candidato). Es el canal #1 para pasantías reales con Ley 26.427. |
| UADE — Búsquedas laborales | uade.edu.ar/acerca-de-uade/desarrollo-profesional.../busquedas-laborales/ | Página índice de ofertas; el paso de aplicar se hace en el portal con login. |

**Acción inmediata:** cargar CV y activar el perfil hoy en `empleos.uade.edu.ar/busquedaslaborales`. Es una fuente que no tiene competencia de toda la web — solo alumnos UADE.

## Incorporación de pestañas del usuario (23, 5/8/2026)

Clasificación por categoría. Se añaden a la rutina diaria según su tier.

### A. Bolsas universitarias / pasantías formales
| Portal | URL | Rol en la rutina |
|---|---|---|
| **Portal de Empleos UADE** | *empleos.uade.edu.ar* | Tier 1 (login) — hay una periodicidad de 2 meses de actualización de CV. |
| **EMPLEOS UADE — Búsquedas disponibles** | empleos.uade.edu.ar/busquedaslaborales | Mismo portal, página de listado. Tier 1. |
| **FirstJob** | firstjob.com / (verificar dominio vigente) | Especializada en "Práctica, Pasantía, Internship y primeros trabajos" — target directo de nuestro perfil. Investigar cobertura AR; si aplica, Tier 1. |
| **BecasIT** (ya listado) | becasit.itechcareer.com/pasantías | Tier 1 (existente). |

### B. Portales generales / tech
- **Indeed Argentina** (8) — Tier 2 (ya listado).
- **Bumeran** ("Bolsa de trabajo Argentina · Portal de empleo Líder en Argentina", 11) — Tier 2.
- **LinkedIn Feed** (8) — Tier 1; el Feed importa para oportunidades "ocultas" (puestos compartidos por reclutadores).
- **Empleos IT** (18) — Tier 2 (ya listado).
- **Get on Board** (14) — Tier 2 (ya listado; API caída, usar web).

### C. Startups / tech / remoto
| Portal | Notas |
|---|---|
| **Wellfound** (9) | wellfound.com — bolsa de startups (ex AngelList), perfiles de empresas de product. Buen candidato a Tier 2 para roles tech en startups early (remoto LATAM). |
| **Y Combinator — Work at a Startup** (7 + Events) | ycombinator.com/work-at-a-startup + events.ycombinator.com: program startups, hiring portal de YC. Útil para ver el ecosistema y algunos roles remotos LatAm. Tier 3. |
| **Vibe Coding Jobs — GoodVibeCode** (12) | goodvibecode.io o similar: roles de AI developer / vibe coding. Nicho naciente; útil como radar novedoso. Tier 3. |
| **Vibehackers** (13) | vibehackers.com: proyectos de vibe coding hechos en público — no es portal de empleo sino comunidad/proyectos. Útil para detectar gente y oportunidades en ciernes. Tier 3. |

### D. **AI / data entry / microtask** (ingresos flexibles, NO pasantía)
- **Alignerr powered by Labelbox** (1) — alineación de datos para AI/RLHF, pago por tareas. Compatible con 20hs.
- **Prolific** (2) — academia, estudios pagos, encuestas y experimentos. Compatible, ingreso modesto.
- **Outlier** (3) — outlier.ai, entrenamiento de IA (labels/corecciones). Flexibilidad total remoto.
- **DataAnnotation** (4) — similar a Outlier, proyectos de anotación. No siempre alocan 10hs; revisar disponibilidad.

> Nota honesta: estos cuatro NO son pasantía IT ni aportan a la carrera como Wetcom/BecasIT/UADE; son income lado flexible. Útiles para cubrir el hueco del monto $[MONT0] mientras sale lo grande, pero no hay que ponerlos como "experiencia IT" en CV. 

### E. Beneficios / credenciales
- **Credly — Editar perfil** (20) — credly.com: badges verificables (probablemente CCNA/NetAcad). Importante: **vincular Credly al perfil de LinkedIn** para que las insignias se vean y validar el CCNA en curso. Tier 3.

### F. Thanks de crecimiento
- **Appgentina** (23) — appgentina.com: eventos de tecnología en Argentina. Útil para networking presencial (meeting con JTs y reclutadores). Tier 3.
- **Robertino Barbuto · Dev freelance** (22) — probablemente referencias de freelancers para redes; revisar si es contacto real para networking.

### G. Tracker propio del usuario
- **Tracker de postulaciones — Ignacio Palmeri (Google Sheets)** (21) — existe UN tracker en Hojas de cálculo del usuario. El CSV (`tracker/applications.csv`) es el canonical del skill; hay que mantenerse sincronizado con el Sheets del usuario (o usar el Sheets como fuente de verdad y el CSV como backup). **Confirmar con el usuario cuál es el sistema maestro.**

> **DECISIÓN (5/8/2026):** el usuario confirmó que el **maestro es su Google Sheets** ("el maestro es mi spreadsheet que ya vengo usando"). El `tracker/applications.csv` local queda como **backup/estado del skill**, y cualquier nueva postulación se registra primero en el Sheets del usuario y después (opcional) en el CSV.

### H. Incorporación v3 (5/8/2026) — Startups Argentina, Silver.dev, InfoJobs
| Portal | URL | Verificación | Clasificación |
|---|---|---|---|
| **Startups Argentina** | startupsargentina.com/jobs | ✅ DNS ok; directorio de startups argentinas + feed de posiciones abiertas con fecha, etapa y link de aplicar. El feed `/jobs` y las fichas `/startups/{slug}` renderizan SSR (scrapeable). | Tier 2 (scrapeable + radar startups locales) |
| **Silver.dev** | silver.dev/argentina | ✅ Talent agency LatAm→US startups (Scale AI, Ramp, Nubank). Requiere **Senior+, inglés fuerte, full-time, timezone US** | ❌ NO apto hoy (perfil senior). Radar largo plazo (3-4 años) |
| **InfoJobs** | infojobs.net (España) | ⚠️ **No hay versión argentina** (`infojobs.com.ar` y `ar.infojobs.net` no resuelven); la .net es España | Descartado para búsqueda local; solo si hubiera avisos remotos globales |

**Conclusiones de la pasada v3:** Bumeran, Indeed, Computrabajo, InfoJobs y similares ya estaban cubiertos en Tier 1/2. Lo nuevo útil: **Startups Argentina** (radar de startups locales) y la confirmación de que Silver.dev no corresponde al perfil. InfoJobs descartado (no opera en AR).

## Notas técnicas de scraping (para el script)

- **Scrapeable directo (sin auth)** — 5 fuentes en el scraper unificado:
  - **LinkedIn guest** `f_TPR=r604800&f_E=1` → las ~15-40 pasantías de la semana (primera página; paginación pide login → alcanza con 1).
  - **Startups Argentina** `/jobs` y `/startups/{slug}` (SSR, sin JS).
  - **Computrabajo** `ar.computrabajo.com/trabajo-de-{kw}` (SSR con `article.box_offer` + `js-o-link`).
  - **BecasIT** `becasit.itechcareer.com/pasantías` (Google Sites SSR; título en el `<hN>` del collapse de cada bloque `oKdM2c ZZyype`).
  - **EmpleosIT** `https://www.empleosit.com.ar/rss/` (feed RSS real con título, link, ubicación, modalidad y jornada).
- **No scrapeable / manual**: Bumeran, ZonaJobs, Jooble (Cloudflare), Indeed (bloquea bots), Wellfound (SPA), FirstJob, Get on Board, UADE (login), paginación de LinkedIn (pide login), EmpleosIT app (solo funciona el RSS público).
- Estrategia: `python scripts/buscar_portales.py --scrape all --write` consolida las 5 fuentes a `radar/daily-YYYY-MM-DD.tsv`; el **agente libre** (prompt `scripts/prompts/agente-libre.md`) cubre Google Empleos, bolsas manuales y radar de campañas en la web abierta → `radar/discoveries-YYYY-MM-DD.md`.
- Keywords términos: `pasantía`, `pasante`, `trainee`, `programa jóvenes talentos`, `estudiante sistemas`, `junior`, `part-time`, `IT`, `IA`, `python`, `datos`, `soporte`, `help desk`, `analista`.
- Zona: Buenos Aires / AMBA / híbrido / remoto Argentina.