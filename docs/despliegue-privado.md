# Publicación privada de FairCourt: Gran Parque y Parque Venecia

Esta guía prepara **un único servicio** para las dos comunidades, con acceso
por vivienda y OTP. La página de acceso es pública; los datos y las reservas no.
El dominio de la primera publicación es `faircourt.es`. Antes de cambiar su
DNS hay que comprobar qué servicio responde actualmente en la raíz y evitar
alterar registros MX/TXT del correo OVH/Brevo.

## Condiciones antes de abrir el acceso

- Un VPS Linux pequeño bajo control del titular, con DNS del nombre elegido
  apuntando al servidor. Abrir al público solo 80/443; limitar SSH.
- Python >= 3.11, Caddy y Restic instalados. Compilar el frontend con Node >= 24
  en un equipo de confianza. Un solo proceso de API: el scheduler se inicia en
  ese proceso y no debe duplicarse con varios workers.
- Repositorio de copias **fuera del VPS**, cifrado con Restic, credenciales
  individuales y contraseña guardada fuera de Git. Probar una restauración.
- Correo SMTP de Brevo validado y una clave JWT aleatoria nueva. Nunca copiar la
  `.env` local ni la base `faircourt-backend/faircourt.db` al servidor.
- Listas reales de viviendas y correos revisadas con el responsable de cada
  comunidad. Los `PILOTO-01` de Parque Venecia no son viviendas definitivas.

## Paquete sin datos locales

Desde el repositorio, ejecutar primero las pruebas; Playwright puede reconstruir
`dist` con la URL de desarrollo. **Después de las pruebas**, compilar el frontend
con `VITE_API_BASE_URL=/api` y
ejecutar `python deploy/package_release.py --output RUTA_FUERA_DEL_REPOSITORIO.tar.gz`.
El empaquetador utiliza una lista cerrada de archivos y excluye bases `.db`,
`.sqlite3`, `.env`, pruebas y dependencias locales. Verificar el contenido del
archivo antes de transferirlo. No clonar el repositorio completo en el VPS:
contiene una base de desarrollo versionada.

Extraer el paquete en `/srv/faircourt/release`, legible por el usuario de
servicio `faircourt` y por Caddy. Crear el entorno virtual en
`/srv/faircourt/release/faircourt-backend/.venv` e instalar allí
`requirements.txt`. La base de datos se guarda exclusivamente en
`/var/lib/faircourt/faircourt.sqlite3`, fuera de la publicación y del código.
No copiar la base local: Alembic crea una base limpia al arrancar el servicio.

## Configuración del servidor

1. Crear el usuario de sistema `faircourt` sin acceso interactivo y los
   directorios `/srv/faircourt/release`, `/var/lib/faircourt` y
   `/etc/faircourt` con permisos mínimos.
2. Usar `deploy/app.env.example` para crear `/etc/faircourt/app.env`, propiedad
   `root:faircourt` y modo `0640`. Sustituir **todos** los marcadores. Generar
   una `SECRET_KEY` nueva con un generador criptográfico; no reutilizar la local.
   `APP_ENV=production` impide arrancar con OTP de consola, HTTP o una base
   relativa/dentro del repositorio.
3. Configurar el bucket privado `faircourt-backup-par-2026` de Scaleway en
   `/etc/faircourt/backup.env` a partir de `deploy/backup.env.example`. Crear
   una clave IAM dedicada al backup, vinculada al proyecto correcto, y guardar
   su secreto solo en el servidor. Proteger la contraseña independiente de
   Restic en `/etc/faircourt/restic-password` (modo `0640`, grupo `faircourt`)
   e inicializar el repositorio remoto. No almacenar la única copia en el VPS.
