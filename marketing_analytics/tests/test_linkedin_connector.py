import datetime
from unittest.mock import MagicMock

import pytest

from marketing_analytics.config.schema import LinkedInConfig
from marketing_analytics.connectors.linkedin.connector import LinkedInConnector


def _config() -> LinkedInConfig:
    return LinkedInConfig(enabled=True, organization_id="1592889", nombre="CAINCO")


def test_fetch_mapea_cada_post_con_sus_estadisticas():
    cliente_falso = MagicMock()
    cliente_falso.obtener_posts.return_value = [
        {"id": "urn:li:share:1", "publishedAt": 1793798107270, "commentary": "Post 1"},
        {"id": "urn:li:ugcPost:2", "publishedAt": 1793798107270, "commentary": "Post 2"},
    ]
    cliente_falso.obtener_estadisticas_post.return_value = {"totalShareStatistics": {"likeCount": 3}}

    conector = LinkedInConnector(_config(), access_token="fake", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert len(registros) == 2
    assert {r.pagina for r in registros} == {"CAINCO"}
    assert cliente_falso.obtener_estadisticas_post.call_count == 2


def test_fetch_usa_organization_id_configurado():
    cliente_falso = MagicMock()
    cliente_falso.obtener_posts.return_value = []

    conector = LinkedInConnector(_config(), access_token="fake", cliente=cliente_falso)
    conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    cliente_falso.obtener_posts.assert_called_once_with("1592889", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))


def test_un_post_con_estadisticas_rotas_no_bloquea_a_los_demas():
    cliente_falso = MagicMock()
    cliente_falso.obtener_posts.return_value = [
        {"id": "urn:li:share:bueno_1", "publishedAt": 1793798107270, "commentary": "ok"},
        {"id": "urn:li:share:malo", "publishedAt": 1793798107270, "commentary": "falla"},
        {"id": "urn:li:share:bueno_2", "publishedAt": 1793798107270, "commentary": "ok"},
    ]

    def estadisticas_con_una_rota(organization_id, post_id):
        if post_id == "urn:li:share:malo":
            raise RuntimeError("timeout")
        return {}

    cliente_falso.obtener_estadisticas_post.side_effect = estadisticas_con_una_rota

    conector = LinkedInConnector(_config(), access_token="fake", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert len(registros) == 2
    assert {r.id_publicacion_origen for r in registros} == {"urn:li:share:bueno_1", "urn:li:share:bueno_2"}


def test_todos_los_posts_fallidos_lanza_error():
    cliente_falso = MagicMock()
    cliente_falso.obtener_posts.return_value = [
        {"id": "urn:li:share:1", "publishedAt": 1793798107270, "commentary": ""},
    ]
    cliente_falso.obtener_estadisticas_post.side_effect = RuntimeError("token inválido")

    conector = LinkedInConnector(_config(), access_token="fake", cliente=cliente_falso)

    with pytest.raises(RuntimeError, match="Todos los posts"):
        conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))


def test_sin_posts_no_falla():
    cliente_falso = MagicMock()
    cliente_falso.obtener_posts.return_value = []

    conector = LinkedInConnector(_config(), access_token="fake", cliente=cliente_falso)
    registros = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert registros == []
