from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# Colors
AZUL = RGBColor(0x1A, 0x2E, 0x4A)
NARANJA = RGBColor(0xE8, 0x61, 0x0A)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
GRIS = RGBColor(0xF2, 0xF2, 0xF2)
GRIS_TEXTO = RGBColor(0x55, 0x55, 0x55)
VERDE = RGBColor(0x1A, 0x7A, 0x4A)
AZUL_CLARO = RGBColor(0xD6, 0xE4, 0xF0)

W = Inches(13.33)
H = Inches(7.5)

prs = Presentation()
prs.slide_width = W
prs.slide_height = H

blank = prs.slide_layouts[6]  # blank layout

def add_rect(slide, x, y, w, h, fill=None, line=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.line.fill.background()
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def add_textbox(slide, text, x, y, w, h, bold=False, size=12, color=AZUL,
                align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txb = slide.shapes.add_textbox(x, y, w, h)
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.bold = bold
    run.font.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    return txb

def add_label_bar(slide, text, y=Inches(0.18)):
    bar = add_rect(slide, Inches(0), y, W, Inches(0.06), fill=NARANJA)
    add_textbox(slide, text, Inches(0.4), Inches(0.08), Inches(12), Inches(0.35),
                bold=True, size=9, color=NARANJA)

def slide_header(slide, title, subtitle=None, dark=False):
    bg_color = AZUL if dark else None
    txt_color = BLANCO if dark else AZUL
    sub_color = RGBColor(0xCC, 0xCC, 0xCC) if dark else GRIS_TEXTO

    if dark:
        add_rect(slide, 0, 0, W, H, fill=AZUL)

    # Top accent line
    add_rect(slide, 0, 0, W, Inches(0.07), fill=NARANJA)

    add_textbox(slide, title, Inches(0.5), Inches(0.15), Inches(12.3), Inches(0.8),
                bold=True, size=22, color=txt_color, align=PP_ALIGN.LEFT)
    if subtitle:
        add_textbox(slide, subtitle, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.35),
                    bold=False, size=12, color=NARANJA if not dark else NARANJA,
                    align=PP_ALIGN.LEFT)

def add_bullet_block(slide, label, bullets, x, y, w, h, label_color=AZUL, bullet_color=AZUL):
    # label
    add_textbox(slide, label.upper(), x, y, w, Inches(0.3),
                bold=True, size=9, color=NARANJA)
    by = y + Inches(0.32)
    for b in bullets:
        # bullet dot
        dot = slide.shapes.add_shape(9, x, by + Inches(0.06), Inches(0.12), Inches(0.12))
        dot.fill.solid(); dot.fill.fore_color.rgb = NARANJA
        dot.line.fill.background()
        add_textbox(slide, b, x + Inches(0.2), by, w - Inches(0.25), Inches(0.38),
                    bold=False, size=10.5, color=bullet_color)
        by += Inches(0.42)

def add_card(slide, number, title, items, x, y, w, h, color=AZUL):
    add_rect(slide, x, y, w, h, fill=color, line=None)
    add_textbox(slide, number, x + Inches(0.2), y + Inches(0.1), Inches(0.5), Inches(0.5),
                bold=True, size=26, color=NARANJA)
    add_textbox(slide, title, x + Inches(0.2), y + Inches(0.55), w - Inches(0.4), Inches(0.45),
                bold=True, size=12, color=BLANCO)
    iy = y + Inches(1.05)
    for item in items:
        add_textbox(slide, f"• {item}", x + Inches(0.2), iy, w - Inches(0.4), Inches(0.38),
                    size=9.5, color=RGBColor(0xCC, 0xDD, 0xEE))
        iy += Inches(0.38)

def add_speaker_note(slide, note):
    slide.notes_slide.notes_text_frame.text = note

# ─────────────────────────────────────────
# SLIDE 1 — PORTADA
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
add_rect(sl, 0, 0, W, H, fill=AZUL)
add_rect(sl, 0, 0, W, Inches(0.07), fill=NARANJA)
add_rect(sl, 0, H - Inches(0.07), W, Inches(0.07), fill=NARANJA)

add_textbox(sl, "ACIERTA CAINCO", Inches(1), Inches(1.2), Inches(11.3), Inches(1.0),
            bold=True, size=40, color=BLANCO, align=PP_ALIGN.CENTER)
add_textbox(sl, "Plan de Marketing Estratégico · 6 meses",
            Inches(1), Inches(2.2), Inches(11.3), Inches(0.6),
            bold=False, size=20, color=NARANJA, align=PP_ALIGN.CENTER)
add_textbox(sl, "Diagnóstico · Estrategia · Ejecución",
            Inches(1), Inches(2.85), Inches(11.3), Inches(0.5),
            bold=False, size=14, color=RGBColor(0xAA, 0xBB, 0xCC), align=PP_ALIGN.CENTER)

# 3 ejes
eje_data = [("🔍", "EJE 1", "Diagnóstico"), ("🧭", "EJE 2", "Estrategia"), ("🚀", "EJE 3", "Ejecución")]
for i, (icon, eje, label) in enumerate(eje_data):
    cx = Inches(2.0 + i * 3.3)
    add_rect(sl, cx, Inches(3.8), Inches(2.8), Inches(1.4),
             fill=RGBColor(0x0D, 0x1E, 0x33))
    add_textbox(sl, icon + " " + eje, cx + Inches(0.15), Inches(3.9), Inches(2.5), Inches(0.4),
                bold=True, size=13, color=NARANJA)
    add_textbox(sl, label, cx + Inches(0.15), Inches(4.3), Inches(2.5), Inches(0.4),
                size=12, color=BLANCO)

add_textbox(sl, "Sandy Daher · Mayo 2026 · Confidencial",
            Inches(1), Inches(6.6), Inches(11.3), Inches(0.4),
            size=10, color=RGBColor(0x77, 0x88, 0x99), align=PP_ALIGN.CENTER)
add_speaker_note(sl, "Buenas tardes. Voy a presentar el Plan de Marketing Estratégico para Acierta — un plan en tres ejes para seis meses.")

# ─────────────────────────────────────────
# SLIDE 2 — 6 DESAFÍOS
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "ACIERTA ENFRENTA 6 DESAFÍOS QUE ESTE PLAN DEBE RESOLVER",
             "EJE 1 · Diagnóstico · El punto de partida real")

