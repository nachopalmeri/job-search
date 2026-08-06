# Formato ATS: .docx vs .pdf — investigación (ágile ago 2026)

## Veredicto

No hay una respuesta universal: **depende del ATS y del canal**, pero con la versión preparada (docx + pdf del mismo archivo, una columna, Calibri/Helvetica, contacto en el cuerpo) cualquiera de los dos pasa filtros modernos. El layout mata más que la extensión.

## Tabla comparativa (con fuentes)

| Factor | .docx | .pdf (texto nativo) | Fuente |
|---|---|---|---|
| Fiabilidad de parseo | 4% de fallo | 18% de fallo | Análisis EDLIGO de 1.000 CV (getnewresume.com) |
| Parseo 5 motores (Workday, Greenhouse, Lever, iCIMS, Taleo) | 95–100% | 80–98% | Test ATS Verification 2026 (atsverification.com) |
| Preferencia de reclutadores (humano) | 24% | **76%** | TopResume 2025 |
| Preservación del formato | Se desacomoda según versión de Word | **Pixel-perfect** | JobScan |
| Export escaneado/imagen | Inaplicable (texto siempre XML) | **0–5% de éxito** | JobMentis, ATS Checker |
| Texto como vector (Canva/InDesign) | Inaplicable | Falla | QuickCV |

## Canal recomendado en Argentina

| Canal | Formato a subir | Por qué |
|---|---|---|
| **Bumeran / CompuTrabajo / ZonaJobs** | **PDF** | Sus propios blogs lo recomiendan; la IA de Bumeran parsea el PDF para autocompletar el perfil |
| **Workday (Accenture, IBM, grandes)** | **.docx o PDF limpio** | Workday parsea docx históricamente más consistente; PDF texto limpio de 1 columna también ok |
| **ATS legacy (dominio taleo.net)** | **.docx** | Taleo es el que más cae con PDF (80%) |
| **Email directo a recruiter** | **PDF** | Conserva diseño; preferencia humana 76% |
| **Aviso que pide formato explícito** | Lo que diga el aviso | Primera regla: seguir la instrucción |

## Reglas de oro (aplicadas en tus PDFs)

1. PDF **nativo de texto** (nunca escaneado/imagen) — tus PDFs están generados por código, texto 100% seleccionable.
2. **Una columna**, sin tablas ni cajas — tus .docx tienen 0 tablas; los PDFs de reportlab son de una columna.
3. Fuentes estándar: **Helvetica** (en los PDFs) / Calibri (en los docx). Elegí una sola family por archivo.
4. Contacto en el **cuerpo**, no en header/footer — respetado.
5. Peso chico (<1 MB): tus PDFs pesan ~7 KB y ~40 KB los docx.
6. Nombre de archivo: `Ignacio_Palmeri_CV_ES.pdf` / `.docx` — correcto.
7. Copiar-pegar test: el texto se pega ordenado de arriba abajo.

## Estrategia práctica para vos

- **Maestro:** siempre editá el `.docx` (es la fuente). Exportá el `.pdf` desde el mismo contenido (ya están sincronizados).
- **Postulá con PDF** en portales argentinos y correo directo.
- **Switcheá a .docx** si el aviso lo pide explícitamente o si el preview del portal al subir el PDF sale roto.
- **NUNCA** mandes ambos en una misma aplicación salvo que el formulario tenga dos campos.
- Completá siempre los **campos del perfil del portal** (Bumeran "Mi CV" / CompuTrabajo): los reclutadores buscan por keywords en la base, no solo abren archivos.
- No uses barras de skill ni porcentajes (el ATS no las lee).

## Conclusión

Para Google/Accenture/IBM (Workday) y portales argentinos: **PDF texto nativo de una columna es lo más seguro y lo recomendado por los propios portales**. .docx planes solo para ATS legacy tipo Taleo o cuando el aviso lo pida. Ya tenés ambos: usá el PDF por defecto.

Fuentes: jobscan.co · atsverification.com · getnewresume.com · quickcv.io · resumeoptimizerpro.com · jobmentis.com · atschecker.ai · computer (ar.computrabajo.com) y Bumeran (bumeran.com.ar/blog).