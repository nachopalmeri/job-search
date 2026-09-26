# Preguntas técnicas Wetcom — repaso 30 min (finde antes del 11/08)

Fuente: preguntas reales reportadas por candidatos de Wetcom en Glassdoor + extensión lógica. Responder en voz alta; luego en inglés la presentación final.

## Fundamentos que preguntan SÍ o SÍ (reportados por candidatos)

### 1. ¿Qué es un bit? ¿Qué es un byte?
- **Bit**: unidad mínima de información digital, valor 0 o 1.
- **Byte**: 8 bits → 1 carácter (ej. la letra "A").
- Velocidades se miden en bits/seg (Mbps); almacenamiento en bytes (GB).

### 2. ¿Qué es el ancho de banda?
- Capacidad máxima de transferencia de datos de una conexión (cuánta "autopista" tenés), medida en Mbps.
- No es velocidad pura: es cuánta data puede circular a la vez.

### 3. Velocidad de carga vs descarga
- **Descarga (download)**: recibís datos (ver video, bajar archivo) — suele ser mayor en conexiones hogareñas.
- **Carga (upload)**: enviás datos (videollamada, subir archivo) — crítica para Meet, sincronizar backups en la nube.
- En la entrevista es por Meet → tu lado de carga importa.

### 4. ¿Qué es VMware / la virtualización?
- **Virtualización**: correr varias máquinas virtuales (VMs) sobre un único servidor físico mediante un hypervisor (VMware ESXi, Hyper-V).
- Beneficios: un solo hardware para muchos sistemas, aislamiento, snapshots (copias instantáneas), disaster recovery.
- En Wetcom es el core del negocio: virtualizan según cliente con VMware, Veeam (backup), Nutanix (hyperconvergencia).

### 5. 2.4GHz vs 5GHz (WiFi)
- **2.4GHz**: más alcance y penetra paredes, pero más lenta y más interferencia (microondas, bluetooth, vecinos).
- **5GHz**: más rápida pero menos alcance.
- Buen momento para mencionar: elegir banda según distancia; hoy hay más bandas nuevas (6GHz/WiFi 6E).

### 6. Comandos Windows (ejemplos + para qué)
- `ipconfig` → ver IP/config de red
- `ping` → probar conectividad (ICMP)
- `netstat` → ver conexiones y puertos en escucha
- `tracert` → ruta hasta un destino (dónde se corta)
- `sfc /scannow` → verificar/reparar archivos de sistema
- `msconfig` → configuración de inicio/servicios
- `taskmgr` → administrador de tareas
- `diskpart` → gestión de discos
- `gpupdate /force` → aplicar políticas

## Extensión probable (redes generales)

### 7. DNS
- Resuelve nombres: `miempresa.com` → IP (ej. 190.x.x.x). Como un directorio telefónico.
- Si "pingueás por IP pero no abrí webs" → falla DNS (tu respuesta en el test: correcta).

### 8. DHCP
- Asigna IP/gateway/DNS automáticamente a los equipos de la red (lease). Sin DHCP, hay que configurar IPs a mano.

### 9. Puertos comunes
- 21 FTP · 22 SSH · 80 HTTP · 443 HTTPS · 3389 RDP.
- Bloquear 21 → denegar FTP (tu respuesta del test).

### 10. Tipos de backup
- **Full**: todo.
- **Incremental**: solo lo nuevo desde el último backup (cualquiera). Restaura + lenta (encadenar todos).
- **Differential**: solo lo nuevo desde el último full. Restaura con 2 jobs: full + último differential. (Tu respuesta del test: correcta.)

### 11. Dominio vs grupo de trabajo
- **Grupo de trabajo**: PCs en la misma red sin server central de control (red doméstica).
- **Dominio (Active Directory)**: servidor central controla usuarios, políticas, auth (empresa). Se une con `joindomain`.

### 12. ¿Qué es el cloud? ¿Nube híbrida?
- **Cloud**: infraestructura y servicios bajo demanda por internet (AWS, Azure, GCP).
- **Híbrida**: mezcla datacenter on-prem + cloud público (foco de Wetcom: modernización de DC).

## Pregunta estrella: "Con toda la plata del mundo, ¿cómo armarías tu PC ideal?"

Estructura de respuesta (elegir 1 razón por componente — no enumerar sin más):

> "Arrancaría con un procesador de última generación (Ryzen 9 / Intel Core i9) porque necesito potencia de cómputo para virtualizar: levanto 2-3 máquinas virtuales a la vez para practicar redes y servidores. Le pondría 64 GB de RAM, que es lo que hace realizable la virtualización sin dramas. SSD NVMe de 2 TB para el sistema y VMs, que los discos de estado sólido cambian todo el arranque; más un HDD de gran capacidad para backups. ¿Gráfica? Una de gama media-alta, no la más cara — no es el cuello de botella para mi uso de infraestructura. Fuente certificada 80+ y buen gabinete con airflow. Pienso la PC como un servidor que también me sirva para jugar."

**Truco de dinero por persona:** al ser grupo, aportá "por qué" de cada elección (la racionalidad) — eso es lo evaluable, no la marca. Si otro propone distinto: "buena elección también, ¿y si combinamos un SSD rápido para el SO + más RAM para las VMs?" — suma la idea, no compite.

## Preguntas de inglés preparadas (por si sale)

- "¿Cuál es tu nivel de inglés oral y escrito?" → "Intermediate, around B1. I read technical documentation every day and I can hold a simple conversation. I don't have a certificate yet, but I'm working on it."
- "¿Por qué querés participar?" → "Because I want to start my career in IT, and the program trains you in virtualization and cloud, which is exactly where I want to grow. The permanent contract and certifications are a plus."

## Repaso 30 min sugerido
1. (5') Leer esta guía en voz alta.
2. (10') Decirle a alguien/nota de voz: definir cada concepto con tus palabras.
3. (10') Responder las preguntas reales de Glassdoor de mínimo 8 veces en total:
   bit/byte, ancho de banda, carga/descarga, VMware, 2.4/5GHz, comandos, PC ideal.
4. (5') Lectura de 1 min en inglés en voz alta (posible etapa presencial posterior).