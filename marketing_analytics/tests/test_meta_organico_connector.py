import datetime
from unittest.mock import MagicMock

import pytest

from marketing_analytics.config.schema import (
    MetaOrganicoConfig,
    PerfilMetaOrganico,
    Red,
)
from marketing_analytics.connectors.meta_organico.connector import MetaOrganicoConnector


def test_fetch_recorre_todos_los_perfiles_sin_importar_cuantos_sean():
    config = MetaOrganicoConfig(
        perfiles=[
            PerfilMetaOrganico(id="p1", nombre="Perfil FB", red=Red.FACEBOOK, page_id="page_1"),
            PerfilMetaOrganico(id="p2", nombre="Perfil IG", red=Red.INSTAGRAM, ig_user_id="ig_1"),
            PerfilMetaOrganico(id="p3", nombre="Perfil IG 2", red=Red.INSTAGRAM, ig_user_id="ig_2"),
        ]
    )

    cliente_falso = MagicMock()
    cliente_falso.obtener_nombre_pagina.return_value = "Página FB"
    cliente_falso.obtener_nombre_cuenta_ig.return_value = "cuenta.ig"
    cliente_falso.obtener_posts_pagina.return_value = [
        {
            "id": "post_1",
            "message": "hola",
            "created_time": "2026-07-01T10:00:00+0000",
            "comments": {"summary": {"total_count": 0}},
            "shares": {"count": 0},
        }
    ]
    cliente_falso.obtener_insights_post.return_value = {}
    cliente_falso.obtener_media_ig.return_value = [
        {
            "id": "media_1",
            "caption": "post ig",
            "media_type": "IMAGE",
            "media_product_type": "FEED",
            "timestamp": "2026-07-02T10:00:00+0000",
            "like_count": 1,
            "comments_count": 0,
        }
    ]
    cliente_falso.obtener_insights_media.return_value = {}

    conector = MetaOrganicoConnector(
        config, access_token="fake", api_version="v21.0", cliente=cliente_falso
    )

    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    # 1 post de FB + 2 perfiles IG con 1 media cada uno = 3 registros
    assert len(registros) == 3
    assert cliente_falso.obtener_media_ig.call_count == 2


def test_agregar_un_perfil_mas_no_requiere_tocar_el_conector():
    """Prueba de arquitectura: el conector no tiene ninguna referencia a IDs
    de perfil concretos; agregar el 14vo perfil es solo config."""
    config = MetaOrganicoConfig(
        perfiles=[
            PerfilMetaOrganico(id=f"p{i}", nombre=f"Perfil {i}", red=Red.INSTAGRAM, ig_user_id=f"ig_{i}")
            for i in range(14)
        ]
    )
    cliente_falso = MagicMock()
    cliente_falso.obtener_nombre_cuenta_ig.return_value = "cuenta.ig"
    cliente_falso.obtener_media_ig.return_value = []

    conector = MetaOrganicoConnector(
        config, access_token="fake", api_version="v21.0", cliente=cliente_falso
    )
    conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert cliente_falso.obtener_media_ig.call_count == 14


def test_fetch_facebook_usa_el_token_de_pagina_no_el_del_sistema():
    """Caso real de QA: Meta exige un token propio de la Página para leer
    /posts. El conector debe intercambiar el token antes de pedir posts/insights."""
    config = MetaOrganicoConfig(
        perfiles=[PerfilMetaOrganico(id="p1", nombre="Perfil FB", red=Red.FACEBOOK, page_id="page_1")]
    )
    cliente_falso = MagicMock()
    cliente_falso.obtener_nombre_pagina.return_value = "Página FB"
    cliente_falso.obtener_token_de_pagina.return_value = "token-de-pagina"
    cliente_falso.obtener_posts_pagina.return_value = [
        {
            "id": "post_1",
            "message": "hola",
            "created_time": "2026-07-01T10:00:00+0000",
            "comments": {"summary": {"total_count": 0}},
            "shares": {"count": 0},
        }
    ]
    cliente_falso.obtener_insights_post.return_value = {}

    conector = MetaOrganicoConnector(
        config, access_token="token-sistema", api_version="v21.0", cliente=cliente_falso
    )
    conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    cliente_falso.obtener_token_de_pagina.assert_called_once_with("page_1")
    _, kwargs_posts = cliente_falso.obtener_posts_pagina.call_args
    assert kwargs_posts["token"] == "token-de-pagina"
    _, kwargs_insights = cliente_falso.obtener_insights_post.call_args
    assert kwargs_insights["token"] == "token-de-pagina"


def test_un_perfil_con_id_invalido_no_bloquea_a_los_demas():
    """Caso real: 13 perfiles cargados de una — si uno tiene un ID mal
    tipeado o un permiso faltante, los otros 12 se tienen que guardar igual."""
    config = MetaOrganicoConfig(
        perfiles=[
            PerfilMetaOrganico(id="p1", nombre="Perfil OK 1", red=Red.INSTAGRAM, ig_user_id="ig_1"),
            PerfilMetaOrganico(id="p2", nombre="Perfil Roto", red=Red.INSTAGRAM, ig_user_id="ig_malo"),
            PerfilMetaOrganico(id="p3", nombre="Perfil OK 2", red=Red.INSTAGRAM, ig_user_id="ig_3"),
        ]
    )

    cliente_falso = MagicMock()
    cliente_falso.obtener_nombre_cuenta_ig.return_value = "cuenta.ig"

    def media_ig_con_un_perfil_roto(ig_user_id, desde, hasta):
        if ig_user_id == "ig_malo":
            raise RuntimeError("permiso denegado")
        return [
            {
                "id": f"media_{ig_user_id}",
                "caption": "post",
                "media_type": "IMAGE",
                "media_product_type": "FEED",
                "timestamp": "2026-07-02T10:00:00+0000",
                "like_count": 1,
                "comments_count": 0,
            }
        ]

    cliente_falso.obtener_media_ig.side_effect = media_ig_con_un_perfil_roto
    cliente_falso.obtener_insights_media.return_value = {}

    conector = MetaOrganicoConnector(
        config, access_token="fake", api_version="v21.0", cliente=cliente_falso
    )

    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    # los 2 perfiles buenos se guardan igual, el roto simplemente no aporta datos
    assert len(registros) == 2
    assert {r.perfil for r in registros} == {"Perfil OK 1", "Perfil OK 2"}


def test_todos_los_perfiles_fallidos_lanza_error():
    config = MetaOrganicoConfig(
        perfiles=[
            PerfilMetaOrganico(id="p1", nombre="Perfil Roto 1", red=Red.INSTAGRAM, ig_user_id="ig_1"),
            PerfilMetaOrganico(id="p2", nombre="Perfil Roto 2", red=Red.INSTAGRAM, ig_user_id="ig_2"),
        ]
    )
    cliente_falso = MagicMock()
    cliente_falso.obtener_nombre_cuenta_ig.side_effect = RuntimeError("token inválido")

    conector = MetaOrganicoConnector(
        config, access_token="fake", api_version="v21.0", cliente=cliente_falso
    )

    with pytest.raises(RuntimeError, match="Todos los perfiles"):
        conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))
