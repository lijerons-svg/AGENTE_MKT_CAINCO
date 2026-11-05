import textwrap

import pytest
import yaml
from pydantic import ValidationError

from marketing_analytics.config.schema import AppConfig


def _config_valida() -> dict:
    return yaml.safe_load(
        textwrap.dedent(
            """
            general:
              timezone: "America/La_Paz"
              output_dir: "output"
              database_path: "database/historico_rrss.db"
              date_range:
                modo: "last_n_days"
                ultimos_n_dias: 30
            meta:
              api_version: "v21.0"
              organico:
                perfiles:
                  - id: "perfil_001"
                    nombre: "Marca X - Instagram"
                    red: "instagram"
                    ig_user_id: "123"
                  - id: "perfil_002"
                    nombre: "Marca X - Facebook"
                    red: "facebook"
                    page_id: "456"
              ads:
                cuentas:
                  - id: "act_123"
                    nombre: "Cuenta Principal"
                    moneda: "BOB"
            mailchimp:
              server_prefix: "us21"
            linkedin:
              enabled: false
            """
        )
    )


def test_config_valida_se_parsea_ok():
    config = AppConfig.model_validate(_config_valida())
    assert len(config.meta.organico.perfiles) == 2
    assert config.linkedin.enabled is False


def test_perfil_instagram_sin_ig_user_id_falla():
    data = _config_valida()
    data["meta"]["organico"]["perfiles"][0].pop("ig_user_id")

    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)


def test_perfil_facebook_sin_page_id_falla():
    data = _config_valida()
    data["meta"]["organico"]["perfiles"][1].pop("page_id")

    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)


def test_linkedin_habilitado_sin_organization_id_falla():
    data = _config_valida()
    data["linkedin"] = {"enabled": True}

    with pytest.raises(ValidationError, match="organization_id"):
        AppConfig.model_validate(data)


def test_linkedin_habilitado_con_organization_id_ok():
    data = _config_valida()
    data["linkedin"] = {"enabled": True, "organization_id": "1592889", "nombre": "CAINCO"}

    config = AppConfig.model_validate(data)

    assert config.linkedin.organization_id == "1592889"


def test_rango_personalizado_requiere_fechas():
    data = _config_valida()
    data["general"]["date_range"] = {"modo": "custom"}

    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)


def test_agregar_un_perfil_no_requiere_cambios_de_esquema():
    data = _config_valida()
    data["meta"]["organico"]["perfiles"].append(
        {"id": "perfil_014", "nombre": "Perfil nuevo", "red": "instagram", "ig_user_id": "999"}
    )
    config = AppConfig.model_validate(data)
    assert len(config.meta.organico.perfiles) == 3
