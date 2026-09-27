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
| Repo (git, remoto `github.com/nachopalmeri/job-search`, privado, rama `master`) | `D:\Dev\jsrepo` |
| **Python a usar** (tiene openpyxl, reportlab, python-docx, pdfminer, pyyaml) | `D:\Dev\wenv\Scripts\python.exe` |
| Scraper | `scripts\buscar_portales.py` |
| Radar del día (no se sube a git) | `radar\daily-AAAA-MM-DD.tsv`, `radar\seen_jobs.json`, `radar\discoveries-AAAA-MM-DD.md` |
| **Excel oficial de seguimiento** | `C:\Users\Nacho\Documents\Busqueda laboral\Postulaciones_Ignacio_Palmeri.xlsx` |
| Backup automático del Excel (uno, se pisa) | `C:\Users\Nacho\Documents\Busqueda laboral\backup\Postulaciones_Ignacio_Palmeri.anterior.xlsx` |
| Script del Excel | `scripts\tracker_add.py` (agregar, actualizar, listar, follow-ups) y `scripts\tracker_xlsx.py` (regenera el Excel desde el CSV) |
| Espejo en git del Excel | `tracker\postulaciones.csv`, `tracker\contactos.csv`; `tracker\applications.csv` es legacy |
| CV maestro (fuente) | `CV_Material_Nacho\cv_master.yaml` → `python CV_Material_Nacho\yaml_to_md.py` → `cv_master_es.md` / `cv_master_en.md` |
| CVs a medida | `CV_Material_Nacho\extras\cvs_personalizados\cv_<slug>.md` → PDF/DOCX `Ignacio_Palmeri_<Slug>.*` |
| Generador y validador | `CV_Material_Nacho\extras\generate_cv_files.py`, `scripts\validate_ats.py --all` (CI: `.github\workflows\cv.yml`) |
| Carpeta de envíos (PDFs, textos de mails) | `D:\Dev\postulaciones_2026-09-25\PARA_ENVIAR\` |
| Textos de mails (BecasIT) | `CV_Material_Nacho\extras\EMAIL_BecasIT_*.txt`, `CV_Material_Nacho\extras\postulaciones_2026-09-25_mensajes.md` |
| Prompts | `scripts\prompts\agente-libre.md` (agente de web abierta), `scripts\prompts\outbound-mail.md` (cold mail a startups) |
| Documentación de fuentes | `portales-argentina.md`, `README.md` |
| Drive de Nacho: carpeta "Búsqueda Laboral" | id `1aEnDGtjkQ_Ck6reQGShGwh538eKYS77B` (copia vieja del Excel, id `1vLl5FuM3BwmDpLU8Jnz51JK-L9qlV1O9`; planilla vieja "Tracker de postulaciones — Ignacio Palmeri", id `1CFP-AKbxUBNPNtUwTD7ADwNq63reIm1XMoHAXrt9wq8`, solo respaldo) |
| OpenCode | config `C:\Users\Nacho\.config\opencode\opencode.json`; comandos `...\opencode\command\`; skill `C:\Users\Nacho\.agents\skills\job-search\SKILL.md`; base de datos de sesiones `C:\Users\Nacho\.local\share\opencode\opencode.db` (no tocar) |

## MCPs de OpenCode (config global, formato plano `mcp.<nombre>`)

- **calendar** (conectado): Google Calendar de Nacho, calendario `primary`. Usarlo para follow-ups y fechas límite. **Siempre listar primero** los eventos que empiezan con `[Búsqueda]` para no duplicar, **mostrar la lista a Nacho y crear solo si dice que sí**, sin invitados. Formato: `[Búsqueda] Follow-up <empresa>` (día 3, 10:00, 15 min) y `[Búsqueda] Vence <empresa>` (todo el día). Nunca agendar entre 18:45 y 22:15 de lunes a viernes: es la cursada.
- **drive** (conectado): leer archivos y, si Nacho lo pide, subir un respaldo del Excel a la carpeta "Búsqueda Laboral". El Drive está casi lleno (99 %): avisar antes de subir. El Excel local sigue siendo el registro oficial.
- **gmail** (apagado, `enabled: false`): si Nacho lo enciende, **solo crear borradores, nunca enviar**.
- No hay MCP de navegador. Para el portal de UADE (pide login) y X, o Nacho pega el texto, o se usa Claude in Chrome desde Claude. Instalar Playwright MCP requiere su OK (regla 8).

## Flujos

### A. Pasada diaria (`/busqueda`)
1. `D:\Dev\wenv\Scripts\python.exe scripts\buscar_portales.py --scrape all --write` (2–3 min). Escribe `radar\daily-<hoy>.tsv` con columnas `portal|fecha|titulo|empresa|ubicacion|modalidad|jornada|estado|url|nuevo|tracker`. Columna `tracker` = `POSTULADA` o `DESCARTADA` si ese aviso exacto (empresa **y** puesto) ya está en el tracker: se ignoran. Nunca cruzar solo por empresa: BecasIT y Sezzle tienen muchos avisos distintos.
2. Fuentes: LinkedIn, Cosign, Startups Argentina, YC, Speedrun, Get on Board, Torre, Computrabajo, BecasIT, EmpleosIT. Bumeran (bloqueado) y UADE (login) dan 0 con aviso. Telegram está apagado (`scripts\feeds_telegram.yaml`: sin canales vivos). Wellfound es SPA con login.
3. **Portal UADE** (`https://www.empleos.uade.edu.ar/Postulaciones`, sesión de Nacho): filtrar por carrera "Licenciatura En Gestión De Tecnología De La Información" y también Informática, Ingeniería en Informática, Inteligencia Artificial y Ciencia de Datos, Desarrollo de Software, Negocios Digitales y "sin carrera específica". Listar los avisos de los últimos 7 días con su número. Solo lectura.
4. **X**: búsqueda "Más reciente" de pasante/junior/trainee + IT/IA/datos + "buscamos"/"contratando". Reportar solo avisos concretos con link o mail. Rinde poco.
5. Web abierta y outbound según `scripts\prompts\agente-libre.md`.
6. **Nunca puntuar por el título.** Para cada candidato leer el aviso completo (Greenhouse `boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>`, Ashby `api.ashbyhq.com/posting-api/job-board/<board>`, LinkedIn `www.linkedin.com/jobs-guest/jobs/api/jobPosting/<id>`, página de BecasIT) y extraer: años de experiencia, inglés, carrera y materias, horas, sueldo, modalidad, ubicación.
7. Puntuar con `rubric-fit.md`. Reporte en `radar\discoveries-AAAA-MM-DD.md` con: Aplicar YA (≥ 4.5), Aplicar esta semana (4–4.4), Evaluar (3–3.9), Descartados con motivo, y **próxima acción #1**. Resumen corto en el chat.

