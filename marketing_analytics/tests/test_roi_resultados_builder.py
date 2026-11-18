import datetime
import tempfile
from pathlib import Path

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas
from marketing_analytics.reports.roi_resultados_builder import generar_roi_resultados

_ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total", "Nombre de evento", "Tipo", "Unidad"]
_ENCABEZADOS_RESUMEN = [
    "Nombre de evento", "Inversión total", "Leads", "Subscribers", "Revenue",
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
    _asignar_evento(ws, "camp_1", "Foro A")
    _asignar_evento(ws, "camp_2", "Foro A")
    wb.save(ruta_resultados)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    filas = list(resumen.iter_rows(min_row=2, values_only=True))

    assert [c.value for c in resumen[1]] == _ENCABEZADOS_RESUMEN
    assert filas == [
        ("Foro A", 80.0, None, None, None, '=IFERROR(B2/C2,"")', '=IFERROR(D2/C2,"")', '=IFERROR((E2-B2)/B2,"")')
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
        ("(Sin asignar)", 50.0, None, None, None, '=IFERROR(B2/C2,"")', '=IFERROR(D2/C2,"")', '=IFERROR((E2-B2)/B2,"")')
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

    assert fila[5].value == '=IFERROR(B2/C2,"")'
    assert fila[6].value == '=IFERROR(D2/C2,"")'
    assert fila[7].value == '=IFERROR((E2-B2)/B2,"")'


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
    _asignar_evento(wb.active, "camp_a", "Foro A")
    wb.save(ruta_resultados)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    resumen = wb["Resumen por Evento"]
    resumen["C2"] = 120  # Leads
    resumen["D2"] = 30  # Subscribers
    resumen["E2"] = 4500.0  # Revenue
    wb.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    fila = list(wb2["Resumen por Evento"].iter_rows(min_row=2, values_only=True))[0]

    assert fila[:5] == ("Foro A", 999.0, 120, 30, 4500.0)


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
