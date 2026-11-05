# Marketing Analytics — plataforma de reportes de RRSS

Base de todos los reportes de Marketing de la organización. Se invoca como Skill de
Claude Code ("Actualizar Reporte RRSS", ver `.claude/skills/actualizar-reporte-rrss/SKILL.md`)
o directamente por CLI. Extrae Meta Ads, Meta Orgánico (Facebook + Instagram) y Mailchimp por
API oficial, mantiene una base histórica en SQLite sin duplicados, y genera Excel + Dashboard
HTML + Log de ejecución en cada corrida.

## Arranque rápido

**Opción recomendada — asistente interactivo** (pide los tokens/IDs, los valida contra
las APIs reales, y escribe `config.yaml`/`.env` por vos):

```bash
pip install -r requirements.txt
python -m marketing_analytics.setup_wizard
```

Se puede correr varias veces — cada corrida solo toca la fuente que le pidas (Mailchimp,
Meta Ads, Meta Orgánico), sin pisar lo que ya configuraste antes. Ideal para ir activando
conectores de a uno.

**Opción manual** (editar los archivos a mano):

```bash
# Linux / macOS
pip install -r requirements.txt
cp config.example.yaml config.yaml   # completar perfiles/cuentas/moneda
cp .env.example .env                 # completar tokens (nunca se commitea)
python -m marketing_analytics.main
```

```powershell
# Windows (PowerShell)
pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml   # completar perfiles/cuentas/moneda
Copy-Item .env.example .env                 # completar tokens (nunca se commitea)
python -m marketing_analytics.main
```

```bat
:: Windows (cmd.exe)
pip install -r requirements.txt
copy config.example.yaml config.yaml
copy .env.example .env
python -m marketing_analytics.main
```

Salida (en `general.output_dir`, por defecto `output/`): `Historico_RRSS.xlsx`,
`Dashboard.html`, `Log_Ejecucion.txt`.

## "Actualizar el reporte" (uso normal, sin fechas)

Para el uso del día a día alcanza con correr `python -m marketing_analytics.main` **sin**
`--desde`/`--hasta`. La corrida queda registrada en la base (tabla `configuracion`), y la
siguiente vez que se corra sin fechas, continúa automáticamente desde el día siguiente a
la última `hasta` procesada — sin importar si pasó un día o un mes entre una corrida y la
otra, y sin arriesgar duplicados (el dedupe por `uid` protege el solape). `general.date_range`
en `config.yaml` (`ultimos_n_dias`) solo se usa como arranque la primerísima vez que se corre
el reporte, antes de que exista un checkpoint.

Además, cada corrida vuelve a traer `dias_solape` días ya cargados (default 7, configurable en
`general.date_range.dias_solape`, alineado con la ventana de atribución estándar de Meta Ads
"7 días clic, 1 día vista"): y como el checkpoint nunca vuelve a mirar fechas ya pasadas, sin
este solape esos ajustes tardíos se perderían en silencio.

`--desde`/`--hasta` quedan para backfills puntuales (traer un rango histórico específico);
también actualizan el checkpoint, así que una corrida manual no rompe la continuidad de las
automáticas siguientes.

## Control de perfiles (hoja CONTROL PERFILES)

Cada corrida guarda, por perfil de Meta Orgánico y mes calendario, un snapshot con seguidores
actuales, seguidores ganados/perdidos vs. el mes anterior ya cerrado, publicaciones del mes,
likes (suma de reacciones), visualizaciones, comentarios, compartidos y tasa de engagement
(interacciones / seguidores). La fila del mes en curso se actualiza en cada corrida (acumula
lo real hasta la fecha); al empezar un mes nuevo se crea una fila nueva y la anterior queda fija
como cierre de ese mes. Solo el conteo de seguidores es una llamada nueva a Meta — el resto se
calcula agregando lo que ya está en la base histórica, sin costo adicional de API.

## Arquitectura

```
config/        Validación de config.yaml (Pydantic) y secretos desde .env
models/        Registros tipados por fuente + uid de deduplicación
database/      Esquema SQLite, upsert (repository.py), historial de ejecuciones
connectors/    Un paquete por fuente (mailchimp/, meta_ads/, meta_organico/) detrás
               de una interfaz común (base.py) + registry.py que arma la lista activa
services/      Orquestador ETL, resolución de rango de fechas, log de ejecución
reports/       Historico_RRSS.xlsx (una hoja por fuente + LOG)
dashboard/     Dashboard.html (Plotly, filtros, KPIs — plantilla HTML+CSS+JS modular)
setup_wizard/  Asistente interactivo: valida tokens/IDs en vivo y escribe config.yaml/.env
main.py        CLI del Skill
tests/         pytest — 66 tests, sin llamadas reales a ninguna API
```

