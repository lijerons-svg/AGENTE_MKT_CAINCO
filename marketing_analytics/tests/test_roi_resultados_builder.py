import datetime
import tempfile
from pathlib import Path

import openpyxl
import pytest

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas
from marketing_analytics.reports.roi_resultados_builder import generar_roi_resultados

_ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total", "Nombre de evento", "Tipo", "Unidad"]
_ENCABEZADOS_RESUMEN = [
    "Nombre de evento", "Tipo", "Unidad", "Inversión total", "Leads", "Subscribers", "Revenue",
    "Costo por lead", "% de conversión", "ROI",
]


def _registro(fecha, red, importe, campana="Campaña Julio", id_campana="camp_1", fecha_inicio_campana=None):
    return MetaAdsRegistro(
        cuenta_publicitaria="123",
        perfil_unidad="CAINCO",
        red=red,
        campana=campana,
        fecha_publicacion=fecha,
        objetivo="OUTCOME_TRAFFIC",
        moneda="BOB",
        importe_gastado=importe,
        alcance=100,
        impresiones=200,
        clics=5,
        ctr=0.025,
        cpc=2.1,
        resultados=1,
        id_campana_origen=id_campana,
        fecha_inicio_campana=fecha_inicio_campana,
    )


def _rutas():
    carpeta = Path(tempfile.mkdtemp())
    return carpeta / "ROI_Campanas.xlsx", carpeta / "ROI_Resultados.xlsx"


def _asignar_evento(ws, id_campana, nombre_evento, tipo=None, unidad=None):
    for fila in ws.iter_rows(min_row=2):
        if fila[2].value == id_campana:
            fila[4].value = nombre_evento
            if tipo is not None:
                fila[5].value = tipo
            if unidad is not None:
                fila[6].value = unidad


def test_sin_archivo_roi_campanas_no_genera_nada():
    ruta_resultados = Path(tempfile.mkdtemp()) / "ROI_Resultados.xlsx"
    resultado = generar_roi_resultados(Path(tempfile.mkdtemp()) / "no_existe.xlsx", ruta_resultados)

    assert resultado is None
    assert not ruta_resultados.exists()


def test_hoja_campanas_solo_tiene_clasificacion_manual_sin_resultados(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, fecha_inicio_campana=datetime.date(2026, 7, 1))],
    )
    generar_roi_campanas(conn, ruta_roi)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    fila = list(ws.iter_rows(min_row=2, values_only=True))[0]

    assert [c.value for c in ws[1]] == _ENCABEZADOS
    assert fila == ("Julio 2026", "Campaña Julio", "camp_1", 50.0, None, None, None)


def test_dos_campanas_generan_dos_filas_sin_agrupar(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a"),
            _registro(datetime.date(2026, 7, 1), "facebook", 30.0, campana="Campaña B", id_campana="camp_b"),
        ],
    )
    generar_roi_campanas(conn, ruta_roi)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    ids = [fila[2] for fila in ws.iter_rows(min_row=2, values_only=True)]

    assert sorted(ids) == ["camp_a", "camp_b"]


