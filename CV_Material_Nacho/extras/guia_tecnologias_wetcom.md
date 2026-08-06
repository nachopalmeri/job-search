# Guía desarrollada — Qué hace Wetcom, el rol del JT y las tecnologías

## 1. Qué hace Wetcom en el fondo (el negocio)

Wetcom es una **consultora de servicios de infraestructura IT**. La diferencia entre "consultora de infraestructura" y "empresa de software" es clave:

- Una empresa de software vende *aplicaciones* (sistemas, apps, páginas).
- Wetcom vende que **las aplicaciones de sus clientes no se caigan y no pierdan datos**.

Las empresas clientes (bancos, telecomunicaciones, retail) tienen cientos de servidores que corren sus sistemas críticos. No quieren ocuparse de mantener ese hardware ellos mismos: se lo tercerizan. Wetcom es la que:
1. **Arma** la infraestructura (instala los servidores, la virtualización, las redes).
2. **La mantiene** (monitoreo 24/7, actualizaciones, soporte).
3. **La protege** (backups, recuperación ante desastres).
4. **La moderniza** (migrar a cloud, consolidar servidores).

**Cómo ganan plata:** contratos de servicio con clientes grandes (banca, telecom, retail) + proyectos de implementación. El producto propio "Insane Support" es exactamente eso: soporte especializado VMware/Veeam vendido como servicio.

**Por qué VMware y Veeam son el corazón de la empresa:** porque la mayoría de sus clientes tienen sus sistemas virtualizados con VMware y respaldados con Veeam. Wetcom es partner **Pinnacle** de VMware (el máximo nivel en LatAm) y partner destacado de Veeam. Esos son los dos productos que sus técnicos más usan a diario.

---

## 2. Virtualización y VMware (la tecnología #1 de Wetcom)

### El problema que resuelve
Antes de la virtualización: cada sistema necesitaba su **servidor físico propio**. Un banco con 50 sistemas tenía 50 máquinas físicas, cada una usando el 10-15% de su capacidad. Eso es: mucho espacio, mucha electricidad, mucho costo, y si se rompía una máquina, ese sistema se caía sí o sí.

### La solución
Un **hipervisor** (ESXi, de VMware) corre en un servidor físico potente y permite crear **máquinas virtuales (VMs)**: servidores "de mentira" que corren dentro del físico. Ahora 50 sistemas caben en 5-6 servidores físicos, y cada sistema está **aislado** (si uno se cae, los demás ni se enteran).

### Vocabulario obligatorio
| Término | Qué es |
|---|---|
| **Hipervisor** | El software que crea y administra las VMs (ESXi es el de VMware) |
| **ESXi** | El hipervisor de VMware que se instala en el servidor físico |
| **vCenter** | La consola central: administra TODOS los ESXi de la empresa desde una pantalla |
| **vSphere** | El paquete completo (ESXi + vCenter + herramientas) |
| **VM (Virtual Machine)** | Un servidor virtual: tiene su propio "procesador virtual", "disco virtual", "RAM virtual" |
| **Snapshot** | Foto instantánea del estado de una VM; si algo sale mal, volvés a la foto |
| **vMotion** | Mover una VM de un servidor físico a otro SIN apagarla (mantenimiento sin cortes) |
| **Host** | El servidor físico donde corren las VMs |
| **Cluster** | Grupo de hosts administrados juntos (si uno se cae, las VMs saltan a otro) |

### Analogía para explicarlo en la llamada
> "Es como tener un edificio donde cada piso es una oficina: antes cada oficina necesitaba su propio edificio. La virtualización es el edificio compartido, y cada sistema es una oficina adentro — si una oficina se prende fuego, las demás siguen funcionando."

### Qué haría un JT con VMware a diario (real, según ex-participantes)
- Abrir vCenter y mirar **alarmas**: "el host 3 perdió conectividad", "la VM X tiene el disco al 95%".
- Verificar que las VMs críticas estén corriendo.
- Reiniciar un servicio dentro de una VM (con permiso, en ventana de mantenimiento).
- Crear un **snapshot** antes de un cambio riesgoso.
- **Documentar** instalaciones de ESXi: IP, red, storage asignado (esto es mucho más importante de lo que parece: los runbooks son la columna vertebral del soporte).

---

## 3. Veeam (backups — "que no se pierda nada")

### El problema que resuelve
Los servidores se rompen, se borran archivos por error, y hoy lo más común: **ransomware** (un virus que cifra todos los datos y pide rescate). Sin backups, una empresa se muere: no hay vuelta atrás.

