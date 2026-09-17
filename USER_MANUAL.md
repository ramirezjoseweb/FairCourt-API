# Manual de usuario de FairCourt

## Introducción
FairCourt es una aplicación destinada a gestionar las reservas de instalaciones deportivas y espacios comunitarios mediante reglas de equidad, listas de espera, control de asistencia y mecanismos de transparencia.
Este manual explica el funcionamiento de la aplicación desde el punto de vista del usuario.

## Entorno de demostración
La versión pública utiliza datos ficticios. Las reservas, notificaciones y códigos de vivienda pueden reiniciarse periódicamente.

## Inicio de sesión  
Cada enlace de acceso pertenece a una comunidad concreta. Por ejemplo,
`/c/comunidad-a` y `/c/comunidad-b` son portales independientes. Un residente
no necesita ni puede utilizar un selector para saltar entre ellas: su vivienda,
su sesión y sus instalaciones deben pertenecer al portal desde el que accede.

Para iniciar sesión se deberá de asociar la primera vez el código de 
vivienda con un correo electrónico, dicho correo tiene que ser siempre el mismo 
posteriormente para que el sistema te permita iniciar sesión con el código de 
vivienda asociado. 
1. Introduce código de vivienda + correo electrónico. 
2. Solicita el código OTP.  
3. Introduce el código OTP generado por el sistema. 
4. Acceder a la página de inicio FairCourt. 
No se podrá acceder si el código de vivienda no existe o si el correo introducido es diferente al asociado previamente a la vivienda.
El mismo código de vivienda puede existir en dos comunidades distintas sin
compartir cuenta, reservas, listas de espera, sanciones, auditoría o
notificaciones.

## Apariencia clara y oscura
FairCourt utiliza inicialmente el tema claro u oscuro configurado en el
dispositivo. El botón con forma de luna o sol permite cambiarlo tanto en la
pantalla de acceso como, una vez dentro, en la barra superior. La elección se
guarda en el navegador y se mantiene al recargar o volver a abrir la aplicación.

## Página de inicio 
Una vez autenticados, FairCourt nos mostrará automáticamente la página 
de inicio principal donde se muestra información resumida sobre la vivienda. 
Dicha información es:  
* Email de la vivienda 
* Código de vivienda 
* Número de strikes 
* Estado de suspensión de la vivienda o si está activa y libre de suspensión. 
* Número de waitlists activas 
También podemos encontrar una barra de navegación en la parte superior 
de la página que nos permite navegar por la aplicación y nos dice en qué estado 
estamos usando la aplicación, online/offline.

## Consulta de disponibilidad de instalaciones
En la página de disponibilidad se elige primero la instalación. Pádel y Tenis
aparecen destacados por ser los espacios más solicitados; el selector completo
incluye también pérgolas, petanca, pista polideportiva, barra de bar, mesas,
sala multiusos y sauna. A continuación se puede elegir una fecha y consultar
las franjas horarias de ese espacio. Cada instalación mantiene su propia
disponibilidad y lista de espera.

El usuario puede crear una reserva o apuntarse a una lista de espera. Al cambiar
de instalación, la agenda se actualiza automáticamente sin mezclar sus reservas
con las de otros espacios.
Como información adicional, en cada franja horaria podemos ver si está libre de 
reserva, ocupada o bloqueada si la vivienda no cumple las reglas, también nos 
indica si hay cola en la lista de waitlists para cualquier slot.

##  Mis reservas 
Desde la vista de mis reservas, podemos ver la instalación asociada a cada reserva activa y
pasadas de nuestra vivienda. También nos muestra el estado de dichas 
reservas. Desde está parte de la aplicación se realizarán acciones críticas 
cuando haya reservas activas, estas acciones son las de realizar el check-in de  
una reserva y la de cancelar reservas activas, esto solo vale para las reservas 
que no son pasadas ni están marcadas como no-show.

## Sección de auditoría  
En esta sección simplemente podemos ver contenido informativo para 
dejar trazabilidad en las acciones del usuario y aportar transparencia y al mismo 
tiempo resolver alguna incongruencia sin dependencia de un administrador. 
Quedan registradas las acciones importantes y el usuario puede ver que 
acciones o eventos son, cuando se han realizado y metadatos de dichos eventos 
como el email, hora de comienzo, nuevos strikes, etc.

