"""Modelos de validación para config.yaml.

Todo lo que NO es secreto (IDs, rutas, rangos de fechas, listas de perfiles)
vive acá. Los secretos (tokens, API keys) se resuelven aparte desde variables
de entorno — ver loader.py.
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Red(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class ModoRangoFechas(str, Enum):
    ULTIMOS_N_DIAS = "last_n_days"
    PERSONALIZADO = "custom"


class RangoFechasConfig(BaseModel):
    modo: ModoRangoFechas = ModoRangoFechas.ULTIMOS_N_DIAS
    ultimos_n_dias: int = Field(default=30, gt=0)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    # Meta Ads sigue ajustando gasto/resultados por ventanas de atribución
    # — el default de Meta es "7 días clic, 1 día vista", o sea que una
    # conversión puede atribuirse hasta 7 días después del clic. Como el
    # checkpoint automático solo avanza hacia adelante y nunca vuelve a
    # revisar fechas ya pasadas, sin este solape esos ajustes tardíos se
    # perderían en silencio. 0 = desactivar (comportamiento viejo).
    dias_solape: int = Field(default=7, ge=0)

    @model_validator(mode="after")
    def _validar_personalizado(self) -> "RangoFechasConfig":
        if self.modo == ModoRangoFechas.PERSONALIZADO:
            if self.fecha_inicio is None or self.fecha_fin is None:
                raise ValueError(
                    "modo 'custom' requiere fecha_inicio y fecha_fin"
                )
            if self.fecha_fin < self.fecha_inicio:
                raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")
        return self


class GeneralConfig(BaseModel):
    timezone: str = "America/La_Paz"
    output_dir: str = "output"
    database_path: str = "database/historico_rrss.db"
    date_range: RangoFechasConfig = Field(default_factory=RangoFechasConfig)


class PerfilMetaOrganico(BaseModel):
    """Un perfil (Página FB o cuenta IG) a recorrer. Agregar uno nuevo = una
    entrada más acá, nunca un cambio de código."""

    id: str
    nombre: str
    # Agrupa Facebook + Instagram de la misma marca como "un solo perfil"
    # para el dashboard Control de Contenido (ej. "Academy" = Academy FB +
    # Academy IG). Si no se especifica, se usa `nombre` — retrocompatible
    # con configs existentes de una sola red por unidad.
    unidad: str = ""
    # Palabra clave corta para emparejar campañas de Meta Ads con esta
    # unidad (ej. "ACADEMY" en vez de "Academy Cainco" — las campañas
    # reales usan la palabra corta, no el nombre completo de la unidad;
    # confirmado con datos reales). Si no se especifica, se usa `unidad`.
    alias_pauta: str = ""
    # Marca este alias como una palabra de formato compartida entre varias
    # unidades (ej. "FORO": varias unidades organizan sus propios "foros",
    # no es exclusivo de una) en vez de un identificador propio de la
    # marca. Un alias genérico solo gana el emparejamiento cuando es la
    # ÚNICA coincidencia; si una campaña también contiene el alias propio
    # de otra unidad (ej. "ICC"), ese gana aunque sea más corto — caso real
    # de QA: "FORO" (genérico, 4 letras) le ganaba a "ICC" (propio, 3
    # letras) y esas campañas quedaban mal asignadas a la unidad equivocada.
    alias_pauta_generico: bool = False
    red: Red
    page_id: str | None = None
    ig_user_id: str | None = None

    @model_validator(mode="after")
    def _default_unidad(self) -> "PerfilMetaOrganico":
        if not self.unidad:
            self.unidad = self.nombre
        if not self.alias_pauta:
            self.alias_pauta = self.unidad
        return self

    @model_validator(mode="after")
    def _validar_id_de_red(self) -> "PerfilMetaOrganico":
        if self.red == Red.FACEBOOK and not self.page_id:
            raise ValueError(f"perfil '{self.id}': red facebook requiere page_id")
        if self.red == Red.INSTAGRAM and not self.ig_user_id:
            raise ValueError(f"perfil '{self.id}': red instagram requiere ig_user_id")
        return self


class MetaOrganicoConfig(BaseModel):
    perfiles: list[PerfilMetaOrganico] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_alias_pauta_sin_colision(self) -> "MetaOrganicoConfig":
        # Dos perfiles de la MISMA unidad (ej. Academy FB + Academy IG)
        # comparten alias_pauta sin problema — es el mismo negocio. El
        # riesgo real es que DOS UNIDADES DISTINTAS terminen con el mismo
        # alias_pauta (fácil de hacer sin querer, ya que por default es
        # igual a `unidad`): el emparejamiento de pauta (matching.py) es
        # un diccionario simple, así que la última unidad pisaría a la
        # primera en silencio y cada campaña de esa unidad se le asignaría
        # a la otra, sin ningún error ni aviso — se detecta acá, al cargar
        # config.yaml, en vez de como un dato mal ubicado meses después.
        unidad_por_alias: dict[str, str] = {}
        for perfil in self.perfiles:
            unidad_previa = unidad_por_alias.setdefault(perfil.alias_pauta, perfil.unidad)
            if unidad_previa != perfil.unidad:
                raise ValueError(
                    f"alias_pauta '{perfil.alias_pauta}' está usado tanto por la unidad '{unidad_previa}' "
                    f"como por '{perfil.unidad}' — una campaña de pauta con ese texto en el nombre se "
                    "asignaría a una unidad al azar, sin ningún aviso. Cambiá el alias_pauta de una de las "
                    "dos unidades en config.yaml para que no colisionen."
                )
        return self


class CuentaPublicitaria(BaseModel):
    id: str
    nombre: str
    # Explícito (sin default): dos cuentas de la misma organización pueden
    # facturar en monedas distintas (visto en la práctica: BOB y USD
    # mezcladas) y sumarlas sin distinguir moneda da un "Gasto" inválido.
    moneda: str = Field(min_length=3, max_length=3)


class MetaAdsConfig(BaseModel):
    cuentas: list[CuentaPublicitaria] = Field(default_factory=list)


class MetaConfig(BaseModel):
    # Meta deprecia versiones ~2 años después de su lanzamiento (v23.0 expiró
    # el 9/jun/2026; v20.0 se apaga en sept/2026). Verificar vigencia en
    # developers.facebook.com/docs/graph-api/changelog/versions/ antes de
    # asumir que este default sigue siendo válido.
    api_version: str = "v25.0"
    organico: MetaOrganicoConfig = Field(default_factory=MetaOrganicoConfig)
    ads: MetaAdsConfig = Field(default_factory=MetaAdsConfig)


class MailchimpConfig(BaseModel):
    server_prefix: str
    enabled: bool = True


class CalendarioConfig(BaseModel):
    """Calendario de publicaciones planificado por el equipo en SharePoint —
    se sincroniza entero en cada corrida (no es un feed histórico
    incremental por rango de fechas, como los demás conectores)."""

    enabled: bool = False
    sharepoint_hostname: str = ""
    site_path: str = ""
    file_name: str = ""
    sheet_name: str = ""


class LinkedInConfig(BaseModel):
    """Community Management API — a diferencia de Meta, autoriza UNA sola
    organización por vez (no una lista de perfiles), y el access token lo
    consigue a mano una persona admin de esa página (ver
    connectors/linkedin/obtener_token.py), no un token de sistema
    permanente."""

    enabled: bool = False
    organization_id: str = ""
    # Nombre para mostrar en los reportes (columna "Página" en el Excel y
    # dashboards) — no se resuelve llamando a la API para no sumar otra
    # llamada más a verificar; se escribe a mano, igual que el "nombre" de
    # cada perfil de Meta Orgánico.
    nombre: str = ""

    @model_validator(mode="after")
    def _validar_organization_id(self) -> "LinkedInConfig":
        if self.enabled and not self.organization_id:
            raise ValueError("linkedin.enabled es true pero falta organization_id")
        return self


class PerfilCompetidor(BaseModel):
    """Una página de Facebook de un competidor, para el reporte PPT.

    Solo Facebook: es la única red donde Meta expone datos públicos
    (seguidores, texto de publicaciones) sin necesitar administrar la
    página. Instagram y LinkedIn no tienen equivalente — no se modelan acá
    para no sugerir una capacidad que no existe."""

    unidad: str
    nombre: str
    facebook_page_alias: str


class CompetenciaConfig(BaseModel):
    enabled: bool = False
    perfiles: list[PerfilCompetidor] = Field(default_factory=list)


class ReportesPptxConfig(BaseModel):
    """Vacío = todas las unidades de `meta.organico.perfiles`. Se puede
    seguir sobreescribiendo puntualmente con `--unidad` en la línea de
    comando, esto es solo el default de todos los días."""

    unidades: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    meta: MetaConfig = Field(default_factory=MetaConfig)
    mailchimp: MailchimpConfig
    calendario: CalendarioConfig = Field(default_factory=CalendarioConfig)
    linkedin: LinkedInConfig = Field(default_factory=LinkedInConfig)
    competencia: CompetenciaConfig = Field(default_factory=CompetenciaConfig)
    reportes_pptx: ReportesPptxConfig = Field(default_factory=ReportesPptxConfig)
