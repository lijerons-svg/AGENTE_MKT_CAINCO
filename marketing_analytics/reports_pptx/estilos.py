"""Paleta y helpers de construcción de slides — estilo aprobado con la
usuaria sobre un mockup con datos ficticios antes de conectar datos
reales. Cambiar acá el diseño lo cambia para las 6 unidades a la vez."""
from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

AZUL = RGBColor(0x00, 0x3A, 0x70)
AZUL_CLARO = RGBColor(0x0A, 0x5A, 0xA0)
CIAN = RGBColor(0x00, 0xA4, 0xC4)
NARANJA = RGBColor(0xFF, 0x8C, 0x1A)
VERDE = RGBColor(0x2F, 0xA8, 0x4F)
ROJO_BAJA = RGBColor(0xC0, 0x39, 0x2B)
GRIS_MEJORA = RGBColor(0x8A, 0x8A, 0x8A)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
GRIS_FONDO = RGBColor(0xF4, 0xF6, 0xF8)
GRIS_TEXTO = RGBColor(0x4A, 0x55, 0x63)
GRIS_BORDE = RGBColor(0xE1, 0xE5, 0xEA)
COLOR_FB = RGBColor(0x16, 0x65, 0xC1)
COLOR_IG = RGBColor(0xC1, 0x39, 0x84)
NEGRO_TEXTO = RGBColor(0x1A, 0x1A, 0x1A)

FUENTE = "Calibri"

COLOR_POR_RED = {"facebook": COLOR_FB, "instagram": COLOR_IG}
ETIQUETA_POR_RED = {"facebook": "FB", "instagram": "IG"}