### B. CV a medida (`/cv <link o empresa>`)
1. Partir de `cv_master_es.md` o `cv_master_en.md` según el idioma del aviso. Copiar a `CV_Material_Nacho\extras\cvs_personalizados\cv_<slug>.md`.
2. **Solo reordenar y enfocar** perfil, proyectos y skills que ya existen. Aplicar las reglas 1 y 2. Línea de inglés exacta: `English: B1 (intermediate), self-assessed, not formally certified. I read technical documentation in English.` / `Inglés: B1 (intermedio), autoevaluado, sin certificación formal. Leo documentación técnica en inglés.`
3. `D:\Dev\wenv\Scripts\python.exe CV_Material_Nacho\extras\generate_cv_files.py` **regenera todos los PDF/DOCX**: dejar solo los del CV nuevo y revertir el resto con `git checkout -- <archivos>`.
4. `D:\Dev\wenv\Scripts\python.exe scripts\validate_ats.py --all` debe dar 0 FAIL. Comprobar que el PDF contenga B1 y ninguna de estas palabras: `B1+`, `B2`, `fluent`, `fluido`, `bilingu`, `advanced English`, `C1`.
5. Copiar el PDF a `D:\Dev\postulaciones_2026-09-25\PARA_ENVIAR\`. Commit en rama y push. Decir a Nacho qué le falta según el aviso (gaps) y qué responder en el formulario.

### C. Registrar una postulación (`/postule <empresa> ...`)
Solo cuando Nacho confirma que **ya postuló**. Con el Excel cerrado:
`D:\Dev\wenv\Scripts\python.exe scripts\tracker_add.py add --empresa "..." --puesto "..." --link URL --fuente LinkedIn --cv archivo.pdf --fit 4.1 --prioridad Alta --descripcion "..." ...`
Cambios de estado: `tracker_add.py update <N°> --estado Entrevista --log "qué pasó"`. El script rechaza duplicados, valida estados, hace backup y actualiza `tracker\postulaciones.csv`. **Si el Excel está abierto avisa y no escribe**: pedirle a Nacho que lo cierre. Después commitear el CSV en una rama.

### D. Seguimiento (`/seguimiento`)
1. `tracker_add.py followups` (regla: follow-up a los 3 días, "sin movimiento" a los 14, entrevistas se revisan a los 3).
2. Proponer el mensaje corto de cada follow-up como **borrador de texto** (nunca enviarlo). Modelo: "Hola [Nombre], quería confirmar si recibiste mi postulación para [Puesto]. Quedo a disposición para una entrevista. ¡Gracias!".
3. Proponer eventos de Calendar (ver MCPs) y esperar el sí de Nacho. Después de que él envíe algo: `tracker_add.py update <N°> --log "..."`.

### E. Mails de postulación (BecasIT y similares)
Solo borradores. BecasIT: a `empleo@itechcareer.com` con copia a `empleoitc@gmail.com`; asunto `Ref: <referencia del aviso> — Ignacio Palmeri — Remuneración pretendida: $700.000`; adjuntar el PDF. Pretensión salarial: **$700.000 ARS** por 20 h semanales. Modelos en `CV_Material_Nacho\extras\EMAIL_BecasIT_*.txt`. Si no tiene experiencia con algo que piden (Flask, Oracle, SQL Server…), el mail lo aclara.

## Verificación antes de dar algo por hecho
- Scraper: termina sin `Traceback`; cada fuente imprime su conteo; `radar\daily-<hoy>.tsv` existe.
- Excel: después de `add`/`update`, `tracker_add.py list` muestra la fila; el CSV cambió.
- CVs: `validate_ats.py --all` en 0 FAIL y texto del PDF revisado.
- Git: `git status` limpio, rama pusheada, CI verde; sin secretos en el diff.
- No decir "listo" sin haber corrido el comando y mirado la salida.

## Estado y pendientes conocidos
- Nada corre solo: la pasada arranca cuando se la pide. Programarla en Windows requiere OK de Nacho (regla 8).
- Navegador para UADE y X: pendiente decidir si se instala el MCP de Playwright.
- Gmail apagado a propósito.
- Tests de integración de MCPs: `opencode mcp list` debe mostrar `calendar` y `drive` en `connected`.
