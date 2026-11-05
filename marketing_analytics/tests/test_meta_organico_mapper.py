import datetime

from marketing_analytics.config.schema import PerfilMetaOrganico, Red
from marketing_analytics.connectors.meta_organico.mapper import (
    mapear_media_instagram,
    mapear_post_facebook,
)

_PERFIL_FB = PerfilMetaOrganico(
    id="perfil_002", nombre="Marca X - Facebook", red=Red.FACEBOOK, page_id="page_1"
)
_PERFIL_IG = PerfilMetaOrganico(
    id="perfil_001", nombre="Marca X - Instagram", red=Red.INSTAGRAM, ig_user_id="ig_1"
)


def test_mapear_post_facebook_suma_reacciones_y_trunca_descripcion():
    post = {
        "id": "post_1",
        "message": "x" * 200,
        "created_time": "2026-07-01T10:00:00+0000",
        "attachments": {"data": [{"media_type": "photo"}]},
        "comments": {"summary": {"total_count": 5}},
        "shares": {"count": 3},
    }
    insights = {
        "post_media_view": 1000,
        "post_clicks": 50,
        "post_clicks_by_type": {"link clicks": 20, "other clicks": 30},
        "post_reactions_by_type_total": {"like": 40, "love": 10},
    }

    registro = mapear_post_facebook(_PERFIL_FB, "Marca X Oficial", post, insights)

    assert registro.tipo == "imagen"
    assert len(registro.descripcion) == 120
    assert registro.visualizaciones == 1000
    assert registro.clics_enlace == 20
    assert registro.reacciones == 50
    assert registro.comentarios == 5
    assert registro.compartidos == 3
    assert registro.total_interacciones == 58


def test_mapear_post_facebook_usa_post_total_media_view_unique_como_alcance():
    post = {
        "id": "post_4",
        "message": "post con alcance",
        "created_time": "2026-07-01T10:00:00+0000",
        "comments": {"summary": {"total_count": 0}},
        "shares": {"count": 0},
    }
    insights = {"post_total_media_view_unique": 750}

    registro = mapear_post_facebook(_PERFIL_FB, "Marca X Oficial", post, insights)

    assert registro.alcance == 750


def test_mapear_post_facebook_alcance_en_cero_si_no_hay_metrica_disponible():
    """Si el candidato "post_total_media_view_unique" no responde para
    algún post (versión de API, permisos, etc.), no se inventa un valor —
    queda en 0, igual que el resto de las métricas con fallback."""
    post = {
        "id": "post_5",
        "message": "post sin alcance",
        "created_time": "2026-07-01T10:00:00+0000",
        "comments": {"summary": {"total_count": 0}},
        "shares": {"count": 0},
    }

    registro = mapear_post_facebook(_PERFIL_FB, "Marca X Oficial", post, {})

    assert registro.alcance == 0


def test_mapear_media_instagram_sin_clics_por_limitacion_de_api():
    media = {
        "id": "media_1",
        "caption": "Post de Instagram",
        "media_type": "IMAGE",
        "media_product_type": "FEED",
        "timestamp": "2026-07-05T12:00:00+0000",
        "like_count": 100,
        "comments_count": 10,
    }
    insights = {"reach": 900, "shares": 4, "saved": 6, "total_interactions": 114}

    registro = mapear_media_instagram(_PERFIL_IG, "marcax.oficial", media, insights)

    assert registro.red == "instagram"
    assert registro.alcance == 900
    assert registro.total_clics == 0
    assert registro.clics_enlace == 0
    assert registro.total_interacciones == 114


def test_mapear_media_instagram_usa_views_como_visualizaciones():
    media = {
        "id": "media_2",
        "caption": "Reel",
        "media_type": "VIDEO",
        "media_product_type": "REELS",
        "timestamp": "2026-07-06T12:00:00+0000",
        "like_count": 50,
        "comments_count": 2,
    }
    insights = {"reach": 500, "shares": 1, "saved": 2, "total_interactions": 53, "views": 2000}

    registro = mapear_media_instagram(_PERFIL_IG, "marcax.oficial", media, insights)

    assert registro.visualizaciones == 2000
