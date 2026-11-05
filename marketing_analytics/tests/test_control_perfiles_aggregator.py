import datetime

from marketing_analytics.connectors.control_perfiles.aggregator import (
    construir_snapshot_mensual,
)
from marketing_analytics.database.repository import upsert_control_perfiles, upsert_meta_organico
from marketing_analytics.models.records import ControlPerfilMensual, MetaOrganicoPost


def _post(perfil, fecha, reacciones=10, comentarios=2, compartidos=1, visualizaciones=100, id_post="p1"):
    total = reacciones + comentarios + compartidos
    return MetaOrganicoPost(
        perfil=perfil,
        pagina="Marca X Oficial",
        red="instagram",
        fecha_publicacion=fecha,
        tipo="imagen",
        descripcion="",
        alcance=0,
        visualizaciones=visualizaciones,
        total_clics=0,
        clics_enlace=0,
        reacciones=reacciones,
        comentarios=comentarios,
        compartidos=compartidos,
        total_interacciones=total,
        id_publicacion_origen=id_post,
    )


def test_agrega_publicaciones_del_mes_actual_sin_llamar_a_meta(conn):
    upsert_meta_organico(
        conn,
        [
            _post("Marca X", datetime.date(2026, 7, 5), reacciones=10, id_post="p1"),
            _post("Marca X", datetime.date(2026, 7, 20), reacciones=20, id_post="p2"),
            _post("Marca X", datetime.date(2026, 6, 15), reacciones=999, id_post="p_mes_viejo"),
        ],
    )

    snapshot = construir_snapshot_mensual(
        conn, "Marca X", "instagram", seguidores_actual=1000, hoy=datetime.date(2026, 7, 25)
    )

    assert snapshot.anio_mes == "2026-07"
    assert snapshot.publicaciones_mes == 2
    assert snapshot.likes_mes == 30
    assert snapshot.seguidores == 1000


def test_seguidores_ganados_es_cero_sin_mes_anterior(conn):
    snapshot = construir_snapshot_mensual(
        conn, "Marca X", "instagram", seguidores_actual=1000, hoy=datetime.date(2026, 7, 25)
    )

    assert snapshot.seguidores_ganados == 0


def test_seguidores_ganados_se_calcula_contra_el_mes_anterior_cerrado(conn):
    upsert_control_perfiles(
        conn,
        [
            ControlPerfilMensual(
                perfil="Marca X", red="instagram", anio_mes="2026-06", seguidores=950
            )
        ],
    )

    snapshot = construir_snapshot_mensual(
        conn, "Marca X", "instagram", seguidores_actual=1000, hoy=datetime.date(2026, 7, 25)
    )

    assert snapshot.seguidores_ganados == 50


def test_tasa_engagement_se_calcula_sobre_seguidores_actuales(conn):
    upsert_meta_organico(
        conn,
        [_post("Marca X", datetime.date(2026, 7, 5), reacciones=8, comentarios=1, compartidos=1)],
    )

    snapshot = construir_snapshot_mensual(
        conn, "Marca X", "instagram", seguidores_actual=1000, hoy=datetime.date(2026, 7, 25)
    )

    assert snapshot.interacciones_mes == 10
    assert snapshot.tasa_engagement == 0.01


def test_tasa_engagement_es_cero_si_no_hay_seguidores(conn):
    snapshot = construir_snapshot_mensual(
        conn, "Marca X", "instagram", seguidores_actual=0, hoy=datetime.date(2026, 7, 25)
    )

    assert snapshot.tasa_engagement == 0.0
