import datetime
import tempfile
from pathlib import Path

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.resultados_producto_builder import generar_resultados_producto
from marketing_analytics.reports.roi_builder import generar_roi_campanas


def _registro(fecha, red, importe, campana, id_campana):
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
    )


def _rutas():
    carpeta = Path(tempfile.mkdtemp())
    return carpeta / "ROI_Campanas.xlsx", carpeta / "ROI_Resultados.xlsx"


def _asignar_producto(ruta_roi, id_campana, nombre_producto):
    wb = openpyxl.load_workbook(ruta_roi)
    ws = wb.active
    for fila in ws.iter_rows(min_row=2):
        if fila[2].value == id_campana:
            fila[6].value = nombre_producto
    wb.save(ruta_roi)


def test_sin_archivo_roi_campanas_no_genera_nada():
    ruta_resultados = Path(tempfile.mkdtemp()) / "ROI_Resultados.xlsx"
    resultado = generar_resultados_producto(Path(tempfile.mkdtemp()) / "no_existe.xlsx", ruta_resultados)

    assert resultado is None
    assert not ruta_resultados.exists()


def test_agrupa_por_nombre_producto_sumando_varias_campanas(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 50.0, "Foro A - Arte 1", "camp_1"),
            _registro(datetime.date(2026, 7, 1), "facebook", 30.0, "Foro A - Arte 2", "camp_2"),
        ],
    )
    generar_roi_campanas(conn, ruta_roi)
    _asignar_producto(ruta_roi, "camp_1", "Foro A")
    _asignar_producto(ruta_roi, "camp_2", "Foro A")

    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert [c.value for c in ws[1]] == ["Nombre_Producto", "Inversión total", "Leads", "Resultados USD", "ROI"]
    assert filas[0][:2] == ("Foro A", 80.0)


def test_campanas_sin_producto_van_a_sin_asignar(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, "Campaña A", "camp_1")])
    generar_roi_campanas(conn, ruta_roi)

    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert filas[0][:2] == ("(Sin asignar)", 50.0)


def test_formula_roi_referencia_inversion_y_resultados(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, "Foro A", "camp_1")])
    generar_roi_campanas(conn, ruta_roi)
    _asignar_producto(ruta_roi, "camp_1", "Foro A")

    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    assert ws["E2"].value == '=IFERROR((D2-B2)/B2,"")'


def test_rerun_actualiza_inversion_y_preserva_leads_y_resultados(conn):
    """La automatización revisa los últimos 7 días y la inversión cambia,
    pero lo que Sandy ya cargó a mano (Leads, Resultados USD) no se toca."""
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, "Foro A", "camp_1")])
    generar_roi_campanas(conn, ruta_roi)
    _asignar_producto(ruta_roi, "camp_1", "Foro A")
    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    ws["C2"] = 120  # Leads
    ws["D2"] = 4500.0  # Resultados USD
    wb.save(ruta_resultados)

    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 2), "facebook", 949.0, "Foro A", "camp_1")])
    generar_roi_campanas(conn, ruta_roi)
    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb2 = openpyxl.load_workbook(ruta_resultados)
    ws2 = wb2.active
    fila = list(ws2.iter_rows(min_row=2, values_only=True))[0]

    assert fila[:4] == ("Foro A", 999.0, 120, 4500.0)


def test_producto_reasignado_no_deja_fila_fantasma_sin_datos_manuales(conn):
    ruta_roi, ruta_resultados = _rutas()
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, "Campaña A", "camp_1")])
    generar_roi_campanas(conn, ruta_roi)
    _asignar_producto(ruta_roi, "camp_1", "Producto viejo")
    generar_resultados_producto(ruta_roi, ruta_resultados)

    _asignar_producto(ruta_roi, "camp_1", "Producto nuevo")
    generar_resultados_producto(ruta_roi, ruta_resultados)

    wb = openpyxl.load_workbook(ruta_resultados)
    ws = wb.active
    nombres = [fila[0] for fila in ws.iter_rows(min_row=2, values_only=True)]

    assert nombres == ["Producto nuevo"]
