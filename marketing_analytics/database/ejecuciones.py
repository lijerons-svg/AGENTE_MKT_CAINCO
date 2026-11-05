"""Persistencia del historial de ejecuciones y logs (tablas `ejecuciones`
y `logs`) — responsabilidad separada del upsert de datos en repository.py.
"""
from __future__ import annotations

import datetime
import sqlite3

from marketing_analytics.database.repository import ResultadoUpsert


def iniciar_ejecucion(conn: sqlite3.Connection) -> int:
    ahora = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO ejecuciones (hora_inicio, estado) VALUES (?, 'en_progreso')",
        (ahora,),
    )
    conn.commit()
    return cursor.lastrowid


def finalizar_ejecucion(
    conn: sqlite3.Connection,
    ejecucion_id: int,
    resultado: ResultadoUpsert,
    estado: str,
    errores: str = "",
) -> None:
    fila = conn.execute(
        "SELECT hora_inicio FROM ejecuciones WHERE id = ?", (ejecucion_id,)
    ).fetchone()
    hora_inicio = datetime.datetime.fromisoformat(fila["hora_inicio"])
    hora_fin = datetime.datetime.now(datetime.timezone.utc)
    tiempo_seg = (hora_fin - hora_inicio).total_seconds()

    conn.execute(
        """
        UPDATE ejecuciones
        SET hora_fin = ?, tiempo_ejecucion_seg = ?, estado = ?,
            registros_descargados = ?, registros_nuevos = ?,
            registros_actualizados = ?, registros_descartados = ?, errores = ?
        WHERE id = ?
        """,
        (
            hora_fin.isoformat(),
            tiempo_seg,
            estado,
            resultado.total,
            resultado.nuevos,
            resultado.actualizados,
            resultado.descartados,
            errores,
            ejecucion_id,
        ),
    )
    conn.commit()


def registrar_log(
    conn: sqlite3.Connection, ejecucion_id: int, nivel: str, fuente: str, mensaje: str
) -> None:
    conn.execute(
        "INSERT INTO logs (ejecucion_id, nivel, fuente, mensaje) VALUES (?, ?, ?, ?)",
        (ejecucion_id, nivel, fuente, mensaje),
    )
    conn.commit()
