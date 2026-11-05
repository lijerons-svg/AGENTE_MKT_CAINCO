---
name: actualizar-reporte-rrss
description: >
  Corre el ciclo completo de Marketing Analytics de la organización: extrae
  Meta Ads, Meta Orgánico (Facebook + Instagram) y Mailchimp por API oficial,
  actualiza la base histórica en SQLite sin duplicar ni perder datos previos,
  y genera Historico_RRSS.xlsx, Dashboard.html y Log_Ejecucion.txt. USA ESTA
  SKILL cuando el usuario diga "actualizar reporte RRSS", "actualiza el
  reporte de marketing", "corre el reporte de redes sociales/RRSS", o pida
  refrescar el dashboard/histórico de Meta Ads, Meta Orgánico, Mailchimp o
  LinkedIn (posts orgánicos de la página de la organización).
---

# Actualizar Reporte RRSS

## Qué hace

Ejecuta `marketing_analytics/main.py`, que corre sin intervención manual:

1. Lee `config.yaml` (perfiles, cuentas, rango de fechas) y `.env` (tokens/API keys).
2. Llama a los conectores activos — Meta Ads, Meta Orgánico, Mailchimp, LinkedIn — cada uno
   contra su API oficial, con retry/backoff y paginación ya resueltos.
3. Hace upsert en la base histórica SQLite (`database_path` de config.yaml), deduplicando
   por `(fuente, perfil, id_publicación/campaña, fecha)`: nunca duplica, actualiza métricas
   cuando cambiaron, descarta lo que sigue igual.
4. Genera en `output_dir`:
   - `Historico_RRSS.xlsx` (hojas META ORGANICO, CONTROL PERFILES, META ADS, MAILCHIMP, CALENDARIO, LINKEDIN, LOG)
   - `Dashboard.html` (KPIs, comparativo Meta vs LinkedIn, tops, evolución, filtros — interactivo)
   - `ControlContenido.html` (Resumen ejecutivo con insights automáticos, Control de Perfiles,
     Análisis, Panel de Planificación y Mailchimp — agrupa Facebook+Instagram por unidad/marca,
     con salud de perfiles y calendario por canal; requiere `unidad`/`alias_pauta` en config.yaml.
     Mailchimp queda global, no por unidad)
   - `Log_Ejecucion.txt` (hora inicio/fin, tiempo, totales, errores)

## Antes de correrla (una sola vez)

1. `cd marketing_analytics && python -m pip install -r requirements.txt` (en Windows, `pip` solo a
   veces no está en el PATH aunque Python sí — invocarlo vía `python -m pip` siempre funciona)
2. Correr el asistente interactivo (valida cada token/ID contra la API real antes de
   guardarlo — se puede correr varias veces, una fuente a la vez, sin pisar lo ya hecho):
   ```bash
   python -m marketing_analytics.setup_wizard
   ```
   O a mano: copiar `config.example.yaml` → `config.yaml` (perfiles de Meta Orgánico, cuentas
   de Meta Ads con su `moneda` obligatoria, `server_prefix` de Mailchimp, `organization_id`/
   `nombre` de LinkedIn) y `.env.example` → `.env` (`META_SYSTEM_USER_TOKEN`,
   `MAILCHIMP_API_KEY`). Nunca commitear `.env` ni `config.yaml` (ya están en `.gitignore`).
3. Para LinkedIn (además de lo anterior): completar `LINKEDIN_CLIENT_ID`/`LINKEDIN_CLIENT_SECRET`
   en `.env` desde la pestaña Autenticación de la app en linkedin.com/developers, y correr una
   vez (y de nuevo cada ~60 días, cuando venza):
   ```bash
   python -m marketing_analytics.connectors.linkedin.obtener_token
   ```
   Abre el navegador para autorizar con una cuenta admin de la página y guarda el token solo
   en `.env` — no requiere copiar nada a mano.

## Cómo correrla

```bash
cd marketing_analytics
python -m marketing_analytics.main
```

