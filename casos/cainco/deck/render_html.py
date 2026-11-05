#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_html.py — deck.json -> output/deck.html

Renderiza la fuente unica (deck.json) como slides HTML 16:9.
Sin dependencias: solo libreria estandar. Para PDF: abre el HTML en el
navegador e imprime (Ctrl+P -> Guardar como PDF); el CSS @media print
deja un slide por pagina horizontal.

Uso:  python render_html.py
"""
import json
import os
import html

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "deck.json")
OUT = os.path.join(HERE, "output", "deck.html")


def esc(s):
    return html.escape(str(s), quote=True)


def css(theme):
    t = theme
    return f"""
:root {{
  --ink:#{t['ink']}; --orange:#{t['orange']}; --paper:#{t['paper']};
  --mist:#{t['mist']}; --line:#{t['line']}; --good:#{t['good']};
  --bad:#{t['bad']}; --muted:#{t['muted']};
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#c9ced8; font-family:{t['fontBody']}; color:var(--ink); padding:24px 0; }}
.slide {{
  width:1280px; height:720px; margin:0 auto 28px; background:var(--paper);
  position:relative; overflow:hidden; box-shadow:0 8px 30px rgba(0,0,0,.18);
  padding:64px 72px;
}}
.slide::after {{
  content:""; position:absolute; left:0; right:0; bottom:0; height:8px;
  background:var(--orange);
}}
.kicker {{ color:var(--orange); font-weight:700; letter-spacing:3px; font-size:18px; }}
h1 {{ font-family:{t['fontHead']}; font-size:40px; line-height:1.15; margin:6px 0 4px; }}
.sub {{ color:var(--muted); font-size:20px; margin-bottom:28px; }}
.foot {{ position:absolute; left:72px; bottom:18px; color:var(--muted); font-size:13px; }}
.pageno {{ position:absolute; right:72px; bottom:18px; color:var(--muted); font-size:13px; }}
.note {{ position:absolute; left:72px; bottom:40px; right:72px; color:#8a93a6;
  font-size:13px; font-style:italic; border-left:3px solid var(--orange); padding-left:10px; }}

/* cover */
.cover {{ display:flex; flex-direction:column; justify-content:center; height:100%; }}
.cover h1 {{ font-size:64px; margin:14px 0; }}
.cover .csub {{ font-size:26px; color:var(--muted); max-width:900px; }}
.cover .cmeta {{ margin-top:30px; color:var(--orange); font-weight:600; font-size:18px; }}

/* two columns */
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; }}
.col {{ border:1px solid var(--line); border-radius:10px; padding:22px 24px; background:var(--mist); }}
.col .clabel {{ font-weight:800; letter-spacing:1px; font-size:16px; margin-bottom:14px; }}
.col.good .clabel {{ color:var(--good); }}
.col.bad .clabel {{ color:var(--bad); }}
.col ul {{ list-style:none; }}
.col li {{ font-size:18px; line-height:1.4; padding:9px 0 9px 22px; position:relative; border-top:1px solid var(--line); }}
.col li:first-child {{ border-top:none; }}
.col li::before {{ content:"\\25B8"; position:absolute; left:0; color:var(--orange); }}