desafios = [
    ("D1", "Dependencia del core", "+70% ingresos de Reclutamiento — riesgo de concentración"),
    ("D2", "Servicios invisibles", "Empresas Familiares, Asesoría Económica sin comunicación activa"),
    ("D3", "Sin leads medidos", "Línea base en 0 — ningún servicio no-core tiene pipeline documentado"),
    ("D4", "Presencia digital débil", "LinkedIn sin estrategia; sin posicionamiento como referente técnico"),
    ("D5", "Audiencia sin segmentar", "4.000 asociados reciben el mismo mensaje genérico"),
    ("D6", "Contexto macro adverso", "Inflación y escasez de divisas frenan inversión en consultoría"),
]
cols = [Inches(0.4), Inches(4.55), Inches(8.7)]
for i, (code, title, desc) in enumerate(desafios):
    col = i % 3
    row = i // 3
    cx = cols[col]
    cy = Inches(1.35) + row * Inches(2.45)
    add_rect(sl, cx, cy, Inches(3.9), Inches(2.2), fill=GRIS)
    add_rect(sl, cx, cy, Inches(0.07), Inches(2.2), fill=NARANJA)
    add_textbox(sl, code, cx + Inches(0.2), cy + Inches(0.12), Inches(0.6), Inches(0.35),
                bold=True, size=11, color=NARANJA)
    add_textbox(sl, title, cx + Inches(0.2), cy + Inches(0.45), Inches(3.5), Inches(0.4),
                bold=True, size=11, color=AZUL)
    add_textbox(sl, desc, cx + Inches(0.2), cy + Inches(0.85), Inches(3.5), Inches(1.1),
                size=9.5, color=GRIS_TEXTO)

add_speaker_note(sl, "El diagnóstico nos dice que Acierta tiene un problema de comunicación, no de producto. El portafolio es sólido. El problema es que nadie lo sabe.")

# ─────────────────────────────────────────
# SLIDE 3 — CONTEXTO MACRO
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "EL CONTEXTO BOLIVIANO ES EL MEJOR ARGUMENTO DE VENTA DE ACIERTA",
             "EJE 1 · Contexto macro como oportunidad estratégica")

rows = [
    ("Inflación + escasez de divisas", "Decisiones de RRHH más selectivas", "Reclutamiento de precisión"),
    ("Incertidumbre económica", "Datos sectoriales para directorio", "Asesoría Económica"),
    ("Presión sobre costos", "Revisión de estructuras y procesos", "Estructura Organizacional"),
    ("Empresas familiares bajo stress", "Sucesión y protocolos urgentes", "Empresas Familiares"),
]
headers = ["CONTEXTO ADVERSO", "NECESIDAD QUE ACTIVA", "SERVICIO ACIERTA"]
col_x = [Inches(0.4), Inches(4.6), Inches(8.9)]
col_w = [Inches(4.0), Inches(4.1), Inches(4.0)]

# header row
for j, hdr in enumerate(headers):
    add_rect(sl, col_x[j], Inches(1.3), col_w[j], Inches(0.38), fill=AZUL)
    add_textbox(sl, hdr, col_x[j] + Inches(0.1), Inches(1.32), col_w[j] - Inches(0.1), Inches(0.35),
                bold=True, size=9, color=BLANCO)

for i, (ctx, need, svc) in enumerate(rows):
    bg = GRIS if i % 2 == 0 else BLANCO
    ry = Inches(1.68) + i * Inches(0.58)
    for j, txt in enumerate([ctx, need, svc]):
        add_rect(sl, col_x[j], ry, col_w[j], Inches(0.56), fill=bg, line=RGBColor(0xDD, 0xDD, 0xDD))
        color = VERDE if j == 2 else AZUL
        add_textbox(sl, txt, col_x[j] + Inches(0.1), ry + Inches(0.08), col_w[j] - Inches(0.15), Inches(0.44),
                    size=10, color=color, bold=(j == 2))

# tagline box
add_rect(sl, Inches(0.4), Inches(5.05), Inches(12.5), Inches(0.65), fill=NARANJA)
add_textbox(sl, '"Cuando el contexto aprieta, Acierta convierte incertidumbre en decisión."',
            Inches(0.6), Inches(5.12), Inches(12.1), Inches(0.5),
            bold=True, size=13, color=BLANCO, align=PP_ALIGN.CENTER, italic=True)
add_speaker_note(sl, "El brief dice que la crisis reduce inversión en consultoría. Yo lo leo al revés: en incertidumbre, quien no tiene datos pierde más. Ese es el argumento de Acierta.")

