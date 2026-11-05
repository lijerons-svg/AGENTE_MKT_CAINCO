import datetime

from marketing_analytics.config.schema import ModoRangoFechas, RangoFechasConfig
from marketing_analytics.database.configuracion import registrar_fecha_hasta
from marketing_analytics.database.connection import get_connection
from marketing_analytics.services.rango_fechas import (
    resolver_rango,
    resolver_rango_automatico,
)


def test_ultimos_n_dias_calcula_desde_relativo_a_hoy():
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=30)
    hoy = datetime.date(2026, 7, 20)

    desde, hasta = resolver_rango(config, hoy=hoy)

    assert hasta == hoy
    assert desde == datetime.date(2026, 6, 20)


def test_personalizado_devuelve_fechas_explicitas_sin_importar_hoy():
    config = RangoFechasConfig(
        modo=ModoRangoFechas.PERSONALIZADO,
        fecha_inicio=datetime.date(2026, 1, 1),
        fecha_fin=datetime.date(2026, 1, 31),
    )

    desde, hasta = resolver_rango(config, hoy=datetime.date(2026, 7, 20))

    assert desde == datetime.date(2026, 1, 1)
    assert hasta == datetime.date(2026, 1, 31)


def test_automatico_sin_corrida_previa_usa_ultimos_n_dias_como_arranque():
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10)
    with get_connection(":memory:") as conn:
        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 21))

    assert desde == datetime.date(2026, 7, 11)
    assert hasta == datetime.date(2026, 7, 21)


def test_automatico_continua_desde_el_dia_siguiente_a_la_ultima_corrida():
    """Caso real pedido por el usuario: hoy corro sin fechas, mañana corro
    "actualizar" sin fechas, en 5 días corro de nuevo sin fechas — siempre
    debe continuar solo, sin pisar el histórico ya cargado. Con solape
    desactivado para aislar este comportamiento del de abajo."""
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10, dias_solape=0)
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 26))

    assert desde == datetime.date(2026, 7, 22)
    assert hasta == datetime.date(2026, 7, 26)


def test_automatico_si_se_corre_el_mismo_dia_no_genera_rango_invertido():
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10, dias_solape=0)
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 21))

    assert desde == datetime.date(2026, 7, 21)
    assert hasta == datetime.date(2026, 7, 21)


def test_automatico_por_defecto_vuelve_a_traer_7_dias_ya_cargados():
    """Meta Ads ajusta gasto/resultados hasta 7 días después por su ventana
    de atribución estándar ("7 días clic, 1 día vista") — el default
    (dias_solape=7) tiene que re-traer esos días ya cargados, no solo lo
    nuevo, para no perder esos ajustes en silencio."""
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10)
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 26))

    assert desde == datetime.date(2026, 7, 15)  # 21 - 7 + 1
    assert hasta == datetime.date(2026, 7, 26)


def test_automatico_solape_no_genera_rango_invertido_en_corridas_seguidas():
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10)
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 21))

    assert desde == datetime.date(2026, 7, 15)
    assert hasta == datetime.date(2026, 7, 21)
    assert desde <= hasta


def test_automatico_solape_configurable():
    config = RangoFechasConfig(modo=ModoRangoFechas.ULTIMOS_N_DIAS, ultimos_n_dias=10, dias_solape=14)
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 26))

    assert desde == datetime.date(2026, 7, 8)  # 21 - 14 + 1


def test_automatico_respeta_modo_personalizado_aunque_haya_checkpoint():
    config = RangoFechasConfig(
        modo=ModoRangoFechas.PERSONALIZADO,
        fecha_inicio=datetime.date(2026, 1, 1),
        fecha_fin=datetime.date(2026, 1, 31),
    )
    with get_connection(":memory:") as conn:
        registrar_fecha_hasta(conn, datetime.date(2026, 7, 21))

        desde, hasta = resolver_rango_automatico(conn, config, hoy=datetime.date(2026, 7, 26))

    assert desde == datetime.date(2026, 1, 1)
    assert hasta == datetime.date(2026, 1, 31)