def test_rerun_actualiza_inversion_y_preserva_clasificacion(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    _asignar_evento(ws, "camp_a", "Foro A", tipo="Curso", unidad="Academy")
    wb.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    fila = list(wb2.active.iter_rows(min_row=2, values_only=True))[0]

    assert fila == ("Julio 2026", "Campaña A", "camp_a", 999.0, "Foro A", "Curso", "Academy")


def test_rerun_actualiza_bien_aunque_la_hoja_activa_sea_resumen(conn):
    """Bug real de QA: Excel guarda como "hoja activa" la pestaña que
    estaba seleccionada la última vez que se guardó el archivo a mano. Si
    Sandy guardaba con "Resumen por Evento" abierto, wb.active apuntaba a
    esa hoja en vez de a "ROI Resultados" — la corrida terminaba
    leyendo/escribiendo la hoja equivocada: "ROI Resultados" se quedaba
    congelada con el monto viejo para siempre, y "Resumen por Evento" se
    llenaba de columnas que no le correspondían."""
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_a", "Foro A", tipo="Curso", unidad="Academy")
    # Simula exactamente lo que hace Excel cuando la usuaria tiene abierta
    # la otra pestaña al guardar.
    wb.active = wb["Resumen por Evento"]
    wb.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    ws2 = wb2["ROI Resultados"]
    fila = list(ws2.iter_rows(min_row=2, values_only=True))[0]
    assert fila == ("Julio 2026", "Campaña A", "camp_a", 999.0, "Foro A", "Curso", "Academy")

    resumen = wb2["Resumen por Evento"]
    assert [c.value for c in resumen[1]] == _ENCABEZADOS_RESUMEN
    filas_resumen = list(resumen.iter_rows(min_row=2, values_only=True))
    assert filas_resumen[0][:4] == ("Foro A", "Curso", "Academy", 999.0)


def test_resumen_por_evento_agrupa_varias_campanas_del_mismo_evento(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Foro A - Arte 1", id_campana="camp_1"),
            _registro(datetime.date(2026, 7, 1), "facebook", 30.0, campana="Foro A - Arte 2", id_campana="camp_2"),
        ],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    _asignar_evento(ws, "camp_1", "Foro A", tipo="Curso", unidad="Academy")
    _asignar_evento(ws, "camp_2", "Foro A")
    wb.save(ruta_resultados)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    filas = list(resumen.iter_rows(min_row=2, values_only=True))

    assert [c.value for c in resumen[1]] == _ENCABEZADOS_RESUMEN
    assert filas == [
        (
            "Foro A", "Curso", "Academy", 80.0, None, None, None,
            '=IFERROR(D2/E2,"")', '=IFERROR(F2/E2,"")', '=IFERROR((G2-D2)/D2,"")',
        )
    ]


def test_resumen_por_evento_sin_asignar(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0)])
    generar_roi_campanas(conn, ruta_roi)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    resumen = wb["Resumen por Evento"]
    filas = list(resumen.iter_rows(min_row=2, values_only=True))

    assert filas == [
        (
            "(Sin asignar)", None, None, 50.0, None, None, None,
            '=IFERROR(D2/E2,"")', '=IFERROR(F2/E2,"")', '=IFERROR((G2-D2)/D2,"")',
        )
    ]


def test_resumen_por_evento_escribe_formulas(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 100.0)])
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    _asignar_evento(ws, "camp_1", "Foro A")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    fila = resumen[2]

    assert fila[7].value == '=IFERROR(D2/E2,"")'
    assert fila[8].value == '=IFERROR(F2/E2,"")'
    assert fila[9].value == '=IFERROR((G2-D2)/D2,"")'


def test_rerun_actualiza_inversion_del_resumen_y_preserva_leads_subscribers_revenue(conn):
    """La automatización revisa los últimos 7 días y la inversión cambia,
    pero lo que Sandy ya cargó a mano en el resumen no se toca."""
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_a", "Foro A", tipo="Curso", unidad="Academy")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    resumen = wb["Resumen por Evento"]
    resumen["E2"] = 120  # Leads
    resumen["F2"] = 30  # Subscribers
    resumen["G2"] = 4500.0  # Revenue
    wb.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    fila = list(wb2["Resumen por Evento"].iter_rows(min_row=2, values_only=True))[0]

    assert fila[:7] == ("Foro A", "Curso", "Academy", 999.0, 120, 30, 4500.0)


def test_evento_reasignado_no_deja_fila_fantasma_sin_datos_manuales(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_a", "Evento viejo")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_a", "Evento nuevo")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    nombres = [fila[0] for fila in wb2["Resumen por Evento"].iter_rows(min_row=2, values_only=True)]

    assert nombres == ["Evento nuevo"]


