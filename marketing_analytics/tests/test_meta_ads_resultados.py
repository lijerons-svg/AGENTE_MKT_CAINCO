from marketing_analytics.connectors.meta_ads.resultados import (
    resolver_conversaciones_iniciadas,
    resolver_resultados,
)


def test_resuelve_link_click_para_objetivo_trafico():
    actions = [
        {"action_type": "link_click", "value": "42"},
        {"action_type": "post_engagement", "value": "100"},
    ]
    assert resolver_resultados("OUTCOME_TRAFFIC", actions) == 42


def test_objetivo_awareness_usa_alcance_no_actions():
    assert resolver_resultados("OUTCOME_AWARENESS", None, reach=5000) == 5000


def test_objetivo_brand_awareness_tambien_usa_alcance():
    """BRAND_AWARENESS es el nombre viejo del mismo objetivo — el dashboard
    y el PPT ya lo tratan como "de alcance", esto tiene que ser consistente."""
    assert resolver_resultados("BRAND_AWARENESS", None, reach=3000) == 3000


def test_objetivo_desconocido_sin_match_devuelve_cero():
    actions = [{"action_type": "otra_cosa", "value": "10"}]
    assert resolver_resultados("OBJETIVO_RARO", actions) == 0


def test_sin_actions_devuelve_cero():
    assert resolver_resultados("OUTCOME_LEADS", None) == 0


def test_conversaciones_iniciadas_se_lee_sin_importar_el_objetivo():
    """Caso real: una campaña de tráfico puede igual generar mensajes de
    WhatsApp — la columna propia de "Conversación iniciada" tiene que verse
    siempre, no solo cuando el objetivo de la campaña es justo MESSAGES."""
    actions = [
        {"action_type": "link_click", "value": "25"},
        {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "7"},
    ]
    assert resolver_conversaciones_iniciadas(actions) == 7


def test_conversaciones_iniciadas_sin_esa_accion_devuelve_cero():
    actions = [{"action_type": "link_click", "value": "25"}]
    assert resolver_conversaciones_iniciadas(actions) == 0


def test_conversaciones_iniciadas_sin_actions_devuelve_cero():
    assert resolver_conversaciones_iniciadas(None) == 0
