# Renovación de FairCourt — matriz funcional

Registrada antes de sustituir la interfaz. Los contratos HTTP y las reglas del servidor se mantienen.

| Capacidad actual | Nueva ubicación | Verificación prevista |
| --- | --- | --- |
| Solicitar OTP con vivienda y correo; verificar; volver; sesión persistente; salir | Acceso y navegación | auth |
| Vivienda, correo, identificador, strikes, suspensión, listas activas | Inicio y detalles de vivienda | home |
| Consulta por fecha y actualización manual | Agenda diaria | agenda |
| Libre/ocupado, reserva propia, pertenencia y tamaño de cola | Franja de agenda | agenda |
| Reservar y entrar en lista; motivos y restricciones | Acciones de franja | booking |
| Reservas activas y pasadas; estado calculado y persistido | Próximas e historial; detalles | reservations |
| Cancelación confirmada | Diálogo de cancelación | cancellation |
| Generar, abrir y copiar enlace de check-in; caducidad | Diálogo de asistencia | checkin |
| Avisos, tipo, fecha, leídos/pendientes, marcado individual y contador | Notificaciones y navegación | notifications |
| Eventos, códigos, identificadores y metadatos | Auditoría y detalles | audit |
| Crear propuesta con motivo, consultar estados y fechas | Desbloqueos | proposals |
| Votar YES/NO; impedir voto propio/cerrado | Propuestas | voting |
| Cargas, errores y actualización manual | Componentes compartidos | errors |
| Lectura cacheada, bloqueo de escrituras, reconexión | Todas las secciones | offline |
| Instalación, recursos locales y apertura offline | PWA | pwa |

## Evidencia

Pendiente de ejecución. Las capturas de antes/después se guardarán en `docs/images/frontend/`.
