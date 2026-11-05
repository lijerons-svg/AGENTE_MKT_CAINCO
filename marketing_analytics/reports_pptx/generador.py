"""Arma el .pptx de una unidad a partir de los datos ya agregados. Separado
de `agregacion.py` (lógica pura) para que la parte de red (descarga de
imágenes) quede aislada y sea fácil de simular en tests."""
from __future__ import annotations

import calendar
from pathlib import Path

from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt

from marketing_analytics.reports_pptx import agregacion, estilos
from marketing_analytics.reports_pptx.imagenes import obtener_imagen_post

_FILAS_POR_SLIDE_DETALLE = 12

_MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _periodo_texto(anio: int, mes: int) -> str:
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return f"1 al {ultimo_dia} de {_MESES_ES[mes]}"


def _slide_portada(
    c: estilos.ConstructorReporte, titulo: str, periodo: str, eyebrow: str = "CONTENIDO ORGÁNICO Y PAUTA RRSS"
) -> None:
    s = c.nueva_slide()
    c.fondo(s, estilos.AZUL)
    c.rectangulo(s, 0, Inches(4.8), c.prs.slide_width, Inches(2.7), color_relleno=estilos.AZUL_CLARO)
    c.caja_texto(s, Inches(0.7), Inches(0.6), Inches(9), Inches(0.5), eyebrow, 15, estilos.CIAN, negrita=True)
    c.caja_texto(s, Inches(0.7), Inches(1.1), Inches(11), Inches(1.2), titulo.upper(), 44, estilos.BLANCO, negrita=True)
    c.caja_texto(s, Inches(0.7), Inches(2.05), Inches(9), Inches(1.0), "(REPORTE MENSUAL)", 30, estilos.BLANCO, negrita=True)
    c.pastilla(s, Inches(0.75), Inches(3.15), f"Del {periodo}", estilos.NARANJA, ancho=Inches(3.2))
    c.caja_texto(s, Inches(0.7), Inches(6.7), Inches(9), Inches(0.5), "CAINCO — Cámara de Industria, Comercio, Servicios y Turismo de Santa Cruz", 11, estilos.BLANCO)


def _pinta_delta(c: estilos.ConstructorReporte, slide, x, y, delta: float | None, es_absoluto: bool = False) -> None:
    """Flecha + variación vs. el mes anterior, verde si sube y rojo si baja.
    No dibuja nada cuando no hay base de comparación (delta None) — el
    primer mes que se genera de una unidad, por ejemplo. `es_absoluto`
    muestra la diferencia en cantidad en vez de porcentaje — para métricas
    que pueden ser negativas (nuevos_seguidores), un % contra una base
    negativa da una lectura que engaña (ver deltas_kpis_red)."""
    if delta is None:
        return
    color = estilos.VERDE if delta >= 0 else estilos.ROJO_BAJA
    flecha = "▲" if delta >= 0 else "▼"
    if es_absoluto:
        texto = f"{flecha} {abs(delta):,.0f} vs mes ant.".replace(",", ".")
    else:
        texto = f"{flecha} {abs(delta):.0f}% vs mes ant."
    c.caja_texto(slide, x, y, Inches(1.4), Inches(0.3), texto, 10, color, negrita=True)


