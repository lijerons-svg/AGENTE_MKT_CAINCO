from marketing_analytics.reports_pptx.generador import (
    _FILAS_POR_SLIDE_DETALLE,
    _anuncio_para_grid,
    _post_para_grid,
    generar_pptx_mailchimp,
    generar_pptx_unidad,
)

_ORGANICO = [
    {"red": "facebook", "fecha": "2026-08-03", "tipo": "photo", "descripcion": "Post FB", "visualizaciones": 1000, "total_interacciones": 80, "total_clics": 12, "alcance": 0, "comentarios": 3, "compartidos": 2, "imagen_url": ""},
    {"red": "instagram", "fecha": "2026-08-05", "tipo": "video", "descripcion": "Reel IG", "visualizaciones": 5000, "total_interacciones": 600, "total_clics": 0, "alcance": 2000, "comentarios": 20, "compartidos": 10, "imagen_url": ""},
    {"red": "facebook", "fecha": "2026-07-20", "tipo": "status", "descripcion": "Post de otro mes", "visualizaciones": 999, "total_interacciones": 999, "total_clics": 0, "alcance": 0, "comentarios": 0, "compartidos": 0, "imagen_url": ""},
]
_CONTROL_PERFILES = [
    {"red": "facebook", "anio_mes": "2026-08", "seguidores": 1000, "seguidores_ganados": 50, "publicaciones_mes": 2, "visualizaciones_mes": 1500, "interacciones_mes": 85},
    {"red": "instagram", "anio_mes": "2026-08", "seguidores": 2000, "seguidores_ganados": 100, "publicaciones_mes": 1, "visualizaciones_mes": 5000, "interacciones_mes": 600},
]
_ADS = [
    {"campana": "ACADEMY - test", "fecha": "2026-08-04", "importe_gastado": 50.0, "impresiones": 10000, "alcance": 4000, "clics": 100, "ctr": 1.0, "cpc": 0.5, "resultados": 20, "objetivo": "OUTCOME_TRAFFIC"},
]


def test_generar_pptx_unidad_arma_siete_slides_con_todo_disponible(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
        competidores=[{"nombre": "Comp X", "seguidores": 500, "cantidad_publicaciones": 3, "publicaciones": ["a", "b"]}],
    )
    assert len(constructor.prs.slides._sldIdLst) == 7


def test_generar_pptx_unidad_filtra_por_mes_pedido(tmp_path):
    """El post de julio no debe colarse en un reporte de agosto."""
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    # Sin competidores: portada + KPIs + campañas + top4 + detalle + mejora = 6 (sin la de competencia)
    assert len(constructor.prs.slides._sldIdLst) == 6


def test_generar_pptx_unidad_sin_publicaciones_no_rompe(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Unidad Vacia", anio=2026, mes=8,
        filas_organico=[], filas_control_perfiles=[], filas_ads=[],
        carpeta_imagenes_tmp=tmp_path,
    )
    # Portada + KPIs (vacío) + campañas (vacío) + detalle (vacío) = 4;
    # sin publicaciones no hay slides de top4/mejora.
    assert len(constructor.prs.slides._sldIdLst) == 4


def test_post_para_grid_sin_imagen_muestra_link_de_respaldo(tmp_path):
    fila = {"red": "facebook", "tipo": "photo", "descripcion": "Post sin imagen", "visualizaciones": 100, "total_interacciones": 5, "total_clics": 1, "imagen_url": "", "link": "https://facebook.com/post/123"}
    resultado = _post_para_grid(fila, tmp_path, "top", 0)
    assert resultado["link_respaldo"] == "https://facebook.com/post/123"


def test_post_para_grid_con_imagen_real_no_muestra_link_de_respaldo(tmp_path, monkeypatch):
    fila = {"red": "facebook", "tipo": "photo", "descripcion": "Post con imagen", "visualizaciones": 100, "total_interacciones": 5, "total_clics": 1, "imagen_url": "https://example.com/foto.png", "link": "https://facebook.com/post/123"}
    monkeypatch.setattr(
        "marketing_analytics.reports_pptx.generador.obtener_imagen_post",
        lambda *args, **kwargs: (tmp_path / "foto.png", False),
    )
    resultado = _post_para_grid(fila, tmp_path, "top", 0)
    assert resultado["link_respaldo"] is None


