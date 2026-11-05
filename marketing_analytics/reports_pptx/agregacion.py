"""Convierte las filas crudas de una unidad (ya agrupadas por
`construir_datos_control_contenido`) en los datos que necesita cada slide
del reporte PPT. Funciones puras — nada de red ni de SQLite acá, para que
se puedan probar con datos ficticios.

Fórmulas consistentes con las que ya usa el dashboard (mismo criterio de
"engagement", "frecuencia" y "conversión" — ver
dashboard/control_contenido/template_datos.js y template_analisis.js) para
que ambos reportes nunca cuenten historias distintas con el mismo dato.
"""
from __future__ import annotations

_OBJETIVOS_DE_ALCANCE = {"OUTCOME_AWARENESS", "REACH", "BRAND_AWARENESS"}

# Facebook no expone alcance orgánico real (Meta lo discontinuó y su
# reemplazo documentado devuelve 0 — ver connectors/meta_organico/client.py)
# — mostrar "Alcance promedio" para Facebook sería mostrar un cero
# maquillado de dato real. Se omite esa fila para Facebook, igual que ya
# se decidió en el dashboard.
REDES_CON_ALCANCE_ORGANICO = {"instagram"}


_FORMATOS = {
    "imagen": "Imagen",
    "album": "Carrusel",
    "video": "Video",
    "link": "Enlace",
    "status": "Texto",
    "feed": "Feed",
    "reels": "Reel",
    "story": "Historia",
    "carousel_album": "Carrusel",
    "image": "Imagen",
}


def formato_post(fila: dict) -> str:
    return _FORMATOS.get((fila.get("tipo") or "").lower(), fila.get("tipo") or "Sin tipo")


def engagement_post(fila: dict) -> float:
    visualizaciones = fila.get("visualizaciones", 0)
    if not visualizaciones:
        return 0.0
    return (fila.get("total_interacciones", 0) / visualizaciones) * 100


def filtrar_por_mes(filas: list[dict], anio: int, mes: int, campo_fecha: str = "fecha") -> list[dict]:
    prefijo = f"{anio:04d}-{mes:02d}"
    return [f for f in filas if str(f.get(campo_fecha, "")).startswith(prefijo)]


def kpis_organico_por_red(filas_control_perfiles: list[dict]) -> dict[str, dict]:
    """A partir de las filas de `control_perfiles` del mes (ya filtradas),
    una por red. Si una red no publicó ese mes, no aparece (no se inventa
    una fila en cero)."""
    por_red: dict[str, dict] = {}
    for fila in filas_control_perfiles:
        red = fila["red"]
        por_red[red] = {
            "seguidores": fila.get("seguidores", 0),
            "nuevos_seguidores": fila.get("seguidores_ganados", 0),
            "publicaciones": fila.get("publicaciones_mes", 0),
            "visualizaciones": fila.get("visualizaciones_mes", 0),
            "interacciones": fila.get("interacciones_mes", 0),
        }
    return por_red


def alcance_promedio_por_red(filas_organico_mes: list[dict]) -> dict[str, int]:
    resultado: dict[str, int] = {}
    for red in REDES_CON_ALCANCE_ORGANICO:
        valores = [f["alcance"] for f in filas_organico_mes if f["red"] == red and f.get("alcance", 0) > 0]
        resultado[red] = round(sum(valores) / len(valores)) if valores else 0
    return resultado


def top_publicaciones(filas_organico_mes: list[dict], cantidad: int = 4, menor_primero: bool = False) -> list[dict]:
    ordenadas = sorted(filas_organico_mes, key=engagement_post, reverse=not menor_primero)
    return ordenadas[:cantidad]


def detalle_publicaciones(filas_organico_mes: list[dict]) -> list[dict]:
    return sorted(filas_organico_mes, key=lambda f: f.get("fecha", ""))


def _es_objetivo_de_alcance(objetivo: str) -> bool:
    return (objetivo or "").upper() in _OBJETIVOS_DE_ALCANCE


_METRICAS_PORCENTUALES = ("visualizaciones", "interacciones")


def mes_anterior(anio: int, mes: int) -> tuple[int, int]:
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


def delta_porcentual(actual: float, anterior: float) -> float | None:
    """None cuando no hay base de comparación real (mes anterior en cero o
    sin datos) — dividir por cero no es "0% de cambio", es "no aplica"."""
    if not anterior:
        return None
    return (actual - anterior) / anterior * 100


