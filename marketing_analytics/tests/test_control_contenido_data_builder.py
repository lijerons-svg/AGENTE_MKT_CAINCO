import datetime

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.dashboard.control_contenido.data_builder import (
    construir_datos_control_contenido,
)
from marketing_analytics.database.repository import (
    upsert_calendario_publicaciones,
    upsert_control_perfiles,
    upsert_mailchimp_campanas,
    upsert_mailchimp_enlaces_whatsapp,
    upsert_meta_ads,
    upsert_meta_organico,
)
from marketing_analytics.models.records import (
    CalendarioPublicacion,
    ControlPerfilMensual,
    MailchimpCampana,
    MailchimpEnlaceWhatsapp,
    MetaAdsRegistro,
    MetaOrganicoPost,
)

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
                    },
                    {
                        "id": "p2",
                        "nombre": "CAINCO",
                        "unidad": "CAINCO",
                        "alias_pauta": "CAINCO",
                        "red": "facebook",
                        "page_id": "2",
                    },
                    {
                        "id": "p3",
                        "nombre": "Cainco Bolivia (IG)",
                        "unidad": "Cainco Bolivia",
                        "red": "instagram",
                        "ig_user_id": "3",
                    },
                ]
            }
        },
    }
)


def test_perfiles_quedan_agrupados_por_unidad(conn):
    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert set(datos["unidades"].keys()) == {"Academy Cainco", "CAINCO", "Cainco Bolivia"}
    assert datos["unidades"]["Academy Cainco"]["perfiles"] == [
        {"nombre": "Academy Cainco", "red": "facebook"}
    ]