def test_espacio_de_mas_en_nombre_de_evento_no_duplica_la_fila(conn):
    """Bug real de QA: una campaña cargada con " Curso X" (espacio al
    principio) generaba una fila nueva en vez de sumarse a la fila ya
    existente de "Curso X", partiendo los resultados de un mismo evento
    en dos filas."""
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_a", "Curso X")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    resumen["E2"] = 20  # Leads cargados a mano en la fila de "Curso X"
    wb2.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 30.0, campana="Campaña B", id_campana="camp_b")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb3 = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb3.active, "camp_b", " Curso X")  # espacio al principio
    wb3.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb4 = openpyxl.load_workbook(ruta_resultados)
    filas = list(wb4["Resumen por Evento"].iter_rows(min_row=2, values_only=True))

    assert len(filas) == 1
    assert filas[0][0] == "Curso X"
    assert filas[0][3] == 80.0  # 50 + 30, las dos campañas sumadas en la misma fila
    assert filas[0][4] == 20  # el Leads cargado a mano no se perdió ni se duplicó


def test_resumen_mantiene_orden_de_entrada_y_agrega_nuevos_al_final(conn):
    """El resumen no se reordena alfabéticamente: los eventos que ya
    tenían fila la mantienen (sin que se muevan ni se toquen sus datos
    manuales), y los eventos nuevos se agregan al final."""
    # Los nombres de campaña se eligen para que el orden en ROI_Campanas
    # (que ordena por campaña) ponga primero a "camp_z"/"Evento Zeta" y
    # después a "camp_m"/"Evento Alfa" — así, si el resumen todavía
    # ordenara alfabéticamente por nombre de EVENTO, "Evento Alfa"
    # aparecería primero, lo cual es justo lo que este test descarta.
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 10.0, campana="Campaña 1", id_campana="camp_z"),
            _registro(datetime.date(2026, 7, 1), "facebook", 20.0, campana="Campaña 2", id_campana="camp_m"),
        ],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_z", "Evento Zeta")
    _asignar_evento(wb.active, "camp_m", "Evento Alfa")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    resumen["E2"] = 5  # Leads de "Evento Zeta", que quedó primero en la hoja
    wb2.save(ruta_resultados)

    # Llega una campaña de un evento nuevo: debe ir al final, no intercalarse
    # alfabéticamente entre "Evento Alfa" y "Evento Zeta".
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 5.0, campana="Campaña B", id_campana="camp_b")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)  # agrega camp_b a "ROI Resultados" sin evento asignado todavía

    wb3 = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb3.active, "camp_b", "Evento Beta")
    wb3.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb4 = openpyxl.load_workbook(ruta_resultados)
    resumen4 = wb4["Resumen por Evento"]
    filas = list(resumen4.iter_rows(min_row=2, values_only=True))

    assert [fila[0] for fila in filas] == ["Evento Zeta", "Evento Alfa", "Evento Beta"]
    assert filas[0][4] == 5  # Leads de "Evento Zeta" no se movió ni se borró


