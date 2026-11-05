#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_pptx.py — deck.json -> output/deck.pptx

Renderiza la MISMA fuente unica (deck.json) como un .pptx 100% editable
en PowerPoint (formas y texto nativos, sin imagenes). Misma paleta y
mismos bloques que render_html.py.

Requiere:  pip install python-pptx
Uso:       python render_pptx.py
"""
import json
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "deck.json")
OUT = os.path.join(HERE, "output", "deck.pptx")

EMU_IN = 914400


def hx(s):
    return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


class Renderer:
    def __init__(self, deck):
        self.deck = deck
        t = deck["theme"]
        self.INK = hx(t["ink"]); self.ORANGE = hx(t["orange"])
        self.PAPER = hx(t["paper"]); self.MIST = hx(t["mist"])
        self.LINE = hx(t["line"]); self.GOOD = hx(t["good"])
        self.BAD = hx(t["bad"]); self.MUTED = hx(t["muted"])
        self.HEAD = "Georgia"; self.BODY = "Segoe UI"
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.W = 13.333; self.H = 7.5
        self.blank = self.prs.slide_layouts[6]

    # ---- low level helpers ----
    def rect(self, sl, x, y, w, h, fill=None, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None):
        sp = sl.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill is None:
            sp.fill.background()
        else:
            sp.fill.solid(); sp.fill.fore_color.rgb = fill
        if line is None:
            sp.line.fill.background()
        else:
            sp.line.color.rgb = line; sp.line.width = Pt(line_w)
        sp.shadow.inherit = False
        return sp

    def text(self, sl, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True, space=4):
        tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = wrap
        tf.vertical_anchor = anchor
        for m in ("left", "right", "top", "bottom"):
            setattr(tf, "margin_" + m, 0)
        # runs: list of paragraphs, each a list of (text, size, color, bold, font, italic)
        for i, para in enumerate(runs):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.space_after = Pt(space); p.space_before = Pt(0)
            for (txt, size, color, bold, font, *rest) in para:
                italic = rest[0] if rest else False
                r = p.add_run(); r.text = txt
                r.font.size = Pt(size); r.font.bold = bold
                r.font.color.rgb = color; r.font.name = font
                r.font.italic = italic
        return tb

    def P(self, txt, size, color, bold=False, font=None, italic=False):
        return [(txt, size, color, bold, font or self.BODY, italic)]

    # ---- chrome ----
    def chrome(self, sl, idx, total, foot, note=None):
        # bottom orange bar
        self.rect(sl, 0, self.H - 0.11, self.W, 0.11, fill=self.ORANGE)
        self.text(sl, 0.85, self.H - 0.42, 8, 0.3, [self.P(foot, 9, self.MUTED)], anchor=MSO_ANCHOR.MIDDLE)
        self.text(sl, self.W - 1.6, self.H - 0.42, 0.9, 0.3, [self.P(f"{idx}/{total}", 9, self.MUTED)], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        if note:
            self.rect(sl, 0.85, self.H - 0.95, 0.04, 0.4, fill=self.ORANGE)
            self.text(sl, 0.98, self.H - 0.98, self.W - 2.0, 0.45, [self.P("Nota oral: " + note, 9, hx("8A93A6"), italic=True)], anchor=MSO_ANCHOR.MIDDLE)

    def header(self, sl, s):
        if s.get("subtitle"):
            self.text(sl, 0.85, 0.55, self.W - 1.7, 0.35, [self.P(s["subtitle"].upper(), 11, self.ORANGE, bold=True)])
        self.text(sl, 0.85, 0.9, self.W - 1.7, 1.1, [self.P(s["title"], 26, self.INK, bold=True, font=self.HEAD)])

    # ---- slide types ----
    def cover(self, sl, s):
        self.rect(sl, 0, 0, self.W, self.H, fill=self.PAPER)
        self.text(sl, 0.95, 2.0, self.W - 2, 0.4, [self.P(s.get("kicker", ""), 13, self.ORANGE, bold=True)])
        self.text(sl, 0.95, 2.45, self.W - 2, 1.4, [self.P(s["title"], 50, self.INK, bold=True, font=self.HEAD)])
        self.text(sl, 0.95, 3.95, self.W - 3, 1.2, [self.P(s.get("subtitle", ""), 20, self.MUTED)])
        self.text(sl, 0.95, 5.2, self.W - 2, 0.5, [self.P(s.get("meta", ""), 14, self.ORANGE, bold=True)])

    def two_columns(self, sl, s):
        self.header(sl, s)
        top = 2.15; h = 4.5; gap = 0.4
        w = (self.W - 1.7 - gap) / 2
        for k, x in (("left", 0.85), ("right", 0.85 + w + gap)):
            c = s[k]
            tone = self.GOOD if c.get("tone") == "good" else (self.BAD if c.get("tone") == "bad" else self.INK)
            self.rect(sl, x, top, w, h, fill=self.MIST, line=self.LINE)
            self.text(sl, x + 0.3, top + 0.25, w - 0.6, 0.4, [self.P(c["label"], 14, tone, bold=True)])
            paras = []
            for it in c["items"]:
                paras.append([("▸  ", 13, self.ORANGE, True, self.BODY, False),
                              (it, 13, self.INK, False, self.BODY, False)])
            self.text(sl, x + 0.3, top + 0.85, w - 0.6, h - 1.1, paras, space=8)

    def table(self, sl, s):
        self.header(sl, s)
        headers = s["headers"]; rows = s["rows"]
        ncol = len(headers)
        x0 = 0.85; top = 2.1; tw = self.W - 1.7
        has_call = bool(s.get("callout"))
        avail = (3.4 if has_call else 4.6)
        rh = min(0.55, avail / (len(rows) + 1))
        hh = rh
        # column widths: first col a bit wider
        widths = [tw * (0.24 if i == 0 else (0.76 / (ncol - 1))) for i in range(ncol)]
        # header
        cx = x0
        for j, htext in enumerate(headers):
            self.rect(sl, cx, top, widths[j], hh, fill=self.INK)
            self.text(sl, cx + 0.12, top, widths[j] - 0.2, hh, [self.P(htext, 11, self.PAPER, bold=True)], anchor=MSO_ANCHOR.MIDDLE)
            cx += widths[j]
        # rows
        for i, row in enumerate(rows):
            ry = top + hh + i * rh
            bg = self.MIST if i % 2 else self.PAPER
            cx = x0
            for j, cell in enumerate(row):
                self.rect(sl, cx, ry, widths[j], rh, fill=bg, line=self.LINE, line_w=0.5)
                self.text(sl, cx + 0.12, ry, widths[j] - 0.2, rh, [self.P(cell, 10.5, self.INK, bold=(j == 0))], anchor=MSO_ANCHOR.MIDDLE)
                cx += widths[j]
        if has_call:
            c = s["callout"]
            cy = top + hh + len(rows) * rh + 0.2
            self.rect(sl, x0, cy, tw, 1.15, fill=hx("FFF4EC"), line=self.ORANGE)
            self.text(sl, x0 + 0.25, cy + 0.15, tw - 0.5, 0.35, [self.P(c["label"], 12, self.ORANGE, bold=True)])
            self.text(sl, x0 + 0.25, cy + 0.5, tw - 0.5, 0.6, [self.P(c["text"], 13, self.INK)])

    def cards(self, sl, s):
        self.header(sl, s)
        ncol = s.get("columns", 2)
        cards = s["cards"]
        x0 = 0.85; top = 2.15; gap = 0.3
        tw = self.W - 1.7
        cw = (tw - gap * (ncol - 1)) / ncol
        nrows = (len(cards) + ncol - 1) // ncol
        facts = s.get("facts")
        avail = (3.7 if facts else 4.55)
        ch = (avail - gap * (nrows - 1)) / nrows
        for i, c in enumerate(cards):
            r = i // ncol; col = i % ncol
            x = x0 + col * (cw + gap); y = top + r * (ch + gap)
            self.rect(sl, x, y, cw, ch, fill=self.PAPER, line=self.LINE)
            self.rect(sl, x, y, cw, 0.07, fill=self.ORANGE)
            self.text(sl, x + 0.25, y + 0.22, cw - 0.5, 0.5, [self.P(c["label"], 14, self.INK, bold=True)])
            self.text(sl, x + 0.25, y + 0.85, cw - 0.5, ch - 1.0, [self.P(c["body"], 11.5, hx("33405B"))], space=2)
        if facts:
            fy = top + nrows * (ch + gap) + 0.05
            fx = x0
            for f in facts:
                w = min(0.18 * len(f) + 0.3, 3.6)
                self.rect(sl, fx, fy, w, 0.42, fill=self.INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                self.text(sl, fx, fy, w, 0.42, [self.P(f, 10.5, self.PAPER, bold=True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                fx += w + 0.2

    def statement(self, sl, s):
        self.header(sl, s)
        top = 2.2
        self.rect(sl, 0.85, top, 0.08, 1.4, fill=self.ORANGE)
        self.text(sl, 1.1, top, self.W - 2.2, 1.5, [self.P("“" + s["quote"] + "”", 28, self.INK, bold=False, font=self.HEAD)])
        sy = top + 1.75
        if s.get("shift"):
            sh = s["shift"]
            self.rect(sl, 0.85, sy, 4.3, 0.7, fill=self.MIST, line=self.LINE)
            self.text(sl, 0.95, sy, 4.1, 0.7, [self.P(sh["from"], 14, self.MUTED)], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
            self.text(sl, 5.25, sy, 0.7, 0.7, [self.P("→", 26, self.ORANGE, bold=True)], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
            self.rect(sl, 6.05, sy, 4.6, 0.7, fill=self.INK)
            self.text(sl, 6.15, sy, 4.4, 0.7, [self.P(sh["to"], 14, self.PAPER, bold=True)], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
            sy += 1.0
        if s.get("extra"):
            self.text(sl, 0.85, sy, self.W - 1.7, 1.5, [self.P(s["extra"], 13, hx("33405B"))], space=4)

    def objectives(self, sl, s):
        self.header(sl, s)
        items = s["items"]; top = 2.15; gap = 0.3
        h = (4.4 - gap * (len(items) - 1)) / len(items)
        for i, o in enumerate(items):
            y = top + i * (h + gap)
            self.rect(sl, 0.85, y, self.W - 1.7, h, fill=self.PAPER, line=self.LINE)
            self.rect(sl, 0.85, y, 1.3, h, fill=self.ORANGE)
            self.text(sl, 0.85, y, 1.3, h, [self.P(o["tag"], 14, self.PAPER, bold=True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            tx = 2.4
            self.text(sl, tx, y + 0.18, self.W - tx - 0.9, 0.4, [self.P(o["name"], 16, self.INK, bold=True)])
            self.text(sl, tx, y + 0.62, self.W - tx - 0.9, 0.7, [self.P(o["goal"], 12, hx("33405B"))])
            kx = tx
            ky = y + h - 0.5
            for k in o["kpis"]:
                w = min(0.11 * len(k) + 0.3, 4.0)
                self.rect(sl, kx, ky, w, 0.36, fill=self.MIST, line=self.LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                self.text(sl, kx, ky, w, 0.36, [self.P(k, 9.5, self.INK, bold=True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                kx += w + 0.15

    def timeline(self, sl, s):
        self.header(sl, s)
        steps = s["steps"]; n = len(steps)
        x0 = 0.85; top = 2.4; gap = 0.25
        tw = self.W - 1.7
        cw = (tw - gap * (n - 1)) / n
        h = 3.5
        for i, st in enumerate(steps):
            x = x0 + i * (cw + gap)
            self.rect(sl, x, top, cw, h, fill=self.PAPER, line=self.LINE)
            self.rect(sl, x, top, cw, 0.07, fill=self.ORANGE)
            self.text(sl, x, top + 0.3, cw, 0.6, [self.P(st["when"], 22, self.ORANGE, bold=True)], align=PP_ALIGN.CENTER)
            self.text(sl, x + 0.18, top + 1.05, cw - 0.36, h - 1.2, [self.P(st["what"], 11, hx("33405B"))], space=2)

    def numbered(self, sl, s):
        self.header(sl, s)
        items = s["items"]; top = 2.2; gap = 0.25
        h = (4.3 - gap * (len(items) - 1)) / len(items)
        for i, it in enumerate(items):
            y = top + i * (h + gap)
            d = 0.85
            self.rect(sl, 0.85, y + (h - d) / 2, d, d, fill=self.INK, shape=MSO_SHAPE.OVAL)
            self.text(sl, 0.85, y + (h - d) / 2, d, d, [self.P(it["n"], 28, self.PAPER, bold=True, font=self.HEAD)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            tx = 2.0
            self.text(sl, tx, y + 0.1, self.W - tx - 0.9, 0.4, [self.P(it["head"], 18, self.INK, bold=True)])
            self.text(sl, tx, y + 0.55, self.W - tx - 0.9, h - 0.6, [self.P(it["body"], 13, hx("33405B"))])
            self.rect(sl, tx, y + h, self.W - tx - 0.9, 0.01, fill=self.LINE)

    DISPATCH = {
        "cover": cover, "two-columns": two_columns, "table": table,
        "cards": cards, "statement": statement, "objectives": objectives,
        "timeline": timeline, "numbered": numbered,
    }

    def build(self):
        foot = self.deck["meta"].get("footer", "")
        slides = self.deck["slides"]
        total = len(slides)
        for i, s in enumerate(slides):
            sl = self.prs.slides.add_slide(self.blank)
            bg = sl.background
            bg.fill.solid(); bg.fill.fore_color.rgb = self.PAPER
            fn = self.DISPATCH.get(s["type"])
            if not fn:
                self.text(sl, 1, 3, 10, 1, [self.P("Tipo no soportado: " + s["type"], 18, self.BAD)])
                continue
            fn(self, sl, s)
            if s["type"] == "cover":
                self.chrome(sl, i + 1, total, foot, None)
            else:
                self.chrome(sl, i + 1, total, foot, s.get("note"))
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        self.prs.save(OUT)
        print("OK PPTX escrito ->", OUT, f"({total} slides)")


def main():
    with open(SRC, encoding="utf-8") as f:
        deck = json.load(f)
    Renderer(deck).build()


if __name__ == "__main__":
    main()
