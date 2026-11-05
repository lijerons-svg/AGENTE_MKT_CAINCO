"""Mapea filas de insights de Meta Ads a MetaAdsRegistro."""
from __future__ import annotations

import datetime

from marketing_analytics.config.schema import CuentaPublicitaria
from marketing_analytics.connectors.meta_ads.resultados import (
    resolver_conversaciones_iniciadas,
    resolver_resultados,
)
from marketing_analytics.models.records import MetaAdsRegistro


def _fecha_o_none(valor: str | None) -> datetime.date | None:
    if not valor:
        return None
    return datetime.date.fromisoformat(valor[:10])


def mapear_fila_insight(
    fila: dict,
    cuenta: CuentaPublicitaria,
    objetivos_por_campana: dict[str, str],
    paginas_por_campana: dict[str, str] | None = None,
    fechas_por_campana: dict[str, tuple[str | None, str | None]] | None = None,
) -> MetaAdsRegistro:
    campaign_id = fila["campaign_id"]
    objetivo = objetivos_por_campana.get(campaign_id, "")
    reach = int(float(fila.get("reach", 0)))
    actions = fila.get("actions")
    inicio, fin = (fechas_por_campana or {}).get(campaign_id, (None, None))

    return MetaAdsRegistro(
        cuenta_publicitaria=cuenta.id,
        perfil_unidad=cuenta.nombre,
        red=fila.get("publisher_platform", ""),
        campana=fila["campaign_name"],
        fecha_publicacion=datetime.date.fromisoformat(fila["date_start"]),
        objetivo=objetivo,
        moneda=cuenta.moneda,
        importe_gastado=float(fila.get("spend", 0)),
        alcance=reach,
        impresiones=int(float(fila.get("impressions", 0))),
        clics=int(float(fila.get("clicks", 0))),
        ctr=float(fila.get("ctr", 0)),
        cpc=float(fila.get("cpc", 0)),
        resultados=resolver_resultados(objetivo, actions, reach),
        id_campana_origen=campaign_id,
        pagina_origen_id=(paginas_por_campana or {}).get(campaign_id, ""),
        conversaciones_iniciadas=resolver_conversaciones_iniciadas(actions),
        fecha_inicio_campana=_fecha_o_none(inicio),
        fecha_fin_campana=_fecha_o_none(fin),
    )


def mapear_insights(
    cuenta: CuentaPublicitaria,
    filas: list[dict],
    objetivos_por_campana: dict[str, str],
    paginas_por_campana: dict[str, str] | None = None,
    fechas_por_campana: dict[str, tuple[str | None, str | None]] | None = None,
) -> list[MetaAdsRegistro]:
    return [
        mapear_fila_insight(fila, cuenta, objetivos_por_campana, paginas_por_campana, fechas_por_campana)
        for fila in filas
    ]
