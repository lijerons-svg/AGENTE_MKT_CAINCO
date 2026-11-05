"""Parsea un recibo de pago de Meta Ads (PDF) a filas de gasto por campaña.

Un recibo de Meta agrupa varias campañas bajo un mismo pago/factura. Este
módulo extrae, por cada campaña listada: el monto y las impresiones (el
único "resultado" que el recibo trae) — y arrastra el número de referencia
del pago, igual para todas las filas de un mismo recibo.

Frágil por diseño: si el formato de Meta cambia, `parsear_recibo_meta`
devuelve una lista vacía en vez de inventar datos (ver `es_recibo_meta`
para detectar antes si el PDF corresponde a este formato).
"""
from __future__ import annotations

import re

from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana

_PATRON_REFERENCIA = re.compile(r"Número de referencia:\s*(\S+)")

_PATRON_CAMPANA = re.compile(
    r"^(?P<nombre>(?!De )[^\n]+?)\n"
    r"De .+?\n"
    r"(?P<monto>\d{1,3}(?:[.\s]\d{3})*,\d{2})\s*\$\s*\n"
    r".+?(?P<impresiones>\d[\d\s]*)\s*Impresiones",
    re.MULTILINE,
)

_SIN_UNIDAD = "SIN IDENTIFICAR"


def es_recibo_meta(texto: str) -> bool:
    return "Meta anuncios" in texto or "Meta Platforms" in texto


def _limpiar_nombre(nombre: str) -> str:
    return " ".join(nombre.replace("\x0c", "").split())


def _monto_a_float(monto_texto: str) -> float:
    # Formato "1.234,56" o "18,44" -> 1234.56 / 18.44
    return float(monto_texto.replace(".", "").replace(" ", "").replace(",", "."))


def parsear_recibo_meta(texto: str, alias_a_unidad: dict[str, tuple[str, bool]]) -> list[dict]:
    referencia_match = _PATRON_REFERENCIA.search(texto)
    referencia = referencia_match.group(1) if referencia_match else ""

    filas = []
    for m in _PATRON_CAMPANA.finditer(texto):
        nombre = _limpiar_nombre(m.group("nombre"))
        unidad = emparejar_unidad_campana(nombre, alias_a_unidad) or _SIN_UNIDAD
        filas.append(
            {
                "codigo_referencia": referencia,
                "identificador_unidad": unidad,
                "nombre_actividad": nombre,
                "monto_invertido": _monto_a_float(m.group("monto")),
                "resultado_obtenido": int(m.group("impresiones").replace(" ", "")),
                "resultado_tipo": "Impresiones",
                "fuente": "Meta Ads",
            }
        )
    return filas
