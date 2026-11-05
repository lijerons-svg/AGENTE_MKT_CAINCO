import datetime
import json

from marketing_analytics.dashboard.builder import generar_dashboard
from marketing_analytics.dashboard.data_builder import construir_datos_dashboard
from marketing_analytics.database.repository import (
    upsert_mailchimp_campanas,
    upsert_meta_ads,
    upsert_meta_organico,
)
from marketing_analytics.models.records import (
    MailchimpCampana,
    MetaAdsRegistro,
    MetaOrganicoPost,
)


def _poblar(conn):
    upsert_meta_organico(
        conn,
        [
            MetaOrganicoPost(
                perfil="Marca X - Instagram",
                pagina="marcax.oficial",
                red="instagram",
                fecha_publicacion=datetime.date(2026, 7, 1),
                tipo="IMAGE",
                descripcion="Post",
                alcance=900,
                visualizaciones=0,
                total_clics=0,
                clics_enlace=0,
                reacciones=100,
                comentarios=10,
                compartidos=4,
                total_interacciones=114,
                id_publicacion_origen="media_1",
            )
        ],
    )
    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="123",
                perfil_unidad="Cuenta Principal",
                red="facebook",
                campana="Campaña Julio",
                fecha_publicacion=datetime.date(2026, 7, 1),
                objetivo="OUTCOME_TRAFFIC",
                moneda="BOB",
                importe_gastado=10.5,
                alcance=1000,
                impresiones=1500,
                clics=30,
                ctr=2.0,
                cpc=0.35,
                resultados=25,
                id_campana_origen="camp_1",
            )
        ],
    )
    upsert_mailchimp_campanas(
        conn,
        [
            MailchimpCampana(
                id_campana_origen="mc_1",
                nombre_campana="Newsletter Julio",
                fecha_envio=datetime.date(2026, 7, 1),
                destinatarios=1000,
                entregas=992,
                tasa_apertura=0.35,
                aperturas_unicas=300,
                aperturas_totales=450,
                tasa_clics=0.05,
                clics_unicos=40,
                clics_totales=60,
                tasa_rebote=0.008,
                rebotes=8,
                bajas=2,
            )
        ],
    )


def test_construir_datos_dashboard_refleja_la_base(conn):
    _poblar(conn)
    datos = construir_datos_dashboard(conn)

    assert len(datos["meta_organico"]) == 1
    assert datos["meta_organico"][0]["perfil"] == "Marca X - Instagram"
    assert len(datos["meta_ads"]) == 1
    assert datos["meta_ads"][0]["moneda"] == "BOB"
    assert len(datos["mailchimp"]) == 1
    assert datos["linkedin"] == []


def _extraer_json_embebido(html: str) -> dict:
    inicio = html.index("const DATA = ") + len("const DATA = ")
    fin = html.index(";\n\nconst COLOR", inicio)
    return json.loads(html[inicio:fin])


def test_generar_dashboard_incrusta_json_valido_y_secciones_clave(conn, tmp_path):
    _poblar(conn)

    ruta = generar_dashboard(conn, tmp_path / "Dashboard.html")
    html = ruta.read_text(encoding="utf-8")

    assert "Comparativo Meta vs LinkedIn" in html
    assert "Top publicaciones" in html
    assert "Top campañas" in html
    assert "Top perfiles" in html
    assert "cdn.plot.ly" in html
    assert "__DATOS_DASHBOARD_JSON__" not in html
    assert "Bootstrap" not in html

    datos = _extraer_json_embebido(html)
    assert len(datos["meta_organico"]) == 1
    assert datos["meta_ads"][0]["campana"] == "Campaña Julio"
    assert "generado_en" in datos


def test_generar_dashboard_con_base_vacia_no_falla(conn, tmp_path):
    ruta = generar_dashboard(conn, tmp_path / "Dashboard.html")
    html = ruta.read_text(encoding="utf-8")

    assert "Dashboard de Marketing" in html
    datos = _extraer_json_embebido(html)
    assert datos["meta_organico"] == []
    assert datos["meta_ads"] == []
    assert datos["mailchimp"] == []
    assert datos["linkedin"] == []


def test_generar_dashboard_falla_si_falta_el_marcador(conn, tmp_path, monkeypatch):
    import marketing_analytics.dashboard.builder as builder_mod

    monkeypatch.setattr(builder_mod, "_MARCADOR_DATOS", "__NO_EXISTE__")

    try:
        generar_dashboard(conn, tmp_path / "Dashboard.html")
        assert False, "debería haber lanzado ValueError"
    except ValueError as error:
        assert "marcador" in str(error)