4. Instalar `deploy/faircourt.service`, `deploy/faircourt-backup.service` y
   `deploy/faircourt-backup.timer` en systemd. Activar la API y el temporizador.
   La API escucha solo en `127.0.0.1:8000` y aplica `alembic upgrade head` antes
   de arrancar. El temporizador hace una copia SQLite consistente a las 03:00
   (hora local del servidor, con pequeño retraso aleatorio) y la sube cifrada.
5. Adaptar `deploy/Caddyfile.example` al nombre elegido e instalarlo en Caddy.
   `/api/*` se envía a FastAPI y el resto sirve la SPA; Caddy gestiona HTTPS.
   DNS y puertos 80/443 deben estar disponibles para que emita el certificado.

Para tareas manuales de alta se puede indicar
`FAIRCOURT_ENV_FILE=/etc/faircourt/app.env` al ejecutar Python como usuario
`faircourt`. Ese archivo se lee como variables, sin ejecutarlo como script de
shell. Si la ruta no existe, el comando se detiene. La URL de producción es
absoluta y queda fuera del repositorio.

## Alta limpia de las dos comunidades

Después de las migraciones, preparar **las dos comunidades reales vacías**:

```bash
FAIRCOURT_ENV_FILE=/etc/faircourt/app.env python -m scripts.bootstrap_production_communities
```

Este comando se ejecuta desde `faircourt-backend` como `faircourt`. Las
migraciones históricas crean una comunidad técnica `faircourt` con instalaciones
de demostración; el bootstrap la deja inactiva **solo si no tiene viviendas ni
usuarios**. Si contiene actividad, se detiene para revisión y no borra nada.
Dar de
alta el administrador con `python -m scripts.bootstrap_platform_admin --email ...`,
usando un correo confirmado por el titular. Después, desde `/admin`:

- Configurar para cada comunidad sus instalaciones, horarios y reglas **aprobadas**.
- Importar el CSV de viviendas/correos revisado de cada comunidad; comprobar la
  vista previa antes de confirmar y verificar qué códigos ya existen.
- Activar los prefijos `GRP` y `PV` solamente cuando **todos** los códigos de
  sus viviendas sean compatibles. No copiar los códigos de prueba
  `PILOTO-01` a los vecinos reales ni asignarles correos ajenos.

No se importan automáticamente reservas, OTP, auditoría ni cuentas de la base
local de Gran Parque. Si alguna información histórica se necesita de verdad,
se define y revisa una migración de datos separada.

## Comprobación obligatoria antes de invitar vecinos

1. Comprobar `https://NOMBRE/api/health`, la carga de `/`, `/admin` y
   `/c/gran-parque` y `/c/parque-venecia` por HTTPS.
2. Probar OTP de administrador y de una vivienda autorizada de **cada**
   comunidad; los correos deben llegar sin que códigos ni claves aparezcan en
   logs o interfaz.
3. Probar que códigos de una comunidad no permiten ver instalaciones,
   disponibilidad, reservas ni notificaciones de la otra.
4. Validar una reserva y cancelación desde móvil, límites, horarios y la
   recepción del correo. Verificar el enlace de check-in bajo `/api`.
5. Ejecutar una copia con `faircourt-backup.service`, comprobar que terminó sin
   errores, listar instantáneas y restaurar **a una ubicación desechable**. La
   base restaurada se llama `faircourt.sqlite3`; Restic recibe cada copia bajo
   ese nombre estable aunque la instantánea SQLite se prepare en un directorio
   temporal diferente cada día.
   Abrir la copia restaurada con SQLite y ejecutar `PRAGMA integrity_check`.
   No restaurar sobre la base viva durante la prueba.
6. Vigilar diariamente el estado del temporizador, la capacidad del repositorio
   remoto y los errores del servicio. Definir retención de instantáneas antes
   de que el espacio sea un problema; no borrar instantáneas sin verificar una
   restauración reciente.

Hasta que se disponga del VPS, DNS, almacenamiento externo y datos reales
revisados, esta configuración está **preparada, no desplegada**. Ningún vecino
debe ser invitado antes de completar la lista de comprobación.
