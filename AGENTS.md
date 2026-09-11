# Guía para agentes de FairCourt

Este archivo se aplica a todo el repositorio. Su objetivo es que los cambios automáticos respeten la arquitectura y los flujos de trabajo que existen actualmente.

## Qué es el proyecto

FairCourt es una aplicación de reservas justas para instalaciones comunitarias. Consta de:

- una API FastAPI con SQLAlchemy, Alembic, JWT y tareas programadas;
- una SPA React 19 + TypeScript construida con Vite, Tailwind CSS y soporte PWA;
- SQLite para desarrollo local, con una posible evolución a PostgreSQL;
- pruebas end-to-end de Playwright que interceptan la API y no escriben en la base de datos real.

En desarrollo, la API se sirve en `http://127.0.0.1:8000` y el frontend en `http://127.0.0.1:5173`. La previsualización usada por Playwright se sirve en el puerto `4173`.

## Estructura relevante

- `faircourt-backend/app/main.py`: creación de FastAPI, CORS, routers y ciclo de vida del scheduler.
- `faircourt-backend/app/models.py`: modelos y restricciones de SQLAlchemy.
- `faircourt-backend/app/schemas.py`: contratos de entrada y salida de la API.
- `faircourt-backend/app/routers/`: endpoints agrupados por dominio.
- `faircourt-backend/app/services/`: reglas de negocio, auditoría, notificaciones y trabajos programados.
- `faircourt-backend/alembic/versions/`: historial de migraciones; es la fuente de verdad del esquema.
- `faircourt-frontend/src/api/`: cliente HTTP, tipos y funciones por recurso.
- `faircourt-frontend/src/components/ui.tsx`: componentes visuales compartidos.
- `faircourt-frontend/src/hooks/useResource.ts`: lecturas con protección frente a respuestas tardías.
- `faircourt-frontend/src/hooks/useAction.ts`: acciones con bloqueo de envíos duplicados.
- `faircourt-frontend/src/index.css`: sistema visual, composición adaptable y movimiento reducido.
- `faircourt-frontend/tests/`: escenarios Playwright y fixtures de API.
- `docs/frontend-parity.md`: matriz funcional y visual del frontend.
- `docs/images/frontend/current/`: capturas verificadas de la versión actual.

## Contexto arquitectónico actual

La aplicación es multipista. `Facility` representa cada instalación, y tanto reservas como listas de espera están asociadas obligatoriamente mediante `facility_id`. Las consultas de disponibilidad, límites, cooldowns, promociones de lista de espera y trabajos programados deben conservar ese ámbito. No reintroduzcas la antigua suposición de que existe una única pista implícita.

El catálogo de instalaciones llega desde `GET /facilities`; no dupliques el catálogo como una lista fija en el frontend. Pádel y Tenis encabezan el catálogo mediante el campo `priority`, pero el orden y la disponibilidad pertenecen al backend.

El frontend actual centraliza los contratos HTTP en `src/api`, las lecturas en `useResource`, las mutaciones en `useAction` y los elementos visuales reutilizables en `components/ui.tsx`. Amplía estas abstracciones antes de crear variantes locales de la misma lógica.

La PWA conserva lecturas en caché. Una pérdida de transporte marca la API como inaccesible y deshabilita escrituras; un error HTTP válido del servidor no equivale a estar sin conexión. Mantén esa distinción.

## Puesta en marcha

Usa Python 3.11.9 o superior, Node.js 24.15.0 o superior y npm 11.12.1 o superior.

