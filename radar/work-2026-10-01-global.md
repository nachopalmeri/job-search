# Evaluación work — lote global: YC + Speedrun + web abierta (ventana 2026-09-28 a 2026-10-01)

Evaluado el 2026-10-01. Fuente base: `radar/daily-2026-10-01.tsv` (sin correr scraper). Regla: solo elegible si la página oficial confirma publicación entre 2026-09-28 y 2026-10-01 inclusive **y** permite trabajar desde Argentina (US-only / visa / relocation / SkillBridge militar EEUU → excluyen). Fecha desconocida, solo-updated, login o 403 → NO_VERIFICABLE, no se puntúa.
Dedup empresa+puesto vs `tracker/postulaciones.csv` y `discoveries-2026-09-27/28/29.md` + `discoveries-2026-10-01.md`: sin coincidencias postuladas; las referencias previas se citan fila por fila.
Perfil: Nacho Palmeri, 19, 2.º año Gestión de TI UADE (15/40), Temperley, cursa Lun-Vie 18:45–22:15, inglés B1 autoevaluado sin certificar, sin experiencia IT. Rúbrica `rubric-fit.md` v2.
Método fecha YC: las páginas de ycombinator.com no muestran fecha visible; se leyó el JSON embebido (`createdAt` relativo + ISO `createdAt` del job), ej.: Astraea `"createdAt":"3 days"` + `2026-09-28T20:47`.

## 1. Y Combinator (4 filas del TSV — lista completa)

| # | Título | Empresa | Fecha origen (JSON YC) | Estado de verificación |
|---|---|---|---|---|
| 1 | QA Engineer | Astraea (P26) | **2026-09-28** ("3 days" + ISO) | **EN_VENTANA — leído completo** → eval abajo (fit 3.1) |
| 2 | Client Support Specialist (Healthcare Facilities - B2B) | Clipboard (W17) | 2025-02-27 ("over 1 year") | **FUERA_DE_VENTANA** — leído completo igualmente (ver §4) |
| 3 | Backend Engineer | GoGoGrandparent (S16) | 2025-07-21 ("about 1 year") | **FUERA_DE_VENTANA** — solo metadata leída, sin puntuar |
| 4 | Founding Full Stack AI Engineer | Rhizome AI (W26) | 2026-05-24 ("4 months") | **FUERA_DE_VENTANA** — además ya referenciada en `outbound-2026-09-29.md` ("acepta AR pero sin fundador AR verificado; excluida") |

Links:
1. https://www.ycombinator.com/companies/astraea/jobs/B99nCmA-qa-engineer
2. https://www.ycombinator.com/companies/clipboard/jobs/EYlMYBU-client-support-specialist-healthcare-facilities-b2b
3. https://www.ycombinator.com/companies/gogograndparent/jobs/2vbzAw8-backend-engineer
4. https://www.ycombinator.com/companies/rhizome-ai/jobs/Qi521kH-founding-full-stack-ai-engineer

Cobertura YC: 4/4 con fecha verificada en el JSON de la página oficial. En ventana: 1. Leídos completos: 2 (Astraea + Clipboard). Puntuados: 1 (solo en ventana).

## 2. Speedrun (17 filas del TSV — lista completa)

La columna `fecha` del TSV coincide con el "posted on" del origen (verificado el 1/10 con GE Vernova 4b6a4d28). Todo con fecha < 2026-09-28 → fuera de ventana, **sin re-leer** (regla del lote).

