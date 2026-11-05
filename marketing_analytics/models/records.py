"""Registros tipados de cada fuente, antes de persistir en SQLite.

Cada modelo sabe construir su propio `uid` de deduplicación mediante
`build_uid`. Los conectores (fase 2/3) devuelven listas de estos modelos;
el repositorio (database/repository.py) es el único que sabe insertarlos.
"""
from __future__ import annotations

import datetime

from pydantic import BaseModel, Field, field_validator

from marketing_analytics.models.uid import build_uid


class MetaOrganicoPost(BaseModel):
    fuente: str = Field(default="meta_organico", frozen=True)
    perfil: str
    pagina: str
    red: str
    fecha_publicacion: datetime.date
    tipo: str
    descripcion: str = ""
    alcance: int = 0
    visualizaciones: int = 0
    total_clics: int = 0
    clics_enlace: int = 0
    reacciones: int = 0
    comentarios: int = 0
    compartidos: int = 0
    total_interacciones: int = 0
    id_publicacion_origen: str
    # URL pública de la imagen/miniatura del post — usada por el reporte
    # PPT para mostrar el contenido real, no un placeholder. Vacía si Meta
    # no la expone para ese post (ej. posts de solo texto).
    imagen_url: str = ""
    # Link a la publicación original — de respaldo cuando no hay imagen_url
    # o la descarga falla (URL firmada vencida), para que se pueda ir a
    # verla a mano mientras tanto.
    link: str = ""

    @field_validator("descripcion")
    @classmethod
    def _truncar_descripcion(cls, v: str) -> str:
        return v[:120]

    @property
    def uid(self) -> str:
        return build_uid(
            fuente=self.fuente,
            fecha=self.fecha_publicacion,
            perfil=self.perfil,
            id_publicacion=self.id_publicacion_origen,
        )


class MetaAdsRegistro(BaseModel):
    fuente: str = Field(default="meta_ads", frozen=True)
    cuenta_publicitaria: str
    perfil_unidad: str
    red: str
    campana: str
    fecha_publicacion: datetime.date
    objetivo: str
    moneda: str
    importe_gastado: float = 0.0
    alcance: int = 0
    impresiones: int = 0
    clics: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    resultados: int = 0
    id_campana_origen: str
    # Página/cuenta de Instagram del post original, solo cuando la campaña
    # es un "boost" de una publicación ya existente (creada con el botón
    # "Promocionar", no armada a mano en Ads Manager). Meta le pone a esas
    # campañas un nombre automático que nunca menciona una unidad, así que
    # el emparejamiento por nombre de campaña no alcanza — esto permite
    # ubicarlas por la página de origen en vez de adivinar por texto. Vacío
    # cuando la campaña no es un boost de un solo post (o no se pudo
    # resolver).
    pagina_origen_id: str = ""
    # Clics en "Enviar mensaje" (WhatsApp/Messenger/Instagram Direct). Vive
    # aparte de `resultados` porque ese campo depende del objetivo de la
    # campaña (ver resultados.py) y se necesita visible siempre, no solo
    # cuando el objetivo de la campaña es justo "MESSAGES".
    conversaciones_iniciadas: int = 0
    # Fechas reales de programación de la campaña en Ads Manager — no el día
    # de este insight puntual (eso ya es `fecha_publicacion`). Meta no las
    # expone en el endpoint de insights, solo en el de campañas, y una
    # campaña sin fecha de fin configurada (corre hasta que se la pause a
    # mano) llega sin `stop_time`.
    fecha_inicio_campana: datetime.date | None = None
    fecha_fin_campana: datetime.date | None = None

    @property
    def uid(self) -> str:
        # Los insights se piden con breakdown por red (publisher_platform):
        # una misma campaña con ubicación automática (Facebook + Instagram)
        # llega como dos filas separadas el mismo día, cada una con su
        # propio gasto. Si `red` no formara parte del uid, ambas filas
        # colisionarían en el mismo identificador y la segunda pisaría a la
        # primera en vez de guardarse aparte — se perdía la plata de una de
        # las dos redes en silencio.
        return build_uid(
            fuente=self.fuente,
            fecha=self.fecha_publicacion,
            perfil=self.perfil_unidad,
            id_campana=f"{self.id_campana_origen}:{self.red}",
        )


