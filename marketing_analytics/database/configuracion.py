"""Checkpoint de la última fecha `hasta` procesada, guardado en la tabla
genérica `configuracion`. Permite que "actualizar el reporte" sin fechas
manuales continúe siempre desde donde quedó la corrida anterior, sin
importar cuánto tiempo haya pasado entre una corrida y la siguiente.
"""
from __future__ import annotations

import datetime
import sqlite3

_CLAVE_ULTIMA_FECHA_HASTA = "ultima_fecha_hasta"


def obtener_ultima_fecha_hasta(conn: sqlite3.Connection) -> datetime.date | None:
    fila = conn.execute(
        "SELECT valor FROM configuracion WHERE clave = ?", (_CLAVE_ULTIMA_FECHA_HASTA,)
    ).fetchone()
    return datetime.date.fromisoformat(fila["valor"]) if fila else None


def registrar_fecha_hasta(conn: sqlite3.Connection, hasta: datetime.date) -> None:
    """Avanza el checkpoint; nunca lo mueve hacia atrás (un backfill manual
    de fechas viejas no debe pisar un checkpoint más reciente)."""
    actual = obtener_ultima_fecha_hasta(conn)
    if actual is not None and actual >= hasta:
        return
    conn.execute(
        """
        INSERT INTO configuracion (clave, valor, actualizado_en)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(clave) DO UPDATE SET
            valor = excluded.valor, actualizado_en = excluded.actualizado_en
        """,
        (_CLAVE_ULTIMA_FECHA_HASTA, hasta.isoformat()),
    )
    conn.commit()
