"""Arma los datos para ControlContenido.html: agrupa Meta Orgánico, Meta
Ads, Control de Perfiles y Calendario por "unidad" (perfil unificado
Facebook+Instagram), leyendo siempre desde la base histórica — nunca se
llama a ninguna API acá, todo ya está guardado.
"""
from __future__ import annotations

import sqlite3

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana


def _filas_a_dicts(conn: sqlite3.Connection, consulta: str) -> list[dict]:
    cursor = conn.execute(consulta)
    columnas = [d[0] for d in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def _nuevo_balde() -> dict:
    return {
        "perfiles": [],
        "control_perfiles": [],
        "control_perfiles_red": [],
        "meta_organico": [],
        "meta_ads": [],
        "calendario": [],
    }


def construir_datos_control_contenido(conn: sqlite3.Connection, config: AppConfig) -> dict:
    perfil_a_unidad = {p.nombre: p.unidad for p in config.meta.organico.perfiles}
    alias_a_unidad = {
        p.alias_pauta: (p.unidad, p.alias_pauta_generico) for p in config.meta.organico.perfiles
    }
    # Respaldo para campañas de pauta que son un "boost" de un post ya
    # existente (creadas con el botón "Promocionar", no armadas en Ads
    # Manager) — Meta les pone un nombre automático que nunca menciona una
    # unidad, así que el emparejamiento por texto no las encuentra. Se
    # ubican por la página/cuenta de origen real del post, ya resuelta en
    # el conector (ver MetaAdsRegistro.pagina_origen_id).
    pagina_a_unidad = {}
    for p in config.meta.organico.perfiles:
        if p.page_id:
            pagina_a_unidad[p.page_id] = p.unidad
        if p.ig_user_id:
            pagina_a_unidad[p.ig_user_id] = p.unidad

    unidades: dict[str, dict] = {}
    for perfil in config.meta.organico.perfiles:
        balde = unidades.setdefault(perfil.unidad, _nuevo_balde())
        balde["perfiles"].append({"nombre": perfil.nombre, "red": perfil.red.value})

    filas_control = _filas_a_dicts(
        conn,
        """
        SELECT perfil, red, anio_mes, seguidores, seguidores_ganados, publicaciones_mes,
               likes_mes, visualizaciones_mes, comentarios_mes, compartidos_mes,
               interacciones_mes
        FROM control_perfiles ORDER BY anio_mes
        """,
    )
    _agregar_control_perfiles(unidades, filas_control, perfil_a_unidad)

    filas_organico = _filas_a_dicts(
        conn,
        """
        SELECT perfil, pagina, red, fecha_publicacion AS fecha, tipo, descripcion,
               alcance, visualizaciones, total_clics, clics_enlace, reacciones,
               comentarios, compartidos, total_interacciones, imagen_url, link
        FROM meta_organico ORDER BY fecha_publicacion
        """,
    )
    for fila in filas_organico:
        unidad = perfil_a_unidad.get(fila["perfil"], fila["perfil"])
        unidades.setdefault(unidad, _nuevo_balde())["meta_organico"].append(fila)

    filas_ads = _filas_a_dicts(
        conn,
        """
        SELECT cuenta_publicitaria, perfil_unidad, red, campana,
               fecha_publicacion AS fecha, objetivo, moneda, importe_gastado,
               alcance, impresiones, clics, ctr, cpc, resultados, pagina_origen_id,
               conversaciones_iniciadas, fecha_inicio_campana, fecha_fin_campana
        FROM meta_ads ORDER BY fecha_publicacion
        """,
    )
    for fila in filas_ads:
        unidad = emparejar_unidad_campana(fila["campana"], alias_a_unidad) or pagina_a_unidad.get(
            fila.get("pagina_origen_id", "")
        )
        if unidad:
            unidades.setdefault(unidad, _nuevo_balde())["meta_ads"].append(fila)

    filas_calendario = _filas_a_dicts(
        conn,
        """
        SELECT id_origen, fecha_publicacion, perfil, bu, campana_evento, tipo, canal,
               formato, objetivo, descripcion_copy, estado, responsable, inversion_usd,
               link_publicacion, notas
        FROM calendario_publicaciones ORDER BY fecha_publicacion
        """,
    )
    for fila in filas_calendario:
        texto = fila.get("bu") or fila.get("perfil") or ""
        unidad = emparejar_unidad_campana(texto, alias_a_unidad)
        if unidad:
            unidades.setdefault(unidad, _nuevo_balde())["calendario"].append(fila)

    # Mailchimp queda global (no por unidad): los envíos de la organización
    # no están ligados a un perfil de Facebook/Instagram en particular.
    mailchimp = _filas_a_dicts(
        conn,
        """
        SELECT id_campana_origen, nombre_campana, fecha_envio AS fecha, destinatarios,
               entregas, tasa_apertura, aperturas_unicas, aperturas_totales, tasa_clics,
               clics_unicos, clics_totales, tasa_rebote, rebotes, bajas
        FROM mailchimp_campanas ORDER BY fecha_envio
        """,
    )
    clics_whatsapp_por_campana: dict[str, int] = {}
    for fila in _filas_a_dicts(
        conn,
        "SELECT id_campana_origen, SUM(clics) AS total FROM mailchimp_enlaces_whatsapp GROUP BY id_campana_origen",
    ):
        clics_whatsapp_por_campana[fila["id_campana_origen"]] = fila["total"]
    for fila in mailchimp:
        fila["clics_whatsapp"] = clics_whatsapp_por_campana.get(fila["id_campana_origen"], 0)

    return {"unidades": unidades, "mailchimp": mailchimp}


def _agregar_control_perfiles(
    unidades: dict[str, dict], filas: list[dict], perfil_a_unidad: dict[str, str]
) -> None:
    """Suma los snapshots mensuales de Facebook + Instagram de la misma
    unidad (ej. seguidores totales = seguidores FB + seguidores IG)."""
    acumulado: dict[tuple[str, str], dict] = {}
    campos_suma = (
        "seguidores", "seguidores_ganados", "publicaciones_mes", "likes_mes",
        "visualizaciones_mes", "comentarios_mes", "compartidos_mes", "interacciones_mes",
    )
    for fila in filas:
        unidad = perfil_a_unidad.get(fila["perfil"], fila["perfil"])
        clave = (unidad, fila["anio_mes"])
        acc = acumulado.setdefault(
            clave, {"unidad": unidad, "anio_mes": fila["anio_mes"], **{c: 0 for c in campos_suma}}
        )
        for campo in campos_suma:
            acc[campo] += fila[campo]

        # Además del snapshot sumado (arriba), se conserva el desglose por red
        # sin sumar — lo necesitan las donas Facebook vs. Instagram del dashboard.
        fila_red = dict(fila)
        fila_red["tasa_engagement"] = (
            round(fila["interacciones_mes"] / fila["seguidores"], 4) if fila["seguidores"] else 0.0
        )
        unidades.setdefault(unidad, _nuevo_balde())["control_perfiles_red"].append(fila_red)

    for (unidad, _anio_mes), acc in acumulado.items():
        acc["tasa_engagement"] = (
            round(acc["interacciones_mes"] / acc["seguidores"], 4) if acc["seguidores"] else 0.0
        )
        unidades.setdefault(unidad, _nuevo_balde())["control_perfiles"].append(acc)