Backend, desde `faircourt-backend`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python seed.py --file households.txt
uvicorn app.main:app --reload
```

Frontend, desde `faircourt-frontend`:

```powershell
npm ci
npm run dev
```

El OTP se imprime en la terminal únicamente en el modo de desarrollo actual. No expongas tokens, OTP ni secretos en la interfaz, capturas, logs añadidos o fixtures que se vayan a versionar.

## Comprobaciones antes de entregar

Para cambios de frontend, ejecuta desde `faircourt-frontend`:

```powershell
npm run lint
npm run build
npm run test:e2e
```

Playwright usa Microsoft Edge por defecto. Para Chrome instalado localmente:

```powershell
$env:PW_CHANNEL = "chrome"
npm run test:e2e
```

Las pruebas levantan una compilación de producción en `127.0.0.1:4173`. Si ya hay un servidor de previsualización reutilizado, asegúrate de haber reconstruido el frontend. Añade o adapta fixtures cuando cambie un contrato de API y cubre, según proceda, estado correcto, error, respuesta tardía, doble clic, teclado, móvil y pérdida de red.

El backend no tiene actualmente una suite automatizada versionada. Como mínimo, para cambios Python ejecuta desde `faircourt-backend`:

```powershell
python -m compileall app
```

Además, prueba los endpoints afectados con una base de datos desechable o una copia explícita; no uses la base de trabajo para pruebas destructivas. Si un cambio cruza backend y frontend, verifica también que los esquemas Pydantic, los tipos TypeScript, los fixtures y las llamadas HTTP coincidan.

## Base de datos y migraciones

- `faircourt-backend/faircourt.db` es estado local versionado y puede contener actividad del usuario. No lo modifiques, reemplaces ni reviertas salvo petición expresa.
- Los archivos `*.db.backup` son copias locales. No los añadas al control de versiones.
- No ejecutes `reset_all.py`, `reset_reservations.py` ni `reset_votes.py` sin autorización explícita: son utilidades destructivas.
- Todo cambio de esquema requiere una nueva migración de Alembic. No edites una migración ya aplicada para representar un cambio nuevo.
- Mantén las migraciones reversibles y compatibles con SQLite. Usa operaciones por lotes de Alembic cuando sea necesario para alterar restricciones o claves foráneas.
- No elimines ni relajes los índices y restricciones que separan instalaciones, especialmente los que incluyen `facility_id` y `start_at`.

## Convenciones de implementación

Backend:

- Mantén los routers finos; sitúa las reglas reutilizables en `app/services`.
- Declara contratos públicos en `app/schemas.py` y relaciones/persistencia en `app/models.py`.
- Usa la dependencia `get_db` para el ciclo de vida de la sesión y confirma transacciones de forma explícita.
- Conserva auditoría, notificaciones y promoción de lista de espera al modificar reservas o sanciones.
- Registra routers nuevos en `app/main.py` y asigna prefijo y etiqueta de dominio.

Frontend:

- Mantén TypeScript estricto y evita `any` salvo en límites externos justificados.
- Añade las llamadas de cada dominio bajo `src/api`; no uses `fetch` directamente desde componentes.
- Reutiliza `apiRequest` para autorización y detección de alcance de la API.
- Preserva navegación por teclado, foco de diálogos, contraste, `prefers-reduced-motion` y los diseños de 375, 768 y 1440 píxeles.
- No registres el service worker durante desarrollo; el comportamiento PWA se valida sobre la compilación de producción.
- Sigue el formato existente y deja que ESLint, TypeScript y la compilación detecten regresiones. No hay un script de formato obligatorio en `package.json`.

## Documentación y capturas

Actualiza `README`, `USER_MANUAL.md` y/o `docs/frontend-parity.md` cuando cambien la instalación, el comportamiento visible o la paridad funcional.

Después de una batería Playwright completa y correcta, las capturas verificadas pueden exportarse con:

```powershell
npm run test:e2e:export
```

No exportes capturas de una ejecución parcial o fallida. `test-results`, `playwright-report`, `dist` y `node_modules` son artefactos locales y no deben versionarse.

## Disciplina de cambios

- Revisa `git status` antes y después de trabajar.
- Preserva cambios locales ajenos a la tarea, en especial bases de datos y copias de seguridad.
- Limita cada cambio al dominio solicitado; evita refactorizaciones amplias no relacionadas.
- No cambies contratos de API silenciosamente: actualiza consumidores, fixtures, pruebas y documentación en el mismo cambio.
- Explica qué validaciones se ejecutaron y cuáles no pudieron ejecutarse al entregar el trabajo.
