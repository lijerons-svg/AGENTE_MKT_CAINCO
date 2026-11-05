from marketing_analytics.dashboard.control_contenido.matching import emparejar_unidad_campana

_ALIAS_A_UNIDAD = {
    "CAINCO": ("CAINCO", False),
    "CAINCO INVERSIONES": ("CAINCO Inversiones", False),
    "ACADEMY": ("Academy Cainco", False),
    "ACIERTA": ("Acierta CAINCO", False),
}


def test_matchea_por_alias_corto_no_por_nombre_completo_de_la_unidad():
    """Caso real de QA: las campañas usan la palabra clave corta ("ACADEMY"),
    no el nombre completo de la unidad ("Academy Cainco") — matchear por
    nombre completo fallaba en la enorme mayoría de las campañas reales."""
    assert (
        emparejar_unidad_campana(
            "ENERO 2026 - ACADEMY - PRODUCTIVIDAD AVANZADA", _ALIAS_A_UNIDAD
        )
        == "Academy Cainco"
    )


def test_sin_coincidencia_devuelve_none():
    assert emparejar_unidad_campana("CAMPAÑA SIN MARCA RECONOCIBLE", _ALIAS_A_UNIDAD) is None


def test_coincidencia_ambigua_se_queda_con_la_mas_especifica():
    """"CAINCO" matchea tanto al alias "CAINCO" como a "CAINCO INVERSIONES"
    — se queda con el más largo para no perder especificidad."""
    assert (
        emparejar_unidad_campana("CAMPAÑA CAINCO INVERSIONES 2024", _ALIAS_A_UNIDAD)
        == "CAINCO Inversiones"
    )


def test_coincidencia_simple_no_ambigua():
    assert emparejar_unidad_campana("CAMPAÑA CAINCO JULIO", _ALIAS_A_UNIDAD) == "CAINCO"


_ALIAS_CON_GENERICO = {
    "FORO": ("Foros Cainco", True),
    "ICC": ("ICC Bolivia", False),
    "FUNDARE": ("Fundares Santa Cruz", False),
}


def test_alias_generico_pierde_contra_uno_propio_aunque_sea_mas_corto():
    """Caso real de QA: Meta Ads tenía campañas como "OCTUBRE 2026 - FORO
    ICC LABOR & TALENT" — de la unidad ICC Bolivia, no de Foros Cainco,
    aunque la palabra "foro" también aparezca ahí. Con la regla vieja de
    "el alias más largo gana", "FORO" (4 letras, genérico) le ganaba a
    "ICC" (3 letras, propio) y esas campañas (y su inversión real) quedaban
    mal asignadas a Foros Cainco."""
    assert (
        emparejar_unidad_campana(
            "OCTUBRE 2026 - FORO ICC LABOR & TALENT CAMPAÑA 2", _ALIAS_CON_GENERICO
        )
        == "ICC Bolivia"
    )


def test_alias_generico_gana_cuando_es_la_unica_coincidencia():
    """Sin ningún alias propio compitiendo, el genérico sigue funcionando
    normalmente para sus propias campañas."""
    assert (
        emparejar_unidad_campana(
            "ABRIL 2026 - FORO DE LOGÍSTICA 02", _ALIAS_CON_GENERICO
        )
        == "Foros Cainco"
    )
