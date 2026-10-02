# Hoja de ruta del piloto de FairCourt

El objetivo inmediato es validar FairCourt con usuarios reales de Comunidad B
antes de ampliar funciones. No se desarrollarán opciones futuras sin una
necesidad observada durante el piloto.

1. **Entrega real del OTP por correo.** Mantener la consola solo para desarrollo
   y configurar un proveedor SMTP seguro en el entorno publicado.
2. **Preparar Comunidad B.** Configurar la pista, sus horarios, las reglas
   acordadas y una primera carga de 5–10 viviendas con correos verificados.
3. **Desplegar un entorno privado.** Publicar Gran Parque y Parque Venecia en
   un servicio con HTTPS, almacenamiento persistente y copias de seguridad
   antes de invitar residentes. Ver [guía de despliegue](despliegue-privado.md).
4. **Completar un ciclo real.** Verificar OTP, aislamiento comunitario, reserva,
   cancelación, límites, uso móvil y recuperación administrativa de acceso.
5. **Priorizar evidencia.** Registrar los problemas observados y desarrollar
   únicamente lo que el piloto demuestre necesario.

## Estado

- Punto 1: implementación y envío SMTP real validados en local.
- Punto 2: [Parque Venecia](parque-venecia-pilot.md) está configurada localmente
  con una pista, reglas provisionales y ocho viviendas controladas. Falta
  sustituir esos datos por los horarios, normas, viviendas y correos confirmados
  por la comunidad.
- Puntos 3–5: pendientes; no se adelantan hasta validar los datos reales del
  punto 2.
