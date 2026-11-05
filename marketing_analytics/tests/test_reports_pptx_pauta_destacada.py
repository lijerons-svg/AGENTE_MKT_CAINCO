import datetime

import responses

from marketing_analytics.reports_pptx.pauta_destacada import (
    formato_creativo,
    obtener_creativo_anuncio,
    obtener_insights_anuncios,
    top_anuncios_destacados,
)


@responses.activate
def test_obtener_insights_anuncios_pagina_resultados():
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/act_123/insights",
        json={
            "data": [{"ad_id": "1", "ad_name": "Anuncio 1"}],
            "paging": {"next": "https://graph.facebook.com/v25.0/act_123/insights?after=xyz"},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/act_123/insights?after=xyz",
        json={"data": [{"ad_id": "2", "ad_name": "Anuncio 2"}]},
        status=200,
    )

    filas = obtener_insights_anuncios(
        "123", "token-falso", "v25.0", datetime.date(2026, 8, 1), datetime.date(2026, 8, 31)
    )
    assert [f["ad_id"] for f in filas] == ["1", "2"]


@responses.activate
def test_obtener_creativo_anuncio_prefiere_image_url_sobre_thumbnail():
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/999",
        json={"creative": {"image_url": "https://x/img.png", "thumbnail_url": "https://x/thumb.png", "object_type": "PHOTO"}},
        status=200,
    )
    resultado = obtener_creativo_anuncio("999", "token-falso", "v25.0")
    assert resultado == {"imagen_url": "https://x/img.png", "tipo": "PHOTO"}


def test_formato_creativo_mapea_tipos_conocidos_y_desconocidos():
    assert formato_creativo("PHOTO") == "Imagen"
    assert formato_creativo("VIDEO") == "Video"
    assert formato_creativo("CAROUSEL") == "Carrusel"
    assert formato_creativo("ALGO_RARO") == "Anuncio"
    assert formato_creativo("") == "Anuncio"


@responses.activate
def test_top_anuncios_destacados_rankea_por_engagement_y_solo_pide_imagen_del_top():
    filas = [
        {
            "ad_id": "bajo",
            "ad_name": "Anuncio bajo",
            "publisher_platform": "facebook",
            "impressions": "1000",
            "clicks": "5",
            "spend": "10",
            "actions": [{"action_type": "post_engagement", "value": "5"}],
        },
        {
            "ad_id": "alto",
            "ad_name": "Anuncio alto",
            "publisher_platform": "instagram",
            "impressions": "5000",
            "clicks": "50",
            "spend": "40",
            "actions": [{"action_type": "post_engagement", "value": "500"}],
        },
    ]
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/alto",
        json={"creative": {"image_url": "https://x/alto.png", "object_type": "VIDEO"}},
        status=200,
    )

    resultado = top_anuncios_destacados(filas, "token-falso", "v25.0", cantidad=1)

    assert len(resultado) == 1
    assert resultado[0]["ad_id"] == "alto"
    assert resultado[0]["engagement"] == 500
    assert resultado[0]["tipo"] == "Video"
    assert resultado[0]["imagen_url"] == "https://x/alto.png"
    # Solo se llamó a la API de creativo una vez, para el que entró al top.
    assert len(responses.calls) == 1


@responses.activate
def test_top_anuncios_destacados_usa_fallback_de_acciones_sin_post_engagement():
    filas = [
        {
            "ad_id": "1",
            "ad_name": "Anuncio",
            "publisher_platform": "facebook",
            "impressions": "100",
            "clicks": "1",
            "spend": "1",
            "actions": [
                {"action_type": "post_reaction", "value": "3"},
                {"action_type": "comment", "value": "2"},
                {"action_type": "post_share", "value": "1"},
            ],
        },
    ]
    responses.add(
        responses.GET,
        "https://graph.facebook.com/v25.0/1",
        json={"creative": {}},
        status=200,
    )
    resultado = top_anuncios_destacados(filas, "token-falso", "v25.0", cantidad=4)
    assert resultado[0]["engagement"] == 6


def test_top_anuncios_destacados_sin_filas_no_llama_a_la_api():
    assert top_anuncios_destacados([], "token-falso", "v25.0") == []