| # | Título | Empresa | Fecha | Estado |
|---|---|---|---|---|
| 1 | Entry Level Technical Field Advisor (TFA) Steam Turbine | GE Vernova | **2026-09-29** | **EN_VENTANA — ya evaluado el 1/10 en `work-01-eval-otros.md`**: fit **1.0**, descartado (solo EE.UU. "legally authorized to work in the United States", título Ing. Mecánica o 4 años, 80 % de viajes). Cita, no re-evaluado. |
| 2 | Entry Level Technical Field Advisor (TFA) Steam Turbine | GE Vernova | 2026-09-25 | FUERA_DE_VENTANA (25/9) + DUPLICADO empresa+puesto del #1 (otro ID de aviso) |
| 3 | Services Internship - Engineering-1 | GE Vernova | 2026-09-24 | FUERA_DE_VENTANA (24/9); referenciado sin evaluar en `discoveries-2026-09-27.md` #29 (3.6*) |
| 4 | Software Engineer - Intern | Realm | 2026-08-26 | FUERA_DE_VENTANA; además descartado por país (EE.UU.) en `discoveries-2026-09-28.md` |
| 5 | Product Design Co-op – International Growth | Ancestry | 2026-08-25 | FUERA_DE_VENTANA (además rol de diseño, no IT) |
| 6 | Junior Quantitative Trader | DV Trading | 2026-08-19 | FUERA_DE_VENTANA (además rol de trading, no IT/IA) |
| 7 | Data Analyst, User Operations | Cursor | 2026-06-24 | FUERA_DE_VENTANA |
| 8 | CX Data Analyst | Harvey | 2026-06-15 | FUERA_DE_VENTANA; referenciado sin evaluar en `discoveries-2026-09-27.md` #35 (3.5*) |
| 9 | Junior UA/Growth Manager | Xsolla | 2026-04-28 | FUERA_DE_VENTANA |
| 10 | Software Engineer, Windows AI Automation | Sola | 2026-04-08 | FUERA_DE_VENTANA |
| 11 | SkillBridge Intern - Growth | Rise8 | 2025-05-02 | FUERA_DE_VENTANA + **SkillBridge = solo veteranos militares de EEUU** (excluyente) |
| 12 | SkillBridge Intern - Marketing | Rise8 | 2025-12-12 | FUERA_DE_VENTANA + SkillBridge (excluyente) |
| 13 | SkillBridge Intern - Product Manager | Rise8 | 2024-04-25 | FUERA_DE_VENTANA + SkillBridge (excluyente) |
| 14 | SkillBridge Project Management Internship | Technergetics | 2024-03-13 | FUERA_DE_VENTANA + SkillBridge (excluyente) |
| 15 | Intelligence Skillbridge Intern | Flashpoint | 2025-02-04 | FUERA_DE_VENTANA + SkillBridge (excluyente) |
| 16 | Customer Support Specialist | Cluely | 2025-11-30 | FUERA_DE_VENTANA |
| 17 | Research Intern | Gensyn | 2025-04-23 | FUERA_DE_VENTANA |

Links: #1/#2 https://speedrun-talent-network.com/jobs/entry-level-technical-field-advisor-tfa-steam-turbine-ge-vernova-4b6a4d28 (y `...-df270e41` para el #2); #3 https://speedrun-talent-network.com/jobs/services-internship-engineering-1-ge-vernova-eb8ef405 ; #4 https://speedrun-talent-network.com/jobs/software-engineer-intern-realm-a8a2f78e ; #8 https://speedrun-talent-network.com/jobs/cx-data-analyst-harvey-e69f2050 ; #16 https://speedrun-talent-network.com/jobs/customer-support-specialist-cluely-8df702c4 ; #7 https://speedrun-talent-network.com/jobs/data-analyst-user-operations-cursor-c43bdded ; #9 https://speedrun-talent-network.com/jobs/junior-ua-growth-manager-xsolla-6173525e ; #6 https://speedrun-talent-network.com/jobs/junior-quantitative-trader-dv-trading-b8361f8f ; #10 https://speedrun-talent-network.com/jobs/software-engineer-windows-ai-automation-sola-9a9c39a9 ; #5 https://speedrun-talent-network.com/jobs/product-design-co-op-international-growth-ancestry-58a1a59a ; #17 https://speedrun-talent-network.com/jobs/research-intern-gensyn-5ac09ece ; #11 https://speedrun-talent-network.com/jobs/skillbridge-intern-growth-rise8-9ebd7fd4 ; #12 https://speedrun-talent-network.com/jobs/skillbridge-intern-marketing-rise8-ab373f85 ; #13 https://speedrun-talent-network.com/jobs/skillbridge-intern-product-manager-rise8-f7fd317a ; #14 https://speedrun-talent-network.com/jobs/skillbridge-project-management-internship-technergetics-7a213fd3 ; #15 https://speedrun-talent-network.com/jobs/intelligence-skillbridge-intern-flashpoint-9023f2aa

Cobertura Speedrun: 17/17 con estado. En ventana: 1 (ya evaluado en work-01). Fuera de ventana: 16 sin re-leer. Matches fit≥3 en ventana: 0.

## 3. Get on Board (105) y Torre (41) — resumen por estado (evidencia: `work-01-eval-otros.md`)

