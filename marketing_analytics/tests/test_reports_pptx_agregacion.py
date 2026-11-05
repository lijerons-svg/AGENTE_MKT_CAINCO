from marketing_analytics.reports_pptx import agregacion


def test_engagement_post_es_cero_sin_visualizaciones():
    assert agregacion.engagement_post({"visualizaciones": 0, "total_interacciones": 50}) == 0.0


def test_engagement_post_formula():
    fila = {"visualizaciones": 1000, "total_interacciones": 80}
    assert agregacion.engagement_post(fila) == 8.0


def test_filtrar_por_mes_solo_deja_el_mes_pedido():
    filas = [{"fecha": "2026-08-03"}, {"fecha": "2026-07-31"}, {"fecha": "2026-08-31"}]
    resultado = agregacion.filtrar_por_mes(filas, 2026, 8)
    assert len(resultado) == 2


def test_kpis_organico_por_red_una_entrada_por_red():
    filas = [
        {"red": "facebook", "seguidores": 100, "seguidores_ganados": 5, "publicaciones_mes": 3, "visualizaciones_mes": 900, "interacciones_mes": 40},
        {"red": "instagram", "seguidores": 200, "seguidores_ganados": 10, "publicaciones_mes": 2, "visualizaciones_mes": 500, "interacciones_mes": 60},
    ]
    resultado = agregacion.kpis_organico_por_red(filas)
    assert resultado["facebook"]["publicaciones"] == 3
    assert resultado["instagram"]["nuevos_seguidores"] == 10


def test_kpis_organico_por_red_no_inventa_red_sin_datos():
    resultado = agregacion.kpis_organico_por_red([{"red": "facebook", "seguidores": 1}])
    assert "instagram" not in resultado


def test_alcance_promedio_solo_para_instagram():
    filas = [
        {"red": "facebook", "alcance": 500},
        {"red": "instagram", "alcance": 1000},
        {"red": "instagram", "alcance": 2000},
    ]
    resultado = agregacion.alcance_promedio_por_red(filas)
    assert "facebook" not in resultado
    assert resultado["instagram"] == 1500


def test_alcance_promedio_ignora_ceros_no_informados():
    filas = [{"red": "instagram", "alcance": 0}, {"red": "instagram", "alcance": 400}]
    assert agregacion.alcance_promedio_por_red(filas)["instagram"] == 400


def test_top_publicaciones_ordena_por_engagement_descendente():
    filas = [
        {"visualizaciones": 100, "total_interacciones": 1},
        {"visualizaciones": 100, "total_interacciones": 50},
        {"visualizaciones": 100, "total_interacciones": 20},
    ]
    top = agregacion.top_publicaciones(filas, cantidad=2)
    assert [f["total_interacciones"] for f in top] == [50, 20]


def test_top_publicaciones_menor_primero_para_contenido_a_mejorar():
    filas = [
        {"visualizaciones": 100, "total_interacciones": 1},
        {"visualizaciones": 100, "total_interacciones": 50},
    ]
    peores = agregacion.top_publicaciones(filas, cantidad=1, menor_primero=True)
    assert peores[0]["total_interacciones"] == 1


def test_detalle_publicaciones_ordena_por_fecha():
    filas = [{"fecha": "2026-08-20"}, {"fecha": "2026-08-01"}]
    resultado = agregacion.detalle_publicaciones(filas)
    assert [f["fecha"] for f in resultado] == ["2026-08-01", "2026-08-20"]


def test_detalle_campanas_frecuencia_y_conversion():
    filas = [
        {"campana": "X", "importe_gastado": 10.0, "impresiones": 1000, "alcance": 500, "clics": 50, "ctr": 5.0, "cpc": 0.2, "resultados": 10, "objetivo": "OUTCOME_TRAFFIC"},
    ]
    resultado = agregacion.detalle_campanas(filas)
    assert resultado[0]["frecuencia"] == 2.0
    assert resultado[0]["conversion"] == 20.0


def test_detalle_campanas_conversion_no_aplica_en_campana_de_alcance():
    filas = [
        {"campana": "Y", "importe_gastado": 5.0, "impresiones": 500, "alcance": 500, "clics": 10, "ctr": 2.0, "cpc": 0.5, "resultados": 500, "objetivo": "OUTCOME_AWARENESS"},
    ]
    resultado = agregacion.detalle_campanas(filas)
    assert resultado[0]["conversion"] is None


def test_detalle_campanas_conversion_no_aplica_sin_clics():
    filas = [
        {"campana": "Z", "importe_gastado": 1.0, "impresiones": 100, "alcance": 100, "clics": 0, "ctr": 0.0, "cpc": 0.0, "resultados": 0, "objetivo": "OUTCOME_TRAFFIC"},
    ]
    assert agregacion.detalle_campanas(filas)[0]["conversion"] is None


def test_formato_post_mapea_tipos_conocidos():
    # "tipo" ya viene traducido por el mapper (ej. "photo" -> "imagen")
    # antes de llegar acá — se prueba con el valor ya mapeado.
    assert agregacion.formato_post({"tipo": "imagen"}) == "Imagen"
    assert agregacion.formato_post({"tipo": "album"}) == "Carrusel"