def _slide_kpis_organico(
    c: estilos.ConstructorReporte, periodo: str, kpis_red: dict, alcance_red: dict, deltas_red: dict | None = None
) -> None:
    s = c.nueva_slide()
    c.encabezado_slide(s, "CONTENIDO ORGÁNICO — MÉTRICAS", periodo)
    redes_presentes = [r for r in ("facebook", "instagram") if r in kpis_red]
    if not redes_presentes:
        c.caja_texto(s, Inches(0.5), Inches(1.5), Inches(10), Inches(0.6), "Sin publicaciones registradas este mes.", 14, estilos.GRIS_TEXTO)
        return
    deltas_red = deltas_red or {}
    ancho_col = Inches(3.0)
    x0 = Inches(0.5)
    espacio = Inches(0.35)
    for i, red in enumerate(redes_presentes):
        datos = kpis_red[red]
        deltas = deltas_red.get(red, {})
        x = x0 + i * (ancho_col + espacio)
        c.rectangulo(s, x, Inches(1.25), ancho_col, Inches(5.9), color_relleno=estilos.BLANCO, color_borde=estilos.GRIS_BORDE, radio=True)
        c.caja_texto(s, x + Inches(0.2), Inches(1.4), ancho_col - Inches(0.4), Inches(0.4), red.capitalize(), 18, estilos.COLOR_POR_RED[red], negrita=True)
        c.caja_texto(s, x + Inches(0.2), Inches(1.85), ancho_col - Inches(0.4), Inches(0.35), f"Comunidad Cainco: {datos['seguidores']:,}".replace(",", "."), 10.5, estilos.GRIS_TEXTO)
        filas_kpi = [("Visualizaciones", f"{datos['visualizaciones']:,}".replace(",", "."), deltas.get("visualizaciones"), False), ("Publicaciones", str(datos["publicaciones"]), None, False)]
        if red in agregacion.REDES_CON_ALCANCE_ORGANICO:
            filas_kpi.append(("Alcance promedio", f"{alcance_red.get(red, 0):,}".replace(",", "."), None, False))
        filas_kpi += [
            ("Interacciones", f"{datos['interacciones']:,}".replace(",", "."), deltas.get("interacciones"), False),
            ("Nuevos seguidores", f"{datos['nuevos_seguidores']:+,}".replace(",", "."), deltas.get("nuevos_seguidores"), True),
        ]
        y = Inches(2.4)
        for etiqueta, valor, delta, delta_absoluto in filas_kpi:
            c.rectangulo(s, x + Inches(0.2), y, ancho_col - Inches(0.4), Inches(0.8), color_relleno=estilos.GRIS_FONDO, radio=True)
            c.caja_texto(s, x + Inches(0.35), y + Inches(0.08), ancho_col - Inches(0.7), Inches(0.3), etiqueta, 11, estilos.GRIS_TEXTO)
            c.caja_texto(s, x + Inches(0.35), y + Inches(0.36), ancho_col - Inches(0.7), Inches(0.4), valor, 20, estilos.AZUL, negrita=True)
            _pinta_delta(c, s, x + Inches(1.85), y + Inches(0.44), delta, es_absoluto=delta_absoluto)
            y += Inches(0.95)

    if len(redes_presentes) > 1:
        _grafico_comparativo_redes(s, kpis_red, redes_presentes)


def _grafico_comparativo_redes(slide, kpis_red: dict, redes_presentes: list[str]) -> None:
    """Compara Facebook vs Instagram en el espacio que sobra a la derecha
    de las tarjetas — Visualizaciones e Interacciones son las únicas dos
    métricas que existen igual en ambas redes."""
    datos = CategoryChartData()
    datos.categories = ["Visualizaciones", "Interacciones"]
    for red in redes_presentes:
        d = kpis_red[red]
        datos.add_series(red.capitalize(), (d["visualizaciones"], d["interacciones"]))

    x, y, w, h = Inches(7.3), Inches(1.4), Inches(5.5), Inches(4.2)
    grafico_marco = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, w, h, datos)
    chart = grafico_marco.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(11)
    for serie, red in zip(chart.plots[0].series, redes_presentes):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = estilos.COLOR_POR_RED[red]
    chart.category_axis.tick_labels.font.size = Pt(11)
    chart.value_axis.tick_labels.font.size = Pt(10)
    chart.value_axis.has_major_gridlines = False


