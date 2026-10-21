# BRIEF PARA EL AGENTE: terminar BioTrack cliente/servidor sobre sockets TCP

Eres un agente con acceso de lectura/escritura al repositorio. Tu tarea es **terminar el refactor** de BioTrack (aplicación de terminal con ORM) a una arquitectura **cliente/servidor sobre sockets TCP**, cubriendo **todas** las funciones de `client/cli_app.py`, con tests, documentación y calidad de código.

Este documento es tu especificación completa. Léelo entero antes de tocar nada. Está dividido en **bloques de trabajo (A–F)**. Trabaja bloque a bloque, con **exactamente un commit por bloque completado** (ni más ni menos). Si el usuario te indica "haz solo los bloques A y B", haz solo esos.

Todo el **código, comentarios, docstrings, nombres, mensajes de commit y documentación técnica** va **en inglés**. Este brief está en español solo por comodidad del usuario.

---

## 1. Contexto y objetivo

BioTrack es una app de terminal (menús con Rich) que hoy accede directamente a la base de datos con SQLAlchemy. Se pide partirla en **dos programas independientes**:

- **Servidor:** escucha conexiones TCP, procesa peticiones, ejecuta la lógica de negocio y accede a la BD mediante la capa de persistencia.
- **Cliente:** se conecta por TCP, envía peticiones según el protocolo, y muestra resultados al usuario. **No** conoce SQLAlchemy ni la BD.

### Requisitos del enunciado (resumen literal de lo evaluable)

- Sockets **bloqueantes** de la librería `socket` de Python. **El servidor solo atiende a un cliente a la vez.**
- Protocolo definido y **documentado**: formato de petición, de respuesta, operaciones soportadas, estrategia de errores. (Elegido: **subconjunto de HTTP/1.1 sobre TCP con cuerpo JSON**, ver `docs/protocol.md`.)
- SQLAlchemy **exclusivamente en el servidor**. Entre cliente y servidor solo viajan DTOs/dicts/JSON.
- **Router** en el servidor: recibe la petición, identifica la operación, delega en el **servicio** adecuado, devuelve respuesta formateada.
- **Tests unitarios** de: lógica de servicios, validación de peticiones, router, serialización/deserialización del protocolo. BD y sockets pueden mockearse.
- PEP 8, nombres significativos en inglés, separación de responsabilidades, sin duplicación.
- Entregables: repo Git, documentación del protocolo, SHA del último commit, tag `v2.0.0` (**el tag y el push los hace el usuario, no tú**).

### Rúbrica (cada criterio vale 2 puntos)

1. Arquitectura: capas claras, separación de responsabilidades, mantenible.
2. Protocolo: definido, documentado, implementado, errores consistentes.
3. Separación cliente/servidor/shared: el cliente no depende de persistencia/dominio.
4. Tests unitarios: servicios, router, protocolo, bien organizados y ejecutables.
5. Calidad: PEP 8, nombres en inglés, legibilidad.

---

## 2. Reglas duras

### Permitido
- Librería estándar de Python: `socket`, `json`, `dataclasses`, `datetime`, `decimal`, `logging`, `typing`, `os`, `sys`, `unittest`, `unittest.mock`, `argparse` (opcional), etc.
- SQLAlchemy, Alembic, python-dotenv, psycopg2: **solo servidor**. Rich: **solo cliente**.

### Prohibido (el profesor quiere que el protocolo y el servidor se escriban a mano)
- Frameworks o librerías de red/web: FastAPI, Flask, `requests`, `http.server`, `http.client`, `socketserver`, `urllib.request`, `urllib3`, `aiohttp`, `websockets`, etc.
- Concurrencia: `threading`, `asyncio`, `select`, `selectors`, `multiprocessing`, `concurrent.futures`. El servidor es secuencial y bloqueante.
- Para evitar dudas con el profesor: **no uses `re` ni `urllib.parse`**. El parseo de rutas, query strings y la codificación/decodificación porcentual (`%XX`) se implementan a mano en `shared/protocol.py`.
- Instalar dependencias nuevas de runtime. (`flake8`/`ruff` como herramienta de desarrollo es aceptable; no se importa en el código.)

