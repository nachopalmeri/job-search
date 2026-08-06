# Cheat Sheet — Llamada Fátima (Wetcom, 10 min)

## "¿Por qué Wetcom?"

> "Porque busco mi primera experiencia real en IT y Wetcom es de las empresas del rubro que más invierten en formación de gente sin experiencia: el programa Jóvenes Talentos tiene 17 ediciones, la empresa está certificada por Great Place to Work y capacita en tecnologías que se usan en producción en clientes grandes. Además me gusta que el programa arranca part-time, lo que me permite seguir cursando en la facultad."

**Refuerzos si pregunta algo más:**
- "Me llama la atención que trabajan con clientes de banca y telecom — se aprende de verdad, no en un entorno de juguete."
- "Los testimonios de ex-participantes destacan la capacitación real en VMware y Veeam, que son tecnologías con demanda en el mercado."

## "¿Qué esperás del programa?"

> "Espero aprender las bases de infraestructura desde adentro: monitoreo de backups y virtualización, gestión de tickets, documentación, y entender cómo se trabaja en el área de servicios con clientes reales. Me comprometo a formarme en lo que me pidan y a crecer dentro del área. Mi objetivo es construir una carrera en IT, y Wetcom me parece el lugar ideal para dar ese primer paso con acompañamiento."

**Si pregunta por tu plan a largo plazo:**
- "Me gusta el lado técnico (redes, servidores, cloud) y también el de datos/programación; por eso estoy cursando Gestión de TI y un CCNA. El programa me permite descubrir qué parte del mundo de infraestructura me motiva más."

## ¿Qué hace Wetcom? (en 3 frases)

> "Wetcom es una consultora de infraestructura IT: ayuda a empresas a montar y mantener sus sistemas críticos. Sus dos grandes pilares son la **virtualización con VMware** (varios servidores físicos consolidados en uno solo, para ahorrar costos y simplificar el mantenimiento) y los **backups con Veeam** (copias de seguridad de esos servidores para que si algo se cae, la empresa no pierda datos). También hacen **cloud** (mover servidores a la nube o tenerlos híbridos), redes, storage y datacenter."

## Mini-guía de tecnologías (para no quedarte mudo)

### VMware (vSphere / ESXi)
- **Qué es:** software que permite crear "máquinas virtuales": correr muchos servidores "virtuales" dentro de un mismo servidor físico.
- **Para qué:** aprovechar mejor el hardware, mover servidores entre máquinas sin apagarlos, aislar servicios.
- **Términos que pueden aparecer:** ESXi (el hipervisor = el programa base que corre las VMs), vCenter (la consola central para administrar todo), vSphere (el paquete completo), snapshot (foto instantánea de una VM para poder volver atrás).
- **Tarea típica de un JT:** mirar alarmas en vCenter, reiniciar un servicio en una VM, verificar que las VMs estén corriendo, documentar instalaciones.

### Veeam
- **Qué es:** software de **backup y recuperación** de VMs (y servidores físicos, nube).
- **Para qué:** si un servidor se rompe, se borra info o hay un ransomware, Veeam restaura los datos desde las copias. Es el estándar de la industria para ambientes VMware.
- **Términos:** backup job (la tarea de copia programada), restore (restaurar), repository (dónde se guardan las copias), retention (cuánto tiempo se conservan).
- **Tarea típica de un JT:** verificar que los backups de la noche pasada terminaron OK, reportar fallas, ejecutar restores de prueba.

### Cloud (Google Cloud / AWS / Azure)
- **Qué es:** servidores y servicios que no están en el datacenter de la empresa sino en los datacenter de Google/Amazon/Microsoft, pagados por uso.
- **Híbrido:** parte de los sistemas en la empresa, parte en la nube — lo típico en clientes de Wetcom.
- **Términos:** IaaS (máquinas virtuales en la nube), SaaS (software por suscripción, ej. Gmail), VPC (red virtual de la nube), storage buckets (discos en la nube).

### Otros que pueden aparecer
- **Nutanix:** hiperconvergencia = servidor + storage + red todo en un mismo equipo, fácil de administrar.
- **Fortinet/F5:** firewalls y balanceadores de red (seguridad y distribución de tráfico).
- **Logs/Jira:** Jira es donde se cargan los tickets de soporte; logs son los registros que genera cada sistema (se revisan para encontrar errores).

## Si te pregunta "¿qué sabés de...?" y NO sabés

Respuesta honesta que no te deja afuera:
> "Esa tecnología todavía no la toqué, pero tengo la base para aprenderla rápido: entiendo de redes, Linux y programación, así que ya sé leer cómo se piensan estos sistemas. ¿Qué me recomendarías para ir adelantándome?"

## Cierre de la llamada (preguntas para hacerle)

1. "¿Cuántas instancias tiene el proceso y qué viene después de esta llamada?"
2. "¿Hay entrevista técnica o test, o es con esta charla + CV?"
3. "¿Para cuándo estiman tener la decisión?"
4. "¿El inglés se evalúa en alguna instancia del proceso?" (te sirve para saber si certificar ya)

## Después de la llamada

- Mandarle mensaje corto de agradecimiento en WhatsApp el mismo día:
  > "Gracias por la llamada, Fátima. Me quedó clarísimo el programa y me entusiasma. Cualquier cosa que necesites de mi lado, quedo atento. ¡Saludos!"

## Prohibido en la llamada

- No decir que sabés VMware/Veeam si nunca los tocaste → "no la toqué, pero aprendo rápido" es la respuesta correcta.
- No mencionar JobBot/IA de forma protagonista: el puesto es soporte/infra.
- No inventar disponibilidad: si cursás de noche, 8:30–14:30 es verdad y es compatible; el full-time a los 6 meses es a futuro, no lo prometas como disponible ya.
