import pytest

from marketing_analytics.config.schema import AppConfig
from marketing_analytics.config.secrets import Secrets
from marketing_analytics.connectors.calendario_sharepoint.connector import (
    CalendarioSharePointConnector,
)
from marketing_analytics.connectors.control_perfiles.connector import ControlPerfilesConnector
from marketing_analytics.connectors.linkedin.connector import LinkedInConnector
from marketing_analytics.connectors.mailchimp.connector import MailchimpConnector
from marketing_analytics.connectors.meta_ads.connector import MetaAdsConnector
from marketing_analytics.connectors.meta_organico.connector import MetaOrganicoConnector
from marketing_analytics.connectors.registry import construir_conectores_activos

_SECRETS = Secrets(meta_system_user_token="token-fake", mailchimp_api_key="key-fake")


def test_registry_incluye_meta_ads_solo_si_hay_cuentas():
    config = AppConfig.model_validate(
        {
            "mailchimp": {"server_prefix": "us21", "enabled": False},
            "meta": {"ads": {"cuentas": [{"id": "123", "nombre": "Cuenta X", "moneda": "BOB"}]}},
        }
    )
    conectores = construir_conectores_activos(config, _SECRETS)
    assert any(isinstance(c, MetaAdsConnector) for c in conectores)
    assert not any(isinstance(c, MailchimpConnector) for c in conectores)


def test_registry_incluye_mailchimp_solo_si_esta_habilitado():
    config = AppConfig.model_validate(
        {"mailchimp": {"server_prefix": "us21", "enabled": True}}
    )
    conectores = construir_conectores_activos(config, _SECRETS)
    assert any(isinstance(c, MailchimpConnector) for c in conectores)
    assert not any(isinstance(c, MetaAdsConnector) for c in conectores)


def test_registry_vacio_si_nada_configurado():
    config = AppConfig.model_validate(
        {"mailchimp": {"server_prefix": "us21", "enabled": False}}
    )
    conectores = construir_conectores_activos(config, _SECRETS)
    assert conectores == []


def test_registry_incluye_meta_organico_solo_si_hay_perfiles():
    config = AppConfig.model_validate(
        {
            "mailchimp": {"server_prefix": "us21", "enabled": False},
            "meta": {
                "organico": {
                    "perfiles": [
                        {
                            "id": "perfil_001",
                            "nombre": "Marca X - Instagram",
                            "red": "instagram",
                            "ig_user_id": "123",
                        }
                    ]
                }
            },
        }
    )
    conectores = construir_conectores_activos(config, _SECRETS)
    assert any(isinstance(c, MetaOrganicoConnector) for c in conectores)


def test_registry_incluye_control_perfiles_junto_con_meta_organico():
    config = AppConfig.model_validate(
        {
            "mailchimp": {"server_prefix": "us21", "enabled": False},
            "meta": {
                "organico": {
                    "perfiles": [
                        {
                            "id": "perfil_001",
                            "nombre": "Marca X - Instagram",
                            "red": "instagram",
                            "ig_user_id": "123",
                        }
                    ]
                }
            },
        }
    )
    conectores = construir_conectores_activos(config, _SECRETS)
    assert any(isinstance(c, ControlPerfilesConnector) for c in conectores)


def test_solo_mailchimp_configurado_no_exige_token_de_meta():
    """Caso real de QA: activar solo Mailchimp (fase 1) sin haber configurado
    Meta todavía no debe fallar por falta de META_SYSTEM_USER_TOKEN."""
    config = AppConfig.model_validate({"mailchimp": {"server_prefix": "us5", "enabled": True}})
    secrets_solo_mailchimp = Secrets(mailchimp_api_key="key-fake")

    conectores = construir_conectores_activos(config, secrets_solo_mailchimp)

    assert len(conectores) == 1
    assert isinstance(conectores[0], MailchimpConnector)


def test_meta_configurado_sin_token_lanza_error_claro():
    config = AppConfig.model_validate(
        {
            "mailchimp": {"server_prefix": "us21", "enabled": False},
            "meta": {"ads": {"cuentas": [{"id": "123", "nombre": "Cuenta X", "moneda": "BOB"}]}},
        }
    )
    secrets_sin_token = Secrets(mailchimp_api_key="key-fake")

    with pytest.raises(RuntimeError, match="META_SYSTEM_USER_TOKEN"):
        construir_conectores_activos(config, secrets_sin_token)


def test_mailchimp_habilitado_sin_api_key_lanza_error_claro():
    config = AppConfig.model_validate({"mailchimp": {"server_prefix": "us21", "enabled": True}})
    secrets_sin_key = Secrets(meta_system_user_token="token-fake")

    with pytest.raises(RuntimeError, match="MAILCHIMP_API_KEY"):
        construir_conectores_activos(config, secrets_sin_key)


_CONFIG_CALENDARIO = {
    "mailchimp": {"server_prefix": "us21", "enabled": False},
    "calendario": {
        "enabled": True,
        "sharepoint_hostname": "caincoscz.sharepoint.com",
        "site_path": "/sites/MARKETING",
        "file_name": "CAINCO_Programacion_Publicaciones.xlsx",
        "sheet_name": "Planificacion",
    },
}


def test_registry_incluye_calendario_solo_si_esta_habilitado():
    config = AppConfig.model_validate(_CONFIG_CALENDARIO)
    secrets = Secrets(
        sharepoint_tenant_id="tenant",
        sharepoint_client_id="client",
        sharepoint_client_secret="secret",
    )

    conectores = construir_conectores_activos(config, secrets)

    assert any(isinstance(c, CalendarioSharePointConnector) for c in conectores)


def test_calendario_habilitado_sin_secretos_lanza_error_claro():
    config = AppConfig.model_validate(_CONFIG_CALENDARIO)

    with pytest.raises(RuntimeError, match="SHAREPOINT_TENANT_ID"):
        construir_conectores_activos(config, Secrets())


_CONFIG_LINKEDIN = {
    "mailchimp": {"server_prefix": "us21", "enabled": False},
    "linkedin": {"enabled": True, "organization_id": "1592889", "nombre": "CAINCO"},
}


def test_registry_incluye_linkedin_solo_si_esta_habilitado():
    config = AppConfig.model_validate(_CONFIG_LINKEDIN)
    secrets = Secrets(linkedin_access_token="token-fake")

    conectores = construir_conectores_activos(config, secrets)

    assert any(isinstance(c, LinkedInConnector) for c in conectores)


def test_linkedin_habilitado_sin_token_lanza_error_claro():
    config = AppConfig.model_validate(_CONFIG_LINKEDIN)

    with pytest.raises(RuntimeError, match="LINKEDIN_ACCESS_TOKEN"):
        construir_conectores_activos(config, Secrets())
