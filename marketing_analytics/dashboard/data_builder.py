"""Arma los datos que alimentan Dashboard.html: listas de dicts JSON-
serializables leídas de la base histórica. El HTML nunca consulta SQLite
directamente — todo lo que necesita ya viene embebido como JSON.
"""
from __future__ import annotations

import sqlite3


def _filas_a_dicts(conn: sqlite3.Connection, consulta: str) -> list[dict]:
    cursor = conn.execute(consulta)
    columnas = [d[0] for d in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def construir_datos_dashboard(conn: sqlite3.Connection) -> dict:
    meta_organico = _filas_a_dicts(
        conn,
        """
        SELECT perfil, pagina, red, fecha_publicacion AS fecha, tipo, descripcion,
               alcance, visualizaciones, total_clics, clics_enlace, reacciones,
               comentarios, compartidos, total_interacciones
        FROM meta_organico ORDER BY fecha_publicacion
        """,
    )
    meta_ads = _filas_a_dicts(
        conn,
        """
        SELECT cuenta_publicitaria, perfil_unidad, red, campana,
               fecha_publicacion AS fecha, objetivo, moneda, importe_gastado,
               alcance, impresiones, clics, ctr, cpc, resultados
        FROM meta_ads ORDER BY fecha_publicacion
        """,
    )
    mailchimp = _filas_a_dicts(
        conn,
        """
        SELECT nombre_campana, fecha_envio AS fecha, destinatarios, entregas,
               tasa_apertura, aperturas_unicas, aperturas_totales, tasa_clics,
               clics_unicos, clics_totales, tasa_rebote, rebotes, bajas
        FROM mailchimp_campanas ORDER BY fecha_envio
        """,
    )
    linkedin = _filas_a_dicts(
        conn,
        """
        SELECT pagina, fecha_publicacion AS fecha, tipo, descripcion, impresiones,
               alcance, clics, reacciones, comentarios, compartidos, interacciones
        FROM linkedin_organico ORDER BY fecha_publicacion
        """,
    )

    return {
        "meta_organico": meta_organico,
        "meta_ads": meta_ads,
        "mailchimp": mailchimp,
        "linkedin": linkedin,
    }
