# AGENTS.md — job-search de Nacho Palmeri

Fuente canónica del flujo de búsqueda laboral. La leen OpenCode, Claude Code y cualquier agente compatible con Markdown.
Los comandos globales (`/busqueda`, `/cv`, `/postule`, `/seguimiento`) y la skill `job-search` **solo apuntan acá**: no duplican nada.

Objetivo: conseguir una pasantía o puesto junior de IT/IA (ideal part-time 20 h, AMBA o remoto). Nacho tiene 19 años, cursa el 2.º año de Gestión de TI en UADE (15 de 40 materias, egreso dic 2028), vive en Temperley y cursa de lunes a viernes 18:45–22:15. Perfil completo en `profile.md`; rúbrica en `rubric-fit.md`.

## Reglas duras (no negociables)

1. **Honestidad.** Nunca inflar títulos, tecnologías ni experiencia. Si no usó algo (Looker, Tableau, Snowflake, Go, Flask/Django, Zapier/n8n/Make, .NET, Java, Angular…) no va como usado: como mucho "todavía no lo usé, quiero aprenderlo".
2. **Inglés: B1 (intermedio), autoevaluado y sin certificar.** Nunca B1+, B2, fluido, avanzado, bilingüe ni C1, ni en CVs, ni en mails, ni en respuestas de formularios o entrevistas.
3. **Full-time no descarta.** Se evalúa por mérito y se marca el choque con la cursada (18:45). Sí descartan: años de experiencia exigidos, inglés fluido excluyente, carrera o materias aprobadas que no tiene, ubicación imposible.
4. **Nunca postular, enviar mails o DMs, aceptar términos, crear cuentas ni escribir contraseñas.** Se prepara todo y Nacho aprieta el botón. Si un sitio pide login, se lo pide a él.
5. **Historias y datos personales de formularios** (ej. "contá una vez que ayudaste a alguien"): solo hechos que Nacho cuente. Nunca inventar. Los campos demográficos son opcionales: se sugiere "prefiero no responder".
6. **Registro = archivos de Nacho** (Excel / Google Sheets). Nada de páginas o artefactos que dependan de una suscripción.
7. **Git:** identidad `Nacho Palmeri <ipalmeri@uade.edu.ar>`; trabajar en una rama y hacer push; nunca force-push; **merge a `master` solo con OK explícito de Nacho para ese cambio**.
8. **Sin instalar** MCPs, plugins ni dependencias, y **sin crear tareas programadas**, sin autorización explícita.
9. **Secretos:** nunca imprimir tokens, credenciales ni `client_secret` (`.secrets/`, `~/.config/*-mcp/`, `~/.gmail-mcp/`, `opencode.json.bak*`).
10. Español rioplatense, respuestas cortas y con una prioridad ejecutable. Los CVs van en el idioma del aviso.

## Mapa de rutas