def _slide_competencia(c: estilos.ConstructorReporte, unidad: str, periodo: str, competidores: list[dict]) -> None:
    s = c.nueva_slide()
    c.encabezado_slide(s, f"COMPETENCIA — {unidad.upper()} (solo Facebook, dato público)", periodo)
    n = len(competidores)
    ancho_c = Inches(12.4) / n if n else Inches(4.0)
    x0 = Inches(0.4)
    for i, comp in enumerate(competidores):
        x = x0 + i * (ancho_c + Inches(0.15))
        c.rectangulo(s, x, Inches(1.2), ancho_c, Inches(5.95), color_relleno=estilos.BLANCO, color_borde=estilos.GRIS_BORDE, radio=True)
        c.caja_texto(s, x + Inches(0.25), Inches(1.35), ancho_c - Inches(0.5), Inches(0.45), comp["nombre"], 15, estilos.AZUL, negrita=True)
        ancho_kpi_c = (ancho_c - Inches(0.5)) / 2
        c.rectangulo(s, x + Inches(0.25), Inches(1.85), ancho_kpi_c - Inches(0.05), Inches(0.75), color_relleno=estilos.GRIS_FONDO, radio=True)
        c.caja_texto(s, x + Inches(0.35), Inches(1.92), ancho_kpi_c - Inches(0.2), Inches(0.3), "Seguidores", 9.5, estilos.GRIS_TEXTO)
        c.caja_texto(s, x + Inches(0.35), Inches(2.2), ancho_kpi_c - Inches(0.2), Inches(0.35), f"{comp['seguidores']:,}".replace(",", "."), 16, estilos.AZUL, negrita=True)
        c.rectangulo(s, x + Inches(0.3) + ancho_kpi_c, Inches(1.85), ancho_kpi_c - Inches(0.05), Inches(0.75), color_relleno=estilos.GRIS_FONDO, radio=True)
        c.caja_texto(s, x + Inches(0.4) + ancho_kpi_c, Inches(1.92), ancho_kpi_c - Inches(0.2), Inches(0.3), "Publicaciones", 9.5, estilos.GRIS_TEXTO)
        c.caja_texto(s, x + Inches(0.4) + ancho_kpi_c, Inches(2.2), ancho_kpi_c - Inches(0.2), Inches(0.35), str(comp["cantidad_publicaciones"]), 16, estilos.AZUL, negrita=True)
        c.caja_texto(s, x + Inches(0.25), Inches(2.85), ancho_c - Inches(0.5), Inches(0.3), "PUBLICÓ ESTE MES", 10.5, estilos.GRIS_TEXTO, negrita=True)
        y = Inches(3.25)
        for texto in comp["publicaciones"][:6]:
            recorte = texto if len(texto) <= 90 else texto[:87] + "..."
            c.caja_texto(s, x + Inches(0.3), y, ancho_c - Inches(0.6), Inches(0.65), f"•  {recorte}", 10.5, RGBColor(0x2A, 0x2A, 0x2A))
            y += Inches(0.72)


def _slide_detalle_campanas(c: estilos.ConstructorReporte, periodo: str, filas: list[dict]) -> None:
    s = c.nueva_slide()
    c.encabezado_slide(s, "PAUTA — DETALLE DE CAMPAÑAS", periodo)
    if not filas:
        c.caja_texto(s, Inches(0.5), Inches(1.5), Inches(10), Inches(0.6), "Sin campañas registradas este mes.", 14, estilos.GRIS_TEXTO)
        return
    encabezados = ["Campaña", "Inversión ($)", "Impresiones", "Alcance", "Frecuencia", "Clics", "CTR", "CPC", "Conversión"]
    filas_tabla = [
        [
            f["campana"],
            f"{f['inversion']:.2f}",
            f"{f['impresiones']:,}".replace(",", "."),
            f"{f['alcance']:,}".replace(",", "."),
            f"{f['frecuencia']:.1f}",
            f"{f['clics']:,}".replace(",", "."),
            f"{f['ctr']:.2f}%",
            f"{f['cpc']:.3f}",
            "No aplica" if f["conversion"] is None else f"{f['conversion']:.1f}%",
        ]
        for f in filas
    ]
    c.tabla(s, Inches(0.35), Inches(1.35), Inches(12.6), Inches(2.6), encabezados, filas_tabla, tam_fuente=11)
    c.caja_texto(s, Inches(0.4), Inches(4.7), Inches(11.5), Inches(0.4), "Nota: 'Resultados' de Meta equivale a alcance en campañas de reconocimiento — la conversión no aplica a esas filas.", 9.5, estilos.GRIS_TEXTO)


def _post_para_grid(fila: dict, carpeta_imgs: Path, prefijo: str, indice: int) -> dict:
    red = fila["red"]
    etiqueta = estilos.ETIQUETA_POR_RED.get(red, red[:2].upper())
    ruta_imagen, es_placeholder = obtener_imagen_post(fila.get("imagen_url", ""), etiqueta, carpeta_imgs, f"{prefijo}_{indice}.png")
    kpis = [
        ("Visualización", f"{fila.get('visualizaciones', 0):,}".replace(",", ".")),
        ("Interacción", f"{fila.get('total_interacciones', 0):,}".replace(",", ".")),
        ("Engagement", f"{agregacion.engagement_post(fila):.1f}%"),
        ("Clic", f"{fila.get('total_clics', 0):,}".replace(",", ".") if red == "facebook" else "—"),
    ]
    titulo = (fila.get("descripcion") or "(sin descripción)")[:60]
    return {
        "imagen_ruta": ruta_imagen,
        "red": red,
        "red_label": etiqueta,
        "tipo": agregacion.formato_post(fila),
        "titulo": titulo,
        "kpis": kpis,
        "link_respaldo": fila.get("link") if es_placeholder else None,
    }