Sin `--desde`/`--hasta`, cada corrida "actualiza lo nuevo" sola: continúa automáticamente
desde el día siguiente a la última corrida registrada, sin importar cuánto tiempo pasó
(el checkpoint vive en la propia base SQLite, tabla `configuracion`). `general.date_range`
de `config.yaml` solo se usa como arranque la primera vez, antes de que exista checkpoint.

Opcional, para un backfill puntual (rango de fechas específico):

```bash
python -m marketing_analytics.main --desde 2026-07-01 --hasta 2026-07-31
```

Código de salida: `0` si todo corrió (o corrió parcialmente con al menos un conector
exitoso), `1` si no hay conectores activos o si todos fallaron — revisar `Log_Ejecucion.txt`
para el detalle.

## Limitaciones conocidas (no son bugs, son restricciones reales de las APIs)

- **LinkedIn**: el access token vence cada ~60 días (no hay token de sistema permanente,
  como sí tiene Meta) — hay que volver a correr `obtener_token.py` antes de esa fecha. Las
  estadísticas por publicación (me gusta, comentarios, compartidos, impresiones) se traen de
  un endpoint cuyo formato exacto de respuesta no está 100% confirmado todavía — si algún
  campo no viene como se espera, el conector lo deja en 0 en vez de romper la corrida (ver
  nota en `connectors/linkedin/mapper.py`).
- **Instagram orgánico**: no expone "clics totales" ni "clics a enlace" por publicación vía
  API oficial (limitación de la plataforma) — esos campos quedan en 0 para IG.
- **Métricas de Meta Insights**: si Meta deprecia o renombra una métrica, el conector la
  degrada individualmente (log de advertencia) en vez de romper toda la corrida.
- **Gasto/CPC de Meta Ads**: si hay cuentas con monedas distintas, el Excel y el dashboard
  las muestran agrupadas por moneda — nunca se suman a ciegas.
- **Dashboard.html** usa Plotly vía CDN: hace falta conexión a internet para verlo.

## Escalabilidad (sin tocar el núcleo)

Nuevo conector (GA4, Google Ads, TikTok, YouTube, Search Console, HubSpot, Salesforce...):
implementar `BaseConnector` (`connectors/base.py`) y registrarlo en `connectors/registry.py`.
Nuevo perfil de Meta Orgánico o cuenta de Meta Ads: una entrada más en `config.yaml`, cero
cambios de código.

## Problemas comunes en Windows (encontrados en QA real, ya solucionados o con solución conocida)

- **`pip` no se reconoce**: usar `python -m pip install -r requirements.txt` en su lugar.
- **`python -m marketing_analytics...` da `ModuleNotFoundError`**: hay que pararse un nivel
  *arriba* de la carpeta `marketing_analytics` (la que la contiene), no adentro de ella.
- **Error al escribir `config.yaml`/`.env`/los reportes (`PermissionError`, "Acceso denegado")**:
  típico de correr el proyecto adentro de una carpeta sincronizada por OneDrive. El asistente y
  `main.py` ya avisan esto claro en vez de tirar un traceback — la solución es cerrar programas
  que puedan tener el archivo abierto, o pausar la sincronización de OneDrive, o (mejor) mover
  todo el proyecto fuera de OneDrive (ej. `C:\proyectos\`).
- **Ruta demasiado larga al descomprimir un ZIP** (`Error 0x80010135`): también típico de
  OneDrive con rutas ya largas de por sí. Extraer en una ruta corta fuera de OneDrive.
- **Antes de reemplazar la carpeta del proyecto para actualizar el código**: hacer una copia de
  `config.yaml` y `.env` primero — no vienen en el ZIP/repo (están en `.gitignore` a propósito) y
  se pierden si no se los guarda aparte.
- **Al pegar un token/API key en un campo oculto**: el asistente valida el formato antes de
  llamar a la API (por ejemplo, detecta si una key de Mailchimp quedó con caracteres de más por
  un pegado corrompido) — si avisa que el formato no es el esperado, revisar cómo se pegó antes
  de reintentar.

## Ver también

`marketing_analytics/README.md` — arquitectura completa, módulos, y cómo correr los tests.
