import datetime

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas


def _registro(fecha, red, importe, campana="Campaña Julio", id_campana="camp_1", unidad="CAINCO"):
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
    )


def test_agrupa_por_campana_sumando_inversion_de_todos_los_dias_y_redes(conn):
    upsert_meta_ads(
        conn,
        [
            _registro(datetime.date(2026, 7, 1), "facebook", 10.0),
            _registro(datetime.date(2026, 7, 2), "facebook", 15.0),
            _registro(datetime.date(2026, 7, 1), "instagram", 5.0),
        ],
    )

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert len(filas) == 1
    unidad, campana, id_campana, cierres, no_cierres, monto, inversion = filas[0][:7]
    assert unidad == "CAINCO"
    assert campana == "Campaña Julio"
    assert id_campana == "camp_1"
    assert cierres is None
    assert no_cierres is None
    assert monto is None
    assert inversion == 30.0


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


def test_escribe_formulas_para_costo_de_cierre_ticket_tasa_y_roi(conn):
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 100.0)])

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    fila = ws[2]

    assert fila[7].value == '=IFERROR(G2/D2,"")'
    assert fila[8].value == '=IFERROR(F2/D2,"")'
    assert fila[9].value == '=IFERROR(D2/(D2+E2),"")'
    assert fila[10].value == '=IFERROR((F2-G2)/G2,"")'


def test_preserva_datos_manuales_al_regenerar_aunque_cambie_el_orden(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    ruta = tmp_path_factory_roi()
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    ws["D2"] = 3  # cierres
    ws["E2"] = 2  # no cierres
    ws["F2"] = 1500.0  # monto de cierre
    wb.save(ruta)

    # Se agrega una campaña nueva cuyo nombre la ordena ANTES alfabéticamente,
    # para asegurar que el valor manual no se "pegue" por posición de fila.
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 999.0, campana="Campaña AAA nueva", id_campana="camp_nueva")],
    )
    generar_roi_campanas(conn, ruta)

    wb2 = openpyxl.load_workbook(ruta)
    ws2 = wb2.active
    filas = {fila[2]: fila for fila in ws2.iter_rows(min_row=2, values_only=True)}

    assert filas["camp_a"][3:6] == (3, 2, 1500.0)
    assert filas["camp_nueva"][3:6] == (None, None, None)


def tmp_path_factory_roi():
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / "ROI_Campanas.xlsx"
