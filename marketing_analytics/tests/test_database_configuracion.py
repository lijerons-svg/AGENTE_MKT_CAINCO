import datetime

from marketing_analytics.database.configuracion import (
    obtener_ultima_fecha_hasta,
    registrar_fecha_hasta,
)
from marketing_analytics.database.connection import get_connection


def test_obtener_ultima_fecha_hasta_es_none_si_nunca_se_registro():
    with get_connection(":memory:") as conn:
        assert obtener_ultima_fecha_hasta(conn) is None


def test_registrar_y_obtener_fecha_hasta():
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        assert obtener_ultima_fecha_hasta(conn) == datetime.date(2026, 7, 21)


def test_registrar_fecha_mas_reciente_avanza_el_checkpoint():
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 28))

        assert obtener_ultima_fecha_hasta(conn) == datetime.date(2026, 7, 28)


def test_registrar_fecha_mas_vieja_no_mueve_el_checkpoint_hacia_atras():
    """Un backfill manual de fechas pasadas no debe pisar un checkpoint
    más reciente ya alcanzado por una corrida automática."""
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))
        registrar_fecha_hasta(conn, datetime.date(2026, 1, 1))

        assert obtener_ultima_fecha_hasta(conn) == datetime.date(2026, 7, 21)