| Qué | Ruta |
|---|---|
| Repo (git, remoto `github.com/nachopalmeri/job-search`, privado, rama `master`) | Raíz del checkout actual (`git rev-parse --show-toplevel`; en este entorno `C:\Users\nacho\Downloads\job-search`) |
| **Python para la búsqueda** | `python` desde el checkout; para CV/Excel usar un entorno con las dependencias de esos scripts |
| Scraper | `scripts\buscar_portales.py` |
| Radar del día (no se sube a git) | `radar\daily-AAAA-MM-DD.tsv`, `radar\seen_jobs.json`, `radar\discoveries-AAAA-MM-DD.md` |
| **Excel oficial de seguimiento** | `C:\Users\Nacho\Documents\Busqueda laboral\Postulaciones_Ignacio_Palmeri.xlsx` |
| Backup automático del Excel (uno, se pisa) | `C:\Users\Nacho\Documents\Busqueda laboral\backup\Postulaciones_Ignacio_Palmeri.anterior.xlsx` |
| Script del Excel | `scripts\tracker_add.py` (agregar, actualizar, listar, follow-ups) y `scripts\tracker_xlsx.py` (regenera un Excel desde el CSV; su salida por defecto va a `tracker\` del repo: **nunca apuntarlo al Excel oficial**) |
| **Registro en Obsidian** (tabla + una nota por postulación: link, ruta exacta del CV, descripción, match, historial) | `D:\Facultad\UADE-Vault\Efforts\Trabajo\Postulaciones\` (`Registro de postulaciones.md` + `NNN Empresa - Puesto.md`); se regenera solo con cada `add`/`update`, o a mano con `tracker_add.py export-obsidian` |
| Espejo en git del Excel | `tracker\postulaciones.csv`, `tracker\contactos.csv`; `tracker\applications.csv` es legacy |
| CV maestro (fuente) | `CV_Material_Nacho\cv_master.yaml` → `python CV_Material_Nacho\yaml_to_md.py` → `cv_master_es.md` / `cv_master_en.md` |
| CVs a medida | `CV_Material_Nacho\extras\cvs_personalizados\cv_<slug>.md` → PDF/DOCX `Ignacio_Palmeri_<Slug>.*` |
| Generador y validador | `CV_Material_Nacho\extras\generate_cv_files.py`, `scripts\validate_ats.py --all` (CI: `.github\workflows\cv.yml`) |
| Carpeta de envíos (PDFs, textos de mails) | `D:\Dev\postulaciones_2026-09-25\PARA_ENVIAR\` |
| Textos de mails (BecasIT) | `CV_Material_Nacho\extras\EMAIL_BecasIT_*.txt`, `CV_Material_Nacho\extras\postulaciones_2026-09-25_mensajes.md` |
| Prompts | `scripts\prompts\agente-libre.md` (agente de web abierta), `scripts\prompts\outbound-mail.md` (cold mail a startups) |
| Catálogo y cobertura por fuente | `scripts\search_sources.json`, `scripts\source_coverage.py`, `radar\coverage-AAAA-MM-DD.json` |
| Documentación de fuentes | `portales-argentina.md`, `README.md` |
| Drive de Nacho: carpeta "Búsqueda Laboral" | id `1aEnDGtjkQ_Ck6reQGShGwh538eKYS77B` (copia vieja del Excel, id `1vLl5FuM3BwmDpLU8Jnz51JK-L9qlV1O9`; planilla vieja "Tracker de postulaciones — Ignacio Palmeri", id `1CFP-AKbxUBNPNtUwTD7ADwNq63reIm1XMoHAXrt9wq8`, solo respaldo) |
| OpenCode | config `C:\Users\Nacho\.config\opencode\opencode.json`; comandos `...\opencode\command\`; skill `C:\Users\Nacho\.agents\skills\job-search\SKILL.md`; base de datos de sesiones `C:\Users\Nacho\.local\share\opencode\opencode.db` (no tocar) |

Para delegar a modelos gratuitos desde este flujo, usar `C:\Users\Nacho\.agents\bin\invoke-delegation.ps1` y verificar recibo `SUCCESS`, modelo gratuito, costo y número de workers. El wrapper selecciona el runtime aislado; no invocar la CLI global `opencode` directamente desde el sandbox ni tocar la base global de sesiones/configuración.

## MCPs de OpenCode (config global, formato plano `mcp.<nombre>`)

- **calendar** (conectado): Google Calendar de Nacho, calendario `primary`. Usarlo para follow-ups y fechas límite. **Siempre listar primero** los eventos que empiezan con `[Búsqueda]` para no duplicar, **mostrar la lista a Nacho y crear solo si dice que sí**, sin invitados. Formato: `[Búsqueda] Follow-up <empresa>` (día 3, 10:00, 15 min) y `[Búsqueda] Vence <empresa>` (todo el día). Nunca agendar entre 18:45 y 22:15 de lunes a viernes: es la cursada.
- **drive** (conectado): leer archivos y, si Nacho lo pide, subir un respaldo del Excel a la carpeta "Búsqueda Laboral". El Drive está casi lleno (99 %): avisar antes de subir. El Excel local sigue siendo el registro oficial.
- **gmail** (encendido el 2026-09-26): **solo borradores**. `send_email`, `delete_email` y `batch_delete_emails` están bloqueados por `permissions` en `opencode.json` (regla `effect: deny`), así que `tools.gmail.draft_email` es lo único que sale de la bandeja. Usar `draft_email`, `search_emails`, `read_email`. Nacho revisa y envía a mano desde Gmail.
- **playwright** (instalado el 2026-09-26, `npx -y @playwright/mcp@latest`, herramientas `tools.playwright.browser_*`): para el portal de UADE y X. Perfil persistente: si el login venció, Nacho inicia sesión él en la ventana y se sigue. Nunca escribir contraseñas por él, nunca postular ni enviar desde el navegador (reglas 1 y 4): solo leer avisos y armar la lista.

## Flujos

### A. Pasada diaria (`/busqueda`)
0. `python scripts\source_coverage.py --init`. El catálogo `scripts\search_sources.json` incluye empleo, startups, remoto, tareas de IA y eventos; la pasada debe revisar todos sus IDs. Cada fuente queda pendiente hasta registrar una consulta con/sin resultados, un bloqueo explicado o una exclusión justificada. El checklist diario se preserva si se ejecuta otra vez.
1. `python scripts\buscar_portales.py --scrape all --write`. Escribe `radar\daily-<hoy>.tsv` (ventana principal ≤3 días), `radar\secondary-<hoy>.tsv` (4–14 días) y `radar\unverified-<hoy>.tsv` (fecha, fuente original o elegibilidad pendiente). Los tres resultados conservan `job_id` cuando la fuente lo ofrece; no conviertas fechas de portal/indexación en fecha original.
1a. Ejecutá `python scripts\opportunity_pipeline.py` para fusionar y deduplicar las tres colas, registrar primer/último hallazgo y fuentes, y generar `radar\enrichment-<hoy>.json` + métricas. El pipeline no marca como elegible ni listo para postular hasta verificar la descripción original.
2. Fuentes automáticas de `--scrape all`: LinkedIn guest, Cosign, Startups Argentina, YC, Speedrun, Get on Board, Torre, Computrabajo, BecasIT, EmpleosIT, Jobicy, Himalayas, Remotive, Arbeitnow y tableros Greenhouse/Lever/Ashby de `scripts\ats_boards.json`. Las cuatro fuentes remotas son señales: quedan en `unverified` hasta comprobar anuncio original y elegibilidad desde Argentina. Los ATS usan `first_published` en Greenhouse y `createdAt` en Lever, nunca `updated_at` como fecha original. Un tablero que falle se informa sin abortar los demás. LinkedIn frena al primer HTTP 429. Bumeran requiere revisión separada; UADE y X se revisan en navegador autenticado; Wellfound sigue siendo SPA con login. Telegram está apagado y se excluye de la pasada automática.
3. **Portal UADE** (`https://www.empleos.uade.edu.ar/Postulaciones`, sesión de Nacho): revisar también **sin carrera específica** además de Gestión de TI, Informática, Ciencia de Datos/IA y Desarrollo de Software. Revisar 3 días como ventana principal y 4–14 días secundaria; anotar número, fecha original, requisitos, modalidad, horario y enlace. Solo lectura. Si el control de navegador falla, un reintento por mecanismo compatible; luego registrar el error literal y marcar UADE como parcial. El texto exportado por Nacho se puede importar con `scripts\uade_import.py`, pero una lista pegada no demuestra cobertura de todas las páginas/filtros.
4. **X:** búsquedas cortas por separado en “Latest” (pasantía IT, pasante sistemas, trainee tecnología, pasantía datos, soporte y hashtag local) dentro de una ventana de 4 días. No usar un booleano largo con muchas alternativas. Contar solo publicaciones con enlace al aviso o a la postulación oficial; registrar búsquedas sin resultados y errores por separado.
4a. **Publicaciones sociales y referidos:** sumar consultas por lenguaje natural de contratación (“estamos buscando”, “sumate al equipo”, “busco/tengo referidos”, “buscamos estudiantes”), además de títulos de puestos. Consultas adicionales: `python scripts/social_signals.py --queries`. Descubrir sin sesgo geográfico; comprobar país y elegibilidad en el original. Al importar, guardar fecha original, red social, URL del post, empresa/puesto y enlace oficial de postulación en un JSON y ejecutar `python scripts/social_signals.py --input <archivo>`. Solo las publicaciones de ≤4 días con empresa, título y enlace http(s) oficial salen como **candidatas a oportunidad**; todavía requieren leer la vacante, verificar vigencia y pasar por el ranking habitual. Referidos, recruiters y conversaciones sin vacante verificable van a `networking_leads`, separados de oportunidades activas; no reciben score ni se cuentan como avisos. `stale`, `undated` y `non_actionable` nunca se elevan como nuevos matches. No automatizar contacto: solo preparar un borrador si Nacho lo pide.
5. Web abierta y outbound según `scripts\prompts\agente-libre.md`.
6. **Nunca puntuar por el título.** Para cada candidato fresco leer el aviso original y extraer fecha, vigencia, años de experiencia, inglés, carrera/año, horas, sueldo, modalidad y ubicación. La fecha de indexación no prueba frescura. Al primer error de acceso, probar el navegador una vez; si sigue fallando, marcar la fuente parcial y no repetir llamadas tras 429/captcha.
6b. **Startups: sección propia y obligatoria en el reporte.** Startups Argentina, Cosign, YC, Speedrun, Get on Board y Torre se revisan sin exigir “junior/pasante/intern” en el título; confirmar fecha original y vigencia en el aviso antes de evaluarlo. Los avisos sin fecha comprobable quedan en “Fecha no verificada”, nunca como matches activos.
6c. **Filtro amplio (v4, 28/09/2026): lo que manda es que acepte gente en Argentina y que sea sin experiencia.** No descartar por el título ni por el área si el rol es de entrada: analista, ops, growth, research, CX/soporte, onboarding o QA también cuentan. Una palabra de entrada (intern, trainee, junior, fellow, graduate, estudiante) gana sobre la de seniority ("Product Manager Intern" pasa). Al leer cada aviso, verificar siempre: (1) si acepta candidatos que viven en Argentina (remotos "US only", "authorized to work in the US" o SkillBridge quedan afuera), (2) años de experiencia exigidos, (3) inglés exigido. Solo esos tres, más título excluyente, son motivos de descarte.
6d. **Estafas: se descartan siempre, sin excepción.** El scraper ya saca la lista negra (`scripts\estafas.txt`), títulos típicos de estafa (encuestas pagas, reenvío de paquetes, "agente de pagos", trading/cripto, capacitación paga), links acortados o de WhatsApp/Telegram y avisos de Torre o Get on Board sin empresa identificable; lo descartado queda en `radar\estafas-<fecha>.tsv`. Al leer un aviso, descartarlo también si: pide pagar algo (capacitación, equipo, inscripción), pide instalar software de acceso remoto (AnyDesk, TeamViewer) o descargar un archivo/"test" ejecutable, pide datos bancarios, DNI o fotos antes de una entrevista, solo se contacta por WhatsApp/Telegram, promete un sueldo desproporcionado sin experiencia, o la empresa no tiene web ni LinkedIn verificables. Nunca abrir adjuntos ni ejecutar nada que mande un "reclutador". Cada estafa confirmada se agrega a `scripts\estafas.txt` con fecha y motivo.
7. Registrar cada fuente con `python scripts\source_coverage.py --mark <id> --status <consulted_with_results|consulted_no_results|blocked|not_applicable> --count <n> --note <motivo si bloqueada/no aplicable>`. Un `WARN`, 429 o fallo de sesión es `blocked`, nunca cero resultados. Revisar con `python scripts\source_coverage.py --check`: salida 1 indica pendientes o bloqueos; no declarar pasada completa en ese caso.
8. Puntuar con `rubric-fit.md`. Reporte en `radar\discoveries-AAAA-MM-DD.md` con: Aplicar YA (≥ 4.5), Aplicar esta semana (4–4.4), Evaluar (3–3.9), Descartados con motivo, cobertura por fuente y **próxima acción #1**. Al finalizar, actualizar siempre Notion como vista de lectura: sin duplicados, orden por match, fuente, fecha original verificada y fecha de alta. Si no hay nuevos avisos, anotar cobertura; si Notion falla, indicar el bloqueo. El Excel sigue siendo la fuente de verdad. Resumen corto en el chat.

### Aprendizaje del embudo (sin sobreajustar)

- Para cada postulación enviada, conservar la vacante, versión de CV, fuente/canal y resultado real. Después de rechazo, entrevista o 14 días sin respuesta, registrar qué evidencia del CV funcionó/faltó y qué etapa ocurrió; distinguir silencio de rechazo explícito.
- Usar esos resultados para proponer ajustes en consultas, brechas de skills y materiales de entrevista. No cambiar automáticamente pesos del ranking ni declarar que una variante “gana” por pocos casos: el A/B de CV exige al menos 30 postulaciones enviadas por variante (`scripts/ab_test_tracker.py`).
- Por cada match prioritario, preparar si se solicita un CV centrado en evidencia relevante, brechas honestas y una práctica de entrevista/técnica basada en la descripción real. La búsqueda descubre; los materiales de postulación y la decisión final siguen siendo del estudiante.

### B. CV a medida (`/cv <link o empresa>`)
1. Partir de `cv_master_es.md` o `cv_master_en.md` según el idioma del aviso. Copiar a `CV_Material_Nacho\extras\cvs_personalizados\cv_<slug>.md`.
2. **Solo reordenar y enfocar** perfil, proyectos y skills que ya existen. Aplicar las reglas 1 y 2. Línea de inglés exacta: `English: B1 (intermediate), self-assessed, not formally certified. I read technical documentation in English.` / `Inglés: B1 (intermedio), autoevaluado, sin certificación formal. Leo documentación técnica en inglés.`
3. `python CV_Material_Nacho\extras\generate_cv_files.py` **regenera todos los PDF/DOCX**: preservar cambios ajenos y dejar solo los artefactos del CV nuevo.
4. `python scripts\validate_ats.py --all` debe dar 0 FAIL. Comprobar que el PDF contenga B1 y ninguna de estas palabras: `B1+`, `B2`, `fluent`, `fluido`, `bilingu`, `advanced English`, `C1`.
5. Copiar el PDF a `D:\Dev\postulaciones_2026-09-25\PARA_ENVIAR\` y anotar su **ruta absoluta** (va en `--cv-ruta` al registrar). Commit en rama y push. Decir a Nacho qué le falta según el aviso (gaps) y qué responder en el formulario.

### C. Registrar una postulación (`/postule <empresa> ...`)
Solo cuando Nacho confirma que **ya postuló**. Con el Excel cerrado:
`D:\Dev\wenv\Scripts\python.exe scripts\tracker_add.py add --empresa "..." --puesto "..." --link URL --fuente LinkedIn --cv archivo.pdf --fit 4.1 --prioridad Alta --descripcion "..." ...`
**Registro completo:** cada postulación enviada se carga con `--link`, `--fuente`, `--cv`, `--cv-ruta`, `--descripcion`, `--fit` y notas con match/gaps y condiciones conocidas. El script actualiza Excel y CSV. Obsidian se regenera desde el Excel y conserva “Mis apuntes”. Notion es una vista breve, no otro tracker: actualizarla cuando Nacho lo pide y al finalizar cada pasada diaria; el Excel sigue siendo la fuente de verdad. Usar un conector de Notion disponible y autorizado en la sesión.
Cambios de estado: `tracker_add.py update <N°> --estado Entrevista --log "qué pasó"`. El script rechaza duplicados, valida estados, hace backup y actualiza `tracker\postulaciones.csv`. **Si el Excel está abierto avisa y no escribe**: pedirle a Nacho que lo cierre. Después commitear el CSV en una rama.

### D. Seguimiento (`/seguimiento`)
1. `tracker_add.py followups` (regla: follow-up a los 3 días, "sin movimiento" a los 14, entrevistas se revisan a los 3).
2. Proponer el mensaje corto de cada follow-up como **borrador de texto** (nunca enviarlo). Modelo: "Hola [Nombre], quería confirmar si recibiste mi postulación para [Puesto]. Quedo a disposición para una entrevista. ¡Gracias!".
3. Proponer eventos de Calendar (ver MCPs) y esperar el sí de Nacho. Después de que él envíe algo: `tracker_add.py update <N°> --log "..."`.

### E. Mails de postulación (BecasIT y similares)
Solo borradores. BecasIT: a `empleo@itechcareer.com` con copia a `empleoitc@gmail.com`; asunto `Ref: <referencia del aviso> — Ignacio Palmeri — Remuneración pretendida: $700.000`; adjuntar el PDF. Pretensión salarial: **$700.000 ARS** por 20 h semanales. Modelos en `CV_Material_Nacho\extras\EMAIL_BecasIT_*.txt`. Si no tiene experiencia con algo que piden (Flask, Oracle, SQL Server…), el mail lo aclara.

## Verificación antes de dar algo por hecho
- Scraper: termina sin `Traceback`; cada fuente imprime su conteo; `radar\daily-<hoy>.tsv` existe.
- Excel: después de `add`/`update`, `tracker_add.py list` muestra la fila; el CSV cambió y existe la nota en `...\Efforts\Trabajo\Postulaciones\`.
- CVs: `validate_ats.py --all` en 0 FAIL y texto del PDF revisado.
- Git: `git status` limpio, rama pusheada, CI verde; sin secretos en el diff.
- No decir "listo" sin haber corrido el comando y mirado la salida.

## Estado y pendientes conocidos
- Hay una automatización diaria autorizada por Nacho en Codex (`pasada-diaria-completa-de-oportunidades`); el chequeo de cobertura y el cierre en Notion son obligatorios en cada ejecución. Crear otra tarea programada requiere OK explícito (regla 8).
- Gmail: solo borradores (envío y borrado bloqueados en `opencode.json`). Si se agrega otro MCP de mail, repetir el bloqueo.
- Tests de integración de MCPs: usar el wrapper de delegación desde la raíz del checkout y comprobar los conectores disponibles; no asumir que una ruta `D:\Dev` exista en este equipo.
