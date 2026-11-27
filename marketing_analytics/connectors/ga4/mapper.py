from __future__ import annotations

from marketing_analytics.config.schema import PropiedadGA4
from marketing_analytics.models.records import GA4MetricaDiaria, GA4MetricaPagina


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
    )