# ─────────────────────────────────────────
# SLIDE 4 — PRIMERAS 2 SEMANAS
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "LAS PRIMERAS 2 SEMANAS DEFINEN LA CALIDAD DE TODO LO QUE SIGUE",
             "EJE 1 · Metodología de diagnóstico · Semanas 1–2")

semanas = [
    ("SEM 1", "Entrevistas internas", [
        "Equipo Acierta: ¿Qué servicios cierran más? ¿Cuál es el perfil del cliente que paga mejor?",
        "Revisión de base de datos histórica de clientes (últimos 24 meses)",
        "Identificar 3–5 casos de éxito documentables por servicio",
    ]),
    ("SEM 1–2", "Entrevistas externas + auditoría digital", [
        "Entrevistas a 8–10 clientes: motivación de compra, canales, percepción vs. competencia",
        "Auditoría LinkedIn: frecuencia de publicación, engagement, tipo de contenido actual",
        "Benchmark 3 competidores: presencia digital + servicios + mensajes clave",
    ]),
    ("OUTPUT", "Entregable de diagnóstico", [
        "Matriz de fortalezas/debilidades validada con datos reales (no supuestos)",
        "Perfil de cliente real por línea de servicio",
        "Mapa de brechas entre lo que Acierta comunica y lo que el mercado busca",
    ]),
]
for i, (tag, title, bullets) in enumerate(semanas):
    cx = Inches(0.4 + i * 4.3)
    cy = Inches(1.3)
    add_rect(sl, cx, cy, Inches(4.0), Inches(5.4), fill=GRIS)
    add_rect(sl, cx, cy, Inches(4.0), Inches(0.42), fill=AZUL if i < 2 else VERDE)
    add_textbox(sl, tag, cx + Inches(0.15), cy + Inches(0.06), Inches(3.7), Inches(0.32),
                bold=True, size=12, color=BLANCO)
    add_textbox(sl, title, cx + Inches(0.15), cy + Inches(0.55), Inches(3.7), Inches(0.45),
                bold=True, size=11, color=AZUL)
    by = cy + Inches(1.1)
    for b in bullets:
        dot = sl.shapes.add_shape(9, cx + Inches(0.15), by + Inches(0.1), Inches(0.1), Inches(0.1))
        dot.fill.solid(); dot.fill.fore_color.rgb = NARANJA; dot.line.fill.background()
        add_textbox(sl, b, cx + Inches(0.35), by, Inches(3.4), Inches(0.5), size=9.5, color=GRIS_TEXTO)
        by += Inches(0.62)
add_speaker_note(sl, "No arrancamos con acciones. Arrancamos con escucha. Las primeras dos semanas son las más importantes del plan.")

# ─────────────────────────────────────────
# SLIDE 5 — AUDITORÍA DIGITAL + COMPETIDORES
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "LA AUDITORÍA DIGITAL REVELA DÓNDE SE PIERDE LA OPORTUNIDAD",
             "EJE 1 · Diagnóstico digital y competitivo · Semana 2")

# Left: fortalezas/debilidades
add_rect(sl, Inches(0.4), Inches(1.3), Inches(6.0), Inches(5.4), fill=GRIS)
add_rect(sl, Inches(0.4), Inches(1.3), Inches(6.0), Inches(0.38), fill=AZUL)
add_textbox(sl, "ANÁLISIS INTERNO", Inches(0.55), Inches(1.33), Inches(5.7), Inches(0.32),
            bold=True, size=10, color=BLANCO)

fdb = [
    ("✓ FORTALEZA", "Respaldo institucional CAINCO — credibilidad inmediata sin costo", VERDE),
    ("✓ FORTALEZA", "Portafolio diverso con capacidad técnica instalada (psicotécnicos, economistas)", VERDE),
    ("✗ DEBILIDAD", "LinkedIn sin estrategia — publicaciones esporádicas, sin narrativa de marca", RGBColor(0xCC, 0x33, 0x33)),
    ("✗ DEBILIDAD", "Sin CRM ni tracking de leads — imposible medir qué canal convierte", RGBColor(0xCC, 0x33, 0x33)),
]
fy = Inches(1.8)
for label, text, color in fdb:
    add_textbox(sl, label, Inches(0.55), fy, Inches(1.4), Inches(0.3), bold=True, size=8.5, color=color)
    add_textbox(sl, text, Inches(0.55), fy + Inches(0.28), Inches(5.6), Inches(0.42), size=9.5, color=GRIS_TEXTO)
    fy += Inches(0.78)

# Ventaja diferencial
add_rect(sl, Inches(0.4), Inches(5.15), Inches(6.0), Inches(1.25), fill=RGBColor(0x0D, 0x1E, 0x33))
add_textbox(sl, "VENTAJA DIFERENCIAL", Inches(0.55), Inches(5.2), Inches(5.7), Inches(0.3),
            bold=True, size=9, color=NARANJA)
add_textbox(sl, "Acierta es la única consultora con acceso directo a 4.000 empresas vía CAINCO.",
            Inches(0.55), Inches(5.52), Inches(5.6), Inches(0.6), size=10, color=BLANCO)

# Right: competidores
add_rect(sl, Inches(6.8), Inches(1.3), Inches(6.1), Inches(5.4), fill=GRIS)
add_rect(sl, Inches(6.8), Inches(1.3), Inches(6.1), Inches(0.38), fill=AZUL)
add_textbox(sl, "ANÁLISIS COMPETITIVO", Inches(6.95), Inches(1.33), Inches(5.8), Inches(0.32),
            bold=True, size=10, color=BLANCO)

