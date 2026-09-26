# Prompt multiagente para opencode — mejora de CVs (reutilizable)

Flujo ejecutado el 4/ago/2026. Datos verificados. Reutilizar con `opencode` diciendo: "ejecutá el flujo de audit-cv" y pegando el prompt de abajo.

## Prompt

Quiero que audites y mejores mi set de CVs usando un flujo multiagente.
Contexto: soy estudiante de 2do año (Q4) de Gestión de TI (UADE), busco pasantía
part-time en IT/Automatización/IA. NUNCA quiero exagerar experiencia,
inventar métricas, ni usar títulos como "Desarrollador IA" si en realidad
uso IA para prototipar y reviso/testeo el resultado. Prioridad #1: honestidad
verificable por sobre "venderse mejor".

Datos confirmados (ago 2026): email ignaciopalmeri1@gmail.com · tel +54 9 11 5509-0832 ·
LinkedIn /in/ignaciopalmeri · GitHub /nachopalmeri · UADE Q4, 15/40 materias, promedio 8,2 ·
secundario 9,11 egreso 20/12/2024 · Grido oct 2023 – presente (~10 hs/sem cubriendo francos) ·
disponibilidad 20 hs semanales, turno mañana o tarde · inglés B1 (intermedio) sin certificar ·
JobBot NO es SaaS terminado (bot personal con alertas, sin pagos reales) ·
FranquiYA es prototipo · PISKU open source en GitHub (no PyPI) · RH124 es curso, NO RHCSA ·
CCNA 1 en curso, no certificación completa.

Usá los agentes que ya existen en .agents/ (o creá subagentes temporales
si no cubren esto) con esta división de tareas:

1. AGENTE AUDITOR — Escanea todos los .docx/.pdf de /ai-job-search,
   /GoogleDrive, /PC-Cascade, /PC-Downloads. Genera una tabla con cada
   inconsistencia encontrada: emails distintos, fechas de Grido distintas,
   nivel de inglés distinto, cualquier claim que no esté respaldado en
   otra versión. No corrige nada todavía, solo reporta.

2. AGENTE DE MERCADO — Busca en la web 5-8 postulaciones reales activas
   ahora mismo para "AI Intern" / "IT Support Intern" / "Automation
   Intern" en Argentina y remoto LatAm. Extrae qué keywords y skills
   piden más seguido, para saber qué priorizar en el CV sin inventar
   nada que no tenga.

3. AGENTE ATS — Revisa el CV maestro contra formato ATS estándar
   (sin tablas complejas, sin columnas, fuentes estándar, keywords en
   texto plano) y devuelve una lista de fixes de formato.

4. AGENTE DE CONSISTENCIA FINAL — Toma el output de los 3 anteriores y
   arma UNA versión maestra en /output/cv_master_es.md y
   /output/cv_master_en.md, con changelog explicando cada cambio y
   por qué. Si algo suena a sobreventa, lo marca con [REVISAR] en vez
   de decidir solo.

Al final quiero: (a) la tabla de inconsistencias, (b) los 2 markdown
maestros, (c) un resumen de qué versiones viejas debería borrar o dejar
de usar.

## Resultado del flujo (referencia)

- `output/cv_master_es.md` / `cv_master_en.md` — maestros con datos confirmados
- `output/CHANGELOG.md` — cada cambio aplicado y por qué
- `output/Ignacio_Palmeri_CV_ES.docx` / `CV_EN.docx` — docx finales ATS-friendly
