import datetime

from marketing_analytics.config.schema import PropiedadGA4
from marketing_analytics.connectors.ga4.mapper import (
    mapear_fila,
    mapear_fila_canal,
    mapear_fila_evento,
    mapear_fila_pagina,
)


def test_mapear_fila():
    propiedad = PropiedadGA4(unidad="Academy Cainco", property_id="123456789")
    fila = {
        "fecha": datetime.date(2026, 7, 15),
        "sesiones": 42,
        "usuarios_totales": 35,
        "usuarios_nuevos": 10,
    }

    registro = mapear_fila(propiedad, fila)

    assert registro.unidad == "Academy Cainco"
    assert registro.property_id == "123456789"
    assert registro.fecha == datetime.date(2026, 7, 15)
    assert registro.sesiones == 42
    assert registro.usuarios_totales == 35
    assert registro.usuarios_nuevos == 10
    assert registro.uid == "ga4|123456789|2026-07-15"


def test_mapear_fila_pagina():
    propiedad = PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="476689307")
    fila = {
        "fecha": datetime.date(2026, 7, 15),
        "pagina": "/curso-emprendimiento",
        "sesiones": 5,
        "vistas_pagina": 8,
        "usuarios_totales": 4,
        "usuarios_nuevos": 2,
    }

    registro = mapear_fila_pagina(propiedad, fila)

    assert registro.unidad == "CAINCO Sitio Principal"
    assert registro.property_id == "476689307"
    assert registro.fecha == datetime.date(2026, 7, 15)
    assert registro.pagina == "/curso-emprendimiento"
    assert registro.sesiones == 5
    assert registro.vistas_pagina == 8
    assert registro.usuarios_totales == 4
    assert registro.usuarios_nuevos == 2
    assert registro.uid == "ga4_pagina|476689307|2026-07-15|/curso-emprendimiento"


def test_mapear_fila_canal():
    propiedad = PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="476689307")
    fila = {"fecha": datetime.date(2026, 7, 15), "canal": "Organic Social", "pagina": "/", "sesiones": 61}

    registro = mapear_fila_canal(propiedad, fila)

    assert registro.unidad == "CAINCO Sitio Principal"
    assert registro.canal == "Organic Social"
    assert registro.pagina == "/"
    assert registro.sesiones == 61
    assert registro.uid == "ga4_canal|476689307|2026-07-15|Organic Social|/"


def test_mapear_fila_evento():
    propiedad = PropiedadGA4(unidad="CAINCO Sitio Principal", property_id="476689307")
    fila = {"fecha": datetime.date(2026, 7, 15), "evento": "contact_link_click", "pagina": "/", "conteo": 7}

    registro = mapear_fila_evento(propiedad, fila)

    assert registro.unidad == "CAINCO Sitio Principal"
    assert registro.evento == "contact_link_click"
    assert registro.pagina == "/"
    assert registro.conteo == 7
    assert registro.uid == "ga4_evento|476689307|2026-07-15|contact_link_click|/"