class MailchimpCampana(BaseModel):
    fuente: str = Field(default="mailchimp", frozen=True)
    id_campana_origen: str
    nombre_campana: str = ""
    fecha_envio: datetime.date
    destinatarios: int = 0
    entregas: int = 0
    tasa_apertura: float = 0.0
    aperturas_unicas: int = 0
    aperturas_totales: int = 0
    tasa_clics: float = 0.0
    clics_unicos: int = 0
    clics_totales: int = 0
    tasa_rebote: float = 0.0
    rebotes: int = 0
    bajas: int = 0

    @property
    def uid(self) -> str:
        return build_uid(
            fuente=self.fuente,
            fecha=self.fecha_envio,
            id_campana=self.id_campana_origen,
        )


class MailchimpEnlaceWhatsapp(BaseModel):
    id_campana_origen: str
    url: str
    clics: int = 0


class LinkedInOrganicoPost(BaseModel):
    """Posts orgánicos de la página de LinkedIn de la organización — ver
    connectors/linkedin/."""

    fuente: str = Field(default="linkedin_organico", frozen=True)
    pagina: str
    fecha_publicacion: datetime.date
    tipo: str
    descripcion: str = ""
    impresiones: int = 0
    alcance: int = 0
    clics: int = 0
    reacciones: int = 0
    comentarios: int = 0
    compartidos: int = 0
    interacciones: int = 0
    id_publicacion_origen: str

    @property
    def uid(self) -> str:
        return build_uid(
            fuente=self.fuente,
            fecha=self.fecha_publicacion,
            perfil=self.pagina,
            id_publicacion=self.id_publicacion_origen,
        )


class CalendarioPublicacion(BaseModel):
    """Planificación de publicaciones (SharePoint), no un feed histórico de
    métricas: `fecha_publicacion` es planeada y puede reprogramarse, por eso
    el `uid` se arma solo con el ID propio de la fila (estable), nunca con la
    fecha — si el uid incluyera la fecha, reprogramar un post crearía una fila
    duplicada en vez de actualizar la existente."""

    fuente: str = Field(default="calendario", frozen=True)
    id_origen: str
    fecha_publicacion: datetime.date | None = None
    perfil: str = ""
    bu: str = ""
    campana_evento: str = ""
    tipo: str = ""
    canal: str = ""
    formato: str = ""
    objetivo: str = ""
    descripcion_copy: str = ""
    estado: str = ""
    responsable: str = ""
    inversion_usd: float = 0.0
    link_publicacion: str = ""
    vobo_gcri: str = ""
    notas: str = ""

    @property
    def uid(self) -> str:
        return f"{self.fuente}|{self.id_origen}"


class ControlPerfilMensual(BaseModel):
    """Snapshot mensual de un perfil: seguidores actuales + agregados de sus
    publicaciones del mes. `seguidores_ganados` es el delta contra el mes
    calendario anterior ya cerrado (resuelto en el conector, que sí tiene
    acceso a la base histórica) — el `uid` es por perfil+mes, así que
    reprocesar el mismo mes actualiza la fila en vez de duplicarla."""

    fuente: str = Field(default="control_perfiles", frozen=True)
    perfil: str
    red: str
    anio_mes: str
    seguidores: int = 0
    seguidores_ganados: int = 0
    publicaciones_mes: int = 0
    likes_mes: int = 0
    visualizaciones_mes: int = 0
    comentarios_mes: int = 0
    compartidos_mes: int = 0
    interacciones_mes: int = 0
    tasa_engagement: float = 0.0

    @property
    def uid(self) -> str:
        return f"{self.fuente}|{self.perfil}|{self.anio_mes}"


class EjecucionLog(BaseModel):
    hora_inicio: datetime.datetime
    hora_fin: datetime.datetime | None = None
    estado: str = "en_progreso"
    registros_descargados: int = 0
    registros_nuevos: int = 0
    registros_actualizados: int = 0
    registros_descartados: int = 0
    errores: str = ""
