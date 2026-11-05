"""Arma el snapshot mensual de un perfil combinando el conteo de seguidores
recién leído de Meta con los agregados que ya están en la base histórica
(sin ninguna llamada nueva a la API para publicaciones/likes/vistas/etc.).
"""
from __future__ import annotations

import datetime
import sqlite3

from marketing_analytics.models.records import ControlPerfilMensual


def construir_snapshot_mensual(
    conn: sqlite3.Connection,
    perfil: str,
    red: str,
    seguidores_actual: int,
    hoy: datetime.date | None = None,
) -> ControlPerfilMensual:
    hoy = hoy or datetime.date.today()
    anio_mes = hoy.strftime("%Y-%m")

    agregados = conn.execute(
        """
        SELECT COUNT(*) AS publicaciones, COALESCE(SUM(reacciones), 0) AS likes,
               COALESCE(SUM(visualizaciones), 0) AS visualizaciones,
               COALESCE(SUM(comentarios), 0) AS comentarios,
               COALESCE(SUM(compartidos), 0) AS compartidos,
               COALESCE(SUM(total_interacciones), 0) AS interacciones
        FROM meta_organico
        WHERE perfil = ? AND strftime('%Y-%m', fecha_publicacion) = ?
        """,
        (perfil, anio_mes),
    ).fetchone()

    fila_previa = conn.execute(
        """
        SELECT seguidores FROM control_perfiles
        WHERE perfil = ? AND red = ? AND anio_mes < ?
        ORDER BY anio_mes DESC LIMIT 1
        """,
        (perfil, red, anio_mes),
    ).fetchone()
    seguidores_anterior = fila_previa["seguidores"] if fila_previa else None

    interacciones_mes = agregados["interacciones"]
    tasa_engagement = round(interacciones_mes / seguidores_actual, 4) if seguidores_actual else 0.0

    return ControlPerfilMensual(
        perfil=perfil,
        red=red,
        anio_mes=anio_mes,
        seguidores=seguidores_actual,
        seguidores_ganados=(
            seguidores_actual - seguidores_anterior if seguidores_anterior is not None else 0
        ),
        publicaciones_mes=agregados["publicaciones"],
        likes_mes=agregados["likes"],
        visualizaciones_mes=agregados["visualizaciones"],
        comentarios_mes=agregados["comentarios"],
        compartidos_mes=agregados["compartidos"],
        interacciones_mes=interacciones_mes,
        tasa_engagement=tasa_engagement,
    )
