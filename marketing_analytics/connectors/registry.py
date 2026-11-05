"""Arma la lista de conectores activos según config.yaml.

Sumar una fuente nueva (Meta Orgánico en la fase siguiente, GA4/TikTok/etc.
más adelante) es agregar una condición acá — el orquestador y el resto del
pipeline no cambian.
"""
from __future__ import annotations

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.config.secrets import Secrets
from marketing_analytics.connectors.base import BaseConnector
from marketing_analytics.connectors.calendario_sharepoint.connector import (
    CalendarioSharePointConnector,
)
from marketing_analytics.connectors.control_perfiles.connector import ControlPerfilesConnector
from marketing_analytics.connectors.linkedin.connector import LinkedInConnector
from marketing_analytics.connectors.mailchimp.connector import MailchimpConnector
from marketing_analytics.connectors.meta_ads.connector import MetaAdsConnector
from marketing_analytics.connectors.meta_organico.connector import MetaOrganicoConnector


def construir_conectores_activos(config: AppConfig, secrets: Secrets) -> list[BaseConnector]:
    conectores: list[BaseConnector] = []

    hay_meta_organico = bool(config.meta.organico.perfiles)
    hay_meta_ads = bool(config.meta.ads.cuentas)
    if (hay_meta_organico or hay_meta_ads) and not secrets.meta_system_user_token:
        raise RuntimeError(
            "config.yaml tiene perfiles de Meta Orgánico o cuentas de Meta Ads "
            "configuradas, pero falta META_SYSTEM_USER_TOKEN en el .env."
        )

    if hay_meta_organico:
        conectores.append(
            MetaOrganicoConnector(
                config.meta.organico,
                secrets.meta_system_user_token,
                config.meta.api_version,
            )
        )
        conectores.append(
            ControlPerfilesConnector(
                config.meta.organico,
                secrets.meta_system_user_token,
                config.meta.api_version,
            )
        )

    if hay_meta_ads:
        conectores.append(
            MetaAdsConnector(
                config.meta.ads,
                secrets.meta_system_user_token,
                config.meta.api_version,
            )
        )

    if config.mailchimp.enabled:
        if not secrets.mailchimp_api_key:
            raise RuntimeError(
                "config.yaml tiene mailchimp.enabled: true, pero falta "
                "MAILCHIMP_API_KEY en el .env."
            )
        conectores.append(MailchimpConnector(config.mailchimp, secrets.mailchimp_api_key))

    if config.calendario.enabled:
        faltantes = [
            nombre
            for nombre, valor in (
                ("SHAREPOINT_TENANT_ID", secrets.sharepoint_tenant_id),
                ("SHAREPOINT_CLIENT_ID", secrets.sharepoint_client_id),
                ("SHAREPOINT_CLIENT_SECRET", secrets.sharepoint_client_secret),
            )
            if not valor
        ]
        if faltantes:
            raise RuntimeError(
                "config.yaml tiene calendario.enabled: true, pero falta(n) "
                f"{', '.join(faltantes)} en el .env."
            )
        conectores.append(
            CalendarioSharePointConnector(
                config.calendario,
                secrets.sharepoint_tenant_id,
                secrets.sharepoint_client_id,
                secrets.sharepoint_client_secret,
            )
        )

    if config.linkedin.enabled:
        if not secrets.linkedin_access_token:
            raise RuntimeError(
                "config.yaml tiene linkedin.enabled: true, pero falta LINKEDIN_ACCESS_TOKEN en el "
                ".env — correr python -m marketing_analytics.connectors.linkedin.obtener_token."
            )
        conectores.append(LinkedInConnector(config.linkedin, secrets.linkedin_access_token))

    return conectores
