"""Cliente delgado sobre la Community Management API de LinkedIn.

Dos diferencias grandes con Meta:
- El access token lo consigue a mano una persona admin de la página (ver
  obtener_token.py) y vence cada ~60 días — no hay token de sistema
  permanente para estos endpoints.
- LinkedIn retira versiones de sus endpoints /rest/ con el tiempo (dan 426
  NONEXISTENT_VERSION) sin decir en el propio error cuál es la vigente. En
  vez de una versión fija en el código (que se rompería sola en unos meses,
  sin que nadie lo note hasta la próxima corrida), el cliente prueba los
  últimos 24 meses hasta encontrar una que LinkedIn acepte, y la reutiliza
  durante toda la corrida (ver `_resolver_version`).
"""
from __future__ import annotations

import datetime
import logging
from urllib.parse import quote

from marketing_analytics.connectors.http_utils import ApiError, solicitar

logger = logging.getLogger(__name__)

BASE = "https://api.linkedin.com"


def _generar_versiones_candidatas(meses: int = 24, hoy: datetime.date | None = None) -> tuple[str, ...]:
    """YYYYMM de los últimos `meses`, del más nuevo al más viejo, a partir de
    la fecha de hoy — así no hace falta acordarse de actualizar un número
    fijo cada vez que LinkedIn retira versiones viejas."""
    hoy = hoy or datetime.date.today()
    versiones = []
    for i in range(meses):
        total = (hoy.year * 12 + hoy.month - 1) - i
        anio, mes = divmod(total, 12)
        versiones.append(f"{anio}{mes + 1:02d}")
    return tuple(versiones)


class LinkedInClient:
    def __init__(self, access_token: str):
        self._access_token = access_token
        self._version: str | None = None

    def _resolver_version(self) -> str:
        if self._version:
            return self._version
        for version in _generar_versiones_candidatas():
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "LinkedIn-Version": version,
                "X-Restli-Protocol-Version": "2.0.0",
            }
            try:
                # Llamada liviana (count=1) solo para confirmar que la
                # versión existe — no importa si el resto de la respuesta
                # tiene sentido de negocio, solo que no sea un 426.
                solicitar(
                    "GET",
                    f"{BASE}/rest/posts",
                    headers=headers,
                    params={"q": "author", "author": "urn:li:organization:1", "count": 1},
                )
            except ApiError as error:
                if error.status_code == 426:
                    continue
            self._version = version
            logger.info("LinkedIn-Version detectada: %s", version)
            return version
        raise RuntimeError(
            "Ninguna versión de LinkedIn-Version de los últimos 24 meses fue aceptada — "
            "puede que LinkedIn haya cambiado el formato; revisar a mano."
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "LinkedIn-Version": self._resolver_version(),
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @staticmethod
    def _fecha_post(post: dict) -> datetime.date:
        ms = post.get("publishedAt") or post.get("createdAt") or 0
        return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.timezone.utc).date()

    def obtener_posts(
        self, organization_id: str, desde: datetime.date, hasta: datetime.date, paginas_maximas: int = 10
    ) -> list[dict]:
        """Nota honesta: no hay documentación confirmada de que /rest/posts
        venga ordenado del más nuevo al más viejo — se asume (es lo habitual
        en un feed), y se corta apenas aparece un post anterior a `desde`.
        `paginas_maximas` es una válvula de seguridad: si el supuesto fuera
        incorrecto, evita paginar sin límite en vez de fallar en silencio."""
        org_urn = f"urn:li:organization:{organization_id}"
        encontrados: list[dict] = []
        start = 0
        count = 50

        for _ in range(paginas_maximas):
            data = solicitar(
                "GET",
                f"{BASE}/rest/posts",
                headers=self._headers(),
                params={"author": org_urn, "q": "author", "count": count, "start": start},
            )
            elementos = data.get("elements", [])
            if not elementos:
                break

            corte = False
            for post in elementos:
                fecha = self._fecha_post(post)
                if fecha < desde:
                    corte = True
                    break
                if fecha <= hasta:
                    encontrados.append(post)
            if corte or len(elementos) < count:
                break
            start += count
        else:
            logger.warning(
                "Se llegó al límite de %d páginas trayendo posts de LinkedIn sin encontrar "
                "el límite de fecha '%s' — puede haber posts del rango pedido sin traer.",
                paginas_maximas, desde,
            )

        return encontrados

    def obtener_estadisticas_post(self, organization_id: str, post_id: str) -> dict:
        """Nota honesta: el nombre de los campos de respuesta
        (totalShareStatistics.likeCount/commentCount/shareCount/
        impressionCount/clickCount) sigue el esquema documentado de
        LinkedIn para esta API pero no se verificó contra una respuesta
        real todavía — si algún campo no viene, el mapper lo deja en 0 en
        vez de romper la corrida."""
        org_urn = f"urn:li:organization:{organization_id}"
        # Un post de LinkedIn puede tener id "urn:li:share:..." o
        # "urn:li:ugcPost:..." según cómo se haya creado, y cada tipo
        # necesita su propio nombre de parámetro acá.
        campo = "shares" if post_id.startswith("urn:li:share:") else "ugcPosts"
        query = (
            f"q=organizationalEntity&organizationalEntity={quote(org_urn, safe='')}"
            f"&{campo}=List({quote(post_id, safe='')})"
        )
        try:
            data = solicitar(
                "GET", f"{BASE}/rest/organizationalEntityShareStatistics?{query}", headers=self._headers()
            )
        except ApiError as error:
            logger.warning("No se pudieron traer estadísticas del post %s: %s", post_id, error)
            return {}
        elementos = data.get("elements", [])
        return elementos[0] if elementos else {}

    def obtener_seguidores_totales(self, organization_id: str) -> int:
        org_urn = f"urn:li:organization:{organization_id}"
        data = solicitar(
            "GET",
            f"{BASE}/rest/organizationalEntityFollowerStatistics",
            headers=self._headers(),
            params={"q": "organizationalEntity", "organizationalEntity": org_urn},
        )
        elementos = data.get("elements", [])
        if not elementos:
            return 0
        # Cualquiera de los desgloses completos suma al mismo total (cada
        # uno reparte a TODOS los seguidores desde un ángulo distinto) — se
        # usa el de antigüedad (seniority) por ser el que vino poblado en
        # la respuesta de prueba.
        desglose = elementos[0].get("followerCountsBySeniority", [])
        return sum(
            c.get("followerCounts", {}).get("organicFollowerCount", 0)
            + c.get("followerCounts", {}).get("paidFollowerCount", 0)
            for c in desglose
        )
