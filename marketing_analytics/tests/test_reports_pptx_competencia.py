import datetime

import responses

from marketing_analytics.reports_pptx.competencia import obtener_competidor


@responses.activate
def test_obtener_competidor_trae_seguidores_y_textos_de_posts():
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/CompetidorX",
        json={"name": "Competidor X", "fan_count": 1234},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/CompetidorX/posts",
        json={"data": [{"message": "Post 1"}, {"message": "Post 2"}, {"created_time": "2026-08-01"}]},
        status=200,
    )

    resultado = obtener_competidor(
        "CompetidorX", "token-falso", "v25.0", datetime.date(2026, 8, 1), datetime.date(2026, 8, 31)
    )

    assert resultado["nombre"] == "Competidor X"
    assert resultado["seguidores"] == 1234
    assert resultado["cantidad_publicaciones"] == 3
    # El post sin "message" (solo created_time) no aporta texto, pero sí cuenta como publicación.
    assert resultado["publicaciones"] == ["Post 1", "Post 2"]


@responses.activate
def test_obtener_competidor_pagina_resultados():
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/CompetidorY",
        json={"name": "Competidor Y", "fan_count": 10},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/CompetidorY/posts",
        json={
            "data": [{"message": "Post A"}],
            "paging": {"next": "https://graph.facebook.com/v25.0/CompetidorY/posts?after=xyz"},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/CompetidorY/posts?after=xyz",
        json={"data": [{"message": "Post B"}]},
        status=200,
    )

    resultado = obtener_competidor(
        "CompetidorY", "token-falso", "v25.0", datetime.date(2026, 8, 1), datetime.date(2026, 8, 31)
    )
    assert resultado["cantidad_publicaciones"] == 2
    assert resultado["publicaciones"] == ["Post A", "Post B"]
