import datetime

from marketing_analytics.connectors.linkedin.mapper import mapear_post

# Formas reales de /rest/posts, vistas en una corrida de prueba contra la
# API real (ver connectors/linkedin/probar_api.py).
_POST_CON_DOCUMENTO = {
    "id": "urn:li:ugcPost:7523779688557821953",
    "createdAt": 1793808863102,
    "publishedAt": 1793809803215,
    "commentary": "Fintech Summit Bolivia 2026",
    "content": {"media": {"title": "Panel", "id": "urn:li:document:D4D1FAQHqM3OObXRNIA"}},
}
_POST_CON_VIDEO = {
    "id": "urn:li:ugcPost:7523734389189672960",
    "createdAt": 1793798062815,
    "publishedAt": 1793798107270,
    "commentary": "CAINCO y Bolivia, presentes en el XVI Encuentro Empresarial Iberoamericano.",
    "content": {"media": {"id": "urn:li:video:D4D05AQGAsKO-KiIkng"}},
}
_POST_SIN_MEDIA = {
    "id": "urn:li:share:111",
    "publishedAt": 1793798107270,
    "commentary": "Solo texto, sin imagen ni video.",
}


def test_mapear_post_con_documento_adjunto():
    registro = mapear_post("CAINCO", _POST_CON_DOCUMENTO, {})

    assert registro.pagina == "CAINCO"
    assert registro.tipo == "document"
    assert registro.descripcion == "Fintech Summit Bolivia 2026"
    assert registro.id_publicacion_origen == "urn:li:ugcPost:7523779688557821953"
    assert registro.fecha_publicacion == datetime.datetime.fromtimestamp(
        1793809803215 / 1000, tz=datetime.timezone.utc
    ).date()


def test_mapear_post_con_video_adjunto():
    registro = mapear_post("CAINCO", _POST_CON_VIDEO, {})
    assert registro.tipo == "video"


def test_mapear_post_sin_media_es_texto():
    registro = mapear_post("CAINCO", _POST_SIN_MEDIA, {})
    assert registro.tipo == "texto"


def test_mapear_post_usa_createdat_si_no_hay_publishedat():
    post = {"id": "urn:li:share:222", "createdAt": 1793798062815, "commentary": ""}
    registro = mapear_post("CAINCO", post, {})
    assert registro.fecha_publicacion == datetime.datetime.fromtimestamp(
        1793798062815 / 1000, tz=datetime.timezone.utc
    ).date()


def test_mapear_post_con_estadisticas_completas():
    estadisticas = {
        "totalShareStatistics": {
            "impressionCount": 1000,
            "uniqueImpressionsCount": 800,
            "clickCount": 30,
            "likeCount": 50,
            "commentCount": 5,
            "shareCount": 3,
        }
    }
    registro = mapear_post("CAINCO", _POST_SIN_MEDIA, estadisticas)

    assert registro.impresiones == 1000
    assert registro.alcance == 800
    assert registro.clics == 30
    assert registro.reacciones == 50
    assert registro.comentarios == 5
    assert registro.compartidos == 3
    assert registro.interacciones == 58  # 50 + 5 + 3


def test_mapear_post_sin_estadisticas_no_inventa_valores():
    """Nota honesta del propio mapper: si la respuesta de estadísticas viene
    vacía (falló la llamada, o cambió el formato), todo queda en 0 — nunca
    se inventa un número."""
    registro = mapear_post("CAINCO", _POST_SIN_MEDIA, {})

    assert registro.impresiones == 0
    assert registro.alcance == 0
    assert registro.clics == 0
    assert registro.reacciones == 0
    assert registro.comentarios == 0
    assert registro.compartidos == 0
    assert registro.interacciones == 0
