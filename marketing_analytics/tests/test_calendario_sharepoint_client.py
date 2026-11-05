import pytest
import responses

from marketing_analytics.connectors.calendario_sharepoint.client import (
    CalendarioSharePointClient,
    _encontrar_fila_encabezados,
    _normalizar_encabezado,
)
from marketing_analytics.connectors.http_utils import ApiError

_GRAPH = "https://graph.microsoft.com/v1.0"


def _cliente():
    return CalendarioSharePointClient(
        tenant_id="tenant-1",
        client_id="client-1",
        client_secret="secret-1",
        sharepoint_hostname="caincoscz.sharepoint.com",
        site_path="/sites/MARKETING",
        file_name="CAINCO_Programacion_Publicaciones.xlsx",
        sheet_name="Planificacion",
    )


def test_normalizar_encabezado_maneja_espacios_barras_y_mayusculas():
    assert _normalizar_encabezado(" Inversion USD ") == "inversion_usd"
    assert _normalizar_encabezado("Campana / Evento") == "campana_evento"
    assert _normalizar_encabezado("PERFIL") == "perfil"


def test_encontrar_fila_encabezados_sin_banner_es_la_fila_0():
    assert _encontrar_fila_encabezados([["ID", "PERFIL"], ["1", "Marca X"]]) == 0


def test_encontrar_fila_encabezados_con_banner_arriba_lo_saltea():
    """Caso real de QA: el archivo tiene una fila de título arriba de la
    tabla ("CAINCO - Programación 2026") — usedRange la incluye, y si se
    asume que la fila 0 es el encabezado, todo se lee mal (todas las filas
    terminan con id vacío y colisionan en un único uid)."""
    valores = [
        ["CAINCO - Programación 2026", None],
        ["ID", "PERFIL"],
        ["1", "Marca X"],
    ]
    assert _encontrar_fila_encabezados(valores) == 1


@responses.activate
def test_obtener_filas_calendario_encadena_token_site_item_y_lee_filas(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = _cliente()

    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-1/oauth2/v2.0/token",
        json={"access_token": "token-abc"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/caincoscz.sharepoint.com:/sites/MARKETING",
        json={"id": "site-1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/root/search(q='CAINCO_Programacion_Publicaciones.xlsx')",
        json={"value": [{"id": "item-1", "name": "CAINCO_Programacion_Publicaciones.xlsx"}]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/items/item-1/workbook/worksheets('Planificacion')/usedRange(valuesOnly=true)",
        json={"values": [["ID", "PERFIL"], ["1", "Marca X"], ["2", "Marca Y"]]},
        status=200,
    )

    filas = cliente.obtener_filas_calendario()

    assert filas == [{"id": "1", "perfil": "Marca X"}, {"id": "2", "perfil": "Marca Y"}]
    assert responses.calls[3].request.headers["Authorization"] == "Bearer token-abc"


@responses.activate
def test_obtener_filas_calendario_hoja_vacia_devuelve_lista_vacia(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = _cliente()

    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-1/oauth2/v2.0/token",
        json={"access_token": "token-abc"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/caincoscz.sharepoint.com:/sites/MARKETING",
        json={"id": "site-1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/root/search(q='CAINCO_Programacion_Publicaciones.xlsx')",
        json={"value": [{"id": "item-1", "name": "CAINCO_Programacion_Publicaciones.xlsx"}]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/items/item-1/workbook/worksheets('Planificacion')/usedRange(valuesOnly=true)",
        json={"values": []},
        status=200,
    )

    assert cliente.obtener_filas_calendario() == []


@responses.activate
def test_busca_el_archivo_por_nombre_aunque_no_este_en_la_raiz(monkeypatch):
    """Caso real de QA: el archivo vive en una subcarpeta (ej. "Documentos
    compartidos"), no en la raíz del drive — buscar por nombre lo encuentra
    igual, sin necesitar la ruta exacta."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = _cliente()

    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-1/oauth2/v2.0/token",
        json={"access_token": "token-abc"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/caincoscz.sharepoint.com:/sites/MARKETING",
        json={"id": "site-1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/root/search(q='CAINCO_Programacion_Publicaciones.xlsx')",
        json={
            "value": [
                {"id": "otro-1", "name": "CAINCO_Programacion_Publicaciones - copia.xlsx"},
                {"id": "item-1", "name": "CAINCO_Programacion_Publicaciones.xlsx"},
            ]
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/items/item-1/workbook/worksheets('Planificacion')/usedRange(valuesOnly=true)",
        json={"values": [["ID"], ["1"]]},
        status=200,
    )

    filas = cliente.obtener_filas_calendario()

    assert filas == [{"id": "1"}]


@responses.activate
def test_ignora_banner_arriba_del_encabezado_y_filas_en_blanco(monkeypatch):
    """Reproduce el bug real de QA: título arriba de la tabla + filas en
    blanco al final (por formato aplicado a un rango grande) — antes,
    todas las filas terminaban con id vacío y colapsaban en un solo uid."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = _cliente()

    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-1/oauth2/v2.0/token",
        json={"access_token": "token-abc"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/caincoscz.sharepoint.com:/sites/MARKETING",
        json={"id": "site-1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/root/search(q='CAINCO_Programacion_Publicaciones.xlsx')",
        json={"value": [{"id": "item-1", "name": "CAINCO_Programacion_Publicaciones.xlsx"}]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/items/item-1/workbook/worksheets('Planificacion')/usedRange(valuesOnly=true)",
        json={
            "values": [
                ["CAINCO - Programación 2026", None],
                ["ID", "PERFIL"],
                ["1", "Marca X"],
                ["2", "Marca Y"],
                ["", ""],
                [None, None],
            ]
        },
        status=200,
    )

    filas = cliente.obtener_filas_calendario()

    assert filas == [{"id": "1", "perfil": "Marca X"}, {"id": "2", "perfil": "Marca Y"}]


@responses.activate
def test_archivo_no_encontrado_lanza_error_claro(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    cliente = _cliente()

    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-1/oauth2/v2.0/token",
        json={"access_token": "token-abc"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/caincoscz.sharepoint.com:/sites/MARKETING",
        json={"id": "site-1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{_GRAPH}/sites/site-1/drive/root/search(q='CAINCO_Programacion_Publicaciones.xlsx')",
        json={"value": []},
        status=200,
    )

    with pytest.raises(ApiError, match="No se encontró"):
        cliente.obtener_filas_calendario()