comps = [
    ("Manpower Bolivia", "Global, desde 1991. Fuerte en corporativos.", "↳ Brecha: percibido como extranjero y costoso"),
    ("PRH Bolivia", "17 años. 29K seguidores LinkedIn. Headhunting.", "↳ Brecha: sin consultoría estratégica ni respaldo gremial"),
    ("Talento GTH", "Plataforma propia. 261 empresas. Procesos ágiles.", "↳ Brecha: no tiene el paraguas CAINCO"),
]
cy2 = Inches(1.8)
for name, desc, gap in comps:
    add_rect(sl, Inches(6.95), cy2, Inches(5.7), Inches(1.45), fill=BLANCO, line=RGBColor(0xDD,0xDD,0xDD))
    add_textbox(sl, name, Inches(7.1), cy2 + Inches(0.1), Inches(5.4), Inches(0.32), bold=True, size=11, color=AZUL)
    add_textbox(sl, desc, Inches(7.1), cy2 + Inches(0.4), Inches(5.4), Inches(0.32), size=9.5, color=GRIS_TEXTO)
    add_textbox(sl, gap, Inches(7.1), cy2 + Inches(0.72), Inches(5.4), Inches(0.32), size=9.5, color=NARANJA, italic=True)
    cy2 += Inches(1.55)
add_speaker_note(sl, "La auditoría confirma: el problema no es el producto — es que Acierta no está donde sus clientes deciden.")

# ─────────────────────────────────────────
# SLIDE 6 — BUYER PERSONAS
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "ACIERTA TIENE 3 CLIENTES DISTINTOS QUE HOY RECIBEN EL MISMO MENSAJE",
             "EJE 2 · Buyer Personas · Segmentación estratégica")

personas = [
    (AZUL, "01", "Gerente de RRHH Corporativo",
     "Empresa +100 empleados\nAgroindustrial / financiero, SCZ",
     "Cubrir posiciones clave rápido\ncon garantía de calidad",
     "Reclutamiento & Selección\nEvaluaciones Psicotécnicas",
     "LinkedIn · referidos · contacto directo",
     '"Acierta te entrega el candidato\ncorrecto, no el disponible."'),
    (VERDE, "02", "Dueño de Empresa Familiar",
     "Fundador 2ª–3ª generación\nFacturación USD 1M–10M",
     "Conflictos sucesorios y decisiones\nemocionales que dañan el negocio",
     "Consultoría Empresas Familiares\nPlanificación Estratégica",
     "Eventos CAINCO · gremio · WhatsApp",
     '"Tu empresa puede crecer sin\nque crezcan los conflictos."'),
    (RGBColor(0x7B, 0x2D, 0x8B), "03", "Gerente General en Incertidumbre",
     "CEO / CFO empresa mediana\nAfectado por contexto macro",
     "Datos confiables para justificar\ndecisiones ante el directorio",
     "Asesoría Económica\nInvestigación Sectorial",
     "Email base CAINCO · LinkedIn",
     '"Acierta convierte la incertidumbre\nboliviana en datos para decidir."'),
]

for i, (color, num, title, perfil, dolor, servicio, canal, mensaje) in enumerate(personas):
    cx = Inches(0.35 + i * 4.33)
    cy = Inches(1.28)
    cw = Inches(4.1)

    # Header card
    add_rect(sl, cx, cy, cw, Inches(5.9), fill=BLANCO, line=RGBColor(0xDD,0xDD,0xDD))
    add_rect(sl, cx, cy, cw, Inches(0.65), fill=color)
    add_textbox(sl, f"{num}  {title}", cx + Inches(0.15), cy + Inches(0.12), cw - Inches(0.2), Inches(0.48),
                bold=True, size=11, color=BLANCO)

    fields = [("PERFIL", perfil), ("DOLOR", dolor), ("SERVICIO", servicio), ("CANAL", canal)]
    fy2 = cy + Inches(0.78)
    for label, val in fields:
        add_textbox(sl, label, cx + Inches(0.15), fy2, cw - Inches(0.2), Inches(0.22),
                    bold=True, size=7.5, color=color)
        add_textbox(sl, val, cx + Inches(0.15), fy2 + Inches(0.2), cw - Inches(0.2), Inches(0.45),
                    size=9, color=GRIS_TEXTO)
        fy2 += Inches(0.72)

    # Mensaje
    add_rect(sl, cx, cy + Inches(5.0), cw, Inches(0.9), fill=color)
    add_textbox(sl, mensaje, cx + Inches(0.12), cy + Inches(5.07), cw - Inches(0.2), Inches(0.78),
                size=9, color=BLANCO, italic=True, bold=True)

add_speaker_note(sl, "Un solo mensaje para tres clientes muy distintos es uno de los problemas actuales. Cada persona necesita su propio lenguaje y su propio canal.")

# ─────────────────────────────────────────
# SLIDE 7 — ARQUITECTURA DE MARCA
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "LA ARQUITECTURA DE MARCA ENDOSADA PROTEGE EL CORE Y ESCALA LOS SERVICIOS",
             "EJE 2 · Estrategia de marca · Modelo CAINCO–Acierta")

# Left diagram
cx_d = Inches(0.5)
# CAINCO outer
add_rect(sl, cx_d, Inches(1.3), Inches(5.8), Inches(5.3), fill=AZUL_CLARO, line=AZUL)
add_textbox(sl, "CAINCO", cx_d + Inches(0.2), Inches(1.42), Inches(5.4), Inches(0.4),
            bold=True, size=13, color=AZUL)