### La solución
**Veeam** hace copias de seguridad automáticas de las VMs de VMware (y de servidores físicos y cloud). Cada noche corre un **backup job**: copia el estado de cada VM a un **repositorio** (disco/almacenamiento dedicado). Si algo pasa, en minutos se hace un **restore**: la VM vuelve al estado de la copia.

### La regla de oro del backup: 3-2-1
- **3** copias de tus datos
- en **2** medios distintos (ej. disco local + cinta/nube)
- **1** fuera de la empresa (por si se incendia el datacenter)

### Vocabulario obligatorio
| Término | Qué es |
|---|---|
| **Backup job** | La tarea programada de copia (qué VMs, a qué hora, cada cuánto) |
| **Repository** | El almacenamiento donde se guardan las copias |
| **Retention** | Cuánto tiempo se conservan las copias (ej. 7 días + mensuales por un año) |
| **Restore** | Volver una VM a un punto del pasado desde una copia |
| **Restore de prueba** | Probar que las copias funcionan restaurando en un entorno aparte (el santo grial: una copia que nunca se prueba no sirve) |
| **SLA / RPO / RTO** | Cuánto tiempo de datos se puede perder (RPO) y cuánto tarda la recuperación (RTO) — lo que firman en los contratos |

### Qué haría un JT con Veeam a diario
- **A la mañana: verificar que los backups de anoche terminaron OK** (el 80% de una mañana típica de soporte es esto).
- Reportar los que fallaron y por qué (disco lleno, VM apagada, red caída).
- Ejecutar restores de prueba programados.
- Ver el dashboard de Veeam y sus alarmas.

---

## 4. Cloud (GCP / AWS / Azure)

### Qué es
En vez de tener los servidores en el datacenter de la empresa, se alquilan máquinas y servicios en los datacenters gigantes de Google/Amazon/Microsoft, pagando por uso (como Netflix pero de servidores).

### Modalidades (te las van a nombrar sí o sí)
| Término | Qué es | Analogía |
|---|---|---|
| **IaaS** | Alquilás máquinas virtuales crudas y las administrás vos | Alquilar un auto |
| **PaaS** | Alquilás la plataforma; solo subís tu código | Alquilar auto con chofer |
| **SaaS** | Software completo por suscripción | Uber (pedís el servicio, no pensás en el auto) |
| **Híbrido** | Parte de los sistemas en el datacenter de la empresa, parte en la nube, comunicados | El estándar actual de los clientes de Wetcom |
| **VPC** | La red privada virtual dentro de la nube | El barrio privado adentro de la ciudad |
| **Bucket** | Disco de almacenamiento en la nube (para backups, archivos) | El depósito gigante |

### Qué haría un JT en cloud
- Migraciones guiadas (mover una VM on-premise a la nube siguiendo un checklist).
- Verificar que las conexiones híbridas (VPN) entre la empresa y la nube estén activas.
- Reportar costos/uso desde las consolas de GCP/AWS.

---

## 5. Redes, storage y el resto del ecosistema

### Redes (tu CCNA te da ventaja acá)
- **DNS:** traduce nombres (www.banco.com) a IPs. Un problema de DNS = "no anda el sistema" más común del mundo.
- **Subnetting:** dividir la red en subredes (tu CCNA 1 ya cubre esto).
- **VLANs:** segmentar la red lógica del mismo switch — es "un edificio con paredes invisibles".
- **Firewall (Fortinet):** controla qué tráfico entra y sale.
- **F5:** balanceador — reparte el tráfico entre varios servidores para que ninguno explote.
- **VPN:** túnel cifrado entre dos redes (ej. la empresa y la nube).

### Storage
- **SAN / NAS:** las dos formas de darle discos a los servidores. SAN = discos de alta velocidad conectados por fibra; NAS = almacenamiento por red.
- **RAID:** combinar discos para que si uno muere, no se pierda nada (mirroring, paridad).
- **Nutanix:** "hiperconvergente" = servidor + storage + red empaquetados en un mismo equipo, se administra fácil desde una sola pantalla. El caballito de batalla alternativo a VMware.

### Monitoreo y herramientas del día a día
- **Logs:** los registros que cada sistema genera (cada error queda anotado). Gran parte del soporte es *leer logs*.
- **Grafana/Prometheus:** dashboards de métricas (CPU, RAM, discos) — gráficos en vivo de todo el ambiente.
- **Jira:** la plataforma de tickets. Todo el trabajo de soporte entra y sale por tickets.
- **Windows Server / Active Directory:** los servidores de los clientes suelen ser Windows; AD es el "DNI de la red" (usuarios, permisos, contraseñas). Muy probable que un JT lo toque.

