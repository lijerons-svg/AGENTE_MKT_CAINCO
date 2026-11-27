from __future__ import annotations

from marketing_analytics.config.schema import PropiedadGA4
from marketing_analytics.models.records import (
    GA4MetricaCanal,
    GA4MetricaDiaria,
    GA4MetricaEvento,
    GA4MetricaPagina,
)


def mapear_fila(propiedad: PropiedadGA4, fila: dict) -> GA4MetricaDiaria:
    return GA4MetricaDiaria(
        unidad=propiedad.unidad,
        property_id=propiedad.property_id,
        fecha=fila["fecha"],
        sesiones=fila["sesiones"],
        usuarios_totales=fila["usuarios_totales"],
        usuarios_nuevos=fila["usuarios_nuevos"],
    )


def mapear_fila_pagina(propiedad: PropiedadGA4, fila: dict) -> GA4MetricaPagina:
    return GA4MetricaPagina(
        unidad=propiedad.unidad,
        property_id=propiedad.property_id,
        fecha=fila["fecha"],
        pagina=fila["pagina"],
        sesiones=fila["sesiones"],
        vistas_pagina=fila["vistas_pagina"],
        usuarios_totales=fila["usuarios_totales"],
        usuarios_nuevos=fila["usuarios_nuevos"],
    )


def mapear_fila_canal(propiedad: PropiedadGA4, fila: dict) -> GA4MetricaCanal:
    return GA4MetricaCanal(
        unidad=propiedad.unidad,
        property_id=propiedad.property_id,
        fecha=fila["fecha"],
        canal=fila["canal"],
        pagina=fila["pagina"],
        sesiones=fila["sesiones"],
    )


def mapear_fila_evento(propiedad: PropiedadGA4, fila: dict) -> GA4MetricaEvento:
    return GA4MetricaEvento(
        unidad=propiedad.unidad,
        property_id=propiedad.property_id,
        fecha=fila["fecha"],
        evento=fila["evento"],
        pagina=fila["pagina"],
        conteo=fila["conteo"],
    )
