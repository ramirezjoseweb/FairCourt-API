# FairCourt — frontend

Interfaz de reservas comunitarias construida con React, TypeScript, Vite y Tailwind.

## Desarrollo local

Desde esta carpeta:

```powershell
npm install
npm run dev
```

Abre http://127.0.0.1:5173 para la comunidad inicial o
http://127.0.0.1:5173/c/comunidad-b para un portal comunitario concreto. El
cliente utiliza la API en http://127.0.0.1:8000 y el acceso por vivienda,
correo y OTP. Para utilizar datos reales, inicia el backend siguiendo el README
de la raíz. La ayuda para consultar el OTP en la terminal solo aparece en
desarrollo.

## Comprobaciones

```powershell
npm run build
npm run lint
npm run test:e2e
```

Las pruebas se ejecutan contra la compilación de producción en el puerto 4173. Si no existe un servidor de previsualización, Playwright lo compila e inicia. Si ya está abierto, ejecuta primero el build para actualizarlo.

Se utiliza Microsoft Edge en Windows. Para probar con Google Chrome instalado:

```powershell
$env:PW_CHANNEL = "chrome"
npm run test:e2e
```

El conjunto incluye 33 escenarios de acceso comunitario, reservas, listas de
espera, asistencia, avisos, auditoría, contacto, red, accesibilidad y diseño
adaptable. Las respuestas de la API están controladas dentro de los tests; no
se crean reservas ni votos en la base de datos real.

Las capturas de cada ejecución se guardan dentro de test-results. Tras una batería completa correcta, ejecuta npm run test:e2e:export para copiar las 30 capturas verificadas a ../docs/images/frontend/current. El informe de Playwright se puede abrir con npm run test:e2e:report. Los perfiles de navegador, trazas e informes temporales están excluidos de Git.

## Interfaz y datos

- Componentes visuales compartidos: src/components/ui.tsx.
- Carga de datos con protección frente a respuestas tardías: src/hooks/useResource.ts.
- Acciones con bloqueo de envíos duplicados: src/hooks/useAction.ts.
- Contratos HTTP y almacenamiento de sesión: src/api.
- Estilos, paleta, composición adaptable y movimiento reducido: src/index.css.

Las seis secciones originales y el apartado de contacto siguen disponibles. La navegación es lateral en ordenador e inferior en móvil. Los detalles técnicos útiles de reservas, vivienda y auditoría siguen accesibles mediante desplegables. El token de sesión ya no se expone en pantalla.

## Sin conexión y PWA

La compilación de producción incluye el manifiesto, los iconos y el service worker. El service worker se desactiva en desarrollo para evitar mezclar versiones durante los cambios.

La última información consultada se conserva con claves separadas por
comunidad. Las escrituras se deshabilitan tanto cuando el navegador pierde
conexión como cuando una petición no puede alcanzar la API. Un error HTTP del
servidor no se interpreta como desconexión. Se puede reintentar la conexión y
los datos se actualizan al recuperarla.

La prueba de PWA verifica los requisitos de instalación, el control del service worker, los tamaños reales de los iconos y la recarga con la red bloqueada y la caché HTTP desactivada. No instala un acceso directo en el sistema operativo.

Consulta la matriz completa y las comparaciones visuales en ../docs/frontend-parity.md.