class ConstructorReporte:
    """Envuelve una `Presentation` en blanco con los helpers de slide del
    diseño aprobado. Un `ConstructorReporte` por archivo .pptx generado."""

    def __init__(self) -> None:
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self._layout_blanco = self.prs.slide_layouts[6]

    def guardar(self, ruta) -> None:
        self.prs.save(ruta)

    def nueva_slide(self):
        return self.prs.slides.add_slide(self._layout_blanco)

    def fondo(self, slide, color):
        forma = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        forma.fill.solid()
        forma.fill.fore_color.rgb = color
        forma.line.fill.background()
        forma.shadow.inherit = False
        return forma

    def caja_texto(self, slide, x, y, w, h, texto, tam, color, negrita=False, alineacion=PP_ALIGN.LEFT):
        cuadro = slide.shapes.add_textbox(x, y, w, h)
        tf = cuadro.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = alineacion
        run = p.add_run()
        run.text = texto
        run.font.size = Pt(tam)
        run.font.bold = negrita
        run.font.color.rgb = color
        run.font.name = FUENTE
        return cuadro

    def rectangulo(self, slide, x, y, w, h, color_relleno=None, color_borde=None, radio=False):
        tipo = MSO_SHAPE.ROUNDED_RECTANGLE if radio else MSO_SHAPE.RECTANGLE
        forma = slide.shapes.add_shape(tipo, x, y, w, h)
        if radio:
            forma.adjustments[0] = 0.06
        if color_relleno is not None:
            forma.fill.solid()
            forma.fill.fore_color.rgb = color_relleno
        else:
            forma.fill.background()
        if color_borde is not None:
            forma.line.color.rgb = color_borde
            forma.line.width = Pt(1)
        else:
            forma.line.fill.background()
        forma.shadow.inherit = False
        return forma

    def pastilla(self, slide, x, y, texto, color_fondo, color_texto=BLANCO, ancho=Inches(2.2), tam=12):
        forma = self.rectangulo(slide, x, y, ancho, Inches(0.38), color_relleno=color_fondo, radio=True)
        forma.adjustments[0] = 0.5
        tf = forma.text_frame
        tf.margin_left = tf.margin_right = Pt(4)
        tf.margin_top = tf.margin_bottom = Pt(2)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = texto
        run.font.size = Pt(tam)
        run.font.bold = True
        run.font.color.rgb = color_texto
        run.font.name = FUENTE
        return forma

    def link_texto(self, slide, x, y, w, h, texto, url, tam=9):
        """Textbox con un link real (clickeable en PowerPoint), para posts
        sin imagen descargable — se puede ir a verla a mano mientras tanto."""
        cuadro = slide.shapes.add_textbox(x, y, w, h)
        tf = cuadro.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = texto
        run.font.size = Pt(tam)
        run.font.bold = True
        run.font.color.rgb = CIAN
        run.font.name = FUENTE
        run.hyperlink.address = url
        return cuadro

    def encabezado_slide(self, slide, titulo, periodo):
        self.fondo(slide, AZUL)
        self.rectangulo(slide, 0, Inches(0.9), self.prs.slide_width, Inches(6.6), color_relleno=GRIS_FONDO)
        self.caja_texto(slide, Inches(0.4), Inches(0.18), Inches(7.5), Inches(0.55), titulo, 19, BLANCO, negrita=True)
        self.pastilla(slide, Inches(9.1), Inches(0.2), periodo, CIAN, ancho=Inches(2.6))
        self.caja_texto(slide, Inches(11.7), Inches(0.22), Inches(1.4), Inches(0.5), "CAINCO", 18, BLANCO, negrita=True, alineacion=PP_ALIGN.RIGHT)

    def tabla(self, slide, x, y, w, h, encabezados, filas, tam_fuente=10.5, anchos_columnas=None):
        n_filas = len(filas) + 1
        n_cols = len(encabezados)
        forma = slide.shapes.add_table(n_filas, n_cols, x, y, w, h)
        t = forma.table
        if anchos_columnas is not None:
            for j, ancho in enumerate(anchos_columnas):
                t.columns[j].width = ancho
        for j, texto in enumerate(encabezados):
            celda = t.cell(0, j)
            celda.fill.solid()
            celda.fill.fore_color.rgb = AZUL
            celda.margin_top = celda.margin_bottom = Pt(4)
            p = celda.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = texto
            run.font.size = Pt(tam_fuente)
            run.font.bold = True
            run.font.color.rgb = BLANCO
            run.font.name = FUENTE
        for i, fila in enumerate(filas, start=1):
            color_fila = BLANCO if i % 2 else GRIS_FONDO
            for j, valor in enumerate(fila):
                celda = t.cell(i, j)
                celda.fill.solid()
                celda.fill.fore_color.rgb = color_fila
                celda.margin_top = celda.margin_bottom = Pt(3)
                p = celda.text_frame.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
                run = p.add_run()
                run.text = str(valor)
                run.font.size = Pt(tam_fuente)
                run.font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)
                run.font.name = FUENTE
        return forma

    def slide_grid_posts(self, titulo, periodo, posts, nota_pie=None):
        """`posts`: lista de dicts con imagen_ruta, red, tipo, titulo, kpis
        (lista de tuplas (etiqueta, valor)), y opcionalmente `link_respaldo`
        (se muestra cuando la imagen es un placeholder, para ir a verla a
        mano mientras tanto)."""
        s = self.nueva_slide()
        self.encabezado_slide(s, titulo, periodo)
        ancho_post = Inches(2.95)
        espacio = Inches(0.2)
        x0 = Inches(0.35)
        for i, post in enumerate(posts):
            x = x0 + i * (ancho_post + espacio)
            self.rectangulo(s, x, Inches(1.2), ancho_post, Inches(5.9), color_relleno=BLANCO, color_borde=GRIS_BORDE, radio=True)
            s.shapes.add_picture(str(post["imagen_ruta"]), x + Inches(0.2), Inches(1.4), width=Inches(2.55), height=Inches(2.55))
            color_red = post.get("color_red", COLOR_POR_RED.get(post["red"], GRIS_MEJORA))
            self.pastilla(s, x + Inches(0.2), Inches(4.05), post["red_label"], color_red, ancho=Inches(1.1), tam=10)
            self.caja_texto(s, x + Inches(1.45), Inches(4.06), Inches(1.4), Inches(0.35), post["tipo"], 10, GRIS_TEXTO)
            self.caja_texto(s, x + Inches(0.2), Inches(4.48), ancho_post - Inches(0.4), Inches(0.45), post["titulo"], 11.5, NEGRO_TEXTO, negrita=True)
            if post.get("link_respaldo"):
                self.link_texto(s, x + Inches(0.2), Inches(4.95), ancho_post - Inches(0.4), Inches(0.3), "Ver publicación ↗", post["link_respaldo"])
            y_kpi = Inches(5.25)
            ancho_kpi = (ancho_post - Inches(0.4)) / 2
            for k, (etiqueta, valor) in enumerate(post["kpis"]):
                xi = x + Inches(0.2) + (k % 2) * ancho_kpi
                yi = y_kpi + (k // 2) * Inches(0.85)
                self.rectangulo(s, xi, yi, ancho_kpi - Inches(0.05), Inches(0.75), color_relleno=GRIS_FONDO, radio=True)
                self.caja_texto(s, xi + Inches(0.1), yi + Inches(0.06), ancho_kpi - Inches(0.2), Inches(0.3), etiqueta, 8.5, GRIS_TEXTO)
                self.caja_texto(s, xi + Inches(0.1), yi + Inches(0.34), ancho_kpi - Inches(0.2), Inches(0.35), valor, 14, AZUL, negrita=True)
        if nota_pie:
            self.caja_texto(s, Inches(0.4), Inches(7.05), Inches(11), Inches(0.35), nota_pie, 9.5, GRIS_TEXTO)
        return s
