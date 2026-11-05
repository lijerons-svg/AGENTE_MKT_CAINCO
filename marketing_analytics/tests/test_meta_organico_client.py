import datetime

import responses

from marketing_analytics.connectors.meta_organico.client import MetaOrganicoClient

BASE = "https://graph.facebook.com/v21.0"


@responses.activate
def test_obtener_posts_pagina_sigue_paginando(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")

    responses.add(
        responses.GET,
        f"{BASE}/page_1/posts",
        json={
            "data": [{"id": "post_1", "created_time": "2026-07-01T10:00:00+0000"}],
            "paging": {"next": f"{BASE}/page_1/posts?after=cursor1"},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/page_1/posts",
        json={"data": [{"id": "post_2", "created_time": "2026-07-02T10:00:00+0000"}]},
        status=200,
    )

    posts = cliente.obtener_posts_pagina(
        "page_1", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31)
    )

    assert [p["id"] for p in posts] == ["post_1", "post_2"]


@responses.activate
def test_obtener_posts_pagina_manda_until_exclusivo_para_que_desde_igual_a_hasta_no_falle(
    monkeypatch,
):
    """Caso real de QA: una corrida automática donde desde == hasta == hoy
    rompía con "(#100) since should be less than until" — Meta rechaza
    since == until. Se manda until = hasta + 1 día para evitarlo."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")
    responses.add(responses.GET, f"{BASE}/page_1/posts", json={"data": []}, status=200)

    cliente.obtener_posts_pagina("page_1", datetime.date(2026, 7, 21), datetime.date(2026, 7, 21))

    assert responses.calls[0].request.params["until"] == "2026-07-22"
    assert responses.calls[0].request.params["since"] == "2026-07-21"


@responses.activate
def test_insights_con_fallback_degrada_metrica_por_metrica(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")

    # el batch completo falla (p.ej. una métrica ya no existe en esta versión)
    responses.add(responses.GET, f"{BASE}/post_1/insights", status=400, json={"error": "bad metric"})
    # reintento metrica por metrica: una responde ok, la otra sigue fallando
    responses.add(
        responses.GET,
        f"{BASE}/post_1/insights",
        json={"data": [{"name": "metrica_valida", "values": [{"value": 500}]}]},
        status=200,
    )
    responses.add(responses.GET, f"{BASE}/post_1/insights", status=400, json={"error": "bad metric"})

    resultado = cliente.obtener_insights_con_fallback(
        "post_1", ("metrica_valida", "metrica_deprecada")
    )

    assert resultado == {"metrica_valida": 500}


@responses.activate
def test_insights_con_fallback_avisa_si_la_respuesta_viene_vacia_sin_error(monkeypatch, caplog):
    """Caso real de QA: Meta puede responder 200 con 'data': [] (sin
    lanzar error) cuando el token no tiene permiso read_insights para ese
    objeto — sin este aviso, se ve indistinguible de "0 interacciones
    reales" y el problema queda invisible en los logs."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")
    responses.add(responses.GET, f"{BASE}/post_1/insights", json={"data": []}, status=200)

    with caplog.at_level("WARNING"):
        resultado = cliente.obtener_insights_con_fallback("post_1", ("post_reactions_by_type_total",))

    assert resultado == {}
    assert "Insights vacíos" in caplog.text
    assert "post_1" in caplog.text


@responses.activate
def test_obtener_nombre_pagina(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")
    responses.add(responses.GET, f"{BASE}/page_1", json={"name": "Marca X"}, status=200)

    assert cliente.obtener_nombre_pagina("page_1") == "Marca X"


@responses.activate
def test_obtener_seguidores_pagina(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")
    responses.add(responses.GET, f"{BASE}/page_1", json={"fan_count": 12345}, status=200)

    assert cliente.obtener_seguidores_pagina("page_1") == 12345


@responses.activate
def test_obtener_seguidores_ig(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="fake-token", api_version="v21.0")
    responses.add(responses.GET, f"{BASE}/ig_1", json={"followers_count": 6789}, status=200)

    assert cliente.obtener_seguidores_ig("ig_1") == 6789


@responses.activate
def test_obtener_token_de_pagina(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="token-sistema", api_version="v21.0")
    responses.add(
        responses.GET, f"{BASE}/page_1", json={"access_token": "token-de-pagina"}, status=200
    )

    assert cliente.obtener_token_de_pagina("page_1") == "token-de-pagina"


@responses.activate
def test_obtener_posts_pagina_usa_el_token_de_pagina_si_se_pasa(monkeypatch):
    """Meta exige el token propio de la Página para /posts bajo la 'nueva
    experiencia para páginas' — el token del Usuario del Sistema solo no
    alcanza (caso real encontrado en QA)."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="token-sistema", api_version="v21.0")
    responses.add(
        responses.GET, f"{BASE}/page_1/posts", json={"data": [{"id": "post_1"}]}, status=200
    )

    cliente.obtener_posts_pagina(
        "page_1", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31), token="token-de-pagina"
    )

    assert responses.calls[0].request.params["access_token"] == "token-de-pagina"


@responses.activate
def test_obtener_posts_pagina_usa_token_de_sistema_si_no_se_pasa_ninguno(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = MetaOrganicoClient(access_token="token-sistema", api_version="v21.0")
    responses.add(
        responses.GET, f"{BASE}/page_1/posts", json={"data": []}, status=200
    )

    cliente.obtener_posts_pagina("page_1", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert responses.calls[0].request.params["access_token"] == "token-sistema"