---

## 6. El día a día real de un Jóvenes Talento (qué esperar)

1. **8:30:** arrancás mirando los backups de la noche (Veeam) y las alarmas (vCenter).
2. **Tickets:** entrás a Jira, tomás tickets de clientes según prioridad.
3. **Tareas de soporte N1/N2:** reiniciar servicios, verificar conectividad, revisar logs, atender consultas del cliente.
4. **Documentación:** el 20% de tu día. Runbooks = instrucciones paso a paso de cómo se resuelve cada problema típico.
5. **Capacitación:** los primeros meses tenés formación formal en VMware y Veeam con alguien del equipo (ex-JTs capacitan a los nuevos — los testimonios lo confirman).
6. **Proyectos chicos:** automatizar algo con un script (ej. un bot que avisa por Slack cuando falla un backup — esto es exactamente lo que ya sabés hacer con Python + APIs).

---

## 7. ¿Qué de esto YA usaste? (honesto, con evidencia de tus repos)

| Tecnología de Wetcom | ¿La usaste? | Evidencia y cómo conectarla |
|---|---|---|
| **Cloud (PaaS)** | ✅ SÍ | Tu **prode y tu portfolio corren en Vercel** — eso ES cloud: tu código vive en servidores de otra empresa. Podés decir: "sé desplegar aplicaciones en la nube con Vercel y manejar el ciclo de deploy" |
| **APIs / integraciones** | ✅ SÍ | **Polymarket** (fuente de odds del prode), **Telegram Bot API** (JobBot), **Stripe/MercadoPago** (billing sandbox). Decir: "integré APIs de terceros: de pagos y de datos, en sandbox y producción" |
| **Scripting / automatización** | ✅ SÍ | El motor del prode (Poisson + Monte Carlo) y scripts de procesamiento. Decir: "automaticé procesos con Python: procesamiento de datos y automatización de tareas" |
| **Git / versionado** | ✅ SÍ | 81+ commits en JobBot. Conectalo así: "uso Git en serio: versionado y control de cambios — que es el mismo concepto de los backups: poder volver atrás" |
| **Linux / terminal** | ✅ SÍ | Es tu skill declarado. Todo el mundo de infra se opera desde terminales Linux |
| **Bases de datos** | ✅ SÍ | El prode y JobBot tienen datos persistidos (SQLite/Postgres probable). "Manejo datos con SQL" |
| **Redes** | 🟡 EN CURSO | CCNA 1 en curso: subnetting, IPs, switches. Es real y vale |
| **Procesamiento de datos** | ✅ SÍ | Monte Carlo 10k simulaciones = cómputo. "Corro simulaciones y analizo resultados" |
| **Virtualización (VMware/ESXi)** | ❌ NO | Nunca. No inventarlo. La forma de adelantarte: instalar VirtualBox y crear VMs vos mismo (7 días de práctica y ya sabés hablar con propiedad) |
| **Backups (Veeam)** | ❌ NO | Nunca. Pero entendés el concepto: Git es "volver atrás", un backup job es lo mismo a escala de servidores |
| **Windows Server / AD** | ❌ NO | Nunca. Lo aprendés en el lab |
| **Firewalls / F5 / storage enterprise** | ❌ NO | Nunca. No inventar |

**Regla de la llamada:** las "sí" las mostrás con ejemplos concretos de 1 frase ("desplegué mi portfolio en Vercel", "automaticé un bot con la API de Telegram"). Las "no" las contestás con: *"no la toqué todavía, pero tengo la base — entiendo de redes, Linux y programación. ¿Qué me recomendás para adelantarme?"*

---

## 8. Plan de práctica rápida (si querés adelantarte de verdad antes de la llamada)

1. **VirtualBox** (gratis) + crear una VM con Ubuntu: instalarla, apagarla, snapshot, clonar. 2-3 horas y ya sabés qué es una VM de primera mano.
2. Opcional: **VMware Workstation Player** (gratis para uso personal) — más cercano a lo que usa Wetcom.
3. Armarte un mini-dashboard de monitoreo local: un script Python que lee logs y te avisa por Telegram si algo falla (ya sabés hacer esto — es literalmente el trabajo del JT).
4. Repasar subnetting básico con tu CCNA 1 (IPs, máscaras) — preguntas de "soporte 101" en la entrevista.
