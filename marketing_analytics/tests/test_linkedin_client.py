import datetime

import responses

from marketing_analytics.connectors.linkedin.client import (
    LinkedInClient,
    _generar_versiones_candidatas,
)

BASE = "https://api.linkedin.com"


def test_generar_versiones_candidatas_son_los_ultimos_meses_del_mas_nuevo_al_mas_viejo():
    versiones = _generar_versiones_candidatas(meses=3, hoy=datetime.date(2026, 11, 4))

    assert versiones == ("202611", "202610", "202609")


def test_generar_versiones_candidatas_cruza_el_cambio_de_anio():
    versiones = _generar_versiones_candidatas(meses=3, hoy=datetime.date(2026, 1, 15))

    assert versiones == ("202601", "202512", "202511")


@responses.activate
def test_resolver_version_salta_las_que_dan_426(monkeypatch):
    """Caso real: LinkedIn retira versiones viejas de /rest/ con un 426
    NONEXISTENT_VERSION, sin decir en el error cuál es la vigente — no
    importa qué versión exacta se pruebe primero, solo que siga probando
    hasta encontrar una que no dé ese código."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")

    respuestas = iter([426, 426, 200])

    def callback(request):
        codigo = next(respuestas)
        if codigo == 426:
            return (426, {}, '{"status": 426, "code": "NONEXISTENT_VERSION"}')
        return (200, {}, '{"elements": []}')

    responses.add_callback(responses.GET, f"{BASE}/rest/posts", callback=callback, content_type="application/json")

    version = cliente._resolver_version()

    assert len(responses.calls) == 3
    # Se cachea: una segunda llamada no debe volver a pegarle a la API.
    assert cliente._resolver_version() == version
    assert len(responses.calls) == 3


@responses.activate
def test_obtener_posts_corta_al_llegar_a_una_fecha_anterior_a_desde(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"  # evita la detección de versión en este test

    def ms(fecha: datetime.date) -> int:
        return int(datetime.datetime(fecha.year, fecha.month, fecha.day, tzinfo=datetime.timezone.utc).timestamp() * 1000)

    responses.add(
        responses.GET,
        f"{BASE}/rest/posts",
        json={
            "elements": [
                {"id": "urn:li:share:1", "publishedAt": ms(datetime.date(2026, 7, 15))},
                {"id": "urn:li:share:2", "publishedAt": ms(datetime.date(2026, 7, 10))},
                {"id": "urn:li:share:3", "publishedAt": ms(datetime.date(2026, 6, 20))},  # anterior a `desde`
                {"id": "urn:li:share:4", "publishedAt": ms(datetime.date(2026, 6, 1))},
            ]
        },
        status=200,
    )

    posts = cliente.obtener_posts("1592889", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert [p["id"] for p in posts] == ["urn:li:share:1", "urn:li:share:2"]
    assert len(responses.calls) == 1


@responses.activate
def test_obtener_posts_pagina_hasta_encontrar_el_corte(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    def ms(fecha: datetime.date) -> int:
        return int(datetime.datetime(fecha.year, fecha.month, fecha.day, tzinfo=datetime.timezone.utc).timestamp() * 1000)

    responses.add(
        responses.GET,
        f"{BASE}/rest/posts",
        json={"elements": [{"id": f"urn:li:share:{i}", "publishedAt": ms(datetime.date(2026, 7, 31))} for i in range(50)]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/rest/posts",
        json={"elements": [{"id": "urn:li:share:viejo", "publishedAt": ms(datetime.date(2026, 6, 1))}]},
        status=200,
    )

    posts = cliente.obtener_posts("1592889", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert len(posts) == 50
    assert len(responses.calls) == 2


@responses.activate
def test_obtener_estadisticas_post_usa_shares_para_id_tipo_share(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"elements": [{"totalShareStatistics": {"likeCount": 5}}]},
        status=200,
    )

    resultado = cliente.obtener_estadisticas_post("1592889", "urn:li:share:123")

    assert resultado == {"totalShareStatistics": {"likeCount": 5}}
    assert "shares=List(" in responses.calls[0].request.url
    assert "ugcPosts=" not in responses.calls[0].request.url


@responses.activate
def test_obtener_estadisticas_post_usa_ugcposts_para_id_tipo_ugcpost(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"elements": [{"totalShareStatistics": {"likeCount": 2}}]},
        status=200,
    )

    resultado = cliente.obtener_estadisticas_post("1592889", "urn:li:ugcPost:456")

    assert resultado == {"totalShareStatistics": {"likeCount": 2}}
    assert "ugcPosts=List(" in responses.calls[0].request.url


@responses.activate
def test_obtener_estadisticas_post_no_rompe_si_la_api_falla(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"message": "boom"},
        status=500,
    )
    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"message": "boom"},
        status=500,
    )
    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"message": "boom"},
        status=500,
    )
    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"message": "boom"},
        status=500,
    )
    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityShareStatistics",
        json={"message": "boom"},
        status=500,
    )

    assert cliente.obtener_estadisticas_post("1592889", "urn:li:share:123") == {}


@responses.activate
def test_obtener_seguidores_totales_suma_el_desglose_por_antiguedad(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityFollowerStatistics",
        json={
            "elements": [
                {
                    "followerCountsBySeniority": [
                        {"followerCounts": {"organicFollowerCount": 100, "paidFollowerCount": 5}},
                        {"followerCounts": {"organicFollowerCount": 50, "paidFollowerCount": 0}},
                    ]
                }
            ]
        },
        status=200,
    )

    assert cliente.obtener_seguidores_totales("1592889") == 155


@responses.activate
def test_obtener_seguidores_totales_sin_elementos_devuelve_cero(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = LinkedInClient(access_token="fake-token")
    cliente._version = "202610"

    responses.add(
        responses.GET,
        f"{BASE}/rest/organizationalEntityFollowerStatistics",
        json={"elements": []},
        status=200,
    )

    assert cliente.obtener_seguidores_totales("1592889") == 0