def deltas_kpis_red(kpis_actual: dict[str, dict], kpis_anterior: dict[str, dict]) -> dict[str, dict]:
    """Compara mes contra mes, red por red. Si una red no tiene datos del
    mes anterior (recién empezó, o es el primer mes que se genera), esa red
    no aparece — no se inventa un "0%" que en realidad es "sin base".

    "nuevos_seguidores" se compara en cantidad absoluta, no en porcentaje:
    a diferencia de visualizaciones/interacciones, puede ser negativo (una
    unidad puede perder seguidores en el mes), y un % contra una base
    negativa da una lectura que engaña — ej. pasar de perder 10 seguidores
    a perder solo 5 es una mejora, pero (-5 - -10) / -10 * 100 = -50%, que
    se leería como si hubiera empeorado el doble."""
    resultado: dict[str, dict] = {}
    for red, actual in kpis_actual.items():
        anterior = kpis_anterior.get(red)
        if not anterior:
            continue
        fila = {metrica: delta_porcentual(actual[metrica], anterior[metrica]) for metrica in _METRICAS_PORCENTUALES}
        fila["nuevos_seguidores"] = actual["nuevos_seguidores"] - anterior["nuevos_seguidores"]
        resultado[red] = fila
    return resultado


def _pct(parte: float, total: float) -> float:
    """Mismo criterio que `pct()` del dashboard HTML (template_core.js):
    0 en vez de división por cero, nunca un error ni un dato inventado."""
    return (parte / total) * 100 if total > 0 else 0.0


def kpis_mailchimp(filas_mailchimp_mes: list[dict]) -> dict:
    """Open Rate y Click Rate ponderados por volumen (suma de aperturas/
    clics únicos sobre la suma de entregados), igual que agregadosMailchimp()
    del dashboard — promediar el % de cada campaña sin ponderar distorsiona
    el resultado cuando los envíos tienen tamaños muy distintos."""
    entregados = sum(f.get("entregas", 0) for f in filas_mailchimp_mes)
    aperturas_unicas = sum(f.get("aperturas_unicas", 0) for f in filas_mailchimp_mes)
    clics_unicos = sum(f.get("clics_unicos", 0) for f in filas_mailchimp_mes)
    return {
        "envios": len(filas_mailchimp_mes),
        "entregados": entregados,
        "clics": sum(f.get("clics_totales", 0) for f in filas_mailchimp_mes),
        "apertura_promedio": _pct(aperturas_unicas, entregados),
        "clics_promedio": _pct(clics_unicos, entregados),
        "bajas": sum(f.get("bajas", 0) for f in filas_mailchimp_mes),
    }


def detalle_mailchimp(filas_mailchimp_mes: list[dict]) -> list[dict]:
    """Une cada campaña con sus tasas (Open Rate, Click Rate, CTOR) usando
    el mismo cálculo que la tabla de campañas del dashboard, para que ambos
    reportes muestren siempre el mismo número."""
    resultado = []
    for f in sorted(filas_mailchimp_mes, key=lambda f: f.get("fecha", "")):
        entregas = f.get("entregas", 0)
        aperturas_unicas = f.get("aperturas_unicas", 0)
        clics_unicos = f.get("clics_unicos", 0)
        resultado.append(
            {
                **f,
                "open_rate": _pct(aperturas_unicas, entregas),
                "click_rate": _pct(clics_unicos, entregas),
                "ctor": _pct(clics_unicos, aperturas_unicas),
            }
        )
    return resultado


def detalle_campanas(filas_ads_mes: list[dict]) -> list[dict]:
    """Una fila por campaña, con frecuencia y conversión calculadas igual
    que en el dashboard. `conversion` queda en None ("no aplica") para
    campañas de reconocimiento, donde "Resultados" de Meta es alcance, no
    una conversión real."""
    filas = []
    for c in filas_ads_mes:
        alcance = c.get("alcance", 0)
        impresiones = c.get("impresiones", 0)
        clics = c.get("clics", 0)
        frecuencia = (impresiones / alcance) if alcance > 0 else 0.0
        if _es_objetivo_de_alcance(c.get("objetivo", "")) or not clics:
            conversion = None
        else:
            conversion = (c.get("resultados", 0) / clics) * 100
        filas.append(
            {
                "campana": c.get("campana", ""),
                "inversion": c.get("importe_gastado", 0.0),
                "impresiones": impresiones,
                "alcance": alcance,
                "frecuencia": frecuencia,
                "clics": clics,
                "ctr": c.get("ctr", 0.0),
                "cpc": c.get("cpc", 0.0),
                "conversion": conversion,
            }
        )
    return filas
