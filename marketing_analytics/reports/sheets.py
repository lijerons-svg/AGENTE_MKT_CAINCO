"""Construye cada una de las 5 hojas de Historico_RRSS.xlsx, siempre leyendo
desde la base histórica (SQLite) — el Excel es un reporte, nunca la fuente
de la que se lee para volver a escribir.
"""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from openpyxl.workbook import Workbook

from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana
from marketing_analytics.reports.excel_writer_utils import escribir_hoja

if TYPE_CHECKING:
    from marketing_analytics.config.schema import AppConfig


def _detalle_whatsapp_por_campana(conn: sqlite3.Connection) -> dict[str, tuple[int, str]]:
    filas = conn.execute(
        "SELECT id_campana_origen, url, clics FROM mailchimp_enlaces_whatsapp ORDER BY url"
    ).fetchall()
    por_campana: dict[str, list[tuple[str, int]]] = {}
    for fila in filas:
        por_campana.setdefault(fila["id_campana_origen"], []).append((fila["url"], fila["clics"]))

    return {
        id_campana: (
            sum(clics for _, clics in enlaces),
            "; ".join(f"{url} ({clics} clics)" for url, clics in enlaces),
        )
        for id_campana, enlaces in por_campana.items()
    }


def agregar_hoja_meta_organico(wb: Workbook, conn: sqlite3.Connection) -> None:
    ws = wb.create_sheet("META ORGANICO")
    filas = conn.execute(
        """
        SELECT perfil, pagina, red, fecha_publicacion, tipo, descripcion, alcance,
               visualizaciones, total_clics, clics_enlace, reacciones, comentarios,
               compartidos, total_interacciones
        FROM meta_organico ORDER BY fecha_publicacion, perfil
        """
    ).fetchall()
    encabezados = [
        "Perfil", "Página", "Red", "Fecha publicación", "Tipo", "Descripción",
        "Alcance", "Visualizaciones", "Total clics", "Clics enlace", "Reacciones",
        "Comentarios", "Compartidos", "Total interacciones",
    ]
    escribir_hoja(ws, encabezados, [tuple(f) for f in filas])


def agregar_hoja_control_perfiles(wb: Workbook, conn: sqlite3.Connection) -> None:
    ws = wb.create_sheet("CONTROL PERFILES")
    filas = conn.execute(
        """
        SELECT perfil, red, anio_mes, seguidores, seguidores_ganados, publicaciones_mes,
               likes_mes, visualizaciones_mes, comentarios_mes, compartidos_mes,
               interacciones_mes, tasa_engagement
        FROM control_perfiles ORDER BY anio_mes, perfil
        """
    ).fetchall()
    encabezados = [
        "Perfil", "Red", "Mes", "Seguidores", "Seguidores ganados", "Publicaciones",
        "Likes", "Visualizaciones", "Comentarios", "Compartidos", "Interacciones",
        "Tasa de engagement",
    ]
    # "Tasa de engagement" (índice 11) se guarda como fracción (0.0523) —
    # sin formato de %, Excel la muestra tal cual y se lee fácil como
    # "0.05%" en vez del 5.23% real.
    escribir_hoja(ws, encabezados, [tuple(f) for f in filas], columnas_porcentaje={11})


def agregar_hoja_meta_ads(wb: Workbook, conn: sqlite3.Connection, config: "AppConfig | None" = None) -> None:
    ws = wb.create_sheet("META ADS")
    filas = conn.execute(
        """
        SELECT cuenta_publicitaria, perfil_unidad, red, campana, id_campana_origen, fecha_publicacion,
               objetivo, moneda, importe_gastado, alcance, impresiones, clics, ctr,
               cpc, resultados, pagina_origen_id, conversaciones_iniciadas,
               fecha_inicio_campana, fecha_fin_campana
        FROM meta_ads ORDER BY fecha_publicacion, campana
        """
    ).fetchall()
    encabezados = [
        "Cuenta publicitaria", "Perfil / Unidad", "Red", "Campaña", "ID Campaña", "Fecha publicación",
        "Objetivo", "Moneda", "Importe gastado", "Alcance", "Impresiones", "Clics", "CTR",
        "CPC", "Resultados",
        # Las 3 columnas de abajo son para poder chequear a ojo si el
        # emparejamiento por texto del nombre de campaña (frágil: errores de
        # tipeo, o una palabra de formato como "foro" que varias unidades
        # comparten) coincide con la página/cuenta real a la que pertenece
        # el anuncio — un dato duro, no un adivinado por texto. Quedan
        # vacías si no se generó con la configuración (`config.yaml`) a
        # mano, como en una corrida de solo-lectura.
        "Unidad (por nombre de campaña)", "Unidad (por página de origen)", "ID página/cuenta de origen",
        # Clics en "Enviar mensaje" (WhatsApp/Messenger/Instagram Direct) y
        # fechas de programación reales de la campaña en Ads Manager — no el
        # día puntual de esta fila ("Fecha publicación" de arriba).
        "Conversación iniciada", "Fecha inicio (campaña)", "Fecha fin (campaña)",
    ]

    alias_a_unidad: dict[str, tuple[str, bool]] = {}
    pagina_a_unidad: dict[str, str] = {}
    if config is not None:
        for perfil in config.meta.organico.perfiles:
            alias_a_unidad[perfil.alias_pauta] = (perfil.unidad, perfil.alias_pauta_generico)
            if perfil.page_id:
                pagina_a_unidad[perfil.page_id] = perfil.unidad
            if perfil.ig_user_id:
                pagina_a_unidad[perfil.ig_user_id] = perfil.unidad

    filas_con_unidad = []
    for f in filas:
        pagina_origen_id = f["pagina_origen_id"] or ""
        unidad_por_texto = emparejar_unidad_campana(f["campana"] or "", alias_a_unidad) if config else ""
        unidad_por_pagina = pagina_a_unidad.get(pagina_origen_id, "") if config else ""
        # Las primeras 15 columnas del SELECT son los datos "reales"
        # (encabezados de arriba hasta "Resultados"); lo que sigue
        # (pagina_origen_id en adelante) son columnas de apoyo que se
        # reordenan/calculan acá, no se copian tal cual.
        datos_principales = tuple(f)[:15]
        filas_con_unidad.append(
            datos_principales
            + (unidad_por_texto or "", unidad_por_pagina or "", pagina_origen_id)
            + (f["conversaciones_iniciadas"], f["fecha_inicio_campana"], f["fecha_fin_campana"])
        )

    escribir_hoja(ws, encabezados, filas_con_unidad)


