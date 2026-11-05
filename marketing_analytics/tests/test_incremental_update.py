"""Una segunda corrida solo debe insertar lo nuevo y actualizar métricas de lo
existente cuando cambiaron — sin tocar ni duplicar lo que sigue igual."""
import datetime

from marketing_analytics.database.repository import upsert_meta_organico
from marketing_analytics.models.records import MetaOrganicoPost


def _post(id_publicacion_origen: str, alcance: int, reacciones: int) -> MetaOrganicoPost:
    return MetaOrganicoPost(
        perfil="perfil_001",
        pagina="Marca X - Instagram",
        red="instagram",
        fecha_publicacion=datetime.date(2026, 7, 1),
        tipo="imagen",
        descripcion="Publicación de prueba",
        alcance=alcance,
        visualizaciones=alcance + 200,
        total_clics=50,
        clics_enlace=10,
        reacciones=reacciones,
        comentarios=5,
        compartidos=2,
        total_interacciones=reacciones + 7,
        id_publicacion_origen=id_publicacion_origen,
    )


def test_segunda_corrida_solo_toca_lo_nuevo_y_lo_cambiado(conn):
    corrida_1 = [
        _post("post_A", alcance=1000, reacciones=100),
        _post("post_B", alcance=2000, reacciones=150),
        _post("post_C", alcance=3000, reacciones=200),
    ]
    resultado_1 = upsert_meta_organico(conn, corrida_1)
    assert resultado_1.nuevos == 3
    assert resultado_1.actualizados == 0
    assert resultado_1.descartados == 0

    corrida_2 = [
        _post("post_A", alcance=1000, reacciones=100),  # sin cambios
        _post("post_B", alcance=2500, reacciones=180),  # métricas subieron
        _post("post_C", alcance=3000, reacciones=200),  # sin cambios
        _post("post_D", alcance=500, reacciones=20),  # nueva publicación
    ]
    resultado_2 = upsert_meta_organico(conn, corrida_2)

    assert resultado_2.nuevos == 1
    assert resultado_2.actualizados == 1
    assert resultado_2.descartados == 2

    total_filas = conn.execute("SELECT COUNT(*) AS n FROM meta_organico").fetchone()["n"]
    assert total_filas == 4

    alcance_post_b = conn.execute(
        "SELECT alcance, reacciones FROM meta_organico WHERE id_publicacion_origen = 'post_B'"
    ).fetchone()
    assert alcance_post_b["alcance"] == 2500
    assert alcance_post_b["reacciones"] == 180


def test_ejecucion_incremental_no_pierde_historico_de_publicaciones_viejas(conn):
    """Simula: mes 1 se cargan publicaciones de julio; mes 2 se corre de nuevo
    solo con agosto — julio debe seguir intacto en la base histórica."""
    julio = [_post("post_julio_1", alcance=1000, reacciones=100)]
    upsert_meta_organico(conn, julio)

    agosto = [
        MetaOrganicoPost(
            perfil="perfil_001",
            pagina="Marca X - Instagram",
            red="instagram",
            fecha_publicacion=datetime.date(2026, 8, 1),
            tipo="video",
            descripcion="Publicación de agosto",
            alcance=4000,
            visualizaciones=4200,
            total_clics=80,
            clics_enlace=20,
            reacciones=300,
            comentarios=10,
            compartidos=5,
            total_interacciones=315,
            id_publicacion_origen="post_agosto_1",
        )
    ]
    resultado = upsert_meta_organico(conn, agosto)

    assert resultado.nuevos == 1
    total_filas = conn.execute("SELECT COUNT(*) AS n FROM meta_organico").fetchone()["n"]
    assert total_filas == 2

    julio_sigue = conn.execute(
        "SELECT alcance FROM meta_organico WHERE id_publicacion_origen = 'post_julio_1'"
    ).fetchone()
    assert julio_sigue["alcance"] == 1000
