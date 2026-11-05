import datetime

from marketing_analytics.database.repository import upsert_calendario_publicaciones
from marketing_analytics.models.records import CalendarioPublicacion


def _fila(id_origen="1", estado="Planeado", fecha=datetime.date(2026, 7, 1)):
    return CalendarioPublicacion(
        id_origen=id_origen,
        fecha_publicacion=fecha,
        perfil="Marca X",
        estado=estado,
    )


def test_fila_nueva_se_inserta(conn):
    resultado = upsert_calendario_publicaciones(conn, [_fila()])

    assert resultado.nuevos == 1
    fila = conn.execute("SELECT * FROM calendario_publicaciones WHERE uid = ?", ("calendario|1",)).fetchone()
    assert fila["estado"] == "Planeado"


def test_reprogramar_la_fecha_actualiza_en_vez_de_duplicar(conn):
    """Caso real: el equipo mueve la fecha planeada de un post ya cargado —
    como el uid se arma solo con el ID, debe actualizar la misma fila, no
    crear una nueva con la fecha distinta."""
    upsert_calendario_publicaciones(conn, [_fila(fecha=datetime.date(2026, 7, 1))])
    resultado = upsert_calendario_publicaciones(conn, [_fila(fecha=datetime.date(2026, 7, 15))])

    assert resultado.actualizados == 1
    filas = conn.execute("SELECT * FROM calendario_publicaciones").fetchall()
    assert len(filas) == 1
    assert filas[0]["fecha_publicacion"] == "2026-07-15"


def test_misma_fila_sin_cambios_se_descarta(conn):
    upsert_calendario_publicaciones(conn, [_fila()])

    resultado = upsert_calendario_publicaciones(conn, [_fila()])

    assert resultado.descartados == 1
    assert resultado.nuevos == 0
