import datetime

from marketing_analytics.connectors.calendario_sharepoint.mapper import (
    _parsear_numero,
    mapear_fila,
)


def test_mapear_fila_completa():
    fila = {
        "id": "1",
        "fecha_de_publicaicon": "2026-07-15",
        "perfil": "Marca X",
        "bu": "Comercio",
        "campana_evento": "Feria Julio",
        "tipo": "Post",
        "canal": "Instagram",
        "formato": "Reel",
        "objetivo": "Awareness",
        "descripcion_copy": "Copy de la publicación",
        "estado": "Aprobado",
        "responsable": "Sandy",
        "inversion_usd": 120.5,
        "link_publicacion": "https://instagram.com/p/123",
        "vobo_gcri": "Si",
        "notas": "Reprogramado",
    }

    registro = mapear_fila(fila)

    assert registro.id_origen == "1"
    assert registro.fecha_publicacion == datetime.date(2026, 7, 15)
    assert registro.campana_evento == "Feria Julio"
    assert registro.inversion_usd == 120.5
    assert registro.uid == "calendario|1"


def test_mapear_fila_sin_fecha_ni_campos_opcionales_no_falla():
    registro = mapear_fila({"id": "2"})

    assert registro.fecha_publicacion is None
    assert registro.perfil == ""
    assert registro.inversion_usd == 0.0


def test_mapear_fila_con_fecha_invalida_queda_en_none():
    registro = mapear_fila({"id": "3", "fecha_de_publicaicon": "pendiente de definir"})

    assert registro.fecha_publicacion is None


def test_mapear_fila_con_fecha_como_numero_de_serie_de_excel():
    """Caso real: Graph devuelve las celdas con formato de fecha como
    número de serie de Excel (días desde 30/dic/1899), no como texto,
    aunque en la hoja se vea "1/2/2026"."""
    registro = mapear_fila({"id": "5", "fecha_de_publicaicon": 46024})

    assert registro.fecha_publicacion == datetime.date(2026, 1, 2)


def test_parsear_numero_con_coma_decimal_y_espacio_invisible():
    """Caso real de QA: '78,92\xa0' (formato boliviano + espacio no
    separable pegado al copiar desde Excel) rompía con ValueError."""
    assert _parsear_numero("78,92\xa0") == 78.92


def test_parsear_numero_con_miles_y_decimales():
    assert _parsear_numero("1.234,56") == 1234.56


def test_parsear_numero_con_punto_decimal_normal():
    assert _parsear_numero("120.5") == 120.5


def test_parsear_numero_vacio_o_no_numerico_da_cero():
    assert _parsear_numero("") == 0.0
    assert _parsear_numero(None) == 0.0
    assert _parsear_numero("pendiente") == 0.0


def test_mapear_fila_con_inversion_formato_boliviano_no_falla():
    registro = mapear_fila({"id": "4", "inversion_usd": "78,92\xa0"})

    assert registro.inversion_usd == 78.92
