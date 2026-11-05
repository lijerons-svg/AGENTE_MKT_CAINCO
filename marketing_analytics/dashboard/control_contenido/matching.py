"""Empareja campañas de Meta Ads con su "unidad" (marca/perfil unificado).

Meta Ads no tiene un campo que vincule una campaña con una unidad de
negocio — se agrupan por cuenta publicitaria, no por marca. El nombre de
campaña usa una palabra clave corta de la marca (ej. "ACADEMY"), no el
nombre completo de la unidad ("Academy Cainco") — confirmado con datos
reales: matchear por el nombre completo fallaba en la enorme mayoría de
las campañas. Por eso se matchea contra un alias corto configurable por
unidad (`alias_pauta` en config.yaml), no contra `unidad` directamente.
Frágil de todos modos si una campaña no sigue la convención — por eso el
resultado se verifica con datos reales antes de darlo por bueno (ver
`verificar_unidades.py`).
"""
from __future__ import annotations


def emparejar_unidad_campana(
    nombre_campana: str, alias_a_unidad: dict[str, tuple[str, bool]]
) -> str | None:
    """Devuelve la unidad cuyo alias aparece dentro de `nombre_campana`
    (sin distinguir mayúsculas/minúsculas).

    `alias_a_unidad` mapea alias -> (unidad, es_generico). Un alias
    "genérico" (ej. "FORO" para la unidad Foros Cainco) describe un formato
    de evento que OTRAS unidades también usan en sus propias campañas (ej.
    "OCTUBRE 2026 - FORO ICC LABOR & TALENT" es de ICC, no de Foros Cainco,
    aunque contenga la palabra "foro") — confirmado con datos reales: con
    la regla vieja de "el alias más largo gana", "FORO" (4 letras) le
    ganaba a "ICC" (3 letras) y esas campañas quedaban mal asignadas. Por
    eso un alias genérico solo se usa cuando es la ÚNICA coincidencia; si
    compite con un alias no genérico, pierde sin importar la longitud. Si
    ninguno matchea, devuelve None (no se inventa una unidad)."""
    nombre_normalizado = nombre_campana.lower()
    coincidencias = [
        alias for alias in alias_a_unidad if alias.lower() in nombre_normalizado
    ]
    if not coincidencias:
        return None
    especificas = [a for a in coincidencias if not alias_a_unidad[a][1]]
    candidatas = especificas or coincidencias
    return alias_a_unidad[max(candidatas, key=len)][0]
