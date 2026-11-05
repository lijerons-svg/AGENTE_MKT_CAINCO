import pytest

from marketing_analytics.config.schema import MetaOrganicoConfig, PerfilMetaOrganico, Red


def test_unidad_por_defecto_es_el_nombre_del_perfil():
    perfil = PerfilMetaOrganico(id="p1", nombre="Academy Cainco", red=Red.FACEBOOK, page_id="123")

    assert perfil.unidad == "Academy Cainco"


def test_unidad_explicita_agrupa_facebook_e_instagram():
    fb = PerfilMetaOrganico(
        id="p1", nombre="CAINCO", unidad="CAINCO", red=Red.FACEBOOK, page_id="123"
    )
    ig = PerfilMetaOrganico(
        id="p2", nombre="Cainco Bolivia (IG)", unidad="CAINCO", red=Red.INSTAGRAM, ig_user_id="456"
    )

    assert fb.unidad == ig.unidad == "CAINCO"


def test_alias_pauta_por_defecto_es_la_unidad():
    perfil = PerfilMetaOrganico(
        id="p1", nombre="Academy Cainco", unidad="Academy Cainco", red=Red.FACEBOOK, page_id="123"
    )

    assert perfil.alias_pauta == "Academy Cainco"


def test_alias_pauta_explicito_para_matchear_campanas_con_nombre_corto():
    """Caso real: las campañas de Meta Ads usan la palabra clave corta
    ("ACADEMY"), no el nombre completo de la unidad ("Academy Cainco")."""
    perfil = PerfilMetaOrganico(
        id="p1",
        nombre="Academy Cainco",
        unidad="Academy Cainco",
        alias_pauta="ACADEMY",
        red=Red.FACEBOOK,
        page_id="123",
    )

    assert perfil.alias_pauta == "ACADEMY"
    assert perfil.unidad == "Academy Cainco"


def test_mismo_alias_pauta_para_la_misma_unidad_no_es_error():
    """Facebook + Instagram de la misma marca comparten alias_pauta sin
    problema — es el mismo negocio, no una colisión."""
    fb = PerfilMetaOrganico(id="p1", nombre="Academy FB", unidad="Academy Cainco", red=Red.FACEBOOK, page_id="1")
    ig = PerfilMetaOrganico(id="p2", nombre="Academy IG", unidad="Academy Cainco", red=Red.INSTAGRAM, ig_user_id="2")

    config = MetaOrganicoConfig(perfiles=[fb, ig])

    assert len(config.perfiles) == 2


def test_alias_pauta_repetido_en_dos_unidades_distintas_es_error():
    """Si dos unidades distintas terminan con el mismo alias_pauta (fácil
    de hacer sin querer, ya que por default es igual a `unidad`), una
    campaña con ese texto se le asignaría a una unidad al azar sin ningún
    aviso — esto tiene que fallar fuerte al cargar la config, no en
    silencio meses después."""
    academy = PerfilMetaOrganico(
        id="p1", nombre="Academy", unidad="Academy Cainco", alias_pauta="ACADEMY", red=Red.FACEBOOK, page_id="1"
    )
    otra = PerfilMetaOrganico(
        id="p2", nombre="Otra unidad", unidad="Otra Unidad", alias_pauta="ACADEMY", red=Red.FACEBOOK, page_id="2"
    )

    with pytest.raises(ValueError, match="alias_pauta 'ACADEMY'"):
        MetaOrganicoConfig(perfiles=[academy, otra])
