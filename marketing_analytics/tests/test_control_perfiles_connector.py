import datetime
from unittest.mock import MagicMock

import pytest

from marketing_analytics.config.schema import MetaOrganicoConfig, PerfilMetaOrganico, Red
from marketing_analytics.connectors.control_perfiles.connector import ControlPerfilesConnector


def _config():
    return MetaOrganicoConfig(
        perfiles=[
            PerfilMetaOrganico(id="p1", nombre="Perfil FB", red=Red.FACEBOOK, page_id="page_1"),
            PerfilMetaOrganico(id="p2", nombre="Perfil IG", red=Red.INSTAGRAM, ig_user_id="ig_1"),
        ]
    )


def test_fetch_lee_seguidores_de_cada_perfil_segun_su_red():
    cliente_falso = MagicMock()
    cliente_falso.obtener_seguidores_pagina.return_value = 500
    cliente_falso.obtener_seguidores_ig.return_value = 300

    conector = ControlPerfilesConnector(_config(), "token", "v21.0", cliente=cliente_falso)
    datos = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert {"perfil": "Perfil FB", "red": "facebook", "seguidores": 500} in datos
    assert {"perfil": "Perfil IG", "red": "instagram", "seguidores": 300} in datos
    cliente_falso.obtener_seguidores_pagina.assert_called_once_with("page_1")
    cliente_falso.obtener_seguidores_ig.assert_called_once_with("ig_1")


def test_un_perfil_fallido_no_bloquea_a_los_demas():
    cliente_falso = MagicMock()
    cliente_falso.obtener_seguidores_pagina.side_effect = RuntimeError("token inválido")
    cliente_falso.obtener_seguidores_ig.return_value = 300

    conector = ControlPerfilesConnector(_config(), "token", "v21.0", cliente=cliente_falso)
    datos = conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))

    assert len(datos) == 1
    assert datos[0]["perfil"] == "Perfil IG"


def test_todos_los_perfiles_fallidos_lanza_error():
    cliente_falso = MagicMock()
    cliente_falso.obtener_seguidores_pagina.side_effect = RuntimeError("token inválido")
    cliente_falso.obtener_seguidores_ig.side_effect = RuntimeError("token inválido")

    conector = ControlPerfilesConnector(_config(), "token", "v21.0", cliente=cliente_falso)

    with pytest.raises(RuntimeError, match="Todos los perfiles"):
        conector.fetch(datetime.date(2026, 7, 1), datetime.date(2026, 7, 31))


def test_upsert_arma_el_snapshot_y_lo_persiste(conn):
    cliente_falso = MagicMock()
    conector = ControlPerfilesConnector(_config(), "token", "v21.0", cliente=cliente_falso)
    datos = [{"perfil": "Perfil FB", "red": "facebook", "seguidores": 500}]

    resultado = conector.upsert(conn, datos)

    assert resultado.nuevos == 1
    fila = conn.execute("SELECT * FROM control_perfiles").fetchone()
    assert fila["perfil"] == "Perfil FB"
    assert fila["seguidores"] == 500