add_textbox(sl, "100 años · 4.000 asociados · Credibilidad institucional",
            cx_d + Inches(0.2), Inches(1.82), Inches(5.4), Inches(0.35), size=9, color=AZUL)

# ACIERTA inner
add_rect(sl, cx_d + Inches(0.4), Inches(2.3), Inches(5.0), Inches(2.8), fill=AZUL, line=None)
add_textbox(sl, "ACIERTA", cx_d + Inches(0.6), Inches(2.42), Inches(4.5), Inches(0.45),
            bold=True, size=16, color=NARANJA)
add_textbox(sl, "una empresa de CAINCO", cx_d + Inches(0.6), Inches(2.88), Inches(4.5), Inches(0.35),
            size=10, color=BLANCO, italic=True)
add_textbox(sl, "Especialización técnica · Cercanía con el cliente",
            cx_d + Inches(0.6), Inches(3.25), Inches(4.5), Inches(0.35), size=9, color=RGBColor(0xAA,0xBB,0xCC))

# Services tags
services = ["Reclutamiento", "Psicotécnicos", "Empresas Familiares", "Asesoría Económica", "Planificación"]
sx = cx_d + Inches(0.4)
sy = Inches(5.25)
for s in services:
    add_rect(sl, sx, sy, Inches(1.8), Inches(0.32), fill=NARANJA)
    add_textbox(sl, s, sx + Inches(0.07), sy + Inches(0.04), Inches(1.65), Inches(0.26),
                size=7.5, color=BLANCO, bold=True)
    sx += Inches(1.92)
    if sx > cx_d + Inches(5.5):
        sx = cx_d + Inches(0.4); sy += Inches(0.38)

# Right: bullets
rx = Inches(6.8)
blocks = [
    ("BENEFICIOS DEL MODELO", [
        "CAINCO transfiere confianza — Acierta no parte de cero",
        "Reduce CAC: el endoso actúa como referido permanente",
        "Escala a nuevas líneas sin perder autoridad institucional",
    ]),
    ("RIESGO A GESTIONAR", [
        "Dependencia de la reputación de CAINCO",
        "Mitigación: construir casos de éxito propios de Acierta",
    ]),
]
by2 = Inches(1.35)
for label, bullets in blocks:
    add_rect(sl, rx, by2, Inches(6.1), Inches(0.35), fill=AZUL)
    add_textbox(sl, label, rx + Inches(0.15), by2 + Inches(0.05), Inches(5.8), Inches(0.27),
                bold=True, size=9, color=BLANCO)
    by2 += Inches(0.4)
    for b in bullets:
        dot = sl.shapes.add_shape(9, rx + Inches(0.15), by2 + Inches(0.1), Inches(0.1), Inches(0.1))
        dot.fill.solid(); dot.fill.fore_color.rgb = NARANJA; dot.line.fill.background()
        add_textbox(sl, b, rx + Inches(0.35), by2, Inches(5.6), Inches(0.4), size=10, color=GRIS_TEXTO)
        by2 += Inches(0.48)
    by2 += Inches(0.2)

add_speaker_note(sl, "El modelo endosado no es una limitación — es la ventaja competitiva más difícil de replicar que tiene Acierta.")

# ─────────────────────────────────────────
# SLIDE 8 — OBJETIVOS SMART
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "DOS OBJETIVOS SMART QUE HACEN EL ÉXITO MEDIBLE DESDE EL DÍA 1",
             "EJE 2 · Objetivos estratégicos · Meses 1–6")

obj_data = [
    ("O1", "Consolidar el core con mayor eficiencia",
     "+20% tasa conversión lead→propuesta\nen Reclutamiento & Selección al mes 6",
     ["CRM + tracking de origen de leads", "Scripts de seguimiento estandarizados", "Hito mes 3: todos los leads con origen identificado"],
     AZUL),
    ("O2", "Construir el pipeline que Acierta nunca tuvo",
     "15 leads calificados/mes en servicios\nno-core al mes 6 (desde línea base 0)",
     ["Hito mes 2: 5 leads/mes no-core", "Hito mes 4: 10 leads/mes no-core", "Base: 4.000 asociados + webinars + Barómetro"],
     VERDE),
]
for i, (num, title, meta, acciones, color) in enumerate(obj_data):
    cx = Inches(0.4 + i * 6.5)
    cy = Inches(1.3)
    add_rect(sl, cx, cy, Inches(6.1), Inches(4.3), fill=color)
    add_textbox(sl, num, cx + Inches(0.2), cy + Inches(0.1), Inches(0.7), Inches(0.55),
                bold=True, size=28, color=NARANJA)
    add_textbox(sl, title, cx + Inches(0.2), cy + Inches(0.65), Inches(5.7), Inches(0.45),
                bold=True, size=12, color=BLANCO)
    add_textbox(sl, meta, cx + Inches(0.2), cy + Inches(1.15), Inches(5.7), Inches(0.8),
                size=11, color=NARANJA, bold=True)
    ay = cy + Inches(2.1)
    for a in acciones:
        add_textbox(sl, f"• {a}", cx + Inches(0.2), ay, Inches(5.7), Inches(0.38),
                    size=9.5, color=RGBColor(0xCC, 0xDD, 0xEE))
        ay += Inches(0.42)