def _anuncio_para_grid(anuncio: dict, carpeta_imgs: Path, indice: int) -> dict:
    red = anuncio.get("red", "")
    etiqueta = estilos.ETIQUETA_POR_RED.get(red, (red[:2] or "AD").upper())
    ruta_imagen, _ = obtener_imagen_post(anuncio.get("imagen_url", ""), etiqueta, carpeta_imgs, f"pauta_{indice}.png")
    kpis = [
        ("Impresiones", f"{anuncio.get('impresiones', 0):,}".replace(",", ".")),
        ("Clics", f"{anuncio.get('clics', 0):,}".replace(",", ".")),
        ("Engagement", f"{anuncio.get('engagement', 0):,}".replace(",", ".")),
        ("Inversión", f"${anuncio.get('inversion', 0):.2f}"),
    ]
    return {
        "imagen_ruta": ruta_imagen,
        "red": red,
        "red_label": etiqueta,
        "tipo": anuncio.get("tipo", "Anuncio"),
        "titulo": (anuncio.get("titulo") or "(sin nombre)")[:60],
        "kpis": kpis,
        "link_respaldo": None,
    }


def _slide_detalle_publicaciones(c: estilos.ConstructorReporte, periodo: str, filas: list[dict]) -> None:
    titulo_base = "DETALLE DE PUBLICACIONES ORGÁNICAS"
    if not filas:
        s = c.nueva_slide()
        c.encabezado_slide(s, titulo_base, periodo)
        c.caja_texto(s, Inches(0.5), Inches(1.5), Inches(10), Inches(0.6), "Sin publicaciones registradas este mes.", 14, estilos.GRIS_TEXTO)
        return

    encabezados = ["Red", "Fecha", "Publicación", "Visualizaciones", "Interacción", "Comentarios", "Compartidos", "Engagement"]
    # La columna "Publicación" necesita mucho más ancho que las demás — si
    # se reparte parejo (default de python-pptx), el texto envuelve a 3
    # líneas y con 12 filas por slide la tabla termina saliéndose del
    # slide por abajo (visto al renderizar con datos reales).
    anchos_columnas = [Inches(0.7), Inches(0.9), Inches(4.2), Inches(1.5), Inches(1.4), Inches(1.3), Inches(1.3), Inches(1.3)]
    paginas = [filas[i:i + _FILAS_POR_SLIDE_DETALLE] for i in range(0, len(filas), _FILAS_POR_SLIDE_DETALLE)]
    for indice, pagina in enumerate(paginas, start=1):
        s = c.nueva_slide()
        titulo = titulo_base if len(paginas) == 1 else f"{titulo_base} ({indice}/{len(paginas)})"
        c.encabezado_slide(s, titulo, periodo)
        filas_tabla = [
            [
                estilos.ETIQUETA_POR_RED.get(f["red"], f["red"][:2].upper()),
                f["fecha"][8:10] + "/" + f["fecha"][5:7],
                (f.get("descripcion") or "(sin descripción)")[:45],
                f"{f.get('visualizaciones', 0):,}".replace(",", "."),
                f"{f.get('total_interacciones', 0):,}".replace(",", "."),
                f.get("comentarios", 0),
                f.get("compartidos", 0),
                f"{agregacion.engagement_post(f):.1f}%",
            ]
            for f in pagina
        ]
        c.tabla(s, Inches(0.35), Inches(1.2), Inches(12.6), Inches(5.5), encabezados, filas_tabla, tam_fuente=10, anchos_columnas=anchos_columnas)


_FILAS_POR_SLIDE_MAILCHIMP = 9
_ALTURA_FILA_MAILCHIMP = Inches(0.45)