### Get on Board — 105 filas
- **En ventana (28/9–1/10): 16** → **9 leídos y evaluados el 1/10** (work-01) + **7 DUPLICADO** (ya descartados en discoveries 28-29/9: Economic Impact Catalyst, Sendu, DroneSight, Grupo Mariposa AI Senior, Interfell, Factor IT, WiTi).
  - Los 9 evaluados: Launchpad 1.5, Niuro GTM 1.5, Agilesoft FE 1.0, Mediastream 1.5, 42Labs 1.0, I2B 1.5, LeadPlexity 1.5, Agilesoft BE 1.0, Improving RoR 1.0 → **0 matches fit≥3** (detalle y links en `work-01-eval-otros.md`).
- **Fuera de ventana: 89** (fecha feed < 28/9) → excluidos sin leer por edad.
- **Estafas: 0.** FECHA_NO_VERIFICABLE: 0 (todas las 105 tienen fecha en el TSV).

### Torre — 41 filas
- **En ventana: 1** → ApexNeural "Audio AI Intern" (28/9) = **DUPLICADO**, ya descartado en `discoveries-2026-09-28.md`.
- **Fuera de ventana: 40** (la más cercana: Solodesk Business Development Intern 26/9, Scale Pledge Recruitment & Onboarding Intern 25/9 — ambas a 2-3 días de la ventana, sin leer).
- **Estafas: 0.** FECHA_NO_VERIFICABLE: 0.

### Plausibles NO leídos por fecha vieja (listado, sin evaluar — para seguimiento si la ventana se amplía)

Get on Board (fecha | título | empresa | link):
- 2026-09-25 | Customer Support Specialist | Healthatom | https://www.getonbrd.com/jobs/customer-support-specialist-healthatom-remote-7e55
- 2026-09-25 | Customer Success LATAM | OZmap | https://www.getonbrd.com/jobs/customer-success-latam-ozmap-remote
- 2026-09-25 | Full-Stack Developer | Lead Gen Team LLC | https://www.getonbrd.com/jobs/full-stack-developer-lead-gen-team-llc-remote
- 2026-09-24 | Estimating & Operations Associate (Training Track) | Renaissance Restoration | https://www.getonbrd.com/jobs/estimating-operations-associate-training-track-renaissance-restoration-remote
- 2026-09-23 | Tosca Developer / QA Automation Engineer (Tricentis Tosca) | Niuro | https://www.getonbrd.com/jobs/tricentis-tosca-developer-niuro-remote
- 2026-09-20 | Ejecutivo de Onboarding Junior | AgendaPro | https://www.getonbrd.com/jobs/ejecutivo-de-onboarding-junior-agendapro-buenos-aires-4848
- 2026-09-18 | SDET + Python + Playwright + Document Processing (XBRL) | Improving | https://www.getonbrd.com/jobs/sdet-python-playwright-document-processing-xbrl-improving-remote
- 2026-09-14 | SDET (Software Development Engineer in Test) | Improving | https://www.getonbrd.com/jobs/sdet-software-development-engineer-in-test-improving-remote
- 2026-09-11 | Bilingual (Spanish/English) Full-Stack Developer | Tabiya US | https://www.getonbrd.com/jobs/bilingual-spanish-english-full-stack-developer-tabiya-us-remote
- 2026-09-09 | Technical Support Specialist | Arbostar | https://www.getonbrd.com/jobs/sales-development-representative-sdr-arbostar-remote
- 2026-09-08 | QA & Support Engineer | Niuro | https://www.getonbrd.com/jobs/qa-support-engineer-niuro-remote
- 2026-08-28 | Agente de Customer Care | ComunidadFeliz | https://www.getonbrd.com/jobs/agente-de-customer-care-comunidadfeliz-remote-a735
- 2026-08-22 | Junior IT Support Technician | Bitmax Technologies, LLC | https://www.getonbrd.com/jobs/junior-it-support-technician-bitmax-technologies-llc-remote
- 2026-06-16 | Analytics Engineer Jr | Galilei | https://www.getonbrd.com/jobs/analytics-engineer-jr-galilei-remote (ojo: descartado en `discoveries-2026-09-28.md` por Chile)
- 2026-05-13 | Desarrollador/a Full-Stack Jr | BC Tecnología | https://www.getonbrd.com/jobs/desarrollador-a-full-stack-jr-bc-tecnologia-remote
- 2026-03-31 | Soporte Operativo Junior | BC Tecnología | https://www.getonbrd.com/jobs/soporte-operativo-junior-bc-tecnologia-remote

