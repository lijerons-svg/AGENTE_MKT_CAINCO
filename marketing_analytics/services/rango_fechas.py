"""Resuelve el rango [desde, hasta] a consultar a partir de config.general.date_range."""
from __future__ import annotations

import datetime
import sqlite3

from marketing_analytics.config.schema import ModoRangoFechas, RangoFechasConfig
from marketing_analytics.database.configuracion import obtener_ultima_fecha_hasta


def resolver_rango(
    config: RangoFechasConfig, hoy: datetime.date | None = None
) -> tuple[datetime.date, datetime.date]:
    hoy = hoy or datetime.date.today()

    if config.modo == ModoRangoFechas.PERSONALIZADO:
        return config.fecha_inicio, config.fecha_fin

    desde = hoy - datetime.timedelta(days=config.ultimos_n_dias)
    return desde, hoy


def resolver_rango_automatico(
    conn: sqlite3.Connection, config: RangoFechasConfig, hoy: datetime.date | None = None
) -> tuple[datetime.date, datetime.date]:
    """Como `resolver_rango`, pero si ya hay una corrida previa registrada
    continúa desde el día siguiente a su `hasta` — así "actualizar el
    reporte" nunca requiere pensar en rangos de fechas, sin importar
    cuánto tiempo haya pasado desde la última vez que se corrió.

    Además vuelve a traer `dias_solape` días ya cargados (default 3): Meta
    Ads sigue ajustando gasto/resultados unos días después por ventanas de
    atribución, y como esto nunca vuelve a mirar fechas ya pasadas del
    checkpoint, sin el solape esos ajustes tardíos se perderían en
    silencio. Re-traer días ya cargados es seguro (el dedupe por uid solo
    actualiza si algo cambió, no duplica)."""
    if config.modo == ModoRangoFechas.PERSONALIZADO:
        return resolver_rango(config, hoy)

    hoy = hoy or datetime.date.today()
    ultima_fecha_hasta = obtener_ultima_fecha_hasta(conn)
    if ultima_fecha_hasta is None:
        return resolver_rango(config, hoy)

    desde = ultima_fecha_hasta + datetime.timedelta(days=1 - config.dias_solape)
    return min(desde, hoy), hoy
