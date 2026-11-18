import datetime
import tempfile
from pathlib import Path

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas
from marketing_analytics.reports.roi_resultados_builder import generar_roi_resultados

_ENCABEZADOS = [
    "Mes", "Campaña", "ID de campaña", "Inversión total", "Nombre de evento", "Tipo", "Unidad",
    "Leads", "Subscribers", "Revenue", "Costo por lead", "% de conversión", "ROI",
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


def _completar_fila(ws, id_campana, valores):
    for fila in ws.iter_rows(min_row=2):
        if fila[2].value == id_campana:
            for columna, valor in valores.items():
                fila[columna - 1].value = valor


def test_sin_archivo_roi_campanas_no_genera_nada():
    ruta_resultados = Path(tempfile.mkdtemp()) / "ROI_Resultados.xlsx"
    resultado = generar_roi_resultados(Path(tempfile.mkdtemp()) / "no_existe.xlsx", ruta_resultados)

    assert resultado is None
    assert not ruta_resultados.exists()


def test_encabezados_y_fila_por_campana_igual_que_roi_campanas(conn):
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
    assert fila[:4] == ("Julio 2026", "Campaña Julio", "camp_1", 50.0)
    assert fila[4:10] == (None, None, None, None, None, None)


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


def test_escribe_formulas_de_costo_por_lead_conversion_y_roi(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 100.0)])
    generar_roi_campanas(conn, ruta_roi)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    fila = ws[2]

    assert fila[10].value == '=IFERROR(D2/H2,"")'
    assert fila[11].value == '=IFERROR(I2/H2,"")'
    assert fila[12].value == '=IFERROR((J2-D2)/D2,"")'


def test_rerun_actualiza_inversion_y_preserva_datos_manuales(conn):
    """La automatización revisa los últimos 7 días y la inversión cambia,
    pero lo que Sandy ya cargó a mano no se toca."""
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    _completar_fila(
        ws, "camp_a",
        {5: "Foro A", 6: "Curso", 7: "Academy", 8: 120, 9: 30, 10: 4500.0},
    )
    wb.save(ruta_resultados)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    ws2 = wb2.active
    fila = list(ws2.iter_rows(min_row=2, values_only=True))[0]

    assert fila[:10] == (
        "Julio 2026", "Campaña A", "camp_a", 999.0, "Foro A", "Curso", "Academy", 120, 30, 4500.0,
    )


def test_campana_nueva_no_desordena_datos_manuales_de_otra_campana(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    _completar_fila(ws, "camp_a", {5: "Foro A", 8: 120})
    wb.save(ruta_resultados)

    # Campaña nueva que ordenaría ANTES alfabéticamente.
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 999.0, campana="Campaña AAA nueva", id_campana="camp_nueva")],
    )
    generar_roi_campanas(conn, ruta_roi)
    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    ws2 = wb2.active
    filas = {fila[2]: fila for fila in ws2.iter_rows(min_row=2, values_only=True)}

    assert filas["camp_a"][4:10] == ("Foro A", None, None, 120, None, None)
    assert filas["camp_nueva"][4:10] == (None, None, None, None, None, None)


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
    _completar_fila(ws, "camp_1", {5: "Foro A", 8: 70, 9: 20, 10: 3000.0})
    _completar_fila(ws, "camp_2", {5: "Foro A", 8: 50, 9: 10, 10: 1500.0})
    wb.save(ruta_resultados)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    resumen = wb2["Resumen por Evento"]
    filas = list(resumen.iter_rows(min_row=2, values_only=True))

    assert [c.value for c in resumen[1]] == [
        "Nombre de evento", "Inversión total", "Leads", "Subscribers", "Revenue",
        "Costo por lead", "% de conversión", "ROI",
    ]
    assert filas == [("Foro A", 80.0, 120, 30, 4500.0, '=IFERROR(B2/C2,"")', '=IFERROR(D2/C2,"")', '=IFERROR((E2-B2)/B2,"")')]


def test_resumen_por_evento_agrupa_sin_asignar(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0)])
    generar_roi_campanas(conn, ruta_roi)

    generar_roi_resultados(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    resumen = wb["Resumen por Evento"]
    filas = list(resumen.iter_rows(min_row=2, values_only=True))

    assert filas[0][0] == "(Sin asignar)"
    assert filas[0][1] == 50.0


def tmp_path_factory_roi():
    return Path(tempfile.mkdtemp()) / "ROI_Resultados.xlsx"