def test_meta_organico_va_a_la_unidad_de_su_perfil(conn):
    upsert_meta_organico(
        conn,
        [
            MetaOrganicoPost(
                perfil="Academy Cainco",
                pagina="Academy Cainco",
                red="facebook",
                fecha_publicacion=datetime.date(2026, 7, 1),
                tipo="imagen",
                id_publicacion_origen="post_1",
            )
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert len(datos["unidades"]["Academy Cainco"]["meta_organico"]) == 1
    assert datos["unidades"]["CAINCO"]["meta_organico"] == []


def test_meta_ads_matchea_por_alias_de_la_campana(conn):
    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="act_1",
                perfil_unidad="Cuenta X",
                red="facebook",
                campana="ENERO 2026 - ACADEMY - CURSO",
                fecha_publicacion=datetime.date(2026, 1, 1),
                objetivo="TRAFFIC",
                moneda="BOB",
                id_campana_origen="camp_1",
            ),
            MetaAdsRegistro(
                cuenta_publicitaria="act_1",
                perfil_unidad="Cuenta X",
                red="facebook",
                campana="CAMPAÑA SIN MARCA RECONOCIBLE",
                fecha_publicacion=datetime.date(2026, 1, 2),
                objetivo="TRAFFIC",
                moneda="BOB",
                id_campana_origen="camp_2",
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert len(datos["unidades"]["Academy Cainco"]["meta_ads"]) == 1
    assert datos["unidades"]["Academy Cainco"]["meta_ads"][0]["campana"] == "ENERO 2026 - ACADEMY - CURSO"
    # la campaña sin marca reconocible no se le asigna a ninguna unidad
    assert all(
        "SIN MARCA" not in c["campana"]
        for u in datos["unidades"].values()
        for c in u["meta_ads"]
    )


def test_meta_ads_sin_alias_matchea_por_pagina_origen_del_boost(conn):
    """Una campaña de "Promocionar" (boost de un post) le pone a la campaña
    un nombre automático que no menciona ninguna unidad — se ubica por la
    página de origen del post en vez de perderse."""
    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="act_1",
                perfil_unidad="Cuenta X",
                red="facebook",
                campana="Boosted post: Hoy da inicio la Rueda de Negocios",
                fecha_publicacion=datetime.date(2026, 9, 1),
                objetivo="TRAFFIC",
                moneda="BOB",
                id_campana_origen="camp_boost",
                pagina_origen_id="2",
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert len(datos["unidades"]["CAINCO"]["meta_ads"]) == 1
    assert datos["unidades"]["Academy Cainco"]["meta_ads"] == []


def test_meta_ads_sin_alias_ni_pagina_conocida_sigue_sin_asignarse(conn):
    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="act_1",
                perfil_unidad="Cuenta X",
                red="facebook",
                campana="Boosted post: algo genérico",
                fecha_publicacion=datetime.date(2026, 9, 1),
                objetivo="TRAFFIC",
                moneda="BOB",
                id_campana_origen="camp_boost_2",
                pagina_origen_id="999999",
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert all(u["meta_ads"] == [] for u in datos["unidades"].values())


def test_calendario_matchea_por_bu(conn):
    upsert_calendario_publicaciones(
        conn,
        [
            CalendarioPublicacion(
                id_origen="1",
                fecha_publicacion=datetime.date(2026, 1, 1),
                perfil="CAINCO",
                bu="Academy",
                campana_evento="ENERO 2026 - ACADEMY - CURSO",
                estado="Publicado",
            )
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert len(datos["unidades"]["Academy Cainco"]["calendario"]) == 1


def test_control_perfiles_suma_facebook_e_instagram_de_la_misma_unidad(conn):
    upsert_control_perfiles(
        conn,
        [
            ControlPerfilMensual(
                perfil="CAINCO", red="facebook", anio_mes="2026-07", seguidores=1000,
                seguidores_ganados=10, publicaciones_mes=5, likes_mes=50,
                visualizaciones_mes=500, comentarios_mes=20, compartidos_mes=5,
                interacciones_mes=75,
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)
    filas = datos["unidades"]["CAINCO"]["control_perfiles"]

    assert len(filas) == 1
    assert filas[0]["seguidores"] == 1000
    assert filas[0]["tasa_engagement"] == 0.075


def test_control_perfiles_red_conserva_el_desglose_sin_sumar(conn):
    """Las donas Facebook vs. Instagram del dashboard necesitan el dato
    por red, sin sumar entre perfiles de la misma unidad."""
    upsert_control_perfiles(
        conn,
        [
            ControlPerfilMensual(
                perfil="CAINCO", red="facebook", anio_mes="2026-07", seguidores=1000,
                seguidores_ganados=10, publicaciones_mes=5, likes_mes=50,
                visualizaciones_mes=500, comentarios_mes=20, compartidos_mes=5,
                interacciones_mes=75,
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)
    filas_red = datos["unidades"]["CAINCO"]["control_perfiles_red"]

    assert len(filas_red) == 1
    assert filas_red[0]["red"] == "facebook"
    assert filas_red[0]["seguidores"] == 1000
    assert filas_red[0]["tasa_engagement"] == 0.075


def test_mailchimp_es_global_e_incluye_clics_whatsapp(conn):
    """Mailchimp no se liga a ninguna unidad (decisión de la usuaria): va
    aparte, a nivel raíz, con los clics a wa.me ya sumados por campaña."""
    upsert_mailchimp_campanas(
        conn,
        [
            MailchimpCampana(
                id_campana_origen="camp_1", nombre_campana="Newsletter Julio",
                fecha_envio=datetime.date(2026, 7, 1), destinatarios=1000, entregas=980,
                tasa_apertura=0.3, aperturas_unicas=294, aperturas_totales=350,
                tasa_clics=0.05, clics_unicos=49, clics_totales=60, bajas=3,
            ),
        ],
    )
    upsert_mailchimp_enlaces_whatsapp(
        conn,
        [MailchimpEnlaceWhatsapp(id_campana_origen="camp_1", url="https://wa.me/123", clics=12)],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)

    assert len(datos["mailchimp"]) == 1
    assert datos["mailchimp"][0]["nombre_campana"] == "Newsletter Julio"
    assert datos["mailchimp"][0]["clics_whatsapp"] == 12