def _tarjetas_kpi_mailchimp(c: estilos.ConstructorReporte, slide, kpis: dict) -> None:
    tarjetas = [
        ("Campañas", f"{kpis['envios']:,}".replace(",", ".")),
        ("Entregados", f"{kpis['entregados']:,}".replace(",", ".")),
        ("Clics totales", f"{kpis['clics']:,}".replace(",", ".")),
        ("Open Rate", f"{kpis['apertura_promedio']:.1f}%"),
        ("Click Rate", f"{kpis['clics_promedio']:.1f}%"),
        ("Bajas", f"{kpis['bajas']:,}".replace(",", ".")),
    ]
    ancho_kpi = Inches(1.95)
    espacio = Inches(0.15)
    x0 = Inches(0.4)
    for i, (etiqueta, valor) in enumerate(tarjetas):
        x = x0 + i * (ancho_kpi + espacio)
        c.rectangulo(slide, x, Inches(1.2), ancho_kpi, Inches(1.0), color_relleno=estilos.GRIS_FONDO, radio=True)
        c.caja_texto(slide, x + Inches(0.15), Inches(1.3), ancho_kpi - Inches(0.3), Inches(0.3), etiqueta, 10, estilos.GRIS_TEXTO)
        c.caja_texto(slide, x + Inches(0.15), Inches(1.58), ancho_kpi - Inches(0.3), Inches(0.5), valor, 18, estilos.AZUL, negrita=True)


def _slide_mailchimp(c: estilos.ConstructorReporte, periodo: str, filas: list[dict]) -> None:
    titulo_base = "EMAIL MARKETING — MAILCHIMP"
    if not filas:
        s = c.nueva_slide()
        c.encabezado_slide(s, titulo_base, periodo)
        c.caja_texto(s, Inches(0.5), Inches(1.5), Inches(10), Inches(0.6), "Sin envíos registrados este mes.", 14, estilos.GRIS_TEXTO)
        return

    kpis = agregacion.kpis_mailchimp(filas)
    detalle = agregacion.detalle_mailchimp(filas)
    encabezados = ["Campaña", "Fecha", "Entregados", "Open Rate", "Click Rate", "CTOR", "Clics", "Clics WhatsApp", "Bajas"]
    anchos_columnas = [Inches(3.2), Inches(0.8), Inches(1.3), Inches(1.2), Inches(1.2), Inches(1.1), Inches(1.0), Inches(1.9), Inches(0.9)]
    paginas = [detalle[i:i + _FILAS_POR_SLIDE_MAILCHIMP] for i in range(0, len(detalle), _FILAS_POR_SLIDE_MAILCHIMP)]

    for indice, pagina in enumerate(paginas, start=1):
        s = c.nueva_slide()
        titulo = titulo_base if len(paginas) == 1 else f"{titulo_base} ({indice}/{len(paginas)})"
        c.encabezado_slide(s, titulo, periodo)
        # Las tarjetas de KPIs del mes solo van en la primera página — son
        # el resumen del mes completo, no de esa página en particular.
        if indice == 1:
            _tarjetas_kpi_mailchimp(c, s, kpis)
            y_tabla = Inches(2.5)
        else:
            y_tabla = Inches(1.2)
        filas_tabla = [
            [
                f.get("nombre_campana", "(sin nombre)"),
                f.get("fecha", "")[8:10] + "/" + f.get("fecha", "")[5:7],
                f"{f.get('entregas', 0):,}".replace(",", "."),
                f"{f['open_rate']:.1f}%",
                f"{f['click_rate']:.1f}%",
                f"{f['ctor']:.1f}%",
                f"{f.get('clics_totales', 0):,}".replace(",", "."),
                f.get("clics_whatsapp", 0),
                f.get("bajas", 0),
            ]
            for f in pagina
        ]
        # La altura de la tabla sigue la cantidad real de filas de esta
        # página, no el espacio disponible completo — si no, la última
        # página (que suele tener pocas filas) queda con filas
        # gigantes y espacio en blanco abajo, en vez de compacta.
        altura_tabla = min(Inches(7.0) - y_tabla, _ALTURA_FILA_MAILCHIMP * (len(pagina) + 1))
        c.tabla(s, Inches(0.35), y_tabla, Inches(12.6), altura_tabla, encabezados, filas_tabla, tam_fuente=10, anchos_columnas=anchos_columnas)
        c.caja_texto(s, Inches(0.4), Inches(7.1), Inches(11.5), Inches(0.35), "'Clics WhatsApp' = clics en enlaces de WhatsApp dentro del correo (atribuidos por campaña).", 9, estilos.GRIS_TEXTO)


