import datetime

from marketing_analytics.database.repository import upsert_linkedin_organico
from marketing_analytics.models.records import LinkedInOrganicoPost


def _post(id_publicacion_origen="urn:li:share:1", reacciones=10):
    return LinkedInOrganicoPost(
        pagina="CAINCO",
        fecha_publicacion=datetime.date(2026, 7, 1),
        tipo="video",
        descripcion="Post de prueba",
        impresiones=1000,
        alcance=800,
        clics=20,
        reacciones=reacciones,
        comentarios=5,
        compartidos=2,
        interacciones=reacciones + 5 + 2,
        id_publicacion_origen=id_publicacion_origen,
    )


def test_post_nuevo_se_inserta(conn):
    resultado = upsert_linkedin_organico(conn, [_post()])

    assert resultado.nuevos == 1
    fila = conn.execute("SELECT * FROM linkedin_organico").fetchone()
    assert fila["pagina"] == "CAINCO"
    assert fila["reacciones"] == 10


def test_correr_de_nuevo_con_metricas_actualizadas_no_duplica(conn):
    upsert_linkedin_organico(conn, [_post(reacciones=10)])
    resultado = upsert_linkedin_organico(conn, [_post(reacciones=25)])

    assert resultado.actualizados == 1
    filas = conn.execute("SELECT * FROM linkedin_organico").fetchall()
    assert len(filas) == 1
    assert filas[0]["reacciones"] == 25


def test_sin_cambios_se_descarta(conn):
    upsert_linkedin_organico(conn, [_post()])

    resultado = upsert_linkedin_organico(conn, [_post()])

    assert resultado.descartados == 1


def test_dos_posts_distintos_el_mismo_dia_se_guardan_separados(conn):
    upsert_linkedin_organico(conn, [_post(id_publicacion_origen="urn:li:share:1")])
    upsert_linkedin_organico(conn, [_post(id_publicacion_origen="urn:li:share:2")])

    filas = conn.execute("SELECT id_publicacion_origen FROM linkedin_organico").fetchall()
    assert {f["id_publicacion_origen"] for f in filas} == {"urn:li:share:1", "urn:li:share:2"}
