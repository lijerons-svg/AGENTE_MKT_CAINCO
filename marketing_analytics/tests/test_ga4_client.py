import datetime

import responses

from marketing_analytics.connectors.ga4.client import GA4Client

BASE = "https://analyticsdata.googleapis.com/v1beta"


def _token_falso(ruta_credenciales: str) -> str:
    """Evita depender de una firma JWT real (y de que `cryptography` esté
    instalada/funcionando en la máquina que corre los tests) solo para
    probar la forma de la consulta y el mapeo de la respuesta — eso ya lo
    cubre el hecho de que `auth.obtener_token` se usa tal cual en
    producción, inyectado acá solo para los tests."""
    return "fake-token"


@responses.activate
def test_obtener_metricas_diarias_mapea_filas_de_ga4():
    cliente = GA4Client("ruta/falsa.json", obtener_token_fn=_token_falso)
    responses.add(
        responses.POST,
        f"{BASE}/properties/123456789:runReport",
        json={
            "rows": [
                {
                    "dimensionValues": [{"value": "20260715"}],
                    "metricValues": [{"value": "42"}, {"value": "35"}, {"value": "10"}],
                },
                {
                    "dimensionValues": [{"value": "20260716"}],
                    "metricValues": [{"value": "50"}, {"value": "40"}, {"value": "12"}],
                },
            ]
        },
        status=200,
    )

    filas = cliente.obtener_metricas_diarias(
        "123456789", datetime.date(2026, 7, 15), datetime.date(2026, 7, 16)
    )

    assert filas == [
        {
            "fecha": datetime.date(2026, 7, 15),
            "sesiones": 42,
            "usuarios_totales": 35,
            "usuarios_nuevos": 10,
        },
        {
            "fecha": datetime.date(2026, 7, 16),
            "sesiones": 50,
            "usuarios_totales": 40,
            "usuarios_nuevos": 12,
        },
    ]


@responses.activate
def test_sin_filas_en_el_rango_devuelve_lista_vacia():
    cliente = GA4Client("ruta/falsa.json", obtener_token_fn=_token_falso)
    responses.add(
        responses.POST,
        f"{BASE}/properties/123456789:runReport",
        json={},  # GA4 no manda "rows" cuando el rango no tiene datos
        status=200,
    )

    filas = cliente.obtener_metricas_diarias(
        "123456789", datetime.date(2026, 7, 15), datetime.date(2026, 7, 16)
    )

    assert filas == []


@responses.activate
def test_usa_el_token_que_devuelve_obtener_token_fn():
    llamadas = []

    def token_fn(ruta_credenciales):
        llamadas.append(ruta_credenciales)
        return "un-token-cualquiera"

    cliente = GA4Client("ruta/credenciales.json", obtener_token_fn=token_fn)
    responses.add(
        responses.POST, f"{BASE}/properties/999:runReport", json={"rows": []}, status=200
    )

    cliente.obtener_metricas_diarias("999", datetime.date(2026, 7, 1), datetime.date(2026, 7, 1))

    assert llamadas == ["ruta/credenciales.json"]
    assert responses.calls[0].request.headers["Authorization"] == "Bearer un-token-cualquiera"