def test_slide_kpis_agrega_grafico_comparativo_solo_con_dos_redes(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    slide_kpis = constructor.prs.slides[1]
    graficos = [shape for shape in slide_kpis.shapes if shape.has_chart]
    assert len(graficos) == 1
    series = list(graficos[0].chart.series)
    assert series[0].values == (1500, 85)  # facebook: visualizaciones, interacciones
    assert series[1].values == (5000, 600)  # instagram: visualizaciones, interacciones


def test_slide_kpis_no_agrega_grafico_con_una_sola_red(tmp_path):
    control_una_red = [_CONTROL_PERFILES[0]]
    organico_una_red = [f for f in _ORGANICO if f["red"] == "facebook"]
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=organico_una_red, filas_control_perfiles=control_una_red, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    slide_kpis = constructor.prs.slides[1]
    graficos = [shape for shape in slide_kpis.shapes if shape.has_chart]
    assert graficos == []


def test_anuncio_para_grid_arma_kpis_de_pauta(tmp_path):
    anuncio = {
        "ad_id": "1", "titulo": "Anuncio top", "red": "facebook", "tipo": "Imagen",
        "imagen_url": "", "impresiones": 1000, "clics": 20, "engagement": 50, "inversion": 12.5,
    }
    resultado = _anuncio_para_grid(anuncio, tmp_path, 0)
    assert resultado["titulo"] == "Anuncio top"
    assert resultado["link_respaldo"] is None
    assert ("Inversión", "$12.50") in resultado["kpis"]


def test_generar_pptx_unidad_agrega_slide_de_pauta_destacada_si_hay_anuncios(tmp_path):
    anuncios = [
        {"ad_id": "1", "titulo": "A1", "red": "facebook", "tipo": "Imagen", "imagen_url": "", "impresiones": 10, "clics": 1, "engagement": 5, "inversion": 1.0},
    ]
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
        anuncios_destacados=anuncios,
    )
    # Sin competidores + con pauta destacada: portada + KPIs + campañas + pauta destacada + top4 + detalle + mejora = 7
    assert len(constructor.prs.slides._sldIdLst) == 7


def test_generar_pptx_unidad_sin_anuncios_destacados_no_agrega_slide(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
        anuncios_destacados=None,
    )
    assert len(constructor.prs.slides._sldIdLst) == 6


def test_detalle_publicaciones_pagina_cuando_hay_mas_filas_que_el_limite(tmp_path):
    muchas_filas = [
        {"red": "facebook", "fecha": f"2026-08-{dia:02d}", "tipo": "photo", "descripcion": f"Post {dia}", "visualizaciones": 10, "total_interacciones": 1, "total_clics": 0, "comentarios": 0, "compartidos": 0, "imagen_url": ""}
        for dia in range(1, _FILAS_POR_SLIDE_DETALLE + 3)
    ]
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=muchas_filas, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    # Portada + KPIs + campañas + top4 + detalle(x2 páginas) + mejora = 7
    assert len(constructor.prs.slides._sldIdLst) == 7
    titulos = [
        shape.text_frame.text
        for slide in constructor.prs.slides
        for shape in slide.shapes
        if shape.has_text_frame and "DETALLE DE PUBLICACIONES" in shape.text_frame.text
    ]
    assert any("(1/2)" in t for t in titulos)
    assert any("(2/2)" in t for t in titulos)


def test_generar_pptx_mailchimp_arma_portada_y_slide_de_envios():
    mailchimp = [
        {"nombre_campana": "Newsletter", "fecha": "2026-08-05", "destinatarios": 100, "tasa_apertura": 0.3, "tasa_clics": 0.05, "bajas": 1, "clics_whatsapp": 3},
    ]
    constructor = generar_pptx_mailchimp(2026, 8, mailchimp)
    # Portada + slide de Mailchimp = 2, no ligado a ninguna unidad.
    assert len(constructor.prs.slides._sldIdLst) == 2


