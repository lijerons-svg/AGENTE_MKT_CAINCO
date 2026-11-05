"""Upsert con deduplicación por `uid`. Único punto del sistema que escribe
en la base histórica — los conectores y servicios nunca tocan SQL directo.

Regla: mismo uid + mismos valores => descartado (no-op). Mismo uid + valores
distintos => actualizado (se refrescan las métricas). uid nuevo => nuevo.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from marketing_analytics.models.records import (
    CalendarioPublicacion,
    ControlPerfilMensual,
    LinkedInOrganicoPost,
    MailchimpCampana,
    MailchimpEnlaceWhatsapp,
    MetaAdsRegistro,
    MetaOrganicoPost,
)


@dataclass
class ResultadoUpsert:
    nuevos: int = 0
    actualizados: int = 0
    descartados: int = 0

    def __iadd__(self, other: "ResultadoUpsert") -> "ResultadoUpsert":
        self.nuevos += other.nuevos
        self.actualizados += other.actualizados
        self.descartados += other.descartados
        return self

    @property
    def total(self) -> int:
        return self.nuevos + self.actualizados + self.descartados


def _upsert_por_uid(
    conn: sqlite3.Connection,
    tabla: str,
    uid: str,
    campos: dict,
) -> str:
    fila = conn.execute(f"SELECT * FROM {tabla} WHERE uid = ?", (uid,)).fetchone()

    if fila is None:
        columnas = ["uid", *campos.keys()]
        placeholders = ", ".join(["?"] * len(columnas))
        conn.execute(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})",
            [uid, *campos.values()],
        )
        return "nuevo"

    hay_cambios = any(fila[campo] != campos[campo] for campo in campos)
    if not hay_cambios:
        return "descartado"

    asignaciones = ", ".join(f"{campo} = ?" for campo in campos)
    conn.execute(
        f"UPDATE {tabla} SET {asignaciones}, actualizado_en = datetime('now') WHERE uid = ?",
        [*campos.values(), uid],
    )
    return "actualizado"


def _registrar(resultado: ResultadoUpsert, tipo: str) -> None:
    if tipo == "nuevo":
        resultado.nuevos += 1
    elif tipo == "actualizado":
        resultado.actualizados += 1
    else:
        resultado.descartados += 1


def upsert_meta_organico(
    conn: sqlite3.Connection, registros: list[MetaOrganicoPost]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "perfil": r.perfil,
            "pagina": r.pagina,
            "red": r.red,
            "fecha_publicacion": r.fecha_publicacion.isoformat(),
            "tipo": r.tipo,
            "descripcion": r.descripcion,
            "alcance": r.alcance,
            "visualizaciones": r.visualizaciones,
            "total_clics": r.total_clics,
            "clics_enlace": r.clics_enlace,
            "reacciones": r.reacciones,
            "comentarios": r.comentarios,
            "compartidos": r.compartidos,
            "total_interacciones": r.total_interacciones,
            "id_publicacion_origen": r.id_publicacion_origen,
            "imagen_url": r.imagen_url,
            "link": r.link,
        }
        tipo = _upsert_por_uid(conn, "meta_organico", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_meta_ads(
    conn: sqlite3.Connection, registros: list[MetaAdsRegistro]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "cuenta_publicitaria": r.cuenta_publicitaria,
            "perfil_unidad": r.perfil_unidad,
            "red": r.red,
            "campana": r.campana,
            "fecha_publicacion": r.fecha_publicacion.isoformat(),
            "objetivo": r.objetivo,
            "moneda": r.moneda,
            "importe_gastado": r.importe_gastado,
            "alcance": r.alcance,
            "impresiones": r.impresiones,
            "clics": r.clics,
            "ctr": r.ctr,
            "cpc": r.cpc,
            "resultados": r.resultados,
            "id_campana_origen": r.id_campana_origen,
            "pagina_origen_id": r.pagina_origen_id,
            "conversaciones_iniciadas": r.conversaciones_iniciadas,
            "fecha_inicio_campana": r.fecha_inicio_campana.isoformat() if r.fecha_inicio_campana else None,
            "fecha_fin_campana": r.fecha_fin_campana.isoformat() if r.fecha_fin_campana else None,
        }
        tipo = _upsert_por_uid(conn, "meta_ads", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_mailchimp_campanas(
    conn: sqlite3.Connection, registros: list[MailchimpCampana]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "id_campana_origen": r.id_campana_origen,
            "nombre_campana": r.nombre_campana,
            "fecha_envio": r.fecha_envio.isoformat(),
            "destinatarios": r.destinatarios,
            "entregas": r.entregas,
            "tasa_apertura": r.tasa_apertura,
            "aperturas_unicas": r.aperturas_unicas,
            "aperturas_totales": r.aperturas_totales,
            "tasa_clics": r.tasa_clics,
            "clics_unicos": r.clics_unicos,
            "clics_totales": r.clics_totales,
            "tasa_rebote": r.tasa_rebote,
            "rebotes": r.rebotes,
            "bajas": r.bajas,
        }
        tipo = _upsert_por_uid(conn, "mailchimp_campanas", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_linkedin_organico(
    conn: sqlite3.Connection, registros: list[LinkedInOrganicoPost]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "pagina": r.pagina,
            "fecha_publicacion": r.fecha_publicacion.isoformat(),
            "tipo": r.tipo,
            "descripcion": r.descripcion,
            "impresiones": r.impresiones,
            "alcance": r.alcance,
            "clics": r.clics,
            "reacciones": r.reacciones,
            "comentarios": r.comentarios,
            "compartidos": r.compartidos,
            "interacciones": r.interacciones,
            "id_publicacion_origen": r.id_publicacion_origen,
        }
        tipo = _upsert_por_uid(conn, "linkedin_organico", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_calendario_publicaciones(
    conn: sqlite3.Connection, registros: list[CalendarioPublicacion]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "id_origen": r.id_origen,
            "fecha_publicacion": r.fecha_publicacion.isoformat() if r.fecha_publicacion else None,
            "perfil": r.perfil,
            "bu": r.bu,
            "campana_evento": r.campana_evento,
            "tipo": r.tipo,
            "canal": r.canal,
            "formato": r.formato,
            "objetivo": r.objetivo,
            "descripcion_copy": r.descripcion_copy,
            "estado": r.estado,
            "responsable": r.responsable,
            "inversion_usd": r.inversion_usd,
            "link_publicacion": r.link_publicacion,
            "vobo_gcri": r.vobo_gcri,
            "notas": r.notas,
        }
        tipo = _upsert_por_uid(conn, "calendario_publicaciones", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_control_perfiles(
    conn: sqlite3.Connection, registros: list[ControlPerfilMensual]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        campos = {
            "perfil": r.perfil,
            "red": r.red,
            "anio_mes": r.anio_mes,
            "seguidores": r.seguidores,
            "seguidores_ganados": r.seguidores_ganados,
            "publicaciones_mes": r.publicaciones_mes,
            "likes_mes": r.likes_mes,
            "visualizaciones_mes": r.visualizaciones_mes,
            "comentarios_mes": r.comentarios_mes,
            "compartidos_mes": r.compartidos_mes,
            "interacciones_mes": r.interacciones_mes,
            "tasa_engagement": r.tasa_engagement,
        }
        tipo = _upsert_por_uid(conn, "control_perfiles", r.uid, campos)
        _registrar(resultado, tipo)
    conn.commit()
    return resultado


def upsert_mailchimp_enlaces_whatsapp(
    conn: sqlite3.Connection, registros: list[MailchimpEnlaceWhatsapp]
) -> ResultadoUpsert:
    resultado = ResultadoUpsert()
    for r in registros:
        fila = conn.execute(
            "SELECT clics FROM mailchimp_enlaces_whatsapp WHERE id_campana_origen = ? AND url = ?",
            (r.id_campana_origen, r.url),
        ).fetchone()
        if fila is None:
            conn.execute(
                "INSERT INTO mailchimp_enlaces_whatsapp (id_campana_origen, url, clics) "
                "VALUES (?, ?, ?)",
                (r.id_campana_origen, r.url, r.clics),
            )
            resultado.nuevos += 1
        elif fila["clics"] != r.clics:
            conn.execute(
                "UPDATE mailchimp_enlaces_whatsapp SET clics = ? "
                "WHERE id_campana_origen = ? AND url = ?",
                (r.clics, r.id_campana_origen, r.url),
            )
            resultado.actualizados += 1
        else:
            resultado.descartados += 1
    conn.commit()
    return resultado
