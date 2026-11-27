import datetime

from marketing_analytics.config.schema import PropiedadGA4
from marketing_analytics.connectors.ga4.mapper import mapear_fila, mapear_fila_pagina


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
    }

    registro = mapear_fila_pagina(propiedad, fila)

    assert registro.unidad == "CAINCO Sitio Principal"
    assert registro.property_id == "476689307"
    assert registro.fecha == datetime.date(2026, 7, 15)
    assert registro.pagina == "/curso-emprendimiento"
    assert registro.sesiones == 5
    assert registro.vistas_pagina == 8
    assert registro.uid == "ga4_pagina|476689307|2026-07-15|/curso-emprendimiento"
