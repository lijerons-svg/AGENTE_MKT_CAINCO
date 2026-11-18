import datetime

import openpyxl

from marketing_analytics.database.repository import upsert_meta_ads
from marketing_analytics.models.records import MetaAdsRegistro
from marketing_analytics.reports.roi_builder import generar_roi_campanas

_ENCABEZADOS = ["Mes", "Campaña", "ID de campaña", "Inversión total", "Unidad", "Tipo de campaña", "Nombre_Producto"]


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


def test_encabezados_automaticos_y_manuales_en_el_orden_pedido(conn):
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 10.0)])

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active

    assert [c.value for c in ws[1]] == _ENCABEZADOS


def test_campana_nueva_tiene_columnas_manuales_vacias(conn):
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 10.0)])

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    fila = list(ws.iter_rows(min_row=2, values_only=True))[0]

    assert fila == ("Julio 2026", "Campaña Julio", "camp_1", 10.0, None, None, None)


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
    fila = list(ws.iter_rows(min_row=2, values_only=True))[0]

    assert fila[:4] == ("Julio 2026", "Campaña Julio", "camp_1", 30.0)


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

    assert len(filas) == 1
    assert filas[0][:4] == ("Julio 2026", "Campaña A", "camp_a", 75.0)


def test_preserva_columnas_manuales_al_regenerar_aunque_cambie_el_orden(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    ruta = tmp_path_factory_roi()
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    ws["E2"] = "Academy"
    ws["F2"] = "Curso"
    ws["G2"] = "Liderazgo"
    wb.save(ruta)

    # Campaña nueva que ordenaría ANTES alfabéticamente, para confirmar que
    # lo manual queda pegado al ID, no a la posición de la fila.
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 999.0, campana="Campaña AAA nueva", id_campana="camp_nueva")],
    )
    generar_roi_campanas(conn, ruta)

    wb2 = openpyxl.load_workbook(ruta)
    ws2 = wb2.active
    filas = {fila[2]: fila for fila in ws2.iter_rows(min_row=2, values_only=True)}

    assert filas["camp_a"][4:] == ("Academy", "Curso", "Liderazgo")
    assert filas["camp_nueva"][4:] == (None, None, None)


def test_archivo_con_esquema_viejo_se_reconstruye_sin_duplicar(conn):
    """Si el archivo existente tiene otra cantidad de columnas (de una
    versión anterior del esquema), el matcheo por ID buscaría en la
    columna equivocada y duplicaría todo — en vez de eso, se reconstruye
    desde cero."""
    ruta = tmp_path_factory_roi()
    wb_viejo = openpyxl.Workbook()
    ws_viejo = wb_viejo.active
    ws_viejo.append(["Mes", "Campaña", "ID de campaña", "Inversión total"])
    ws_viejo.append(["Julio 2026", "Campaña A", "camp_a", 999.0])
    ruta.parent.mkdir(parents=True, exist_ok=True)
    wb_viejo.save(ruta)

    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    filas = list(ws.iter_rows(min_row=2, values_only=True))

    assert [c.value for c in ws[1]] == _ENCABEZADOS
    assert len(filas) == 1
    assert filas[0][:4] == ("Julio 2026", "Campaña A", "camp_a", 50.0)


def tmp_path_factory_roi():
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / "ROI_Campanas.xlsx"
