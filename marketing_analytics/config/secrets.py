"""Secretos (tokens, API keys) — SIEMPRE desde variables de entorno, nunca
desde config.yaml ni desde el repositorio.

Deliberadamente NO exige acá que estén todos presentes: no todas las
fuentes tienen por qué estar configuradas al mismo tiempo (ej. activar
solo Mailchimp mientras Meta todavía no se configuró). Quién sabe qué
secreto hace falta es `connectors/registry.py`, que ya sabe qué fuentes
están activas en config.yaml.
"""
from __future__ import annotations

import os

from pydantic import BaseModel


class Secrets(BaseModel):
    meta_system_user_token: str = ""
    mailchimp_api_key: str = ""
    sharepoint_tenant_id: str = ""
    sharepoint_client_id: str = ""
    sharepoint_client_secret: str = ""
    linkedin_access_token: str = ""

    @classmethod
    def from_env(cls) -> "Secrets":
        return cls(
            meta_system_user_token=os.environ.get("META_SYSTEM_USER_TOKEN", ""),
            mailchimp_api_key=os.environ.get("MAILCHIMP_API_KEY", ""),
            sharepoint_tenant_id=os.environ.get("SHAREPOINT_TENANT_ID", ""),
            sharepoint_client_id=os.environ.get("SHAREPOINT_CLIENT_ID", ""),
            sharepoint_client_secret=os.environ.get("SHAREPOINT_CLIENT_SECRET", ""),
            linkedin_access_token=os.environ.get("LINKEDIN_ACCESS_TOKEN", ""),
        )
