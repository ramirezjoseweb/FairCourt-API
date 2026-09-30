# Piloto de Parque Venecia

## Configuración provisional

- Comunidad: **Parque Venecia**.
- Identificador del portal: `parque-venecia`.
- Zona horaria: `Europe/Madrid`.
- Instalación: una pista de **Pádel**.
- Horario: de 09:00 a 22:00.
- Duración de cada turno: 60 minutos.
- Antelación máxima para reservar: 7 días.
- Reservas activas máximas: 1 al día y 2 a la semana por vivienda.
- Cancelación permitida hasta 4 horas antes.

Estos valores permiten probar el flujo completo, pero no deben considerarse
normas aprobadas por la comunidad.

## Viviendas iniciales

La prueba local contiene ocho viviendas, desde `PILOTO-01` hasta `PILOTO-08`.
Son identificadores temporales porque todavía no se conocen los bloques ni la
numeración real. Sus correos son alias controlados de la cuenta del responsable,
por lo que ningún vecino recibirá mensajes durante las pruebas.
Se puede probar `PILOTO-01` desde la entrada general `/`, porque actualmente
identifica una única vivienda. El prefijo definitivo `PV` se configurará en el
panel cuando se conozcan los códigos reales y las viviendas existentes lo
respeten; no se han inventado códigos `PV000X` para residentes reales.

El archivo local que contiene esos correos termina en `.local.csv` y está
excluido de Git. Cuando se disponga del listado real, debe prepararse un CSV con
estas columnas:

```csv
codigo_vivienda;correo;activa
BLOQUE-PORTAL-PUERTA;persona@ejemplo.es;si
```

Antes de importar el archivo real hay que comprobar que cada dirección pertenece
a la vivienda indicada y que existe consentimiento para usarla en el piloto.

## Pendiente de confirmar

1. Número de pistas y nombre con el que las conoce la urbanización.
2. Horario real de apertura y cierre.
3. Duración real de los turnos.
4. Bloques, portales y numeración de viviendas.
5. Reglas de antelación, límites y cancelación acordadas por la comunidad.
6. Lista de 5–10 participantes voluntarios y sus correos verificados.

El portal local del piloto es `http://127.0.0.1:5173/c/parque-venecia`.
