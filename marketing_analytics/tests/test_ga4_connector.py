import datetime
from unittest.mock import MagicMock

import pytest

from marketing_analytics.config.schema import GA4Config, PropiedadGA4
from marketing_analytics.connectors.ga4.connector import GA4Connector


def _cliente_falso(
    filas_diarias=None,
    filas_paginas=None,
    filas_canales=None,
    filas_eventos=None,
    side_effect_diarias=None,
):
    cliente = MagicMock()
    if side_effect_diarias is not None:
        cliente.obtener_metricas_diarias.side_effect = side_effect_diarias
    else:
        cliente.obtener_metricas_diarias.return_value = filas_diarias or [
            {"fecha": datetime.date(2026, 7, 1), "sesiones": 10, "usuarios_totales": 8, "usuarios_nuevos": 2}
        ]
    cliente.obtener_metricas_por_pagina.return_value = filas_paginas or []
    cliente.obtener_metricas_por_canal.return_value = filas_canales or []
    cliente.obtener_metricas_por_evento.return_value = filas_eventos or []
    return cliente


def test_fetch_recorre_todas_las_propiedades():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )
    cliente_falso = _cliente_falso()

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    resultado = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(resultado.metricas_diarias) == 2
    assert {r.unidad for r in resultado.metricas_diarias} == {"Academy Cainco", "Acierta CAINCO"}
    assert cliente_falso.obtener_metricas_diarias.call_count == 2
    assert cliente_falso.obtener_metricas_por_pagina.call_count == 2
    assert cliente_falso.obtener_metricas_por_canal.call_count == 2
    assert cliente_falso.obtener_metricas_por_evento.call_count == 2


def test_fetch_tambien_trae_el_desglose_por_pagina():
    config = GA4Config(propiedades=[PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="111")])
    cliente_falso = _cliente_falso(
        filas_paginas=[
            {"fecha": datetime.date(2026, 7, 1), "pagina": "/curso-emprendimiento", "sesiones": 5, "vistas_pagina": 8, "usuarios_totales": 4, "usuarios_nuevos": 2}
        ]
    )

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    resultado = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(resultado.metricas_paginas) == 1
    assert resultado.metricas_paginas[0].pagina == "/curso-emprendimiento"
    assert resultado.metricas_paginas[0].unidad == "CAINCO Sitio Principal"


def test_fetch_tambien_trae_el_desglose_por_canal():
    config = GA4Config(propiedades=[PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="111")])
    cliente_falso = _cliente_falso(
        filas_canales=[{"fecha": datetime.date(2026, 7, 1), "canal": "Organic Social", "sesiones": 42}]
    )

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    resultado = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(resultado.metricas_canales) == 1
    assert resultado.metricas_canales[0].canal == "Organic Social"
    assert resultado.metricas_canales[0].sesiones == 42


def test_fetch_tambien_trae_el_desglose_por_evento():
    config = GA4Config(propiedades=[PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="111")])
    cliente_falso = _cliente_falso(
        filas_eventos=[{"fecha": datetime.date(2026, 7, 1), "evento": "contact_link_click", "conteo": 7}]
    )

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    resultado = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(resultado.metricas_eventos) == 1
    assert resultado.metricas_eventos[0].evento == "contact_link_click"
    assert resultado.metricas_eventos[0].conteo == 7


def test_una_propiedad_rota_no_bloquea_a_las_demas():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Propiedad Rota", property_id="999"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )

    def metricas_con_una_rota(property_id, desde, hasta):
        if property_id == "999":
            raise RuntimeError("sin acceso (PERMISSION_DENIED)")
        return [
            {"fecha": datetime.date(2026, 7, 1), "sesiones": 10, "usuarios_totales": 8, "usuarios_nuevos": 2}
        ]

    cliente_falso = _cliente_falso(side_effect_diarias=metricas_con_una_rota)

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    resultado = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert len(resultado.metricas_diarias) == 2
    assert {r.unidad for r in resultado.metricas_diarias} == {"Academy Cainco", "Acierta CAINCO"}


def test_todas_las_propiedades_fallidas_lanza_error():
    config = GA4Config(
        propiedades=[
            PropiedadGA4(unidad="Academy Cainco", property_id="111"),
            PropiedadGA4(unidad="Acierta CAINCO", property_id="222"),
        ]
    )
    cliente_falso = _cliente_falso(side_effect_diarias=RuntimeError("sin acceso"))

    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)

    with pytest.raises(RuntimeError, match="Todas las propiedades"):
        conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))


def test_upsert_delega_al_repositorio(conn):
    config = GA4Config(propiedades=[PropiedadGA4(unidad="Academy Cainco", property_id="111")])
    cliente_falso = _cliente_falso(
        filas_paginas=[
            {"fecha": datetime.date(2026, 7, 1), "pagina": "/curso-x", "sesiones": 3, "vistas_pagina": 4, "usuarios_totales": 2, "usuarios_nuevos": 1}
        ],
        filas_canales=[{"fecha": datetime.date(2026, 7, 1), "canal": "Direct", "sesiones": 6}],
        filas_eventos=[{"fecha": datetime.date(2026, 7, 1), "evento": "btn_consultas", "conteo": 2}],
    )
    conector = GA4Connector(config, ruta_credenciales="fake.json", cliente=cliente_falso)
    datos = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    resultado = conector.upsert(conn, datos)

    assert resultado.nuevos == 4  # 1 diaria + 1 página + 1 canal + 1 evento
    fila_diaria = conn.execute("SELECT * FROM ga4_metricas_diarias").fetchone()
    assert fila_diaria["unidad"] == "Academy Cainco"
    assert fila_diaria["sesiones"] == 10
    fila_pagina = conn.execute("SELECT * FROM ga4_metricas_paginas").fetchone()
    assert fila_pagina["pagina"] == "/curso-x"
    assert fila_pagina["vistas_pagina"] == 4
    fila_canal = conn.execute("SELECT * FROM ga4_metricas_canales").fetchone()
    assert fila_canal["canal"] == "Direct"
    assert fila_canal["sesiones"] == 6
    fila_evento = conn.execute("SELECT * FROM ga4_metricas_eventos").fetchone()
    assert fila_evento["evento"] == "btn_consultas"
    assert fila_evento["conteo"] == 2