Torre (fecha | título | empresa | link):
- 2026-09-26 | Business Development Intern | Solodesk | https://torre.ai/post/0wxM3Nvd
- 2026-09-25 | Recruitment & Onboarding Intern | Scale Pledge | https://torre.ai/post/QweM1j8w
- 2026-09-17 | Ingeniero de Datos | Makers Solutions | https://torre.ai/post/OwGoXjaw
- 2026-09-15 | Desarrollador Frontend Junior | Axiora AI | https://torre.ai/post/8wDab1Ad
- 2026-09-14 | Product QA Engineer | Singular Agency | https://torre.ai/post/ZW2OvJNw
- 2026-08-23 | AI Agent Training Contributor | Outlier AI | https://torre.ai/post/JWO84jnw

## 4. Web abierta (intentos del lote)

### Wellfound — **BLOQUEADO** (sin crear cuenta)
- `/jobs` (landing) renderiza parcial: trending "today/yesterday", pero la búsqueda, filtros y postulación exigen signup/login ("Sign up & search", "Log in").
- `/job-collections/junior-software-engineer-jobs` es un artículo viejo (2020; el único job listado "8 meses atrás"), sin fecha de ventana.
- Acción tomada: registración del bloqueo. No se creó ninguna cuenta. Brecha: sin Wellfound no hay cobertura de la bolsa junior remote de startups.

### Techstars — accesible (bolsa Getro `jobs.techstars.com`), cobertura parcial
- `techstars.com/portfolio` = directorio de empresas, sin avisos fechados. `techstars.com/careers` = empleo en Techstars (Greenhouse `techstars57`), sin relevancia entry AR.
- **Bolsa red `jobs.techstars.com/jobs`: 5.288 avisos, sí muestra fecha ("Posted: Today/1 day").** Portada (20 avisos, los 20 en ventana: 18 "Today" + 2 "1 day"): revisados por título/ubicación/fecha; 19 descartables por seniority/país/ubicación sin lectura (Staff/Sr/PM/Founding, Denver/SF/Berlín/París/US, Zipline intern onsite SF Summer 2027) → **1 leído completo**: Super Dispatch (ver §5).
- El filtro por keyword no funciona vía URL sin JS → **5.268 avisos restantes sin rastrear (brecha)**.

### Bolsas públicas remote/startups globales
- **RemoteOK** (API pública): 99 avisos con fecha, feed llega hasta **2026-09-26** → **0 en ventana**. Sin candidatos.
- **startup.jobs**: **BLOQUEADO** — 403 Cloudflare ("Just a moment..."). Sin cuenta, sin retry agresivo.
- **We Work Remotely** (RSS de remote-programming-jobs): 25 items, fechas mezcladas 15-16/9 y 17/8 → **0 en ventana** (el RSS no cubre la ventana) → sin candidatos verificables.

## 5. Evaluaciones con detalle (lectura completa de la página oficial)

Formato: fecha | antigüedad | título | empresa | exp | inglés | jornada/modalidad | acepta_AR | fit | motivo/gap | link

- **2026-09-28 | 3 días | QA Engineer | Astraea (YC P26) | "Experience: Any (new grads ok)" → exp 0 OK, pero pide "hands-on experience testing web applications" (gap: sin QA formal) | no exige inglés en el aviso (equipo de SF → comunicación EN de facto; B1 defensivo en escrito) | Contract 40 h/sem, remoto, horario/timezone a declarar en la postulación | Sí ("US citizenship/visa not required", remoto) | 3.1** | Único match en ventana del lote. Rúbrica v2: evidencia 2.5 (bullets de QA/Playwright/Cypress casi inexistentes; sí SQL básico y testing propio) + jornada 3 (full-time, no veto, pero 40 h vs objetivo 20 h) + compat horaria 4 (remoto flexible: se puede evitar la cursada 18:45) + carrera 4 (QA en health-tech YC, escalable a SDET) + demanda 3. Deal-breakers: ninguno duro (no pide años, título, inglés certificado ni residencia; verificable en YC/bookface, sin pedidos de pago → no estafa). Gap principal: full-time 40 h concurrente con la cursada + sin experiencia QA formal; $25K–75K/año como contractor. | https://www.ycombinator.com/companies/astraea/jobs/B99nCmA-qa-engineer
- 2026-09-28 | 3 días | *(relectura completa)* Client Support Specialist (Healthcare Facilities - B2B) | Clipboard (YC W17) | — | — | — | — | **no puntúa: FUERA_DE_VENTANA** (publicado 2025-02-27). Nota: de haber estado en ventana, vetos por inglés ("Clear, professional English spoken and written is critical", 30 llamadas + 15 tickets diarios en inglés) y ritmo full-time de soporte B2B; "1+ años" en la ficha vs "all experience levels" en el cuerpo. | https://www.ycombinator.com/companies/clipboard/jobs/EYlMYBU-client-support-specialist-healthcare-facilities-b2b
- 2026-10-01 | 0 días | Customer Support Specialist (Bilingual/Spanish) | Super Dispatch (Techstars network) | 2-4 años en customer support SaaS (excluyente) | no es el gap (español requerido) | Full-time, turnos 11-19 CST + fines de semana fijos | **No** — "Open to candidates within the United States only... not eligible for international remote work" + "Candidates must be U.S. citizens" | **no puntúa (elegible=false)** | En ventana y leído completo, pero triple descarte: solo EE.UU. con ciudadanía exigida, 2-4 años de experiencia y horario con fines de semana (pisaría la cursada). | https://jobs.techstars.com/companies/super-dispatch-2/jobs/95442759-customer-support-specialist-bilingual-spanish
- *(cita, ya evaluado el 1/10 en work-01)* 2026-09-29 | 2 días | Entry Level TFA Steam Turbine | GE Vernova | fit **1.0** | descartado: solo EE.UU., título Ing. Mecánica, 80 % viajes | https://speedrun-talent-network.com/jobs/entry-level-technical-field-advisor-tfa-steam-turbine-ge-vernova-4b6a4d28