def test_leer_resumen_por_evento_arma_rango_de_meses_cruzando_con_roi_resultados():
    from marketing_analytics.reports.roi_resultados_builder import leer_resumen_por_evento

    ruta = Path(tempfile.mkdtemp()) / "ROI_Resultados.xlsx"
    wb = openpyxl.Workbook()
    ws_campanas = wb.active
    ws_campanas.title = "ROI Resultados"
    ws_campanas.append(_ENCABEZADOS)
    ws_campanas.append(["Julio 2026", "Camp A", "id1", 100.0, "Curso X", "Curso", "Academy"])
    # Espacio de más a propósito: debe seguir cruzando con "Curso X" en el
    # resumen (ver _normalizar_nombre).
    ws_campanas.append(["Septiembre 2026", "Camp B", "id2", 50.0, " Curso X ", "Curso", "Academy"])
    ws_campanas.append(["Agosto 2026", "Camp C", "id3", 30.0, None, None, None])

    ws_resumen = wb.create_sheet("Resumen por Evento")
    ws_resumen.append(_ENCABEZADOS_RESUMEN)
    ws_resumen.append(["Curso X", "Curso", "Academy", 150.0, 20, 5, 500.0, 7.5, 0.25, 2.3333333333333335])
    ws_resumen.append(["Evento Pendiente", None, None, 0, None, None, None, "", "", ""])
    wb.save(ruta)

    eventos = leer_resumen_por_evento(ruta)
    roi_curso_x = eventos[0]["roi"]
    assert roi_curso_x == pytest.approx(2.3333333333333335)

    assert eventos == [
        {
            "nombre_evento": "Curso X",
            "tipo": "Curso",
            "unidad": "Academy",
            "inversion_total": 150,
            "leads": 20,
            "subscribers": 5,
            "revenue": 500,
            "costo_por_lead": 7.5,
            "conversion": 0.25,
            "roi": roi_curso_x,  # redondeo de ida y vuelta por XML, no importa acá
            "mes": "Julio – Septiembre 2026",
            "mes_orden": 2026 * 12 + 7,
            "meses": ["Julio 2026", "Septiembre 2026"],
        },
        {
            "nombre_evento": "Evento Pendiente",
            "tipo": None,
            "unidad": None,
            "inversion_total": 0,
            "leads": None,
            "subscribers": None,
            "revenue": None,
            "costo_por_lead": None,  # "" de IFERROR == pendiente, no cero
            "conversion": None,
            "roi": None,
            "mes": "",
            "mes_orden": 0,
            "meses": [],
        },
    ]


def test_leer_resumen_por_evento_sin_archivo_devuelve_lista_vacia():
    from marketing_analytics.reports.roi_resultados_builder import leer_resumen_por_evento

    assert leer_resumen_por_evento(Path(tempfile.mkdtemp()) / "no_existe.xlsx") == []


def test_leer_resumen_por_evento_calcula_costo_lead_conversion_y_roi_sin_depender_de_excel(conn):
    """Caso real de QA (Sandy): Costo por lead/% de conversión/ROI son
    fórmulas de Excel (IFERROR) que `generar_roi_resultados` reescribe en
    cada corrida de la automatización — openpyxl nunca deja un valor
    cacheado en una fórmula recién escrita, Excel lo calcula solo cuando
    alguien abre el archivo a mano. Como nadie abre el archivo entre que la
    automatización lo escribe y el dashboard lo lee, leer esas 3 celdas
    directamente siempre daba "pendiente" — aunque Leads/Subscribers/Revenue
    sí estuvieran cargados. Por eso se calculan acá en Python, no se leen
    de Excel."""
    from marketing_analytics.reports.roi_resultados_builder import leer_resumen_por_evento

    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 100.0)])
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    _asignar_evento(wb.active, "camp_1", "Rueda de Negocios")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)  # agrupa en "Resumen por Evento"

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    resumen["E2"] = 1008  # Leads
    resumen["F2"] = 109  # Subscribers
    resumen["G2"] = 18858  # Revenue
    wb2.save(ruta_resultados)

    # Esta corrida reescribe las fórmulas de Costo por lead/% de
    # conversión/ROI (columnas H/I/J) SIN ningún valor cacheado todavía —
    # exactamente como las deja la automatización real.
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb3 = openpyxl.load_workbook(ruta_resultados)
    resumen3 = wb3["Resumen por Evento"]
    assert resumen3["H2"].value == '=IFERROR(D2/E2,"")'  # sigue siendo una fórmula sin calcular

    eventos = leer_resumen_por_evento(ruta_resultados)

    assert eventos[0]["leads"] == 1008
    assert eventos[0]["costo_por_lead"] == pytest.approx(100.0 / 1008)
    assert eventos[0]["conversion"] == pytest.approx(109 / 1008)
    assert eventos[0]["roi"] == pytest.approx((18858 - 100.0) / 100.0)
