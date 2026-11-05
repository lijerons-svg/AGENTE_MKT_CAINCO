"""Conexión SQLite + aplicación de esquema."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator


def _schema_sql() -> str:
    return resources.files("marketing_analytics.database").joinpath("schema.sql").read_text(
        encoding="utf-8"
    )


# Columnas agregadas después de que las bases de datos ya existían en
# producción — `CREATE TABLE IF NOT EXISTS` no las suma a una tabla vieja,
# por eso se agregan a mano acá, una sola vez, sin perder nada de lo ya
# guardado.
_COLUMNAS_NUEVAS: tuple[tuple[str, str, str], ...] = (
    ("meta_organico", "imagen_url", "TEXT NOT NULL DEFAULT ''"),
    ("meta_organico", "link", "TEXT NOT NULL DEFAULT ''"),
    ("meta_ads", "pagina_origen_id", "TEXT NOT NULL DEFAULT ''"),
    ("meta_ads", "conversaciones_iniciadas", "INTEGER NOT NULL DEFAULT 0"),
    ("meta_ads", "fecha_inicio_campana", "TEXT"),
    ("meta_ads", "fecha_fin_campana", "TEXT"),
)


def _aplicar_migraciones_columnas(conn: sqlite3.Connection) -> None:
    for tabla, columna, definicion in _COLUMNAS_NUEVAS:
        existentes = {fila[1] for fila in conn.execute(f"PRAGMA table_info({tabla})")}
        if columna not in existentes:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_schema_sql())
    _aplicar_migraciones_columnas(conn)
    conn.commit()


@contextmanager
def get_connection(database_path: str | Path = ":memory:") -> Iterator[sqlite3.Connection]:
    """Abre una conexión, aplica el esquema si hace falta y la cierra al salir.

    Usar ":memory:" en tests para no tocar disco.
    """
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        initialize_schema(conn)
        yield conn
    finally:
        conn.close()
