import datetime

import openpyxl

from marketing_analytics.database.ejecuciones import finalizar_ejecucion, iniciar_ejecucion
from marketing_analytics.database.repository import (
    ResultadoUpsert,
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
from marketing_analytics.reports.excel_builder import generar_historico_excel


def _poblar_datos_de_prueba(conn):
    upsert_meta_organico(
        conn,
        [
            MetaOrganicoPost(
                perfil="Marca X - Instagram",
                pagina="marcax.oficial",
                red="instagram",
                fecha_publicacion=datetime.date(2026, 7, 1),
                tipo="IMAGE",
                descripcion="Post de prueba",
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
                conversaciones_iniciadas=3,
                fecha_inicio_campana=datetime.date(2026, 7, 1),
                fecha_fin_campana=datetime.date(2026, 7, 31),
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
    upsert_mailchimp_enlaces_whatsapp(
        conn,
        [MailchimpEnlaceWhatsapp(id_campana_origen="mc_1", url="https://wa.me/59171234567", clics=12)],
    )
    upsert_calendario_publicaciones(
        conn,
        [
            CalendarioPublicacion(
                id_origen="1",
                fecha_publicacion=datetime.date(2026, 7, 1),
                perfil="Marca X - Instagram",
                bu="Marketing",
                campana_evento="Campaña Julio",
                tipo="Post",
                canal="Instagram",
                formato="Imagen",
                objetivo="Awareness",
                descripcion_copy="Copy de prueba",
                estado="Aprobado",
                responsable="Sandy",
                inversion_usd=50.0,
                link_publicacion="",
                vobo_gcri="Si",
                notas="",
            )
        ],
    )
    upsert_control_perfiles(
        conn,
        [
            ControlPerfilMensual(
                perfil="Marca X - Instagram",
                red="instagram",
                anio_mes="2026-07",
                seguidores=1000,
                seguidores_ganados=50,
                publicaciones_mes=1,
                likes_mes=100,
                visualizaciones_mes=0,
                comentarios_mes=10,
                compartidos_mes=4,
                interacciones_mes=114,
                tasa_engagement=0.114,
            )
        ],
    )

    ejecucion_id = iniciar_ejecucion(conn)
    finalizar_ejecucion(
        conn, ejecucion_id, ResultadoUpsert(nuevos=3, actualizados=0, descartados=0), "exitoso"
    )


def test_genera_las_7_hojas_requeridas_con_datos_correctos(conn, tmp_path):
    _poblar_datos_de_prueba(conn)

    ruta = generar_historico_excel(conn, tmp_path / "Historico_RRSS.xlsx")
    wb = openpyxl.load_workbook(ruta)

    assert wb.sheetnames == [
        "META ORGANICO", "CONTROL PERFILES", "META ADS", "MAILCHIMP", "CALENDARIO",
        "LINKEDIN", "LOG",
    ]

    hoja_organico = wb["META ORGANICO"]
    assert hoja_organico["A1"].value == "Perfil"
    assert hoja_organico["A2"].value == "Marca X - Instagram"

    hoja_control_perfiles = wb["CONTROL PERFILES"]
    assert hoja_control_perfiles["A1"].value == "Perfil"
    assert hoja_control_perfiles["C2"].value == "2026-07"
    assert hoja_control_perfiles["D2"].value == 1000
    assert hoja_control_perfiles["E2"].value == 50
    # "Tasa de engagement" se guarda como fracción (0.114) pero con formato
    # de Excel para que se lea "11.40%", no "0.114" a secas.
    assert hoja_control_perfiles["L2"].value == 0.114
    assert hoja_control_perfiles["L2"].number_format == "0.00%"

    hoja_ads = wb["META ADS"]
    assert hoja_ads["D2"].value == "Campaña Julio"
    assert hoja_ads["E2"].value == "camp_1"  # ID Campaña
    assert hoja_ads["H2"].value == "BOB"
    assert hoja_ads["I2"].value == 10.5
    assert hoja_ads["S1"].value == "Conversación iniciada"
    assert hoja_ads["S2"].value == 3
    assert hoja_ads["T1"].value == "Fecha inicio (campaña)"
    assert hoja_ads["T2"].value == "2026-07-01"
    assert hoja_ads["U1"].value == "Fecha fin (campaña)"
    assert hoja_ads["U2"].value == "2026-07-31"

    hoja_mailchimp = wb["MAILCHIMP"]
    assert hoja_mailchimp["N2"].value == 12  # Clics WhatsApp
    assert "wa.me" in hoja_mailchimp["O2"].value  # Detalle enlaces WhatsApp
    # Tasa apertura (E), tasa clics (H) y tasa rebote (K): mismo caso.
    assert hoja_mailchimp["E2"].value == 0.35
    assert hoja_mailchimp["E2"].number_format == "0.00%"
    assert hoja_mailchimp["H2"].number_format == "0.00%"
    assert hoja_mailchimp["K2"].number_format == "0.00%"

    hoja_calendario = wb["CALENDARIO"]
    assert hoja_calendario["A1"].value == "ID"
    assert hoja_calendario["E2"].value == "Campaña Julio"
    assert hoja_calendario["M2"].value == 50.0

    hoja_linkedin = wb["LINKEDIN"]
    assert hoja_linkedin["A1"].value == "Página"
    assert hoja_linkedin.max_row == 1  # sin conector activo, solo encabezado

    hoja_log = wb["LOG"]
    assert hoja_log["A1"].value == "ID Ejecución"
    assert hoja_log["E2"].value == "exitoso"


def test_excel_con_base_vacia_no_falla_solo_quedan_encabezados(conn, tmp_path):
    ruta = generar_historico_excel(conn, tmp_path / "Historico_RRSS.xlsx")
    wb = openpyxl.load_workbook(ruta)

    for nombre_hoja in wb.sheetnames:
        assert wb[nombre_hoja].max_row == 1


def test_meta_ads_muestra_unidad_por_texto_y_por_pagina_de_origen(conn, tmp_path):
    """Caso real de QA: el nombre de una campaña no siempre identifica bien
    la unidad (errores de tipeo, palabras de formato compartidas como
    "foro"), así que el Excel debe poder mostrar, lado a lado, a qué unidad
    la manda el texto de la campaña y a qué unidad pertenece realmente la
    página/cuenta de origen del anuncio — un dato duro, no adivinado."""
    from marketing_analytics.config.schema import (
        AppConfig,
        MailchimpConfig,
        MetaConfig,
        MetaOrganicoConfig,
        PerfilMetaOrganico,
    )

    config = AppConfig(
        mailchimp=MailchimpConfig(server_prefix="us1"),
        meta=MetaConfig(
            organico=MetaOrganicoConfig(
                perfiles=[
                    PerfilMetaOrganico(
                        id="icc", nombre="ICC Bolivia", red="facebook", page_id="111",
                        alias_pauta="ICC",
                    ),
                    PerfilMetaOrganico(
                        id="fundare", nombre="Fundares Santa Cruz", red="facebook", page_id="222",
                        alias_pauta="FUNDARE",
                    ),
                ]
            )
        ),
    )

    upsert_meta_ads(
        conn,
        [
            MetaAdsRegistro(
                cuenta_publicitaria="999", perfil_unidad="Cuenta compartida", red="facebook",
                campana="OCTUBRE 2026 - FORO ICC LABOR & TALENT", fecha_publicacion=datetime.date(2026, 10, 16),
                objetivo="OUTCOME_TRAFFIC", moneda="BOB", importe_gastado=50.0, id_campana_origen="camp_icc",
            ),
            MetaAdsRegistro(
                cuenta_publicitaria="999", perfil_unidad="Cuenta compartida", red="facebook",
                campana="Boost automático 04112026", fecha_publicacion=datetime.date(2026, 10, 20),
                objetivo="OUTCOME_TRAFFIC", moneda="BOB", importe_gastado=30.0, id_campana_origen="camp_boost",
                pagina_origen_id="222",
            ),
        ],
    )

    ruta = generar_historico_excel(conn, tmp_path / "Historico_RRSS.xlsx", config)
    wb = openpyxl.load_workbook(ruta)
    hoja_ads = wb["META ADS"]

    assert hoja_ads["P1"].value == "Unidad (por nombre de campaña)"
    assert hoja_ads["Q1"].value == "Unidad (por página de origen)"
    assert hoja_ads["R1"].value == "ID página/cuenta de origen"

    # Fila 1 de datos: emparejada por el texto de la campaña ("ICC").
    assert hoja_ads["P2"].value == "ICC Bolivia"
    assert hoja_ads["Q2"].value is None

    # Fila 2: nombre automático de boost, sin texto reconocible — se
    # identifica por la página real de origen.
    assert hoja_ads["P3"].value is None
    assert hoja_ads["Q3"].value == "Fundares Santa Cruz"
    assert hoja_ads["R3"].value == "222"