# KPIs bar
add_rect(sl, Inches(0.4), Inches(5.75), Inches(12.5), Inches(0.9), fill=GRIS)
add_textbox(sl, "KPIs:  Leads/mes por servicio no-core  ·  Conversión lead→propuesta (meta 20%)  ·  Asistentes a webinars  ·  Descargas Barómetro",
            Inches(0.6), Inches(5.85), Inches(12.1), Inches(0.6),
            size=9.5, color=AZUL, align=PP_ALIGN.CENTER)
add_speaker_note(sl, "Objetivo 2 no pide 50 clientes en 6 meses. Pide construir el pipeline que Acierta nunca tuvo y demostrar que el canal funciona.")

# ─────────────────────────────────────────
# SLIDE 9 — ESTRATEGIA DE CONTENIDOS
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "LA ESTRATEGIA DE CONTENIDOS CONVIERTE LINKEDIN EN UNA MÁQUINA DE LEADS",
             "EJE 2 · Estrategia de contenidos · 4 pilares + canal email segmentado")

pilares = [
    ("01", "Autoridad técnica", "Análisis económico, laboral y\norganizacional", "2×/semana"),
    ("02", "Casos de éxito", "Historias reales de clientes\n(el formato que más convierte)", "1×/semana"),
    ("03", "Educación del mercado", "Posts que explican por qué los\nservicios no-core importan", "1×/semana"),
    ("04", "Humanización", "El equipo de Acierta como\nexpertos visibles — nombre + cara", "2×/mes"),
]
for i, (num, title, desc, freq) in enumerate(pilares):
    px = Inches(0.4 + i * 3.23)
    py = Inches(1.3)
    add_rect(sl, px, py, Inches(3.0), Inches(2.7), fill=AZUL)
    add_textbox(sl, num, px + Inches(0.15), py + Inches(0.1), Inches(0.5), Inches(0.45),
                bold=True, size=22, color=NARANJA)
    add_textbox(sl, title, px + Inches(0.15), py + Inches(0.6), Inches(2.7), Inches(0.4),
                bold=True, size=11, color=BLANCO)
    add_textbox(sl, desc, px + Inches(0.15), py + Inches(1.05), Inches(2.7), Inches(0.7),
                size=9, color=RGBColor(0xAA,0xBB,0xCC))
    add_rect(sl, px, py + Inches(2.3), Inches(3.0), Inches(0.38), fill=NARANJA)
    add_textbox(sl, freq, px + Inches(0.1), py + Inches(2.35), Inches(2.8), Inches(0.28),
                bold=True, size=9, color=BLANCO, align=PP_ALIGN.CENTER)

# Email segmentación
add_rect(sl, Inches(0.4), Inches(4.2), Inches(12.5), Inches(0.35), fill=AZUL)
add_textbox(sl, "EMAIL SEGMENTADO — LOS 4.000 ASOCIADOS CAINCO", Inches(0.55), Inches(4.25),
            Inches(12.1), Inches(0.27), bold=True, size=9, color=BLANCO)

seg_data = [
    ("A — Empresas grandes", "Casos de éxito reclutamiento", "Mensual"),
    ("B — Empresas familiares", "Gobierno corporativo + webinars", "Bimensual"),
    ("C — Gerentes/CFOs", "Barómetro + análisis sectorial", "Mensual"),
    ("D — Sin servicio previo", "Awareness del portafolio completo", "Trimestral"),
]
for i, (seg, content, freq) in enumerate(seg_data):
    sx = Inches(0.4 + i * 3.23)
    sy = Inches(4.58)
    bg = GRIS if i % 2 == 0 else BLANCO
    add_rect(sl, sx, sy, Inches(3.0), Inches(1.55), fill=bg, line=RGBColor(0xDD,0xDD,0xDD))
    add_textbox(sl, seg, sx + Inches(0.12), sy + Inches(0.08), Inches(2.75), Inches(0.32),
                bold=True, size=9, color=AZUL)
    add_textbox(sl, content, sx + Inches(0.12), sy + Inches(0.42), Inches(2.75), Inches(0.38),
                size=9, color=GRIS_TEXTO)
    add_rect(sl, sx, sy + Inches(1.1), Inches(3.0), Inches(0.32), fill=NARANJA)
    add_textbox(sl, freq, sx + Inches(0.1), sy + Inches(1.13), Inches(2.8), Inches(0.24),
                size=8.5, color=BLANCO, bold=True, align=PP_ALIGN.CENTER)

add_speaker_note(sl, "El contenido no es un fin en sí mismo. Cada pieza tiene un objetivo de conversión: que alguien nos contacte, descargue algo, o asista a un webinar.")

# ─────────────────────────────────────────
# SLIDE 10 — QUICK WINS
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "LOS PRIMEROS 60 DÍAS GENERAN RESULTADOS ANTES DE GASTAR UN PESO",
             "EJE 3 · Quick Wins · 3 acciones de alto impacto, bajo costo")

