# Hoja de ruta del piloto de FairCourt

El objetivo inmediato es validar FairCourt con usuarios reales de Comunidad B
antes de ampliar funciones. No se desarrollarán opciones futuras sin una
necesidad observada durante el piloto.

1. **Entrega real del OTP por correo.** Mantener la consola solo para desarrollo
   y configurar un proveedor SMTP seguro en el entorno publicado.
2. **Preparar Comunidad B.** Configurar la pista, sus horarios, las reglas
   acordadas y una primera carga de 5–10 viviendas con correos verificados.
3. **Desplegar un entorno privado.** Usar HTTPS, almacenamiento persistente y
   copias de seguridad antes de invitar residentes.
4. **Completar un ciclo real.** Verificar OTP, aislamiento comunitario, reserva,
   cancelación, límites, uso móvil y recuperación administrativa de acceso.
5. **Priorizar evidencia.** Registrar los problemas observados y desarrollar
   únicamente lo que el piloto demuestre necesario.

## Estado

- Punto 1: implementación completada y validada. Falta configurar las
  credenciales del proveedor SMTP en el entorno publicado y hacer un envío real.
- Puntos 2–5: pendientes; no se adelantan hasta completar el punto anterior.