def agregar_hoja_mailchimp(wb: Workbook, conn: sqlite3.Connection) -> None:
    ws = wb.create_sheet("MAILCHIMP")
    whatsapp_por_campana = _detalle_whatsapp_por_campana(conn)
    campanas = conn.execute(
        """
        SELECT id_campana_origen, nombre_campana, fecha_envio, destinatarios, entregas,
               tasa_apertura, aperturas_unicas, aperturas_totales, tasa_clics,
               clics_unicos, clics_totales, tasa_rebote, rebotes, bajas
        FROM mailchimp_campanas ORDER BY fecha_envio
        """
    ).fetchall()

    encabezados = [
        "Fecha de envío", "Nombre campaña", "Destinatarios", "Entregas", "Tasa apertura",
        "Aperturas únicas", "Aperturas totales", "Tasa clics", "Clics únicos",
        "Clics totales", "Tasa rebote", "Rebotes", "Bajas", "Clics WhatsApp",
        "Detalle enlaces WhatsApp",
    ]
    filas = []
    for c in campanas:
        clics_wa, detalle_wa = whatsapp_por_campana.get(c["id_campana_origen"], (0, ""))
        filas.append(
            (
                c["fecha_envio"], c["nombre_campana"], c["destinatarios"], c["entregas"],
                c["tasa_apertura"], c["aperturas_unicas"], c["aperturas_totales"],
                c["tasa_clics"], c["clics_unicos"], c["clics_totales"], c["tasa_rebote"],
                c["rebotes"], c["bajas"], clics_wa, detalle_wa,
            )
        )
    # "Tasa apertura" (4), "Tasa clics" (7) y "Tasa rebote" (10) vienen de
    # Mailchimp como fracción (0-1) — mismo motivo que en CONTROL PERFILES.
    escribir_hoja(ws, encabezados, filas, columnas_porcentaje={4, 7, 10})


def agregar_hoja_linkedin(wb: Workbook, conn: sqlite3.Connection) -> None:
    """Sin conector activo (fuera de alcance por ahora) — hoja con
    encabezados listos, sin filas, para no romper el Excel el día que se
    active LinkedIn."""
    ws = wb.create_sheet("LINKEDIN")
    filas = conn.execute(
        """
        SELECT pagina, fecha_publicacion, tipo, descripcion, impresiones, alcance,
               clics, reacciones, comentarios, compartidos, interacciones
        FROM linkedin_organico ORDER BY fecha_publicacion
        """
    ).fetchall()
    encabezados = [
        "Página", "Fecha", "Tipo", "Descripción", "Impresiones", "Alcance", "Clics",
        "Reacciones", "Comentarios", "Compartidos", "Interacciones",
    ]
    escribir_hoja(ws, encabezados, [tuple(f) for f in filas])


def agregar_hoja_calendario(wb: Workbook, conn: sqlite3.Connection) -> None:
    ws = wb.create_sheet("CALENDARIO")
    filas = conn.execute(
        """
        SELECT id_origen, fecha_publicacion, perfil, bu, campana_evento, tipo, canal,
               formato, objetivo, descripcion_copy, estado, responsable, inversion_usd,
               link_publicacion, vobo_gcri, notas
        FROM calendario_publicaciones ORDER BY fecha_publicacion, id_origen
        """
    ).fetchall()
    encabezados = [
        "ID", "Fecha de publicación", "Perfil", "BU", "Campaña / Evento", "Tipo", "Canal",
        "Formato", "Objetivo", "Descripción / Copy", "Estado", "Responsable",
        "Inversión USD", "Link publicación", "VoBo GCRI", "Notas",
    ]
    escribir_hoja(ws, encabezados, [tuple(f) for f in filas])


def agregar_hoja_log(wb: Workbook, conn: sqlite3.Connection) -> None:
    ws = wb.create_sheet("LOG")
    filas = conn.execute(
        """
        SELECT id, hora_inicio, hora_fin, tiempo_ejecucion_seg, estado,
               registros_descargados, registros_nuevos, registros_actualizados,
               registros_descartados, errores
        FROM ejecuciones ORDER BY id DESC
        """
    ).fetchall()
    encabezados = [
        "ID Ejecución", "Hora inicio", "Hora final", "Tiempo (seg)", "Estado",
        "Registros descargados", "Registros nuevos", "Registros actualizados",
        "Registros descartados", "Errores",
    ]
    escribir_hoja(ws, encabezados, [tuple(f) for f in filas])
