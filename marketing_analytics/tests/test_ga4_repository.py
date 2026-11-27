import datetime

from marketing_analytics.database.repository import upsert_ga4_metricas_diarias
from marketing_analytics.models.records import GA4MetricaDiaria


def _metrica(fecha=datetime.date(2026, 7, 1), sesiones=100, property_id="123456789"):
    return GA4MetricaDiaria(
        unidad="Academy Cainco",
        property_id=property_id,
        fecha=fecha,
        sesiones=sesiones,
        usuarios_totales=80,
        usuarios_nuevos=20,
    )


def test_metrica_nueva_se_inserta(conn):
    resultado = upsert_ga4_metricas_diarias(conn, [_metrica()])

    assert resultado.nuevos == 1
    fila = conn.execute(
        "SELECT * FROM ga4_metricas_diarias WHERE uid = ?", ("ga4|123456789|2026-07-01",)
    ).fetchone()
    assert fila["sesiones"] == 100
    assert fila["unidad"] == "Academy Cainco"


def test_correr_de_nuevo_el_mismo_dia_actualiza_no_duplica(conn):
    upsert_ga4_metricas_diarias(conn, [_metrica(sesiones=100)])
    resultado = upsert_ga4_metricas_diarias(conn, [_metrica(sesiones=130)])

    assert resultado.actualizados == 1
    filas = conn.execute("SELECT * FROM ga4_metricas_diarias").fetchall()
    assert len(filas) == 1
    assert filas[0]["sesiones"] == 130


def test_sin_cambios_se_descarta(conn):
    upsert_ga4_metricas_diarias(conn, [_metrica()])

    resultado = upsert_ga4_metricas_diarias(conn, [_metrica()])

    assert resultado.descartados == 1


def test_dos_propiedades_el_mismo_dia_no_colisionan(conn):
    """El uid es por property_id+fecha, no solo por fecha — dos propiedades
    (unidades) distintas con datos el mismo día deben guardarse como dos
    filas separadas, no pisarse una a la otra."""
    upsert_ga4_metricas_diarias(conn, [_metrica(property_id="111", sesiones=50)])
    upsert_ga4_metricas_diarias(conn, [_metrica(property_id="222", sesiones=90)])

    filas = conn.execute("SELECT property_id, sesiones FROM ga4_metricas_diarias ORDER BY property_id").fetchall()
    assert [(f["property_id"], f["sesiones"]) for f in filas] == [("111", 50), ("222", 90)]