## 6. Matches del lote (postulables)

- **Aplicar YA (≥ 4.5):** ninguno.
- **Aplicar esta semana (4.0–4.4):** ninguno.
- **Evaluar (3.0–3.9):** **1 — Astraea QA Engineer, fit 3.1, pub. 28/9, remoto, exp 0, sin inglés exigido**: https://www.ycombinator.com/companies/astraea/jobs/B99nCmA-qa-engineer
  Próxima acción #1: si Nacho quiere, CV a medida QA/testing (keywords: manual/exploratory testing, bug reports, SQL, regression) y postular él a mano vía YC (requiere login de él; no se crean cuentas).
- **Descartados en ventana con lectura:** Super Dispatch (US-only + ciudadanía + 2-4 años), GE Vernova TFA (ya work-01).

## 7. Cobertura exacta por fuente y brechas

| Fuente | Universo | En ventana | Leídos completos | Evaluados (fit) | Estado resto |
|---|---|---|---|---|---|
| YC | 4 | 1 | 2 | 1 (Astraea 3.1) | 3 fuera de ventana (Clipboard leído; GoGo/Rhizome solo metadata) |
| Speedrun | 17 | 1 | 1 (vía work-01, citado) | 1 (GE Vernova 1.0) | 16 fuera de ventana sin re-leer |
| Get on Board | 105 | 16 | 9 (+7 dup) | 9 (0 matches) — evidencia work-01 | 89 fuera de ventana |
| Torre | 41 | 1 | 0 (+1 dup) | 0 | 40 fuera de ventana |
| Wellfound | n/a | n/a | landing + colección vieja | 0 | **BLOQUEADO (login/SPA para búsqueda)** |
| Techstars red (Getro) | 5.288 | 20 en portada | 1 (Super Dispatch) | 1 (elegible=false) | **5.268 sin rastrear (sin filtro server-side)** |
| RemoteOK | 99 (API) | 0 | 0 | 0 | feed llega solo a 26/9 |
| startup.jobs | n/a | n/a | 0 | 0 | **BLOQUEADO (403 Cloudflare)** |
| We Work Remotely | 25 (RSS) | 0 | 0 | 0 | RSS no cubre la ventana |

Brechas declaradas (no es fuente completa con pendientes):
1. Techstars: 5.268 avisos de la bolsa red sin filtrar (falta filtro por keyword/fecha con sesión o JS).
2. Wellfound: bloqueado por login — cubrir solo si Nacho autoriza crear perfil él mismo.
3. RemoteOK/WWR/startup.jobs: feeds no alcanzan la ventana o piden desafío → 0 candidatos verificables hoy.
4. Get on Board/Torre: los 89 + 40 fuera de ventana no se re-leen (regla); los 16 plausibles viejos quedan listados en §3 por si se amplía la ventana.
5. PENDIENTE DEL DÍA (otro lote): LinkedIn 19 bloqueos 429 + 2 detalle pendiente — fuera de este lote, ver `discoveries-2026-10-01.md`.

## 8. Verificación de límites

- No se corrió el scraper; no se tocó tracker, CVs, outbound ni Notion; no se crearon cuentas, no se postuló ni contactó; ningún archivo escrito fuera de este (`radar/work-2026-10-01-global.md`).
