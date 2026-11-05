"""Descarga la imagen real de un post para el PPT. Si no hay imagen_url
(post de solo texto) o la descarga falla (URL firmada vencida, timeout),
se genera un placeholder neutro en vez de romper la corrida — un reporte
con un ícono genérico en un post puntual es preferible a que falle todo
el archivo por una sola publicación."""
from __future__ import annotations

import logging
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

_TAMANO = (500, 500)
_FUENTE_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FUENTE_NEGRITA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_COLOR_PLACEHOLDER = (0x8A, 0x8A, 0x8A)


def _fuente(tam: int, negrita: bool = False) -> ImageFont.ImageFont:
    ruta = _FUENTE_NEGRITA if negrita else _FUENTE_REGULAR
    try:
        return ImageFont.truetype(ruta, tam)
    except OSError:
        return ImageFont.load_default()


def _placeholder(carpeta_destino: Path, nombre_archivo: str, etiqueta_red: str) -> Path:
    img = Image.new("RGB", _TAMANO, _COLOR_PLACEHOLDER)
    draw = ImageDraw.Draw(img)
    draw.text((_TAMANO[0] / 2, _TAMANO[1] / 2 - 30), etiqueta_red, font=_fuente(80, negrita=True), anchor="mm", fill="white")
    draw.text((_TAMANO[0] / 2, _TAMANO[1] / 2 + 50), "Sin imagen disponible", font=_fuente(22), anchor="mm", fill="white")
    ruta = carpeta_destino / nombre_archivo
    img.save(ruta)
    return ruta


def obtener_imagen_post(
    imagen_url: str, etiqueta_red: str, carpeta_destino: Path, nombre_archivo: str
) -> tuple[Path, bool]:
    """Devuelve (ruta_imagen, es_placeholder) — `es_placeholder` en True le
    dice al llamador que no hay imagen real, para que pueda mostrar el link
    de la publicación como respaldo en su lugar."""
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    if not imagen_url:
        return _placeholder(carpeta_destino, nombre_archivo, etiqueta_red), True
    try:
        respuesta = requests.get(imagen_url, timeout=15)
        respuesta.raise_for_status()
        ruta = carpeta_destino / nombre_archivo
        ruta.write_bytes(respuesta.content)
        # Verificar que sea una imagen válida antes de dársela a python-pptx
        # (una URL vencida a veces responde 200 con una página de error en
        # HTML, no una imagen — mejor descartarla acá que romper el .pptx).
        Image.open(ruta).verify()
        return ruta, False
    except Exception:
        logger.warning("No se pudo descargar la imagen del post (%s); uso placeholder", imagen_url)
        return _placeholder(carpeta_destino, nombre_archivo, etiqueta_red), True
