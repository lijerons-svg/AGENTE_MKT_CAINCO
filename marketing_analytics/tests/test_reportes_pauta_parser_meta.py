from marketing_analytics.reportes_pauta.parser_meta import (
    es_recibo_meta,
    parsear_recibo_meta,
)

_TEXTO_RECIBO_META = """Recibo para CAINCO BOLIVIA 2025
Identificador de cuenta: 666496419433136
Fecha de la factura/pago
5 jun. 2026, 11:51
Método de pago
Visa ···· 7093
Número de referencia: CBUHRT57F2
Identificador de la transacción
27346477548372238-27346477648372228
Tipo de producto
Meta anuncios
Pagado
479,00 $
Se te ha emitido una factura porque has alcanzado tu umbral de pago de 479,00 $.
Campañas
MAYO 2026 - INNOVA - FI - MICROLABS
De 25 may. 2026, 0:00 a 5 jun. 2026, 11:51
18,44 $
MAYO 2026 - INNOVA - FI - MICROLABS 21 285 Impresiones 18,44 $
MAYO 2026 - ACADEMY - CONTRATOS EMPRESARIALES SIN ERRORES
De 25 may. 2026, 0:00 a 5 jun. 2026, 11:51
0,01 $
MAYO 2026 - ACADEMY - CONTRATOS EMPRESARIALES SIN ERRORES 2 Impresiones 0,01 $
MAYO 2026 - ACIERTA - RECLUTAMIENTO SERVICIO
De 25 may. 2026, 0:00 a 5 jun. 2026, 11:51
45,54 $
MAYO 2026 - ACIERTA - RECLUTAMIENTO SERVICIO 20 082 Impresiones 45,54 $
"""

_ALIAS_A_UNIDAD = {"ACADEMY": ("Academy Cainco", False), "ACIERTA": ("Acierta Cainco", False)}


def test_es_recibo_meta_detecta_por_tipo_de_producto():
    assert es_recibo_meta(_TEXTO_RECIBO_META) is True
    assert es_recibo_meta("cualquier otro texto") is False


def test_parsear_recibo_meta_extrae_una_fila_por_campana():
    filas = parsear_recibo_meta(_TEXTO_RECIBO_META, _ALIAS_A_UNIDAD)
    assert len(filas) == 3


def test_parsear_recibo_meta_arrastra_el_numero_de_referencia_en_todas_las_filas():
    filas = parsear_recibo_meta(_TEXTO_RECIBO_META, _ALIAS_A_UNIDAD)
    assert all(f["codigo_referencia"] == "CBUHRT57F2" for f in filas)


def test_parsear_recibo_meta_matchea_unidad_por_alias():
    filas = parsear_recibo_meta(_TEXTO_RECIBO_META, _ALIAS_A_UNIDAD)
    por_nombre = {f["nombre_actividad"]: f for f in filas}
    assert por_nombre["MAYO 2026 - ACADEMY - CONTRATOS EMPRESARIALES SIN ERRORES"]["identificador_unidad"] == "Academy Cainco"
    assert por_nombre["MAYO 2026 - ACIERTA - RECLUTAMIENTO SERVICIO"]["identificador_unidad"] == "Acierta Cainco"


def test_parsear_recibo_meta_no_inventa_unidad_si_no_hay_alias_que_matchee():
    filas = parsear_recibo_meta(_TEXTO_RECIBO_META, _ALIAS_A_UNIDAD)
    por_nombre = {f["nombre_actividad"]: f for f in filas}
    assert por_nombre["MAYO 2026 - INNOVA - FI - MICROLABS"]["identificador_unidad"] == "SIN IDENTIFICAR"


def test_parsear_recibo_meta_convierte_monto_y_resultado_a_numero():
    filas = parsear_recibo_meta(_TEXTO_RECIBO_META, _ALIAS_A_UNIDAD)
    por_nombre = {f["nombre_actividad"]: f for f in filas}
    fila = por_nombre["MAYO 2026 - ACIERTA - RECLUTAMIENTO SERVICIO"]
    assert fila["monto_invertido"] == 45.54
    assert fila["resultado_obtenido"] == 20082
    assert fila["resultado_tipo"] == "Impresiones"