### Seguridad de datos y repositorio
- **No ejecutes** los notebooks, `alembic upgrade/downgrade`, ni nada que escriba en `data/biotrack.db`. No modifiques migraciones ni el esquema de la BD ni los modelos ORM salvo que sea imprescindible (y si lo haces, avísalo en el informe).
- Las pruebas manuales end-to-end se hacen con `ENVIRONMENT=test` (usa `data/biotrack_test.db`) y, si tocas datos, sobre una **copia temporal** de esa BD que no se commitea.
- Git: trabaja en la rama `feature/client-server` (créala desde `main`). **Prohibido `git push` en cualquier forma** (tampoco `--force`, ni `git remote add/set-url`, ni subir tags), y prohibido `git merge`, `git tag`, `git rebase` y `git reset --hard`. Todo se queda en local. Antes de empezar: `git status` debe estar limpio; si no lo está, **detente y avisa**.
- No commitees `.env`, `__pycache__`, `*.db` de pruebas ni archivos temporales.
- **Un solo commit por bloque, y solo cuando el bloque esté completo y sus tests pasen.** No hagas commits intermedios ni de trabajo a medias. Si un bloque no está terminado, no commitees.
- Prefijos de commit: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`. Mensaje en inglés, una línea de resumen más una lista breve de lo hecho.

### Entorno
- Windows, Git Bash/PowerShell. venv en `./venv`: usa `./venv/Scripts/python.exe` (o `python` con el venv activo).
- Todo se ejecuta **desde la raíz** del proyecto. Imports **absolutos desde la raíz** (`from shared.dtos import ...`).
- Arranque: `python run_server.py`, `python run_client.py`. Tests: `python -m unittest discover -s tests -t .`.
- No ejecutes archivos de dentro de `client/` o `server/` directamente.

---

## 3. Estado actual (verifícalo primero, no lo des por supuesto)

El usuario ya hizo lo siguiente (comprueba cada punto con comandos de solo lectura y **reporta cualquier discrepancia**):

- `src/domain/` se movió a `server/persistence/` (config.py, database.py, `models/`, `repositories/`). Existen `server/__init__.py`, `shared/`, `client/`, `tests/{shared,server,client}/`, `docs/` con sus `__init__.py` (excepto `docs/`).
- `docs/protocol.md` existe (versión 1.0, en inglés). Es el **contrato**. Léelo completo. Más abajo (sección 5) hay **enmiendas obligatorias** porque la CLI original necesita datos/operaciones que ese documento todavía no cubre.
- `server/tcp_server.py`: servidor de prueba tipo "eco" (`serve(handler)` con `handler: bytes -> bytes`, `settimeout`, `SO_REUSEADDR`, `listen(5)`, `accept` con timeout de 1 s para permitir Ctrl+C en Windows). Se refactorizará.
- `run_server.py`: arranca `serve(echo_handler)`. `run_client.py`: arranca `client.cli_app.main()`.
- `shared/protocol.py`: solo contiene `build_request(method, path, body, host)`.
- `client/connection.py`: `send_request(method, path, body)` devuelve los **bytes crudos** de una sola llamada a `recv`.
- `client/api_client.py`: solo `list_patients(active_only)` (devuelve bytes crudos).
- `client/cli_app.py`: es el `cli_app.py` original (~1800 líneas) movido a `client/`. **Todavía importa `server.persistence`** y casi todas las funciones usan `UnitOfWorkFactory` y repositorios directamente. Solo `list_patients` está adaptada provisionalmente (imprime la respuesta cruda).
- `.env` ya está fuera de Git, existe `.env.example`.
- Git: rama `main`, commits recientes: reorganización de carpetas. `alembic/env.py` ya apunta a `server.persistence`.

Conoce también estas peculiaridades del código existente (de un análisis previo):
- `server/persistence/config.py` busca la raíz subiendo hasta encontrar `.env` y **lanza error si no existe**; construye `DB_URL` según `ENVIRONMENT` (`development` → `data/<DB_FILENAME_DEVELOPMENT>`, `test` → `data/<DB_FILENAME_TEST>`, `production` → `DB_URL_PRODUCTION`).
- `UnitOfWorkFactory(DB_URL).create()` devuelve un context manager: **commit al salir sin excepción, rollback con excepción**, y cierra la sesión. `uow.session` es la sesión. **Importante:** el commit ocurre en el `__exit__`, es decir *fuera* de los `try/except` que pongas dentro del `with`. Por tanto, para convertir `IntegrityError` en `ConflictError` debes llamar a `uow.session.flush()` **dentro** del `with` y dentro del `try`.
- `BaseRepository(session, Model)` tiene `get_by_id`, `get_all`, `save` (solo `session.add`), `delete`, `count`. Hay repositorios específicos (Patient, Staff, ResearchProject, Sample, Protocol, QualityControl, LogTemperature, SampleType, Container) con los métodos listados en la sección 7 y los que ya usa `cli_app.py` (por ejemplo `ContainerRepository.get_by_code_or_type_name`, `StaffRepository.add_to_research_project`, `StaffRepository.get_research_project_with_roles`, `SampleRepository.get_full`, `ResearchProjectRepository.get_with_team`, `PatientRepository.get_with_samples`, `ProtocolRepository.search_by_name` / `get_with_samples`, `QualityControlRepository.get_by_sample_code`). **Léelos antes de escribir servicios** y reutilízalos; no los reescribas.
- Los modelos usan `Mapped`/`mapped_column`; `Sample.volume` es `Numeric(10,4)` (llega como `Decimal`), `status`/`role`/`result` son `Enum` en forma de string, `last_update` es `DateTime`.
- SQLite **no** tiene `PRAGMA foreign_keys=ON` configurado: no confíes en que la BD rechace borrados con hijos. Implementa **comprobaciones explícitas de negocio** (como hacía la CLI) y captura `IntegrityError` como red de seguridad.
- Discrepancia conocida del esquema: `Protocol.creation_date` y `ResearchProjectSamples.sample_assignment_date` están como `DateTime` en el modelo y como `Date` en la migración. No lo arregles: serializa `creation_date` como **fecha** (`YYYY-MM-DD`) y `assignment_date` como datetime ISO o fecha según el valor real (usa una conversión tolerante: si es `datetime` → ISO datetime; si es `date` → ISO date). Documéntalo en el informe.

---

## 4. Arquitectura objetivo

```
biotrack/
├── run_server.py                 # composition + serve()
├── run_client.py                 # client.cli_app.main()
├── shared/                       # sin imports del proyecto
│   ├── __init__.py
│   ├── protocol.py               # codec HTTP-like (bytes <-> dataclasses)
│   ├── dtos.py                   # dataclasses + dto_to_dict / dto_from_dict
│   └── errors.py                 # HttpError, ApiError
├── server/
│   ├── __init__.py
│   ├── settings.py               # host/port/timeouts/limits del servidor
│   ├── app.py                    # build_router(uow_factory) -> Router  (composition root)
│   ├── tcp_server.py             # bucle accept/recv/sendall (secuencial)
│   ├── router.py                 # (method, pattern) -> handler
│   ├── controllers/              # 1 archivo por recurso: valida forma, llama al servicio
│   │   ├── __init__.py
│   │   ├── validation.py         # helpers reutilizables
│   │   └── <resource>_controller.py
│   ├── services/                 # 1 archivo por recurso: reglas de negocio, devuelve DTOs
│   │   ├── __init__.py
│   │   ├── errors.py             # ServiceError, NotFoundError, ConflictError, ServiceValidationError
│   │   └── <resource>_service.py
│   └── persistence/              # YA EXISTE (config, database, models, repositories)
├── client/
│   ├── __init__.py
│   ├── settings.py               # host/port/timeouts del cliente (sin .env)
│   ├── connection.py             # único sitio del cliente con sockets
│   ├── api_client.py             # 1 función por operación; devuelve dicts/listas
│   └── cli_app.py                # menús Rich (UI); sin acceso a datos
├── tests/{shared,server,client}/ # espejo del código; con __init__.py
├── docs/protocol.md
├── README.md
└── requirements-server.txt, requirements-client.txt, requirements-dev.txt
```

### Regla de dependencias (verificable con `grep`)
```
client ──► shared ◄── server ──► server/persistence ──► SQLAlchemy
```
- `client` importa solo `shared` (y stdlib + Rich). Nunca `server`, nunca SQLAlchemy.
- `shared` no importa nada del proyecto.
- Los **servicios** no importan nada de `shared.protocol` (no saben de HTTP). Importan `shared.dtos`.
- Los **controladores** no importan repositorios ni modelos ORM (solo servicios, DTOs y validación).
- Solo `services/` y `persistence/` conocen SQLAlchemy/modelos.

### Flujo de una petición
```
cli_app ─► api_client ─► connection ──TCP──► tcp_server
                                                │ read_http_message / parse_request   (shared)
                                                ▼
                                              Router ─► Controller (valida forma) ─► Service (negocio) ─► Repository ─► BD
                                                │                                        │
                                                └◄── (status, payload) ◄── DTO ◄─────────┘
                                              build_response (shared) ─► sendall ─► close