## Página de desbloqueos 
En este apartado de la aplicación, se realizan algunas acciones 
importantes. En esta se incluyen el sistema de votaciones ligeras sobre 
desbloqueos y la creación de propuestas de desbloqueo para tu propia vivienda. 
Esta función puede ser desactivada por la comunidad; en ese caso, los
desbloqueos se gestionarán administrativamente y no se podrán crear ni votar
propuestas desde la aplicación.
Para realizar la segunda acción tu cuenta debe de estar suspendida y el sistema 
te avisa de cuando puedes realizar esta propuesta. 
Por otro lado, en la parte inferior de la página podemos ver todas las propuestas 
de desbloqueo realizadas por tu vivienda y las demás, aquí es donde el sistema 
de votación se implementa. En cada propuesta el usuario podrá votar si está de 
acuerdo con la propuesta de desbloqueo, pudiendo ver información relevante 
como el código de vivienda proponente, motivo de la propuesta, estado de la 
misma (aprobada, expirada, rechazada) y si la propuesta es tuya o no.

## Notificaciones
La campana de la esquina superior derecha abre una vista rápida con las
notificaciones más recientes sin abandonar la pantalla actual. Desde ese panel
se puede acceder a la bandeja completa mediante **Ver todas las notificaciones**.
El botón **Notificaciones** de la navegación lateral continúa abriendo
directamente la página completa.

En la página de notificaciones al igual que en la de auditoría es de carácter 
informativo. Aunque incluye una función no tan crítica pero válida que es la de 
marcar como leído las notificaciones con el objetivo de no acumularse. Podemos 
ver las notificaciones importantes que afectan a tu vivienda como avisos de 
suspensiones, reservas creadas, promociones obtenidas, avisos de no-show + 
strikes, etc. En cada evento notificado podemos ver información adicional como 
la fecha del suceso del evento y qué tipo de evento ha sido notificado. Una vez 
vistas las notificaciones, se recomienda marcarlas como leídas para mantener 
una buena organización en tu sección de notificaciones.

## Uso sin conexión 
FairCourt ofrece funcionamiento offline-first. Cuando el usuario pierda 
conexión, la aplicación puede mostrar la última información sincronizada como 
reservas, notificaciones, auditoría o disponibilidad.  
Sin embargo, quedarán bloqueadas las acciones críticas para evitar 
conflictos y solapamientos en las reservas.
Cuando el sistema vuelva a estar online, se sincronizarán de nuevo los 
datos.

## Contacto

La sección **Contacto** permite enviar una consulta al equipo de la comunidad.
El formulario solicita nombre, e-mail, número de teléfono y el motivo de la
consulta. El e-mail asociado a la sesión aparece rellenado inicialmente y puede
modificarse antes del envío.

## Cierre de sesión 
Por último, en la parte superior derecha de FairCourt, se podrá observar 
un botón “Cerrar sesión”. Al hacerlo se elimina la sesión activa y será necesario 
repetir el proceso de autenticación mediante OTP.  
También se eliminan los datos offline de esa sesión comunitaria para evitar
que aparezcan al acceder después con otra cuenta en el mismo dispositivo.

## Otros documentos, manuales
Los manuales de instalación y usuario son imprescindibles para el 
funcionamiento de la aplicación, pero el proyecto también cuenta con una serie 
de recursos auxiliares que funcionan junto a la aplicación y que son necesarios. 
Lo primero a tener en cuenta que se considera relevante, es la 
documentación automática generada por FastAPI mediante el Swagger. Esta 
documentación es accesible desde /docs una vez ejecutado el backend. Aparte
de poder revisar la documentación, podemos probar los endpoints principales 
del sistema. 
Otros recursos auxiliares del backend son los archivos households.txt, en 
el que se define las viviendas. Por otra parte, tenemos el seed.py que se encarga 
de cargar las viviendas en la base de datos. Estos recursos facilitan en bastante 
cantidad la preparación del entorno.

