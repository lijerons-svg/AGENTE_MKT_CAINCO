"""Prueba de integración: los datos que arma `construir_datos_control_contenido`
(el mismo builder que usa el dashboard) tienen que poder alimentar
`generar_pptx_unidad` sin romper. Existe porque un bug real (usar el balde
sumado `control_perfiles` en vez del desglosado `control_perfiles_red`) solo
se veía corriendo el pipeline completo, no con fixtures a mano en
test_reports_pptx_generador.py."""
from __future__ import annotations

import datetime

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.dashboard.control_contenido.data_builder import (
    construir_datos_control_contenido,
)
from marketing_analytics.database.repository import (
    upsert_control_perfiles,
    upsert_meta_ads,
    upsert_meta_organico,
)
from marketing_analytics.models.records import (
    ControlPerfilMensual,
    MetaAdsRegistro,
    MetaOrganicoPost,
)
from marketing_analytics.reports_pptx.generador import generar_pptx_unidad

_CONFIG = AppConfig.model_validate(
    {
        "mailchimp": {"server_prefix": "us21", "enabled": False},
        "meta": {
            "organico": {
                "perfiles": [
                    {"id": "p1", "nombre": "Academy FB", "unidad": "Academy Cainco", "alias_pauta": "ACADEMY", "red": "facebook", "page_id": "1"},
                    {"id": "p2", "nombre": "Academy IG", "unidad": "Academy Cainco", "alias_pauta": "ACADEMY", "red": "instagram", "ig_user_id": "2"},
                ]
            }
        },
    }
)


def test_pipeline_real_hasta_generar_pptx_sin_romper(conn, tmp_path):
    upsert_meta_organico(
        conn,
        [
            MetaOrganicoPost(
                perfil="Academy FB", pagina="Academy FB", red="facebook",
                fecha_publicacion=datetime.date(2026, 8, 3), tipo="imagen",
                descripcion="Post de prueba", visualizaciones=1000, total_interacciones=80,
                total_clics=10, comentarios=3, compartidos=2, id_publicacion_origen="post1",
            ),
        ],
    )
    upsert_control_perfiles(
        conn,
        [
            ControlPerfilMensual(perfil="Academy FB", red="facebook", anio_mes="2026-08", seguidores=1000, publicaciones_mes=1, visualizaciones_mes=1000, interacciones_mes=80),
            ControlPerfilMensual(perfil="Academy IG", red="instagram", anio_mes="2026-08", seguidores=2000, publicaciones_mes=0, visualizaciones_mes=0, interacciones_mes=0),
        ],
    )
    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="act_1", perfil_unidad="Academy Cainco", red="facebook",
                campana="ACADEMY - test", fecha_publicacion=datetime.date(2026, 8, 4),
                objetivo="OUTCOME_TRAFFIC", moneda="BOB", importe_gastado=50.0, alcance=4000,
                impresiones=10000, clics=100, ctr=1.0, cpc=0.5, resultados=20,
                id_campana_origen="camp1",
            ),
        ],
    )

    datos = construir_datos_control_contenido(conn, _CONFIG)
    balde = datos["unidades"]["Academy Cainco"]

    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=balde["meta_organico"],
        filas_control_perfiles=balde["control_perfiles_red"],
        filas_ads=balde["meta_ads"],
        carpeta_imagenes_tmp=tmp_path,
    )
    # Portada + KPIs + campañas + top4 + detalle = 5 (sin competencia, sin
    # mejora porque solo hay un post)
    assert len(constructor.prs.slides._sldIdLst) >= 4