```

### Responsabilidades
| Capa | Hace | No hace |
|---|---|---|
| `tcp_server` | accept, timeout, leer mensaje, parsear, despachar, construir respuesta, enviar, cerrar, **convertir cualquier excepción en respuesta** | negocio, SQL |
| `router` | casar (método, ruta), extraer parámetros, 404/405, **traducir errores de servicio → HTTP** | validar datos, BD |
| `controller` | validar **forma** (422), convertir JSON→DTO, llamar al servicio, DTO→dict, elegir 200/201/204 | consultar BD |
| `service` | reglas de negocio (404/409/422 de negocio), usar repositorios/UoW, devolver DTOs | HTTP, JSON, `print` |
| `persistence` | modelos y consultas (ya existente) | todo lo demás |

---

## 5. Protocolo: `docs/protocol.md` y enmiendas OBLIGATORIAS

Implementa exactamente lo que dice `docs/protocol.md` (formato, límites, códigos, serialización, errores). **Además**, la CLI original necesita lo siguiente, que el documento aún no recoge. **Actualiza `docs/protocol.md`** (es un documento aún no entregado; no hace falta subir versión mayor, pero añade una línea al historial de revisiones) con estas enmiendas **antes** de implementar el bloque correspondiente:

1. **`last_update`** (datetime ISO) en las representaciones de: Patient, Sample, Staff, Project, Protocol, Container, SampleType, y en cada elemento de `GET /staff/{code}/assignments`. La CLI lo muestra en casi todas las tablas.
2. **`patient_name`** (string `"<name> <lastname>"`) en la representación de Sample (la usa la tabla de "view protocol samples").
3. **`DELETE /samples/{code}/quality-control`** → 204 (404 si la muestra o su QC no existen). La CLI permite borrar el control de calidad.
4. **`GET /projects?name=<exact name>`**: filtro por nombre **exacto**; devuelve un array con 0 o 1 elemento. Lo usan `search_project_name` y `assign_staff_project` (la CLI pide el nombre del proyecto, no el ID).
5. **`samples[].status`** en el detalle de proyecto (`GET /projects/{id}`), además de `code` y `assignment_date`.
6. **Staff delete:** la CLI original permite borrar personal sin comprobación de negocio (la BD gestiona cascadas). Cambia el texto del documento: `409` solo si la integridad lo impide (no por "estar asignado a un proyecto").
7. **Patients delete:** el `detail` del 409 debe incluir el número de muestras: `"Patient 'PAT-001' has 3 sample(s) linked; delete or reassign them first"`.
8. Amplía los ejemplos solo si algún `Content-Length` cambia; **verifica con Python** (`len(texto.encode("utf-8"))`) que todos los `Content-Length` de los ejemplos del documento son correctos.

Reglas adicionales de implementación del protocolo:
- Cabeceras **siempre** `Content-Length` (0 si no hay cuerpo) y `Connection: close`. `Content-Type: application/json` solo si hay cuerpo (petición); la respuesta lo lleva siempre salvo 204.
- Límites: cabeceras ≤ 8192 bytes, cuerpo ≤ 1 048 576 bytes (→ 413). Timeout de lectura del servidor 5 s (→ 408). Timeout del cliente 10 s.
- `Transfer-Encoding` presente → 400.
- Orden de validación: formato (400/408/413) → ruta (404/405) → forma de datos (422) → reglas de negocio (404/409).
- Errores: cuerpo único `{"status": int, "title": str, "detail": str}`. `title` fijo por código (ver doc). El 500 **nunca** expone detalles; el traceback va al log (`logging`).
- Decimal → string (`"2.5000"`); acepta también número JSON en peticiones. Fechas ISO. Enums en minúscula, sensibles a mayúsculas.
- Los parámetros de ruta y de query se **codifican** en el cliente y se **decodifican** en el servidor (`%XX`, y `+` → espacio en query).

---

## 6. Diseño detallado por componente

### 6.1 `shared/errors.py`
- `HttpError(status: int, detail: str)`: error que se mapea directamente a un código HTTP (lo usan parser, router y controladores).
- `ApiError(status: int, detail: str)`: lo lanza el **cliente** cuando recibe ≥ 400 o hay fallo de red (`status=0`, detail `"Cannot reach the server"`).

### 6.2 `shared/protocol.py` (funciones puras o con un socket inyectado; sin BD)
Mantén `build_request(method, path, body, host)` (ya existe) y añade:
- Constantes: `CRLF`, `HEADER_TERMINATOR = b"\r\n\r\n"`, `MAX_HEADER_BYTES`, `MAX_BODY_BYTES`, `STATUS_REASONS`, `STATUS_TITLES`.
- `@dataclass(frozen=True) HttpRequest(method, path, query: dict[str,str], headers: dict[str,str], body: bytes)` y `HttpResponse(status, headers, body)`.
- `read_http_message(sock, max_header_bytes=..., max_body_bytes=...) -> bytes`: acumula `sock.recv` hasta ver `\r\n\r\n`, lee `Content-Length` y sigue hasta tener el cuerpo completo. 413 si excede límites; 400 si el socket se cierra a medias. **Debe funcionar con mensajes fragmentados** (de 1 byte en 1 byte).
- `parse_request(raw) -> HttpRequest`: algoritmo estricto: separar por `\r\n\r\n`; request line con **exactamente 3 tokens**; método ∈ {GET, POST, PUT, PATCH, DELETE}; versión `HTTP/1.1`; separar path/query por el primer `?`; decodificar; cabeceras `Nombre: valor` en minúscula; rechazar `transfer-encoding`; validar `content-length` (entero ≥ 0, ≤ máximo; ausente = 0); cortar **exactamente N bytes**; error 400 si faltan bytes.
- `parse_response(raw) -> HttpResponse` (lo usa el cliente).
- `build_response(status, payload) -> bytes`: serializa el payload a JSON (utf-8, `separators=(",", ":")`), cabeceras correctas; 204 sin cuerpo y `Content-Length: 0`.
- `build_error_body(status, detail) -> dict`.
- `encode_json(payload) -> bytes` / `decode_json(body: bytes) -> object`: soporta `date`, `datetime` (ISO) y `Decimal` (string). `decode_json` lanza `HttpError(400, "Request body is not valid JSON")`.
- `parse_query(query_string) -> dict[str,str]`, `build_query(params: dict) -> str` (omite valores `None`), `percent_decode(text, plus_as_space=False)`, `percent_encode(text)`. Hechas a mano; deben manejar UTF-8 multibyte (`José` ↔ `Jos%C3%A9`).

### 6.3 `shared/dtos.py`
- Una `@dataclass` por representación del documento de protocolo: `PatientDto`, `PatientCreateDto`, `PatientUpdateDto`, `SampleDto`, `SampleFullDto`, `SampleCreateDto`, `SampleUpdateDto`, `QualityControlDto`, `QualityControlInputDto`, `StaffDto`, `StaffCreateDto`, `StaffUpdateDto`, `AssignmentDto`, `ProjectDto`, `ProjectDetailDto`, `ProjectCreateDto`, `ProjectUpdateDto`, `ProtocolDto`, `ProtocolCreateDto`, `ProtocolUpdateDto`, `ContainerDto`, `ContainerCreateDto`, `SampleTypeDto`, `SampleTypeCreateDto`, y DTOs pequeños para relaciones (`ProjectSampleLinkDto`, `ProjectTeamMemberDto`, `SampleProtocolLinkDto`, etc.). Anidados (p. ej. en `SampleFullDto`) como dataclasses pequeñas.
- Los DTOs de **actualización** (PATCH) tienen todos los campos opcionales con un marcador para distinguir "no enviado" de `null` (necesario para `reviewed_by: null` = quitar revisor). Usa un centinela propio (`UNSET = object()` o similar) o un conjunto `provided_fields`; documenta la decisión.
- `dto_to_dict(dto)` y `dto_from_dict(cls, data)` **genéricos** (por reflexión de `dataclasses.fields`), sin repetir código por DTO. Los DTOs **no** importan SQLAlchemy.
- El **cliente trabaja con dicts** (JSON decodificado); no hace falta reconstruir DTOs en el cliente. Los DTOs son el contrato del servidor y deben coincidir con `docs/protocol.md` (hay un test que lo comprueba para al menos un DTO).

### 6.4 Servidor

**`server/settings.py`**: `HOST`, `PORT` (por defecto `127.0.0.1:8000`), `READ_TIMEOUT_SECONDS=5`, límites. Pueden leerse de variables de entorno con valor por defecto (`BIOTRACK_HOST`, `BIOTRACK_PORT`); no mezcles esto con `persistence/config.py` (que es solo de BD).

**`server/router.py`**
- `Router.add(method, pattern, handler)` con patrones tipo `/patients/{code}`; segmentos separados por `/`; `{name}` captura un segmento. Sin `re`.
- `Router.dispatch(request) -> tuple[int, object | None]`: busca la ruta; si existe el path pero no el método → `HttpError(405)`; si no existe → `HttpError(404)`. El handler es `handler(request, params) -> (status, payload)`.
- **Traducción de errores de servicio** (en un único sitio, p. ej. dentro de `dispatch`): `NotFoundError → 404`, `ConflictError → 409`, `ServiceValidationError → 422`, con `detail` = mensaje de la excepción.
- Router sin estado global; `build_router(uow_factory)` en `server/app.py` crea servicios y controladores y los registra (permite tests con servicios falsos).

**`server/tcp_server.py`**
- `serve(router, host, port)`: `socket` TCP, `SO_REUSEADDR`, `bind`, `listen(5)`, `accept` con timeout corto (1 s) para que Ctrl+C funcione en Windows, `settimeout` de lectura (5 s) en cada conexión aceptada, atender **en el mismo hilo** y cerrar. Sin threading.
- `handle_connection(conn, addr, router)`: función separada y testable con un socket falso. `read_http_message` → `parse_request` → `router.dispatch` → `build_response` → `sendall`. **Un único** bloque de manejo de excepciones que produce la respuesta: `HttpError` → su status; `socket.timeout` → 408; `Exception` → log del traceback + 500 genérico; `OSError` al enviar → ignorar. `logging` con una línea por petición (`método ruta -> status`).
- Una petición mala **nunca** tumba el servidor.

**Controladores** (`server/controllers/`)
- Una clase por recurso: `XController(service)` con `register(router)` y un método por endpoint `(request, params) -> (status, payload)`.
- `validation.py` con helpers **reutilizables** (extráelos solo cuando se repitan): `require_json_object(body_bytes)` (decodifica; cuerpo ausente o no-objeto → 422), `require_fields(data, *names)`, `parse_iso_date(value, field)`, `parse_decimal(value, field)`, `parse_bool(value, field)`, `require_choice(value, allowed, field)`, `parse_int_param(value, name)` (400 si no es entero), `require_query_choice(...)`, etc. Los mensajes de `detail` siguen el patrón del documento (`"birth_date must be a date in YYYY-MM-DD format"`).
- Los controladores validan **forma** (422): campos obligatorios, tipos, formato de fecha, decimal válido, enums permitidos. Las reglas de dominio van al servicio. Query params inválidos → 400.
- Códigos de éxito: listar/leer/actualizar 200, crear 201, borrar 204 (payload `None`), relaciones creadas 201, `PUT` quality-control 200.

**Servicios** (`server/services/`)
- Una clase por recurso: `XService(uow_factory)`. Cada método abre `with self._uow_factory.create() as uow:` y usa los repositorios existentes con `uow.session`. Reciben y devuelven **DTOs** (nunca entidades ORM). Convierte entidad→DTO **dentro** del `with` (antes de cerrar la sesión) con una función privada `_to_dto(entity)` al final del archivo (o `_to_<x>_dto`).
- Errores de negocio con `server/services/errors.py`: `ServiceError` base; `NotFoundError`, `ConflictError`, `ServiceValidationError`. Mensajes en inglés, claros, con el código del recurso (`"Patient 'PAT-999' not found"`, `"Patient 'PAT-001' already exists"`).
- Tras `repo.save(entity)` en creaciones: `uow.session.flush()` y `uow.session.refresh(entity)` para tener `id`, `registration_date`, `last_update`, etc. antes de convertir.
- Operaciones que pueden violar integridad: `flush()` dentro del `try` y convertir `sqlalchemy.exc.IntegrityError` en `ConflictError`.
- Reglas de negocio (extraídas de la CLI original):
  - **Patients:** `code` único (409). Borrar: si `patient.samples` no está vacío → 409 con el número de muestras. Actualizar: solo los campos recibidos.
  - **Samples:** `code` único (409); el paciente (por `patient_code`), el tipo (por `type_name`) y el contenedor (por `code`) deben existir (422 con mensaje claro); `volume > 0`; `status` ∈ enum (default `pending`); `extraction_date` válida. El `PATCH` cambia `volume`, `extraction_date`, `status`, `sample_type`, `container_code`. `/full` usa `SampleRepository.get_full` y compone: paciente, tipo, contenedor, QC, protocolos, `temperature_logs`, y proyectos con su `assignment_date` (esta composición **vive en el servicio**, no en la CLI; hoy la CLI consulta `ResearchProjectSamples` directamente: muévelo aquí).
  - **Quality control:** `PUT` crea o reemplaza (1:1). `purity` ∈ [0,100] (nullable), `concentration` ≥ 0 (nullable), `result` ∈ enum obligatorio. `GET` → 404 si no hay QC. `DELETE` según enmienda 3.
  - **Staff:** `code` único; `role` ∈ enum; `active` por defecto `true`; `PATCH` de `name`, `lastname`, `role`, `active`. Borrado sin comprobación de negocio (enmienda 6); `IntegrityError` → 409. `assignments` usa `StaffRepository.get_research_project_with_roles`.
  - **Projects:** `project_name` único (409; también al renombrar); `GET /projects?name=` exacto; detalle con `team` (nombre, apellidos, `role`) y `samples` (`code`, `assignment_date`, `status`); `link sample`: 404 si no existe proyecto o muestra, 409 si ya enlazada, fecha de asignación **la fija el servidor** (hoy); `add team member`: 404 proyecto o personal inexistente, 409 si ya está en el equipo, 422 si el rol no es válido. Tanto `ResearchProjectSamples` como `ProjectTeam` se crean con los modelos existentes dentro del servicio.
  - **Protocols:** `code` único; `reviewed_by` (código de personal) opcional y debe existir (422); `PATCH` con `reviewed_by: null` quita el revisor; `protocol_file` **no se transmite** (ni en DTOs ni en JSON); `keyword` → `search_by_name` (insensible a mayúsculas); aplicar protocolo a muestra: 404 si falta alguno, 409 si ya aplicado.
  - **Containers:** unicidad por `code` **o** `type_name` (`ContainerRepository.get_by_code_or_type_name`) → 409. **Sample types:** `type_name` único → 409.
- Si un repositorio necesita un método nuevo para una consulta que hoy se hace con `session.query` suelto en la CLI (p. ej. buscar la asociación proyecto-muestra o miembros de equipo), **añádelo al repositorio correspondiente** (cambio mínimo en `persistence/repositories`), no uses `session.query` dentro de controladores. Está permitido en servicios si preferís no ampliar el repositorio, pero se prefiere el repositorio.

### 6.5 Cliente

**`client/settings.py`**: `HOST`, `PORT`, `TIMEOUT_SECONDS` (por defecto `127.0.0.1`, `8000`, `10`), con variables de entorno opcionales (`BIOTRACK_HOST`, `BIOTRACK_PORT`). **El cliente no lee `.env` ni importa `server`**.

**`client/connection.py`**
- `send_request(method, path, body=None, query=None) -> tuple[int, object | None]`: codifica la ruta y query (`percent_encode`, `build_query`), construye la petición con `build_request`, `socket.create_connection` con timeout, `sendall`, `read_http_message`, `parse_response`, `decode_json`. Devuelve `(status, payload)`.
- Fallos de red (`ConnectionRefusedError`, `socket.timeout`, `OSError`, cierre antes de respuesta completa) → `ApiError(0, "Cannot reach the server")`.
- Status ≥ 400 → `ApiError(status, detail)` donde `detail` sale del cuerpo de error.

**`client/api_client.py`**: **una función por operación** del mapa de la sección 7, con nombres claros (`list_patients`, `get_patient`, `create_patient`, `update_patient`, `delete_patient`, `list_patient_samples`, `list_samples`, ...). Devuelven dicts o listas de dicts (o `None` para 204). Sin lógica de UI. Sin duplicación: una pequeña función privada por patrón (`_get`, `_post`, ...) si ayuda.

**`client/cli_app.py`**
- Conserva **exactamente** los menús, textos, prompts, emojis, tablas y paneles de Rich actuales (es la UI). Solo cambia **de dónde salen los datos**: de `api_client` en vez de repositorios.
- Fechas: se envían como `date.isoformat()`; se muestran parseando los strings ISO recibidos. `Decimal`: llegan como string; mostrarlos con `float(...)` en formato `:.2f` donde la CLI original lo hacía.
- **Un único mecanismo** para errores de API (decorador o context manager, p. ej. `handle_api_errors`) que imprime `[bold red]Error: {detail}[/bold red]` y vuelve al menú con `press_any_key()`, para no repetir `try/except ApiError` en cada función.
- Las validaciones de UX locales (`validate_required`, `parse_date`, `volume > 0`) pueden mantenerse por comodidad, pero **el servidor valida siempre**.
- Al terminar: **eliminar todos** los imports de `server.persistence` (config, UoW, repositorios, modelos) y `os`/`decimal` si ya no se usan. El cliente debe poder ejecutarse sin que exista `server/` en disco (prueba de arquitectura, ver bloque F).

---

## 7. Mapa completo: cada función de `cli_app.py` → API

Menús (`main`, `patient_menu`, `sample_menu`, `staff_menu`, `project_menu`, `protocol_menu`, `admin_menu`) y utilidades (`clear_screen`, `show_banner`, `press_any_key`, `validate_required`, `parse_date`) **se quedan en el cliente sin cambios de comportamiento**. El resto:

### Pacientes
| Función CLI | Llamadas a la API | Notas de comportamiento a conservar |
|---|---|---|
| `list_patients(active_only)` / `list_active_patients` | `GET /patients` · `GET /patients?active=true` | Tabla: ID, Code, Full Name, Birth Date, Active (🟢/🔴), Test Info, Last Update. Mensaje si vacío. |
| `create_patient` | `POST /patients` `{code,name,lastname,birth_date,test,active}` | 409 → "already exists". 422 → mostrar `detail`. |
| `update_patient` | `GET /patients/{code}` (valores por defecto) → `PATCH /patients/{code}` `{name,lastname,birth_date,test,active}` | 404 → "not found". |
| `delete_patient` | `GET /patients/{code}` → `Confirm` → `DELETE /patients/{code}` | 409 (tiene muestras) → mostrar el `detail` y no borrar. |
| `search_patient` | `GET /patients/{code}` | Panel con id, code, name, birth date, active, test, registration date. |
| `view_patient_samples` | `GET /patients/{code}` + `GET /patients/{code}/samples` | Tabla: Sample Code, Volume (mL, 2 decimales), Status, Extraction Date. |

### Muestras
| Función CLI | Llamadas a la API | Notas |
|---|---|---|
| `list_samples(status_filter, date_range)` | `GET /samples` · `?status=` · `?from=&to=` | Tabla: ID, Code, Patient Code, Volume, Status, Type, Container, Extraction Date, Last Update. |
| `filter_samples_status` / `filter_samples_date` | igual, con filtros | Error de fecha → mensaje y volver. |
| `create_sample` | `GET /sample-types`, `GET /containers` (para elegir por ID en pantalla) → `POST /samples` `{code,volume(string),extraction_date,patient_code,sample_type(name),container_code,status}` | El cliente traduce el ID elegido al `type_name` / `code`. Comprobar antes que el paciente existe con `GET /patients/{code}` para conservar el error temprano. 409/422 → `detail`. |
| `update_sample` | `GET /samples/{code}` → `PATCH /samples/{code}` `{volume,status,extraction_date}` | 404 → not found. |
| `delete_sample` | `GET /samples/{code}` → `Confirm` → `DELETE` | |
| `search_sample` | `GET /samples/{code}/full` | Panel: id, code, patient name+code, volume, status, type, container code, extraction date. |
| `view_full_sample` | `GET /samples/{code}/full` | Mismo panel grande que hoy: núcleo, paciente, QC, protocolos, proyectos con "Assigned on". **Sin** consultas ORM en la CLI. |
| `manage_quality_control` | `GET /samples/{code}` (existe) → `GET /samples/{code}/quality-control` (404 = no existe) → editar: `PUT` · borrar: `DELETE` · crear: `PUT` | Conserva el submenú E/D/B y los prompts de `result`, purity, concentration. |

### Personal
| Función CLI | Llamadas a la API | Notas |
|---|---|---|
| `list_staff` | `GET /staff` | Tabla: ID, Code, Full Name, Role (`replace("_"," ").upper()`), Last Update. |
| `create_staff` | `POST /staff` `{code,name,lastname,role}` | |
| `update_staff` | `GET /staff/{code}` → `PATCH /staff/{code}` `{name,lastname,role}` | |
| `delete_staff` | `GET` → `Confirm` → `DELETE` | |
| `search_staff` | `GET /staff/{code}` | Panel. |
| `assign_staff_project` | `GET /projects?name=<exact>` (vacío → "project not found") → `POST /projects/{id}/team` `{staff_code,role}` | 404 personal / 409 duplicado → `detail`. |
| `view_staff_assignments` | `GET /staff/{code}/assignments` | Tabla: Research Project Name, Assigned Role, Last Update. Vacío → mensaje. |

### Proyectos
| Función CLI | Llamadas a la API | Notas |
|---|---|---|
| `list_projects` | `GET /projects` | Tabla: ID, Project Name, Start Date, Description (recortada a 50), Last Update. |
| `create_project` | `POST /projects` `{project_name,start_date,description}` | 409 si nombre existe. |
| `update_project` | `GET /projects/{id}` → `PATCH /projects/{id}` | Se pide el ID (como hoy). |
| `delete_project` | `GET /projects/{id}` → `Confirm` → `DELETE` | |
| `search_project_name` | `GET /projects?name=<exact>` | Panel. |
| `link_sample_project` | `GET /projects/{id}` (nombre para el mensaje) → `POST /projects/{id}/samples` `{sample_code}` | 409 "already associated". |
| `view_project_details` | `GET /projects/{id}` | Panel: proyecto, equipo con roles, muestras con "Assigned" y "Status". |

### Protocolos
| Función CLI | Llamadas a la API | Notas |
|---|---|---|
| `list_protocols` | `GET /protocols` | Tabla: ID, Code, Name, Description (recortada), Reviewed By (código o "🔴 UNREVIEWED"), Last Update. |
| `create_protocol` | si se indica revisor: `GET /staff/{code}` (404 → aviso amarillo y se crea sin revisor, como hoy) → `POST /protocols` `{code,name,description,reviewed_by}` | |
| `update_protocol` | `GET /protocols/{code}` → `PATCH /protocols/{code}` `{name,description,reviewed_by?}` | Conserva la lógica: revisor nuevo existente → se asigna; vacío y había revisor → preguntar si quitarlo (`reviewed_by: null`). |
| `delete_protocol` | `GET` → `Confirm` → `DELETE` | |
| `search_protocol_keyword` | `GET /protocols?keyword=...` | Tabla: Code, Name, Reviewer. |
| `apply_protocol_to_sample` | `POST /samples/{sample_code}/protocols` `{protocol_code}` | 404 / 409 → `detail`. |
| `view_protocol_samples` | `GET /protocols/{code}` + `GET /protocols/{code}/samples` | Tabla: Sample Code, Patient Associated (`patient_name`), Status. |

### Administración
| Función CLI | Llamadas a la API | Notas |
|---|---|---|
| `list_containers` | `GET /containers` | Tabla: ID, Code, Type Name, Last Update. |
| `create_container` | `POST /containers` `{code,type_name}` | 409 → "code or type name already exists". |
| `list_sample_types` | `GET /sample-types` | Tabla: ID, Type Name, Last Update. |
| `create_sample_type` | `POST /sample-types` `{type_name}` | 409. |

Queda **fuera de alcance** (no está en la CLI): registros de temperatura (`LogTemperature`) más allá de mostrarlos dentro de `/samples/{code}/full`, `protocol_file` binario, paginación, autenticación, HTTPS.

---

## 8. Tests (`unittest` + `unittest.mock`, sin BD real ni red real)

Estructura espejo: `tests/shared/`, `tests/server/`, `tests/client/`, cada una con `__init__.py`. Nombres que describan el comportamiento (`test_create_patient_raises_conflict_when_code_exists`). Ejecutables con `python -m unittest discover -s tests -t .` desde la raíz **y desde un clon limpio** (sin `.env`; ver bloque A).

Crea utilidades de test compartidas (`tests/helpers.py` o similar): `FakeSocket` (con `recv` por fragmentos y `sendall` acumulando), una fábrica de UoW falso, y constructores de peticiones.

Cobertura mínima exigida:

- **Protocolo (`tests/shared/`)**: ida y vuelta `build_request→parse_request` y `build_response→parse_response`; con/sin cuerpo; cabeceras con mayúsculas mezcladas; query con varios parámetros, `%20`, `+`, UTF-8 multibyte; errores: sin terminador, request line con 2 o 4 tokens, versión distinta, método desconocido, cabecera sin `:`, `Content-Length` no numérico/negativo/excesivo (413), `Transfer-Encoding`, cuerpo más corto que `Content-Length`, cuerpo > límite; `read_http_message` con `FakeSocket` fragmentado (1, 5 y 4096 bytes) y con socket cerrado a medias; JSON con `date`/`datetime`/`Decimal`; JSON inválido; `dto_to_dict`/`dto_from_dict` (ida y vuelta, fechas, decimales, anidados, campos opcionales); `percent_encode/decode`.
- **Router (`tests/server/test_router.py`)**: casar ruta simple y con parámetros; 404; 405; delega con los parámetros correctos; traducción `NotFoundError/ConflictError/ServiceValidationError` → 404/409/422; que `build_router` registra **todas** las rutas del documento (comprueba la tabla de endpoints).
- **Servidor TCP (`handle_connection`)**: petición válida → 200; JSON roto → 400; petición vacía; `socket.timeout` → 408; handler que lanza `Exception` → 500 sin filtrar detalles; cliente que cierra al enviar no rompe nada.
- **Validación (`tests/server/test_validation.py` y tests de controladores)**: campo ausente/vacío, tipo incorrecto, fecha mal formada (`01/05/1990`), decimal inválido, enum fuera de lista, cuerpo no-objeto, query inválida (400), id no numérico (400).
- **Controladores**: con servicio **falso** (`Mock`): el controlador llama al servicio con el DTO correcto, devuelve el status correcto (201/200/204) y el payload serializado.
- **Servicios**: con UoW y repositorios **mockeados** (`unittest.mock.patch` de los repositorios usados en el módulo del servicio o fábrica de UoW falsa): crear OK, duplicado → `ConflictError`, inexistente → `NotFoundError`, regla de negocio violada → error correcto, actualización parcial solo toca los campos recibidos, **el resultado es un DTO y no una entidad**, `IntegrityError` en `flush` → `ConflictError`. Un archivo de tests por servicio. Prioriza `PatientService`, `SampleService`, `ProjectService`, `ProtocolService` (las reglas más ricas), pero cubre **todos**.
- **Cliente**: `connection.send_request` con `socket.create_connection` parcheado (construye la petición correcta, convierte ≥ 400 en `ApiError`, red caída → `ApiError(0)`); `api_client` con `send_request` parcheado (método, ruta, query y cuerpo correctos para cada operación).
- Un test que verifique que **`client` y `shared` no importan `server` ni `sqlalchemy`** (puede recorrer los archivos y buscar los imports con `ast`).

Los tests **no** deben depender de `data/*.db`, del `.env` ni de la red.

---

## 9. Calidad

- PEP 8. Longitud máxima de línea **79**. Parte los strings largos de Rich con concatenación implícita entre paréntesis. Si usas `flake8`, crea `.flake8` con `exclude = venv,alembic/versions,notebooks,.git,__pycache__`.
- Nombres en inglés, descriptivos, `snake_case` / `PascalCase` / `UPPER_SNAKE` para constantes. Sin abreviaturas crípticas.
- Docstrings cortas en inglés en clases y funciones públicas. Anotaciones de tipo en firmas públicas.
- Funciones cortas y con una sola responsabilidad. Sin `print` de depuración (salvo UI del cliente); el servidor usa `logging`.
- **Sin duplicación:** helpers de validación comunes, conversión DTO↔dict genérica, un único manejador de errores en la CLI, un único sitio que traduce errores de servicio a HTTP, un único sitio que convierte excepciones en respuestas en el servidor.
- Elimina código muerto: imports sin usar, `base.py` si nadie lo importa (verifica con `grep` antes), código comentado, el eco de prueba.

---

## 10. Bloques de trabajo

Para cada bloque: haz los cambios, ejecuta tests, `git add -A`, revisa `git status` (que no se cuele `.env`, `__pycache__` ni `*.db`), y haz **un único commit** del bloque. Si un bloque falla en la verificación, **no avances**: arréglalo o repórtalo.

### Bloque A: preparación y contrato
1. Verifica el estado actual (sección 3). `git status` limpio; crea `feature/client-server`.
2. Haz robusto `server/persistence/config.py` para que **un clon limpio sin `.env` pueda importar los servicios y ejecutar los tests**: la raíz del proyecto se busca con un anchor **versionado** (p. ej. `alembic.ini`), el `.env` se carga solo si existe, y hay valores por defecto (`ENVIRONMENT=development`, `DB_FILENAME_DEVELOPMENT=biotrack.db`, `DB_FILENAME_TEST=biotrack_test.db`). No cambies la semántica cuando el `.env` existe. Importar `config.py` no debe lanzar excepción en un clon limpio con ENVIRONMENT por defecto.
3. Aplica las **enmiendas de la sección 5** a `docs/protocol.md` y verifica los `Content-Length` de sus ejemplos con Python.
4. Crea `requirements-server.txt`, `requirements-client.txt`, `requirements-dev.txt` (según el contenido real de imports; revisa `requirements.txt` actual y deja claro cuál se mantiene) y `.flake8` si procede.
5. **Un único commit** del bloque: `chore: amend protocol, make config robust and split requirements`.

### Bloque B: `shared` con tests
Implementa `shared/errors.py`, `shared/protocol.py` (sección 6.2) y `shared/dtos.py` (6.3, empieza por los DTOs de pacientes + la mecánica genérica; el resto de DTOs se añaden con cada recurso en el bloque E). Tests de protocolo y DTOs. Crea los helpers de test (`FakeSocket`, etc.).
Commit: `feat(shared): add HTTP-like protocol codec and DTO utilities with tests`.

### Bloque C: esqueleto de servidor y cliente
- `server/settings.py`, `server/router.py`, `server/tcp_server.py` (reemplaza el eco), `server/app.py` (`build_router`, de momento solo `GET /ping` → `200 {"message": "pong"}`), `run_server.py`.
- `client/settings.py`, `client/connection.py`, `client/api_client.py` (`ping()` y mantén `list_patients` hasta el bloque D).
- Tests de router, `handle_connection`, `connection`.
- Prueba manual: arranca el servidor, `ping` desde un script temporal (no commitear), comprueba 404/405, cliente mudo → 408, servidor apagado → `ApiError(0)`.
Commit: `feat: add TCP server, router and client connection with /ping`.

### Bloque D: pacientes de punta a punta (el molde)
Servicio, controlador, validación común, DTOs, `api_client`, funciones de pacientes de `cli_app.py`, tests (servicio, controlador, validación, api_client). Registra rutas en `build_router`. Prueba manual E2E con `ENVIRONMENT=test`. Este recurso debe quedar **limpio y comentado**: es la plantilla de los demás.
Commit: `feat: implement patients resource end to end`.

### Bloque E: resto de recursos (un único commit al terminar TODO el bloque)
Orden: **containers + sample-types** → **staff** → **samples (+ quality control + `/full`)** → **projects (+ team + link samples)** → **protocols (+ apply to sample)**. Para cada uno: DTOs, servicio, controlador, rutas, funciones de `api_client`, funciones de `cli_app.py` (sección 7), tests. Si repites un patrón tres veces, **extráelo** a un helper común.

### Bloque F: cierre
1. Elimina de `client/cli_app.py` todos los imports de `server.persistence`. Comprobaciones (deben salir vacías):
   ```bash
   grep -rn "server" client/ --include="*.py"
   grep -rniE "sqlalchemy|server\.persistence" client shared --include="*.py"
   grep -rn "^from client\|^import client" shared server --include="*.py"
   grep -rn "threading\|asyncio\|select\|requests\|urllib\|http\.server\|http\.client\|socketserver" . --include="*.py" --exclude-dir=venv --exclude-dir=.git
   ```
   (Ajusta el patrón para que no dé falsos positivos con palabras como `select` de SQLAlchemy en `server/persistence`.)
2. **Prueba de aislamiento del cliente:** comprueba que `python -c "import client.cli_app"` funciona aunque se simule la ausencia de `server` y de `sqlalchemy` (p. ej. con un script temporal que bloquee esos módulos en `sys.modules`/`sys.meta_path`; no lo commitees).
3. Corre todos los tests; linter sin avisos; revisa duplicaciones.
4. **Recorrido E2E manual** (con `ENVIRONMENT=test` sobre una copia de BD) de **todas** las opciones de cada menú, incluyendo errores (404, 409, 422, servidor apagado, cliente mudo).
5. Escribe/actualiza `README.md` (reemplaza el antiguo, que está desactualizado): descripción, arquitectura (diagrama de la sección 4), estructura de carpetas, requisitos, instalación por componente, configuración (`.env.example`), cómo ejecutar (servidor, cliente, tests), resumen del protocolo con enlace a `docs/protocol.md`, limitaciones conocidas (sin autenticación, sin HTTPS, un cliente a la vez, sin `protocol_file`, sin paginación).
6. Limpieza: quitar `cli_app.py` antiguo de la raíz si quedara, `src/` vacío, restos; **no** toques `notebooks/` salvo para no dejar imports rotos (si importan `server.persistence` ya está bien).
7. Commit final: `chore: final cleanup, README and quality pass`.

---

## 11. Informe final (formato)

Al terminar, entrega un único informe con:
1. **Rama y lista de commits** (`git log --oneline`), y el SHA del último.
2. **Resultado de los tests** (número de tests, salida resumida) y del linter.
3. **Tabla de cobertura funcional:** cada función de `cli_app.py` → endpoint(s) → estado (migrada y probada / migrada sin probar / pendiente).
4. **Resultado de las comprobaciones de arquitectura** (los `grep` y la prueba de aislamiento).
5. **Cambios al protocolo** respecto a la versión original de `docs/protocol.md`.
6. **Decisiones tomadas** donde esta especificación era ambigua, y **discrepancias** encontradas en el estado inicial.
7. **Cambios fuera de `server/services`, `server/controllers`, `shared`, `client`, `tests`, `docs`** (p. ej. métodos nuevos en repositorios, `config.py`), justificados uno a uno.
8. **Problemas conocidos o pendientes** y cualquier cosa que el usuario deba revisar a mano.
9. **Instrucciones para el usuario**: cómo arrancar servidor y cliente, cómo ejecutar los tests, y los comandos para entregar (sin ejecutarlos tú):
   ```bash
   git checkout main && git merge feature/client-server
   git tag -a v2.0.0 -m "Client/server refactor"
   git rev-parse HEAD
   git push origin main --tags
   ```

## 12. Si algo falla o no está claro

- Bloqueo real (árbol sucio, tests que no pueden ejecutarse, el estado del proyecto no coincide con la sección 3 de forma que cambia el plan): **detente y pregunta**.
- Ambigüedad menor: elige la opción **más simple** coherente con este documento y `docs/protocol.md`, y anótala en el informe.
- Nunca "arregles" un fallo de verificación saltándote una regla de la sección 2.
