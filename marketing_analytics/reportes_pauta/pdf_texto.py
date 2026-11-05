"""Extracción de texto de un PDF de recibo, sin depender de binarios del
sistema (poppler) — usa pypdf (puro Python) para que funcione igual en
Windows con un simple `pip install`."""
from __future__ import annotations

import io

from pypdf import PdfReader


def extraer_texto(contenido_pdf: bytes) -> str:
    """Devuelve el texto de todas las páginas del PDF, unidas con un salto
    de página (\\x0c) entre cada una — como hace pdftotext."""
    lector = PdfReader(io.BytesIO(contenido_pdf))
    paginas = [pagina.extract_text() or "" for pagina in lector.pages]
    return "\n\x0c".join(paginas)
