import datetime

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas


def _registro(
    fecha,
    red,
    importe,
    campana="Campaña Julio",
    id_campana="camp_1",
    unidad="CAINCO",
    fecha_inicio_campana=None,
):
    return MetaAdsRegistro(
        cuenta_publicitaria="123",
        perfil_unidad=unidad,
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


def test_encabezados_son_mes_campana_id_e_inversion(conn):
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 10.0)])

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active

    assert [c.value for c in ws[1]] == ["Mes", "Campaña", "ID de campaña", "Inversión total"]


def test_agrupa_por_campana_sumando_inversion_de_todos_los_dias_y_redes(conn):
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 10.0, fecha_inicio_campana=datetime.date(2026, 7, 1)),
            _registro(datetime.date(2026, 7, 2), "facebook", 15.0, fecha_inicio_campana=datetime.date(2026, 7, 1)),
            _registro(datetime.date(2026, 7, 1), "instagram", 5.0, fecha_inicio_campana=datetime.date(2026, 7, 1)),
        ],
    )

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert filas == [("Julio 2026", "Campaña Julio", "camp_1", 30.0)]


def test_usa_fecha_inicio_de_campana_cuando_esta_disponible(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 15), "facebook", 10.0, fecha_inicio_campana=datetime.date(2026, 4, 3))],
    )

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active

    assert ws[2][0].value == "Abril 2026"


def test_usa_fecha_de_publicacion_como_respaldo_si_falta_fecha_inicio(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 3, 10), "facebook", 10.0, fecha_inicio_campana=None)],
    )

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active

    assert ws[2][0].value == "Marzo 2026"


def test_dos_campanas_distintas_generan_dos_filas(conn):
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 10.0, campana="Campaña A", id_campana="camp_a"),
            _registro(datetime.date(2026, 7, 1), "facebook", 20.0, campana="Campaña B", id_campana="camp_b"),
        ],
    )

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    ids = [fila[2] for fila in ws.iter_rows(min_row=2, values_only=True)]

    assert sorted(ids) == ["camp_a", "camp_b"]


def test_rerun_actualiza_la_inversion_sin_duplicar_filas(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    ruta = tmp_path_factory_roi()
    generar_roi_campanas(conn, ruta)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 2), "facebook", 25.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert filas == [("Julio 2026", "Campaña A", "camp_a", 75.0)]


def tmp_path_factory_roi():
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / "ROI_Campanas.xlsx"
