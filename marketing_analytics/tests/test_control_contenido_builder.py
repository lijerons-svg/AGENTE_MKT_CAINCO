import datetime

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.dashboard.control_contenido.builder import generar_control_contenido
from marketing_analytics.database.repository import upsert_meta_organico
from marketing_analytics.models.records import MetaOrganicoPost

_CONFIG = AppConfig.model_validate(
    {
        "mailchimp": {"server_prefix": "us21", "enabled": False},
        "meta": {
            "organico": {
                "perfiles": [
                    {
                        "id": "p1",
                        "nombre": "Academy Cainco",
                        "unidad": "Academy Cainco",
                        "alias_pauta": "ACADEMY",
                        "red": "facebook",
                        "page_id": "1",
                    }
                ]
            }
        },
    }
)


def test_genera_html_con_datos_embebidos(conn, tmp_path):
    upsert_meta_organico(
        conn,
        [
            MetaOrganicoPost(
                perfil="Academy Cainco",
                pagina="Academy Cainco",
                red="facebook",
                fecha_publicacion=datetime.date(2026, 7, 1),
                tipo="imagen",
                alcance=500,
                id_publicacion_origen="post_1",
            )
        ],
    )

    ruta = generar_control_contenido(
        conn, _CONFIG, tmp_path / "ControlContenido.html", generado_en=datetime.datetime(2026, 7, 22)
    )

    html = ruta.read_text(encoding="utf-8")
    assert "Control de Contenido" in html
    assert "Academy Cainco" in html
    assert "__DATOS_CONTROL_CONTENIDO_JSON__" not in html
    assert "__CSS_CONTROL_CONTENIDO__" not in html
    assert "__JS_CONTROL_CONTENIDO__" not in html


def test_con_base_vacia_no_falla(conn, tmp_path):
    ruta = generar_control_contenido(conn, _CONFIG, tmp_path / "ControlContenido.html")

    assert ruta.exists()
