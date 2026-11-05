"""La misma publicación/campaña (mismo uid) enviada más de una vez no debe
duplicar filas — debe quedar como 'descartada' si no cambió nada."""
import datetime

from marketing_analytics.database.repository import upsert_meta_ads, upsert_meta_organico
from marketing_analytics.models.records import MetaAdsRegistro, MetaOrganicoPost


def _post(**overrides) -> MetaOrganicoPost:
    base = dict(
        perfil="perfil_001",
        pagina="Marca X - Instagram",
        red="instagram",
        fecha_publicacion=datetime.date(2026, 7, 1),
        tipo="imagen",
        descripcion="Publicación de prueba",
        alcance=1000,
        visualizaciones=1200,
        total_clics=50,
        clics_enlace=10,
        reacciones=100,
        comentarios=5,
        compartidos=2,
        total_interacciones=107,
        id_publicacion_origen="post_123",
    )
    base.update(overrides)
    return MetaOrganicoPost(**base)


def test_mismo_registro_enviado_dos_veces_no_duplica(conn):
    registro = _post()

    resultado_1 = upsert_meta_organico(conn, [registro])
    resultado_2 = upsert_meta_organico(conn, [registro])

    total_filas = conn.execute("SELECT COUNT(*) AS n FROM meta_organico").fetchone()["n"]

    assert resultado_1.nuevos == 1
    assert resultado_2.nuevos == 0
    assert resultado_2.descartados == 1
    assert total_filas == 1


def test_uid_distingue_por_fecha_y_perfil(conn):
    a = _post(id_publicacion_origen="post_1", fecha_publicacion=datetime.date(2026, 7, 1))
    b = _post(id_publicacion_origen="post_1", perfil="perfil_002", fecha_publicacion=datetime.date(2026, 7, 1))
    c = _post(id_publicacion_origen="post_1", fecha_publicacion=datetime.date(2026, 7, 2))

    resultado = upsert_meta_organico(conn, [a, b, c])

    assert resultado.nuevos == 3
    assert len({a.uid, b.uid, c.uid}) == 3


def test_dedupe_tambien_aplica_a_meta_ads(conn):
    campana = MetaAdsRegistro(
        cuenta_publicitaria="act_123",
        perfil_unidad="Marca X",
        red="facebook",
        campana="Campaña Julio",
        fecha_publicacion=datetime.date(2026, 7, 1),
        objetivo="TRAFFIC",
        moneda="BOB",
        importe_gastado=150.5,
        alcance=5000,
        impresiones=8000,
        clics=200,
        ctr=2.5,
        cpc=0.75,
        resultados=40,
        id_campana_origen="camp_999",
    )

    upsert_meta_ads(conn, [campana])
    resultado = upsert_meta_ads(conn, [campana])

    total_filas = conn.execute("SELECT COUNT(*) AS n FROM meta_ads").fetchone()["n"]
    assert resultado.descartados == 1
    assert total_filas == 1


def _campana_ads(**overrides) -> MetaAdsRegistro:
    base = dict(
        cuenta_publicitaria="act_123",
        perfil_unidad="Marca X",
        red="facebook",
        campana="Campaña Julio",
        fecha_publicacion=datetime.date(2026, 7, 1),
        objetivo="TRAFFIC",
        moneda="BOB",
        importe_gastado=150.5,
        alcance=5000,
        impresiones=8000,
        clics=200,
        ctr=2.5,
        cpc=0.75,
        resultados=40,
        id_campana_origen="camp_999",
    )
    base.update(overrides)
    return MetaAdsRegistro(**base)


def test_meta_ads_facebook_e_instagram_de_la_misma_campana_no_se_pisan(conn):
    """Con ubicación automática, Meta manda una fila por red para la misma
    campaña y fecha — antes colisionaban en el mismo uid y una pisaba a la
    otra, perdiendo el gasto de una de las dos redes."""
    fb = _campana_ads(red="facebook", importe_gastado=100.0)
    ig = _campana_ads(red="instagram", importe_gastado=250.0)

    upsert_meta_ads(conn, [fb, ig])

    filas = conn.execute("SELECT red, importe_gastado FROM meta_ads ORDER BY red").fetchall()
    assert len(filas) == 2
    valores = {fila["red"]: fila["importe_gastado"] for fila in filas}
    assert valores == {"facebook": 100.0, "instagram": 250.0}