def test_formato_post_devuelve_tipo_crudo_si_no_esta_mapeado():
    assert agregacion.formato_post({"tipo": "cosa_rara"}) == "cosa_rara"


def test_formato_post_sin_tipo():
    assert agregacion.formato_post({"tipo": ""}) == "Sin tipo"


def test_mes_anterior_caso_normal():
    assert agregacion.mes_anterior(2026, 8) == (2026, 7)


def test_mes_anterior_cruza_de_enero_a_diciembre_del_anio_previo():
    assert agregacion.mes_anterior(2026, 1) == (2025, 12)


def test_delta_porcentual_caso_normal():
    assert agregacion.delta_porcentual(120, 100) == 20.0
    assert agregacion.delta_porcentual(80, 100) == -20.0


def test_delta_porcentual_none_sin_base_de_comparacion():
    assert agregacion.delta_porcentual(50, 0) is None


def test_deltas_kpis_red_compara_metricas_comparables():
    actual = {"facebook": {"visualizaciones": 120, "interacciones": 90, "nuevos_seguidores": 10, "publicaciones": 5}}
    anterior = {"facebook": {"visualizaciones": 100, "interacciones": 100, "nuevos_seguidores": 5, "publicaciones": 4}}
    resultado = agregacion.deltas_kpis_red(actual, anterior)
    assert resultado["facebook"]["visualizaciones"] == 20.0
    assert resultado["facebook"]["interacciones"] == -10.0
    # nuevos_seguidores compara en cantidad absoluta, no en %.
    assert resultado["facebook"]["nuevos_seguidores"] == 5
    assert "publicaciones" not in resultado["facebook"]


def test_deltas_kpis_red_nuevos_seguidores_no_engana_con_base_negativa():
    """Perder 5 seguidores en vez de 10 es una mejora — no debe leerse como
    un empeoramiento del doble solo porque el mes anterior también fue
    negativo."""
    actual = {"facebook": {"visualizaciones": 100, "interacciones": 50, "nuevos_seguidores": -5}}
    anterior = {"facebook": {"visualizaciones": 100, "interacciones": 50, "nuevos_seguidores": -10}}
    resultado = agregacion.deltas_kpis_red(actual, anterior)
    assert resultado["facebook"]["nuevos_seguidores"] == 5  # mejoró: perdió 5 menos que antes


def test_deltas_kpis_red_omite_red_sin_mes_anterior():
    actual = {"instagram": {"visualizaciones": 100, "interacciones": 50, "nuevos_seguidores": 5}}
    resultado = agregacion.deltas_kpis_red(actual, {})
    assert resultado == {}


def test_kpis_mailchimp_pondera_tasas_por_volumen_y_suma_totales():
    filas = [
        {"entregas": 100, "aperturas_unicas": 30, "clics_unicos": 5, "clics_totales": 8, "bajas": 2},
        {"entregas": 900, "aperturas_unicas": 360, "clics_unicos": 63, "clics_totales": 70, "bajas": 3},
    ]
    resultado = agregacion.kpis_mailchimp(filas)
    assert resultado["envios"] == 2
    assert resultado["entregados"] == 1000
    assert resultado["clics"] == 78
    # (30+360)/(100+900)*100 = 39%, ponderado — no el 34.5% de promediar 30% y 45% sin ponderar.
    assert resultado["apertura_promedio"] == 39.0
    assert round(resultado["clics_promedio"], 1) == 6.8
    assert resultado["bajas"] == 5


def test_kpis_mailchimp_sin_envios_no_rompe():
    resultado = agregacion.kpis_mailchimp([])
    assert resultado == {"envios": 0, "entregados": 0, "clics": 0, "apertura_promedio": 0.0, "clics_promedio": 0.0, "bajas": 0}


def test_detalle_mailchimp_ordena_por_fecha():
    filas = [
        {"fecha": "2026-08-20", "entregas": 100, "aperturas_unicas": 20, "clics_unicos": 5},
        {"fecha": "2026-08-01", "entregas": 100, "aperturas_unicas": 20, "clics_unicos": 5},
    ]
    resultado = agregacion.detalle_mailchimp(filas)
    assert [f["fecha"] for f in resultado] == ["2026-08-01", "2026-08-20"]


def test_detalle_mailchimp_calcula_open_rate_click_rate_y_ctor():
    filas = [{"fecha": "2026-08-01", "entregas": 200, "aperturas_unicas": 50, "clics_unicos": 10}]
    resultado = agregacion.detalle_mailchimp(filas)
    assert resultado[0]["open_rate"] == 25.0
    assert resultado[0]["click_rate"] == 5.0
    assert resultado[0]["ctor"] == 20.0


def test_detalle_mailchimp_sin_aperturas_no_rompe_ctor():
    filas = [{"fecha": "2026-08-01", "entregas": 200, "aperturas_unicas": 0, "clics_unicos": 0}]
    resultado = agregacion.detalle_mailchimp(filas)
    assert resultado[0]["ctor"] == 0.0
