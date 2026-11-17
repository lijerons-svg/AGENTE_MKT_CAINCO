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


def test_encabezados_incluyen_unidad_y_nombre_producto(conn):
    upsert_meta_ads(conn, [_registro(datetime.date(2026, 7, 1), "facebook", 10.0)])

    ruta = generar_roi_campanas(conn, tmp_path_factory_roi())
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active

    assert [c.value for c in ws[1]] == [
        "Mes", "Unidad", "Campaña", "ID de campaña", "Nombre_Producto", "Inversión total",
    ]


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

    assert filas == [("Julio 2026", "CAINCO", "Campaña Julio", "camp_1", None, 30.0)]


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
    ids = [fila[3] for fila in ws.iter_rows(min_row=2, values_only=True)]

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

    assert filas == [("Julio 2026", "CAINCO", "Campaña A", "camp_a", None, 75.0)]


def test_preserva_nombre_producto_al_regenerar_aunque_cambie_el_orden(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 50.0, campana="Campaña A", id_campana="camp_a")],
    )
    ruta = tmp_path_factory_roi()
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    ws["E2"] = "Curso de Liderazgo"
    wb.save(ruta)

    # Campaña nueva que ordenaría ANTES alfabéticamente, para confirmar que
    # el valor manual queda pegado al ID, no a la posición de la fila.
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 7, 1), "facebook", 999.0, campana="Campaña AAA nueva", id_campana="camp_nueva")],
    )
    generar_roi_campanas(conn, ruta)

    wb2 = openpyxl.load_workbook(ruta)
    ws2 = wb2.active
    filas = {fila[3]: fila for fila in ws2.iter_rows(min_row=2, values_only=True)}

    assert filas["camp_a"][4] == "Curso de Liderazgo"
    assert filas["camp_nueva"][4] is None


def test_rerun_del_mismo_rango_sin_campanas_nuevas_no_toca_nombre_producto(conn):
    upsert_meta_ads(
        conn,
        [_registro(datetime.date(2026, 4, 1), "facebook", 50.0, campana="Campaña Abril", id_campana="camp_abril")],
    )
    ruta = tmp_path_factory_roi()
    generar_roi_campanas(conn, ruta)

    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    ws["E2"] = "Producto X"
    wb.save(ruta)

    generar_roi_campanas(conn, ruta)

    wb2 = openpyxl.load_workbook(ruta)
    ws2 = wb2.active
    assert ws2["E2"].value == "Producto X"


def test_archivo_con_esquema_viejo_de_4_columnas_se_reconstruye_sin_duplicar(conn):
    """Bug real reportado por la usuaria: un archivo generado antes de
    agregar Unidad/Nombre_Producto (4 columnas: Mes, Campaña, ID de
    campaña, Inversión total) hacía que el matcheo por ID buscara en la
    columna equivocada (la nueva columna D es Unidad, no ID) — como nunca
    encontraba coincidencias, duplicaba todas las campañas al final con el
    esquema nuevo."""
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

    assert [c.value for c in ws[1]] == [
        "Mes", "Unidad", "Campaña", "ID de campaña", "Nombre_Producto", "Inversión total",
    ]
    assert filas == [("Julio 2026", "CAINCO", "Campaña A", "camp_a", None, 50.0)]


def tmp_path_factory_roi():
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / "ROI_Campanas.xlsx"