def test_generar_pptx_mailchimp_filtra_por_mes_pedido():
    """Un envío de julio no debe aparecer en el reporte de agosto."""
    mailchimp = [{"nombre_campana": "Vieja", "fecha": "2026-07-15", "destinatarios": 10, "tasa_apertura": 0.1, "tasa_clics": 0.01, "bajas": 0}]
    constructor = generar_pptx_mailchimp(2026, 8, mailchimp)
    slide_mailchimp = constructor.prs.slides[1]
    textos = [shape.text_frame.text for shape in slide_mailchimp.shapes if shape.has_text_frame]
    assert any("Sin envíos registrados este mes." in t for t in textos)


def test_generar_pptx_mailchimp_sin_envios_no_rompe():
    constructor = generar_pptx_mailchimp(2026, 8, [])
    assert len(constructor.prs.slides._sldIdLst) == 2


def test_generar_pptx_mailchimp_pagina_cuando_hay_muchos_envios():
    muchos = [
        {"nombre_campana": f"Envío {i}", "fecha": f"2026-08-{i:02d}", "entregas": 100, "aperturas_unicas": 30, "clics_unicos": 5, "clics_totales": 6, "bajas": 0, "clics_whatsapp": 1}
        for i in range(1, 15)
    ]
    constructor = generar_pptx_mailchimp(2026, 8, muchos)
    # Portada + 2 páginas de la tabla (14 filas / 9 por slide) = 3 slides.
    assert len(constructor.prs.slides._sldIdLst) == 3
    titulos = [
        shape.text_frame.text
        for slide in constructor.prs.slides
        for shape in slide.shapes
        if shape.has_text_frame and "EMAIL MARKETING" in shape.text_frame.text
    ]
    assert any("(1/2)" in t for t in titulos)
    assert any("(2/2)" in t for t in titulos)


def test_generar_pptx_mailchimp_tarjetas_kpi_solo_en_la_primera_pagina():
    muchos = [
        {"nombre_campana": f"Envío {i}", "fecha": f"2026-08-{i:02d}", "entregas": 100, "aperturas_unicas": 30, "clics_unicos": 5, "clics_totales": 6, "bajas": 0, "clics_whatsapp": 1}
        for i in range(1, 15)
    ]
    constructor = generar_pptx_mailchimp(2026, 8, muchos)
    slide_pagina_1 = constructor.prs.slides[1]
    slide_pagina_2 = constructor.prs.slides[2]
    textos_1 = [shape.text_frame.text for shape in slide_pagina_1.shapes if shape.has_text_frame]
    textos_2 = [shape.text_frame.text for shape in slide_pagina_2.shapes if shape.has_text_frame]
    assert "Open Rate" in textos_1
    assert "Open Rate" not in textos_2


def test_slide_kpis_muestra_delta_vs_mes_anterior(tmp_path):
    control_dos_meses = _CONTROL_PERFILES + [
        {"red": "facebook", "anio_mes": "2026-07", "seguidores": 900, "seguidores_ganados": 40, "publicaciones_mes": 1, "visualizaciones_mes": 1000, "interacciones_mes": 50},
        {"red": "instagram", "anio_mes": "2026-07", "seguidores": 1800, "seguidores_ganados": 80, "publicaciones_mes": 1, "visualizaciones_mes": 4000, "interacciones_mes": 500},
    ]
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=control_dos_meses, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    slide_kpis = constructor.prs.slides[1]
    textos = [shape.text_frame.text for shape in slide_kpis.shapes if shape.has_text_frame]
    assert any("vs mes ant." in t for t in textos)


def test_slide_kpis_sin_mes_anterior_no_muestra_delta(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    slide_kpis = constructor.prs.slides[1]
    textos = [shape.text_frame.text for shape in slide_kpis.shapes if shape.has_text_frame]
    assert not any("vs mes ant." in t for t in textos)


def test_generar_pptx_unidad_se_puede_guardar_a_disco(tmp_path):
    constructor = generar_pptx_unidad(
        unidad="Academy Cainco", anio=2026, mes=8,
        filas_organico=_ORGANICO, filas_control_perfiles=_CONTROL_PERFILES, filas_ads=_ADS,
        carpeta_imagenes_tmp=tmp_path,
    )
    destino = tmp_path / "reporte.pptx"
    constructor.guardar(destino)
    assert destino.exists()
    assert destino.stat().st_size > 0