qws = [
    ("QW1", "Barómetro Empresarial\nSanta Cruz", "Sem. 2–4",
     "Informe económico distribuido a 4.000\nasociados vía email y LinkedIn",
     "Primera medición de open rate\n+ segmentos activos identificados",
     "Bs. 800–1.200", AZUL),
    ("QW2", "Reactivación de base\nde clientes", "Sem. 1–3",
     "WhatsApp Business a últimos 50 clientes\nde Reclutamiento: diagnóstico gratis 30 min",
     "5–10 conversaciones reactivadas\n2–3 propuestas en pipeline",
     "Bs. 200–300", VERDE),
    ("QW3", "Webinar: Empresas\nFamiliares en crisis", "Mes 2",
     "Webinar gratuito para fundadores CAINCO:\n'Cómo proteger tu empresa familiar'",
     "30–50 asistentes\n5 leads calificados mínimo",
     "Bs. 600–900", RGBColor(0x7B, 0x2D, 0x8B)),
]
for i, (num, title, timing, accion, resultado, costo, color) in enumerate(qws):
    cx = Inches(0.4)
    cy = Inches(1.35 + i * 1.9)
    add_rect(sl, cx, cy, Inches(12.5), Inches(1.75), fill=GRIS)
    add_rect(sl, cx, cy, Inches(0.12), Inches(1.75), fill=color)
    add_textbox(sl, num, cx + Inches(0.25), cy + Inches(0.1), Inches(0.7), Inches(0.45),
                bold=True, size=18, color=color)
    add_textbox(sl, title, cx + Inches(0.25), cy + Inches(0.55), Inches(2.0), Inches(0.65),
                bold=True, size=11, color=AZUL)
    add_rect(sl, cx + Inches(0.25), cy + Inches(1.3), Inches(1.5), Inches(0.3), fill=color)
    add_textbox(sl, timing, cx + Inches(0.3), cy + Inches(1.33), Inches(1.4), Inches(0.25),
                size=8, color=BLANCO, bold=True)
    add_textbox(sl, accion, cx + Inches(2.6), cy + Inches(0.12), Inches(4.5), Inches(0.75), size=9.5, color=GRIS_TEXTO)
    add_textbox(sl, "→ " + resultado, cx + Inches(7.5), cy + Inches(0.12), Inches(3.3), Inches(0.75),
                size=9.5, color=VERDE, bold=True)
    add_rect(sl, cx + Inches(11.1), cy + Inches(0.3), Inches(1.2), Inches(0.55), fill=color)
    add_textbox(sl, costo, cx + Inches(11.12), cy + Inches(0.35), Inches(1.15), Inches(0.45),
                size=9, color=BLANCO, bold=True, align=PP_ALIGN.CENTER)

add_speaker_note(sl, "Estos tres Quick Wins cuestan menos de Bs. 2.500 combinados y nos dan datos reales en las primeras 8 semanas. Primero aprendemos, luego escalamos.")

# ─────────────────────────────────────────
# SLIDE 11 — CRONOGRAMA + PRESUPUESTO
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
slide_header(sl, "EL CRONOGRAMA CONVIERTE LA ESTRATEGIA EN ACCIONES MES A MES",
             "EJE 3 · Plan de implementación · 6 meses + presupuesto estimado")

fases = [
    ("MES 1–2", "Diagnóstico\n+ Encendido", ["Entrevistas + auditoría", "CRM básico operativo", "Barómetro #1 + QW1-2", "Webinar #1 (mes 2)"], AZUL),
    ("MES 3–4", "Construcción\nde pipeline", ["LinkedIn 4 pilares activo", "Barómetro #2", "Webinar #2", "Email segmentado operativo"], VERDE),
    ("MES 5–6", "Optimización\ny escala", ["Análisis canal que convierte", "Barómetro #3 + Webinar #3", "Ajuste de mensajes por persona", "1er reporte CAC por servicio"], RGBColor(0x7B, 0x2D, 0x8B)),
]
for i, (mes, fase, items, color) in enumerate(fases):
    fx = Inches(0.4 + i * 4.3)
    fy = Inches(1.3)
    add_rect(sl, fx, fy, Inches(4.1), Inches(3.7), fill=GRIS)
    add_rect(sl, fx, fy, Inches(4.1), Inches(0.55), fill=color)
    add_textbox(sl, mes, fx + Inches(0.15), fy + Inches(0.07), Inches(1.5), Inches(0.42),
                bold=True, size=11, color=BLANCO)
    add_textbox(sl, fase, fx + Inches(1.7), fy + Inches(0.07), Inches(2.2), Inches(0.42),
                bold=True, size=10, color=BLANCO)
    iy = fy + Inches(0.7)
    for item in items:
        dot = sl.shapes.add_shape(9, fx + Inches(0.18), iy + Inches(0.1), Inches(0.1), Inches(0.1))
        dot.fill.solid(); dot.fill.fore_color.rgb = color; dot.line.fill.background()
        add_textbox(sl, item, fx + Inches(0.38), iy, Inches(3.55), Inches(0.38), size=9.5, color=GRIS_TEXTO)
        iy += Inches(0.52)

# Hitos
add_rect(sl, Inches(0.4), Inches(5.15), Inches(12.5), Inches(0.32), fill=AZUL)
add_textbox(sl, "HITOS DE CONTROL", Inches(0.55), Inches(5.18), Inches(12.1), Inches(0.25),
            bold=True, size=8.5, color=BLANCO)
hitos = [("Mes 2", "¿5 leads no-core? ¿Barómetro 25% open rate?"),
         ("Mes 4", "¿10 leads no-core? ¿LinkedIn en crecimiento?"),
         ("Mes 6", "¿15 leads/mes no-core? ¿CAC calculado? ¿ROI positivo?")]
for i, (m, h) in enumerate(hitos):
    hx = Inches(0.5 + i * 4.3)
    add_rect(sl, hx, Inches(5.5), Inches(4.0), Inches(0.55), fill=GRIS)
    add_textbox(sl, m + ": ", hx + Inches(0.1), Inches(5.55), Inches(0.7), Inches(0.38),
                bold=True, size=9, color=NARANJA)
    add_textbox(sl, h, hx + Inches(0.8), Inches(5.55), Inches(3.1), Inches(0.4), size=9, color=GRIS_TEXTO)

