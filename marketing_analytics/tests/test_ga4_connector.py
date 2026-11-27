import datetime
from unittest.mock import MagicMock

import pytest

from marketing_analytics.config.schema import GA4Config, PropiedadGA4
from marketing_analytics.connectors.ga4.connector import GA4Connector


def test_fetch_recorre_todas_las_propiedades():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )
    cliente_falso = MagicMock()
    cliente_falso.obtener_metricas_diarias.return_value = [
        {"fecha": datetime.date(2026, 7, 1), "sesiones": 10, "usuarios_totales": 8, "usuarios_nuevos": 2}
    ]

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(registros) == 2
    assert {r.unidad for r in registros} == {"Academy Cainco", "Acierta CAINCO"}
    assert cliente_falso.obtener_metricas_diarias.call_count == 2


def test_una_propiedad_rota_no_bloquea_a_las_demas():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Propiedad Rota", property_id="999"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )
    cliente_falso = MagicMock()

    def metricas_con_una_rota(property_id, desde, hasta):
        if property_id == "999":
            raise RuntimeError("sin acceso (PERMISSION_DENIED)")
        return [
            {"fecha": datetime.date(2026, 7, 1), "sesiones": 10, "usuarios_totales": 8, "usuarios_nuevos": 2}
        ]

    cliente_falso.obtener_metricas_diarias.side_effect = metricas_con_una_rota

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(registros) == 2
    assert {r.unidad for r in registros} == {"Academy Cainco", "Acierta CAINCO"}


def test_todas_las_propiedades_fallidas_lanza_error():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )
    cliente_falso = MagicMock()
    cliente_falso.obtener_metricas_diarias.side_effect = RuntimeError("sin acceso")

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)

    with pytest.raises(RuntimeError, match="Todas las propiedades"):
        conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))


def test_upsert_delega_al_repositorio(conn):
    config = GA4Config(propiedades=[PropiedadGA4(unidad="Academy Cainco", property_id="111")])
    cliente_falso = MagicMock()
    cliente_falso.obtener_metricas_diarias.return_value = [
        {"fecha": datetime.date(2026, 7, 1), "sesiones": 10, "usuarios_totales": 8, "usuarios_nuevos": 2}
    ]
    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    resultado = conector.upsert(conn, registros)

    assert resultado.nuevos == 1
    fila = conn.execute("SELECT * FROM ga4_metricas_diarias").fetchone()
    assert fila["unidad"] == "Academy Cainco"
    assert fila["sesiones"] == 10