/* table */
table {{ width:100%; border-collapse:collapse; font-size:17px; }}
th {{ background:var(--ink); color:#fff; text-align:left; padding:12px 14px; font-size:15px; letter-spacing:.5px; }}
td {{ padding:11px 14px; border-bottom:1px solid var(--line); vertical-align:top; }}
tr:nth-child(even) td {{ background:var(--mist); }}
.callout {{ margin-top:22px; background:#fff4ec; border:1px solid var(--orange); border-radius:10px; padding:16px 20px; }}
.callout .clabel {{ color:var(--orange); font-weight:800; letter-spacing:1px; font-size:15px; }}
.callout .ctext {{ font-size:18px; line-height:1.4; margin-top:6px; }}

/* cards */
.cards {{ display:grid; gap:18px; }}
.cards.c2 {{ grid-template-columns:1fr 1fr; }}
.cards.c3 {{ grid-template-columns:1fr 1fr 1fr; }}
.card {{ border:1px solid var(--line); border-top:4px solid var(--orange); border-radius:10px; padding:18px 20px; background:#fff; }}
.card .clabel {{ font-weight:800; color:var(--ink); font-size:18px; margin-bottom:8px; }}
.card .cbody {{ font-size:16px; line-height:1.4; color:#33405b; }}
.facts {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }}
.fact {{ background:var(--ink); color:#fff; border-radius:20px; padding:7px 16px; font-size:14px; font-weight:600; }}

/* statement */
.quote {{ font-family:{t['fontHead']}; font-size:34px; line-height:1.3; color:var(--ink);
  border-left:6px solid var(--orange); padding:6px 0 6px 24px; margin:10px 0 26px; }}
.shift {{ display:flex; align-items:center; gap:18px; font-size:20px; margin-bottom:20px; }}
.shift .from {{ background:var(--mist); border:1px solid var(--line); border-radius:8px; padding:12px 18px; color:var(--muted); }}
.shift .arrow {{ color:var(--orange); font-size:30px; font-weight:800; }}
.shift .to {{ background:var(--ink); color:#fff; border-radius:8px; padding:12px 18px; font-weight:600; }}
.extra {{ font-size:17px; line-height:1.5; color:#33405b; max-width:980px; }}

/* objectives */
.objs {{ display:grid; gap:18px; }}
.obj {{ border:1px solid var(--line); border-radius:10px; padding:18px 22px; background:#fff; display:grid; grid-template-columns:120px 1fr; gap:18px; }}
.obj .tag {{ background:var(--orange); color:#fff; font-weight:800; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:18px; }}
.obj .oname {{ font-weight:700; font-size:20px; }}
.obj .ogoal {{ font-size:17px; line-height:1.4; color:#33405b; margin:6px 0 10px; }}
.kpis {{ display:flex; flex-wrap:wrap; gap:8px; }}
.kpi {{ background:var(--mist); border:1px solid var(--line); border-radius:16px; padding:5px 13px; font-size:13px; color:var(--ink); font-weight:600; }}

/* timeline */
.tl {{ display:grid; grid-template-columns:repeat(6,1fr); gap:14px; margin-top:10px; }}
.tstep {{ background:#fff; border:1px solid var(--line); border-top:4px solid var(--orange); border-radius:10px; padding:16px 14px; }}
.tstep .when {{ font-weight:800; color:var(--orange); font-size:22px; }}
.tstep .what {{ font-size:14px; line-height:1.35; color:#33405b; margin-top:8px; }}

/* numbered */
.nums {{ display:grid; gap:18px; }}
.num {{ display:grid; grid-template-columns:70px 1fr; gap:20px; align-items:start; border-bottom:1px solid var(--line); padding-bottom:16px; }}
.num .ncircle {{ width:60px; height:60px; border-radius:50%; background:var(--ink); color:#fff; font-size:30px; font-weight:800; display:flex; align-items:center; justify-content:center; font-family:{t['fontHead']}; }}
.num .nhead {{ font-weight:800; font-size:22px; }}
.num .nbody {{ font-size:18px; line-height:1.4; color:#33405b; margin-top:4px; }}

@media print {{
  @page {{ size:1280px 720px; margin:0; }}
  body {{ background:#fff; padding:0; }}
  .slide {{ margin:0; box-shadow:none; page-break-after:always; }}
}}
"""


def head_block(s, foot, idx, total):
    parts = [f'<div class="kicker">{esc(s.get("subtitle",""))}</div>',
             f'<h1>{esc(s["title"])}</h1>']
    return "".join(parts)


def foot_block(s, foot, idx, total):
    out = f'<div class="foot">{esc(foot)}</div><div class="pageno">{idx}/{total}</div>'
    if s.get("note"):
        out = f'<div class="note">Nota oral: {esc(s["note"])}</div>' + out
    return out


def render_slide(s, theme, foot, idx, total):
    t = s["type"]
    body = ""

    if t == "cover":
        body = f"""<div class="cover">
          <div class="kicker">{esc(s.get('kicker',''))}</div>
          <h1>{esc(s['title'])}</h1>
          <div class="csub">{esc(s.get('subtitle',''))}</div>
          <div class="cmeta">{esc(s.get('meta',''))}</div>
        </div>"""
        note = f'<div class="note">Nota oral: {esc(s["note"])}</div>' if s.get("note") else ""
        return f'<section class="slide">{body}{note}<div class="pageno">{idx}/{total}</div></section>'

    head = f'<div class="kicker">{esc(s.get("subtitle",""))}</div><h1>{esc(s["title"])}</h1>'

    if t == "two-columns":
        def col(c):
            lis = "".join(f"<li>{esc(i)}</li>" for i in c["items"])
            return f'<div class="col {c.get("tone","")}"><div class="clabel">{esc(c["label"])}</div><ul>{lis}</ul></div>'
        body = f'{head}<div class="cols">{col(s["left"])}{col(s["right"])}</div>'

    elif t == "table":
        th = "".join(f"<th>{esc(h)}</th>" for h in s["headers"])
        rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in s["rows"])
        callout = ""
        if s.get("callout"):
            c = s["callout"]
            callout = f'<div class="callout"><div class="clabel">{esc(c["label"])}</div><div class="ctext">{esc(c["text"])}</div></div>'
        body = f'{head}<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>{callout}'

    elif t == "cards":
        ncol = s.get("columns", 2)
        cards = "".join(f'<div class="card"><div class="clabel">{esc(c["label"])}</div><div class="cbody">{esc(c["body"])}</div></div>' for c in s["cards"])
        facts = ""
        if s.get("facts"):
            facts = '<div class="facts">' + "".join(f'<span class="fact">{esc(f)}</span>' for f in s["facts"]) + '</div>'
        body = f'{head}<div class="cards c{ncol}">{cards}</div>{facts}'

    elif t == "statement":
        shift = ""
        if s.get("shift"):
            sh = s["shift"]
            shift = f'<div class="shift"><span class="from">{esc(sh["from"])}</span><span class="arrow">&rarr;</span><span class="to">{esc(sh["to"])}</span></div>'
        extra = f'<div class="extra">{esc(s.get("extra",""))}</div>' if s.get("extra") else ""
        body = f'{head}<div class="quote">&ldquo;{esc(s["quote"])}&rdquo;</div>{shift}{extra}'

    elif t == "objectives":
        objs = ""
        for o in s["items"]:
            kpis = "".join(f'<span class="kpi">{esc(k)}</span>' for k in o["kpis"])
            objs += f'<div class="obj"><div class="tag">{esc(o["tag"])}</div><div><div class="oname">{esc(o["name"])}</div><div class="ogoal">{esc(o["goal"])}</div><div class="kpis">{kpis}</div></div></div>'
        body = f'{head}<div class="objs">{objs}</div>'

    elif t == "timeline":
        steps = "".join(f'<div class="tstep"><div class="when">{esc(x["when"])}</div><div class="what">{esc(x["what"])}</div></div>' for x in s["steps"])
        body = f'{head}<div class="tl">{steps}</div>'

    elif t == "numbered":
        nums = "".join(f'<div class="num"><div class="ncircle">{esc(x["n"])}</div><div><div class="nhead">{esc(x["head"])}</div><div class="nbody">{esc(x["body"])}</div></div></div>' for x in s["items"])
        body = f'{head}<div class="nums">{nums}</div>'

    else:
        body = f'{head}<p>[tipo de slide no soportado: {esc(t)}]</p>'

    note = f'<div class="note">Nota oral: {esc(s["note"])}</div>' if s.get("note") else ""
    return f'<section class="slide">{body}{note}<div class="foot">{esc(foot)}</div><div class="pageno">{idx}/{total}</div></section>'


def main():
    with open(SRC, encoding="utf-8") as f:
        deck = json.load(f)
    theme = deck["theme"]
    foot = deck["meta"].get("footer", "")
    slides = deck["slides"]
    total = len(slides)
    body = "\n".join(render_slide(s, theme, foot, i + 1, total) for i, s in enumerate(slides))
    doc = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>{esc(deck['meta']['title'])}</title>
<style>{css(theme)}</style>
</head><body>
{body}
</body></html>"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("OK HTML escrito ->", OUT, f"({total} slides)")


if __name__ == "__main__":
    main()