# Presupuesto
add_rect(sl, Inches(0.4), Inches(6.15), Inches(12.5), Inches(1.0), fill=RGBColor(0x0D,0x1E,0x33))
add_textbox(sl, "PRESUPUESTO ESTIMADO 6 MESES — máximo impacto, mínima inversión en divisas",
            Inches(0.55), Inches(6.2), Inches(6.0), Inches(0.35), bold=True, size=8.5, color=NARANJA)
budget = [("Barómetro (3 ed.)", "Bs. 2.400–3.600"), ("Webinars (3)", "Bs. 1.800–2.700"),
          ("WhatsApp Business", "Bs. 600–900"), ("Diseño LinkedIn", "Bs. 1.000–1.500"),
          ("CRM + contenido orgánico", "Bs. 0"), ("TOTAL", "Bs. 5.800–8.700")]
bx = Inches(0.55)
for label, val in budget:
    bold = label == "TOTAL"
    color_v = NARANJA if bold else BLANCO
    add_textbox(sl, label, bx, Inches(6.6), Inches(1.8), Inches(0.38), size=8.5, color=RGBColor(0xAA,0xBB,0xCC), bold=bold)
    add_textbox(sl, val, bx, Inches(6.92), Inches(1.8), Inches(0.28), size=9, color=color_v, bold=bold)
    bx += Inches(2.07)

add_speaker_note(sl, "Seis meses, tres fases, menos de Bs. 9.000 de inversión total. El costo más alto es tiempo interno, no divisas.")

# ─────────────────────────────────────────
# SLIDE 12 — CRITERIOS DE ÉXITO
# ─────────────────────────────────────────
sl = prs.slides.add_slide(blank)
add_rect(sl, 0, 0, W, H, fill=AZUL)
add_rect(sl, 0, 0, W, Inches(0.07), fill=NARANJA)

add_textbox(sl, "EL ÉXITO SE MIDE CON 3 CRITERIOS QUE ACIERTA CONTROLA DESDE EL DÍA 1",
            Inches(0.5), Inches(0.15), Inches(12.3), Inches(0.8),
            bold=True, size=20, color=BLANCO)
add_textbox(sl, "EJE 3 · Criterios de éxito · Qué es ganar en 6 meses",
            Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.35),
            size=12, color=NARANJA)

criterios = [
    ("1", "Pipeline construido\ny documentado",
     "15 leads calificados/mes\npara servicios no-core al mes 6",
     "90 leads totales no-core\nregistrados en CRM",
     "Acierta pasa de 0 leads medidos\na pipeline real y auditable"),
    ("2", "Posicionamiento como\nreferente técnico",
     "LinkedIn: +30% seguidores\n+ engagement 3%+ por post",
     "Barómetro: open rate 25%+\nen los 3 envíos",
     "El posicionamiento digital genera\nleads en el mes 7, 8 y 12"),
    ("3", "Eficiencia de inversión\nverificada",
     "CAC por servicio no-core\n≤ 30% del ticket promedio al mes 6",
     "Al menos 2 servicios no-core\ncon clientes nuevos cerrados",
     "No basta con leads — el plan es\nexitoso cuando hay conversión"),
]
for i, (num, title, metric1, metric2, razon) in enumerate(criterios):
    cx = Inches(0.4 + i * 4.3)
    cy = Inches(1.4)
    add_rect(sl, cx, cy, Inches(4.0), Inches(5.5), fill=RGBColor(0x0D,0x1E,0x33))
    add_textbox(sl, num, cx + Inches(0.2), cy + Inches(0.1), Inches(0.6), Inches(0.7),
                bold=True, size=40, color=NARANJA)
    add_textbox(sl, title, cx + Inches(0.2), cy + Inches(0.85), Inches(3.6), Inches(0.55),
                bold=True, size=12, color=BLANCO)
    add_rect(sl, cx + Inches(0.2), cy + Inches(1.55), Inches(3.6), Inches(0.03), fill=NARANJA)
    add_textbox(sl, "Métrica principal:", cx + Inches(0.2), cy + Inches(1.65), Inches(3.6), Inches(0.28),
                bold=True, size=8.5, color=NARANJA)
    add_textbox(sl, metric1, cx + Inches(0.2), cy + Inches(1.95), Inches(3.6), Inches(0.55),
                bold=True, size=10, color=BLANCO)
    add_textbox(sl, "Métrica secundaria:", cx + Inches(0.2), cy + Inches(2.6), Inches(3.6), Inches(0.28),
                size=8.5, color=RGBColor(0x88,0x99,0xAA))
    add_textbox(sl, metric2, cx + Inches(0.2), cy + Inches(2.9), Inches(3.6), Inches(0.55),
                size=9.5, color=RGBColor(0xCC,0xDD,0xEE))
    add_rect(sl, cx, cy + Inches(4.55), Inches(4.0), Inches(0.95), fill=NARANJA)
    add_textbox(sl, razon, cx + Inches(0.15), cy + Inches(4.62), Inches(3.7), Inches(0.75),
                size=8.5, color=BLANCO, italic=True)

add_speaker_note(sl, "En seis meses Acierta no va a dominar el mercado. Va a tener algo que hoy no tiene: datos, pipeline y un sistema que funciona sin depender solo de referidos.")

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
out = "/home/user/AGENTE-MARKETIGN-SDY/casos/cainco/output/Plan_Marketing_Acierta_CAINCO_Sandy.pptx"
prs.save(out)
print(f"Saved: {out}")