**Por qué esta forma y no otra:**

- **Conectores detrás de una interfaz común** (`BaseConnector.fetch()` + `.upsert()`):
  agregar Google Analytics 4, TikTok, etc. es una clase nueva + una entrada en
  `registry.py` — nunca un cambio en `services/` ni `database/`.
- **Perfiles/cuentas como datos de config, no como código**: `config.yaml` es la única
  fuente de qué perfiles de Meta Orgánico o cuentas de Meta Ads recorrer. Agregar el
  perfil 14 (o el 40) no toca ningún archivo `.py`.
- **SQLite como única fuente de verdad histórica**: Excel y Dashboard se regeneran
  siempre desde la base — nunca se lee de vuelta un Excel para escribir otro.
- **Deduplicación por `uid`** (`fuente|perfil|id_publicación|id_campaña|fecha`):
  un mismo registro enviado dos veces no duplica fila; si cambiaron las métricas, se
  actualiza; si no, se descarta. Ver `database/repository.py`.
- **Un conector que falla no tumba la corrida**: el orquestador seguí con los demás y
  deja constancia del error en `ejecuciones`/`logs` y en `Log_Ejecucion.txt`
  (`services/orchestrator.py`).

## Conectores y sus fuentes oficiales

| Fuente | API oficial | Estado |
|---|---|---|
| Meta Ads | Marketing API (Graph API) | Activo |
| Meta Orgánico | Graph API (Páginas + Instagram Business) | Activo |
| Mailchimp | Marketing API v3 | Activo |
| LinkedIn | Community Management API | **Fuera de alcance** — requiere aprobación de LinkedIn como partner, aún no obtenida. Tabla y modelo ya existen en el esquema histórico; activar el conector es agregar una clase, no reescribir nada. |

Limitaciones reales de las APIs (no bugs, documentadas en el código donde aplican):
Instagram orgánico no expone clics por publicación; las métricas de Meta Insights pueden
deprecarse entre versiones (el cliente degrada métrica por métrica en vez de romper la
corrida); dos cuentas de Meta Ads pueden facturar en monedas distintas (Gasto/CPC se
agrupan por moneda, nunca se suman a ciegas).

## Configuración

Todo lo no-sensible vive en `config.yaml` (ver `config.example.yaml`): perfiles de Meta
Orgánico, cuentas de Meta Ads (con `moneda` obligatoria), `server_prefix` de Mailchimp,
rango de fechas, ruta de salida, ruta de la base SQLite. Los secretos
(`META_SYSTEM_USER_TOKEN`, `MAILCHIMP_API_KEY`) viven solo en `.env`, nunca en el repo.

## Escalabilidad

Conectores futuros (Google Analytics 4, Google Ads, TikTok, YouTube, Google Search
Console, HubSpot, Salesforce) se agregan como un paquete nuevo bajo `connectors/`
implementando `BaseConnector`, sin tocar `database/`, `services/`, `reports/` ni
`dashboard/`.

## Automatización (arquitectura lista, scheduler no implementado)

El diseño no asume ninguna forma particular de disparo: `main.py` es un comando de una
sola corrida, idempotente (correr dos veces el mismo rango no duplica nada), pensado para
poder programarse — por ejemplo, todos los lunes a las 09:00 — el día que se decida
implementar el scheduler.

## Tests

```bash
cd marketing_analytics
pytest
```

155 tests: dedupe, actualización incremental, checkpoint automático de fechas (con solape para ajustes tardíos de Meta Ads), snapshot mensual de perfiles (Control Perfiles), agrupamiento por unidad y matching de campañas (Control de Contenido), retry/backoff HTTP, paginación de cada API,
mappers por fuente, orquestador (incluye el caso de un conector caído), generación de
Excel y Dashboard (JSON embebido + secciones clave), el CLI de punta a punta, y el
asistente de configuración (flujo interactivo simulado + validadores) — todo con mocks
HTTP (`responses`), sin llamadas reales a ninguna API.
