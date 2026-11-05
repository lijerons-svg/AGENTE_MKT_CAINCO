from marketing_analytics.database.repository import upsert_control_perfiles
from marketing_analytics.models.records import ControlPerfilMensual


def _snapshot(anio_mes="2026-07", seguidores=1000):
    return ControlPerfilMensual(
        perfil="Marca X", red="instagram", anio_mes=anio_mes, seguidores=seguidores
    )


def test_snapshot_nuevo_se_inserta(conn):
    resultado = upsert_control_perfiles(conn, [_snapshot()])

    assert resultado.nuevos == 1
    fila = conn.execute(
        "SELECT * FROM control_perfiles WHERE uid = ?", ("control_perfiles|Marca X|2026-07",)
    ).fetchone()
    assert fila["seguidores"] == 1000


def test_correr_de_nuevo_en_el_mismo_mes_actualiza_no_duplica(conn):
    upsert_control_perfiles(conn, [_snapshot(seguidores=1000)])
    resultado = upsert_control_perfiles(conn, [_snapshot(seguidores=1050)])

    assert resultado.actualizados == 1
    filas = conn.execute("SELECT * FROM control_perfiles").fetchall()
    assert len(filas) == 1
    assert filas[0]["seguidores"] == 1050


def test_sin_cambios_se_descarta(conn):
    upsert_control_perfiles(conn, [_snapshot()])

    resultado = upsert_control_perfiles(conn, [_snapshot()])

    assert resultado.descartados == 1


def test_mes_nuevo_crea_fila_separada_de_la_anterior(conn):
    upsert_control_perfiles(conn, [_snapshot(anio_mes="2026-06", seguidores=950)])
    upsert_control_perfiles(conn, [_snapshot(anio_mes="2026-07", seguidores=1000)])

    filas = conn.execute("SELECT anio_mes, seguidores FROM control_perfiles ORDER BY anio_mes").fetchall()
    assert [(f["anio_mes"], f["seguidores"]) for f in filas] == [("2026-06", 950), ("2026-07", 1000)]
