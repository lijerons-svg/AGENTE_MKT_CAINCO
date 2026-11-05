"""Mapea filas del Excel de calendario (ya normalizadas por client.py) al
modelo interno CalendarioPublicacion.

Encabezados esperados en la hoja (tal como existen hoy en
CAINCO_Programacion_Publicaciones.xlsx — incluye el typo real
"Publicaicon"; si el equipo lo corrige en SharePoint, actualizar acá):
ID, Fecha de Publicaicon, PERFIL, BU, Campana / Evento, Tipo, Canal, Formato,
Objetivo, Descripcion / Copy, Estado, Responsable, Inversion USD,
Link Publicacion, VoBo GCRI, Notas.
"""
from __future__ import annotations

import datetime
import re

from marketing_analytics.models.records import CalendarioPublicacion

_CLAVE_FECHA = "fecha_de_publicaicon"
_EPOCA_EXCEL = datetime.date(1899, 12, 30)


def _parsear_fecha(valor) -> datetime.date | None:
    """La API de Graph devuelve celdas con formato de fecha como número de
    serie de Excel (días desde el 30/dic/1899), no como texto — aunque en
    la hoja se vea "1/2/2026". Si viniera como texto ISO (otro origen), se
    soporta igual."""
    if not valor and valor != 0:
        return None
    if isinstance(valor, datetime.date):
        return valor
    if isinstance(valor, (int, float)):
        try:
            return _EPOCA_EXCEL + datetime.timedelta(days=int(valor))
        except (OverflowError, ValueError):
            return None
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        return datetime.datetime.fromisoformat(texto.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parsear_numero(valor) -> float:
    """Tolerante a cómo el equipo tipea montos a mano: separador decimal
    coma (formato boliviano, ej. "78,92"), espacios/espacios no separables
    (\xa0) pegados por copiar-pegar, o símbolos de moneda sueltos."""
    if valor in (None, ""):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = re.sub(r"[^0-9,.\-]", "", str(valor))
    if not texto:
        return 0.0
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def mapear_fila(fila: dict) -> CalendarioPublicacion:
    return CalendarioPublicacion(
        id_origen=str(fila.get("id", "")),
        fecha_publicacion=_parsear_fecha(fila.get(_CLAVE_FECHA)),
        perfil=str(fila.get("perfil") or ""),
        bu=str(fila.get("bu") or ""),
        campana_evento=str(fila.get("campana_evento") or ""),
        tipo=str(fila.get("tipo") or ""),
        canal=str(fila.get("canal") or ""),
        formato=str(fila.get("formato") or ""),
        objetivo=str(fila.get("objetivo") or ""),
        descripcion_copy=str(fila.get("descripcion_copy") or ""),
        estado=str(fila.get("estado") or ""),
        responsable=str(fila.get("responsable") or ""),
        inversion_usd=_parsear_numero(fila.get("inversion_usd")),
        link_publicacion=str(fila.get("link_publicacion") or ""),
        vobo_gcri=str(fila.get("vobo_gcri") or ""),
        notas=str(fila.get("notas") or ""),
    )
