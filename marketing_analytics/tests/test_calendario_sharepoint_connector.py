import datetime
from unittest.mock import MagicMock

from marketing_analytics.config.schema import CalendarioConfig
from marketing_analytics.connectors.calendario_sharepoint.connector import (
    CalendarioSharePointConnector,
)


def test_fetch_ignora_desde_hasta_y_trae_la_hoja_entera():
    """El calendario no es un feed incremental: fetch siempre trae todo,
    sin importar qué rango de fechas se le pase."""
    cliente_falso = MagicMock()
    cliente_falso.obtener_filas_calendario.return_value = [
        {"id": "1", "perfil": "Marca X"},
        {"id": "2", "perfil": "Marca Y"},
    ]
    conector = CalendarioSharePointConnector(
        CalendarioConfig(), "tenant", "client", "secret", cliente=cliente_falso
    )

    registros = conector.fetch(datetime.date(2026, 1, 1), datetime.date(2026, 1, 2))

    assert len(registros) == 2
    assert {r.id_origen for r in registros} == {"1", "2"}


def test_upsert_persiste_via_repository(conn):
    cliente_falso = MagicMock()
    cliente_falso.obtener_filas_calendario.return_value = [{"id": "1", "perfil": "Marca X"}]
    conector = CalendarioSharePointConnector(
        CalendarioConfig(), "tenant", "client", "secret", cliente=cliente_falso
    )

    registros = conector.fetch(datetime.date(2026, 1, 1), datetime.date(2026, 1, 2))
    resultado = conector.upsert(conn, registros)

    assert resultado.nuevos == 1
    fila = conn.execute("SELECT * FROM calendario_publicaciones").fetchone()
    assert fila["perfil"] == "Marca X"