def generar_pptx_unidad(
    unidad: str,
    anio: int,
    mes: int,
    filas_organico: list[dict],
    filas_control_perfiles: list[dict],
    filas_ads: list[dict],
    carpeta_imagenes_tmp: Path,
    competidores: list[dict] | None = None,
    anuncios_destacados: list[dict] | None = None,
) -> "estilos.ConstructorReporte":
    periodo = _periodo_texto(anio, mes)
    organico_mes = agregacion.filtrar_por_mes(filas_organico, anio, mes)
    control_mes = agregacion.filtrar_por_mes(filas_control_perfiles, anio, mes, campo_fecha="anio_mes")
    ads_mes = agregacion.filtrar_por_mes(filas_ads, anio, mes)
    anio_ant, mes_ant = agregacion.mes_anterior(anio, mes)
    control_mes_anterior = agregacion.filtrar_por_mes(filas_control_perfiles, anio_ant, mes_ant, campo_fecha="anio_mes")

    kpis_red = agregacion.kpis_organico_por_red(control_mes)
    kpis_red_anterior = agregacion.kpis_organico_por_red(control_mes_anterior)
    deltas_red = agregacion.deltas_kpis_red(kpis_red, kpis_red_anterior)
    alcance_red = agregacion.alcance_promedio_por_red(organico_mes)
    campanas = agregacion.detalle_campanas(ads_mes)
    top4 = agregacion.top_publicaciones(organico_mes, cantidad=4, menor_primero=False)
    peores4 = agregacion.top_publicaciones(organico_mes, cantidad=4, menor_primero=True)
    detalle = agregacion.detalle_publicaciones(organico_mes)

    c = estilos.ConstructorReporte()
    _slide_portada(c, unidad, periodo)
    _slide_kpis_organico(c, periodo, kpis_red, alcance_red, deltas_red)
    if competidores:
        _slide_competencia(c, unidad, periodo, competidores)
    _slide_detalle_campanas(c, periodo, campanas)

    if anuncios_destacados:
        anuncios_grid = [_anuncio_para_grid(a, carpeta_imagenes_tmp, i) for i, a in enumerate(anuncios_destacados)]
        c.slide_grid_posts("CONTENIDO DE PAUTA DESTACADO — TOP 4", periodo, anuncios_grid)

    if top4:
        posts_top = [_post_para_grid(f, carpeta_imagenes_tmp, "top", i) for i, f in enumerate(top4)]
        c.slide_grid_posts(
            "CONTENIDO ORGÁNICO DESTACADO — TOP 4", periodo, posts_top,
            nota_pie="'Clic' no aplica a Instagram — Meta no expone esa métrica para contenido orgánico de esa red.",
        )

    _slide_detalle_publicaciones(c, periodo, detalle)

    if peores4:
        posts_peores = [_post_para_grid(f, carpeta_imagenes_tmp, "mejora", i) for i, f in enumerate(peores4)]
        for p in posts_peores:
            p["color_red"] = estilos.GRIS_MEJORA
        c.slide_grid_posts("CONTENIDO PARA MEJORAR — MENOR ENGAGEMENT", periodo, posts_peores)

    return c


def generar_pptx_mailchimp(anio: int, mes: int, filas_mailchimp: list[dict]) -> "estilos.ConstructorReporte":
    """Reporte aparte, no ligado a ninguna unidad — Mailchimp usa una sola
    audiencia para toda la organización, sin ningún dato (ni de la API, ni
    de convención de nombres real) que permita repartir los envíos entre
    Academy/Acierta/GS1/etc. sin inventarlo."""
    periodo = _periodo_texto(anio, mes)
    mailchimp_mes = agregacion.filtrar_por_mes(filas_mailchimp, anio, mes, campo_fecha="fecha")
    c = estilos.ConstructorReporte()
    _slide_portada(c, "Email Marketing", periodo, eyebrow="CAINCO")
    _slide_mailchimp(c, periodo, mailchimp_mes)
    return c
