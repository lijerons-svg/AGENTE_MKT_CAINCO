import io

import responses
from PIL import Image

from marketing_analytics.reports_pptx.imagenes import obtener_imagen_post


def _png_valido() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), (255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_sin_imagen_url_genera_placeholder(tmp_path):
    ruta, es_placeholder = obtener_imagen_post("", "FB", tmp_path, "post_0.png")
    assert ruta.exists()
    assert ruta.parent == tmp_path
    assert es_placeholder is True


@responses.activate
def test_descarga_exitosa_guarda_la_imagen_real(tmp_path):
    contenido_png = _png_valido()
    responses.add(responses.GET, "https://example.com/foto.png", body=contenido_png, status=200)

    ruta, es_placeholder = obtener_imagen_post("https://example.com/foto.png", "FB", tmp_path, "post_0.png")
    assert ruta.read_bytes() == contenido_png
    assert es_placeholder is False


@responses.activate
def test_descarga_fallida_cae_a_placeholder_sin_romper(tmp_path):
    responses.add(responses.GET, "https://example.com/foto.png", status=500)
    ruta, es_placeholder = obtener_imagen_post("https://example.com/foto.png", "IG", tmp_path, "post_0.png")
    assert ruta.exists()
    assert es_placeholder is True


@responses.activate
def test_respuesta_no_es_imagen_valida_cae_a_placeholder(tmp_path):
    responses.add(responses.GET, "https://example.com/foto.png", body=b"<html>no es una imagen</html>", status=200)
    ruta, es_placeholder = obtener_imagen_post("https://example.com/foto.png", "IG", tmp_path, "post_0.png")
    assert ruta.exists()
    assert es_placeholder is True
