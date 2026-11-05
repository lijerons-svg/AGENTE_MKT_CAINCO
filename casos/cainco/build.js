const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// ---------- design system ----------
const INK = "1A2238";      // dominant dark
const ORANGE = "E8732A";   // brand accent (CAINCO/etika)
const SLATE = "5B6472";    // muted text
const LIGHT = "FFFFFF";
const PANEL = "F2F3F6";    // soft panel
const GREEN = "2E7D5B";
const TERRA = "C0492B";
const HFONT = "Georgia";
const BFONT = "Calibri";

const mkShadow = () => ({ type: "outer", color: "1A2238", blur: 7, offset: 3, angle: 135, opacity: 0.16 });

async function icon(IconComp, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComp, { color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const p = new pptxgen();
  p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
  p.layout = "W";
  p.author = "Subgerencia de Marketing Estratégico";
  p.title = "Plan de Marketing — Acierta by CAINCO";
  const W = 13.333, H = 7.5, M = 0.6;

  // preload icons
  const ic = {
    bolt: await icon(fa.FaBolt, "#FFFFFF"),
    target: await icon(fa.FaBullseye, "#FFFFFF"),
    chart: await icon(fa.FaChartLine, "#FFFFFF"),
    brand: await icon(fa.FaCertificate, "#FFFFFF"),
    linked: await icon(fa.FaLinkedin, "#FFFFFF"),
    flag: await icon(fa.FaFlagCheckered, "#FFFFFF"),
    map: await icon(fa.FaCompass, "#FFFFFF"),
    search: await icon(fa.FaSearch, "#FFFFFF"),
    trophy: await icon(fa.FaTrophy, "#FFFFFF"),
    check: await icon(fa.FaCheck, "#FFFFFF"),
  };

  // helpers
  function kicker(s, txt, color = ORANGE) {
    s.addText(txt.toUpperCase(), { x: M, y: 0.42, w: 11, h: 0.3, fontSize: 12, bold: true, color, fontFace: BFONT, charSpacing: 3, margin: 0 });
  }
  function title(s, txt, color = INK) {
    s.addText(txt, { x: M, y: 0.72, w: W - 2 * M, h: 0.8, fontSize: 30, bold: true, color, fontFace: HFONT, margin: 0 });
  }
  function iconBadge(s, data, x, y, d = 0.62, fill = ORANGE) {
    s.addShape(p.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, shadow: mkShadow() });
    s.addImage({ data, x: x + d * 0.26, y: y + d * 0.26, w: d * 0.48, h: d * 0.48 });
  }

  // ============ S1 — TITLE ============
  let s = p.addSlide();
  s.background = { color: INK };
  s.addShape(p.shapes.OVAL, { x: 9.7, y: -2.0, w: 6.2, h: 6.2, fill: { color: "232C49" } });
  s.addShape(p.shapes.OVAL, { x: 11.4, y: 4.3, w: 3.6, h: 3.6, fill: { color: ORANGE, transparency: 78 } });
  s.addText("ACIERTA  ·  BY CAINCO", { x: M, y: 1.7, w: 10, h: 0.4, fontSize: 14, bold: true, color: ORANGE, fontFace: BFONT, charSpacing: 4, margin: 0 });
  s.addText("Plan de Marketing\nEstratégico", { x: M, y: 2.15, w: 10.5, h: 2.0, fontSize: 50, bold: true, color: LIGHT, fontFace: HFONT, lineSpacingMultiple: 0.95, margin: 0 });
  s.addText("Primeros 6 meses de gestión  ·  Subgerencia de Marketing Estratégico", { x: M, y: 4.35, w: 11, h: 0.4, fontSize: 17, color: "C7CCDA", fontFace: BFONT, margin: 0 });
  s.addShape(p.shapes.LINE, { x: M, y: 6.55, w: 2.2, h: 0, line: { color: ORANGE, width: 2.5 } });
  s.addText("Confidencial — ETIKA SRL  ·  Santa Cruz · La Paz · Cochabamba", { x: M, y: 6.7, w: 11, h: 0.3, fontSize: 11, color: "8E96AC", italic: true, fontFace: BFONT, margin: 0 });

  // ============ S2 — DIAGNÓSTICO DIGITAL ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 1 · Diagnóstico"); title(s, "Auditoría digital: lo que ya tenemos vs. lo que frena");
  const colW = 5.85, gap = 0.43, leftX = M, rightX = M + colW + gap, topY = 1.75, cardH = 4.9;
  // strengths card
  s.addShape(p.shapes.RECTANGLE, { x: leftX, y: topY, w: colW, h: cardH, fill: { color: PANEL }, shadow: mkShadow() });
  s.addShape(p.shapes.RECTANGLE, { x: leftX, y: topY, w: 0.1, h: cardH, fill: { color: GREEN } });
  iconBadge(s, ic.check, leftX + 0.32, topY + 0.32, 0.6, GREEN);
  s.addText("3 FORTALEZAS", { x: leftX + 1.05, y: topY + 0.4, w: 4, h: 0.45, fontSize: 17, bold: true, color: GREEN, fontFace: BFONT, valign: "middle", margin: 0 });
  const strengths = [
    ["Respaldo CAINCO", "+100 años, 4.000 asociadas, 45.8k seguidores en LinkedIn. Credibilidad que ningún privado iguala."],
    ["Base social construida", "Facebook con 19.752 seguidores: capital hoy subutilizado, listo para activar."],
    ["Activos de contenido únicos", "Mensajes de valor ya escritos + data económica propia (CEBEC) sin explotar."],
  ];
  let yy = topY + 1.25;
  strengths.forEach(([h, d]) => {
    s.addText(h, { x: leftX + 0.4, y: yy, w: colW - 0.7, h: 0.32, fontSize: 14.5, bold: true, color: INK, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: leftX + 0.4, y: yy + 0.34, w: colW - 0.7, h: 0.8, fontSize: 12, color: SLATE, fontFace: BFONT, margin: 0 });
    yy += 1.2;
  });
  // weaknesses card
  s.addShape(p.shapes.RECTANGLE, { x: rightX, y: topY, w: colW, h: cardH, fill: { color: PANEL }, shadow: mkShadow() });
  s.addShape(p.shapes.RECTANGLE, { x: rightX, y: topY, w: 0.1, h: cardH, fill: { color: TERRA } });
  iconBadge(s, ic.search, rightX + 0.32, topY + 0.32, 0.6, TERRA);
  s.addText("3 DEBILIDADES", { x: rightX + 1.05, y: topY + 0.4, w: 4, h: 0.45, fontSize: 17, bold: true, color: TERRA, fontFace: BFONT, valign: "middle", margin: 0 });
  const weaks = [
    ["Identidad fragmentada", "2 dominios web, showcase escondido bajo CAINCO y 3 WhatsApp distintos: el lead no sabe dónde vive Acierta."],
    ["El feed = bolsa de empleo", "Domina el \u201Cbuscamos [cargo]\u201D \u2192 comunica \u201Cagencia de vacantes\u201D e invisibiliza consultoría y asesoría."],
    ["Canal B2B desaprovechado", "El peso está en Facebook (postulantes), no en LinkedIn (decisores). Solo 4 reseñas, sin prueba social."],
  ];
  yy = topY + 1.25;
  weaks.forEach(([h, d]) => {
    s.addText(h, { x: rightX + 0.4, y: yy, w: colW - 0.7, h: 0.32, fontSize: 14.5, bold: true, color: INK, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: rightX + 0.4, y: yy + 0.34, w: colW - 0.7, h: 0.85, fontSize: 12, color: SLATE, fontFace: BFONT, margin: 0 });
    yy += 1.2;
  });

  // ============ S3 — MAPA COMPETITIVO ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 1 · Competencia"); title(s, "Mapa competitivo: dónde está el hueco para Acierta");
  const rows = [
    [{ text: "Competidor", options: { bold: true, color: LIGHT, fill: { color: INK }, fontSize: 13, align: "left" } },
     { text: "Posicionamiento", options: { bold: true, color: LIGHT, fill: { color: INK }, fontSize: 13 } },
     { text: "Diferenciador", options: { bold: true, color: LIGHT, fill: { color: INK }, fontSize: 13 } },
     { text: "Huella digital", options: { bold: true, color: LIGHT, fill: { color: INK }, fontSize: 13 } }],
    ["Manpower Bolivia", "Líder global, transaccional", "Escala mundial, franquicia desde 1991", "LinkedIn 10.3k · FB 17.5k"],
    ["EY Bolivia", "Big Four, premium corporativo", "Metodología global, prestigio", "Marca global"],
    ["Exaudi / boutiques", "Especialista empresa familiar", "Foco 100% familia, cercanía", "Nicho, eventos locales"],
    ["ACIERTA by CAINCO", "Socio de gestión cercano", "Respaldo gremial + local + accesible", "Showcase + FB 19.7k"],
  ];
  s.addTable(rows, {
    x: M, y: 1.75, w: W - 2 * M, colW: [2.7, 3.3, 3.6, 2.51], rowH: [0.45, 0.62, 0.62, 0.62, 0.7],
    fontFace: BFONT, fontSize: 12, color: "27324B", valign: "middle", align: "left",
    border: { pt: 0.5, color: "D8DCE4" }, autoPage: false,
  });
  // highlight last row via overlay accent
  s.addShape(p.shapes.RECTANGLE, { x: M, y: 1.75 + 0.45 + 0.62 * 3, w: 0.1, h: 0.7, fill: { color: ORANGE } });
  // hueco callout
  s.addShape(p.shapes.RECTANGLE, { x: M, y: 5.5, w: W - 2 * M, h: 1.35, fill: { color: INK }, shadow: mkShadow() });
  iconBadge(s, ic.map, M + 0.35, 5.85, 0.65, ORANGE);
  s.addText("El cuadrante vacío", { x: M + 1.25, y: 5.68, w: 4, h: 0.4, fontSize: 16, bold: true, color: ORANGE, fontFace: BFONT, margin: 0 });
  s.addText("Nadie combina respaldo institucional CAINCO + cercanía local + precio accesible. Manpower gana por escala, EY por prestigio, las boutiques por especialización. Ese cruce es el territorio de Acierta.", { x: M + 1.25, y: 6.08, w: W - 2 * M - 1.6, h: 0.7, fontSize: 12.5, color: "D7DBE6", fontFace: BFONT, margin: 0 });

  // ============ S4 — CONTEXTO MACRO ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 1 · Contexto"); title(s, "El contexto macro no es excusa: es el gancho");
  const stats = [
    ["20,4% \u2192 14-15%", "Inflación: cerró 2025 alta, baja en 2026"],
    ["Bs 11 \u2192 9,6", "Tipo de cambio en normalización"],
    ["-3,2%", "PIB proyectado 2026 (Banco Mundial)"],
  ];
  let sx = M, sw = 3.78, sgap = 0.3;
  stats.forEach(([n, l], i) => {
    const x = sx + i * (sw + sgap);
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.8, w: sw, h: 1.5, fill: { color: PANEL } });
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.8, w: sw, h: 0.09, fill: { color: ORANGE } });
    s.addText(n, { x: x + 0.05, y: 1.98, w: sw - 0.1, h: 0.72, fontSize: 30, bold: true, color: INK, fontFace: HFONT, align: "center", margin: 0 });
    s.addText(l, { x: x + 0.2, y: 2.72, w: sw - 0.4, h: 0.5, fontSize: 11.5, color: SLATE, fontFace: BFONT, align: "center", margin: 0 });
  });
  s.addText("Implicaciones que cambian la propuesta de valor:", { x: M, y: 3.65, w: 11, h: 0.4, fontSize: 14, bold: true, color: INK, fontFace: BFONT, margin: 0 });
  const ins = [
    ["Vende R&S como seguro", "Con caja apretada sube el miedo a un mal hire. R&S = costo evitado, en bolivianos."],
    ["La crisis activa lo olvidado", "Reestructuración, sucesión y planificación son más necesarias en recesión, no un lujo."],
    ["Data CEBEC = imán de leads", "En plena incertidumbre cambiaria, los datos confiables atraen al decisor B2B."],
  ];
  ins.forEach(([h, d], i) => {
    const x = sx + i * (sw + sgap);
    s.addShape(p.shapes.RECTANGLE, { x, y: 4.2, w: sw, h: 2.5, fill: { color: INK }, shadow: mkShadow() });
    s.addText((i + 1).toString(), { x: x + 0.28, y: 4.42, w: 0.7, h: 0.7, fontSize: 32, bold: true, color: ORANGE, fontFace: HFONT, margin: 0 });
    s.addText(h, { x: x + 0.3, y: 5.2, w: sw - 0.6, h: 0.6, fontSize: 14.5, bold: true, color: LIGHT, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: x + 0.3, y: 5.78, w: sw - 0.6, h: 0.85, fontSize: 11.5, color: "C7CCDA", fontFace: BFONT, margin: 0 });
  });

  // ============ S5 — ARQUITECTURA DE MARCA ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 2 · Marca"); title(s, "Arquitectura de marca: \u201CAcierta, by CAINCO\u201D");
  // endorsed model visual
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.95, w: 3.4, h: 1.5, fill: { color: PANEL }, rectRadius: 0.08, shadow: mkShadow() });
  s.addText("CAINCO", { x: M, y: 2.18, w: 3.4, h: 0.5, fontSize: 22, bold: true, color: INK, fontFace: HFONT, align: "center", margin: 0 });
  s.addText("El aval de confianza", { x: M, y: 2.72, w: 3.4, h: 0.4, fontSize: 12, color: SLATE, fontFace: BFONT, align: "center", margin: 0 });
  s.addText("+", { x: M + 3.45, y: 2.2, w: 0.7, h: 1.0, fontSize: 34, bold: true, color: ORANGE, fontFace: HFONT, align: "center", margin: 0 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M + 4.2, y: 1.95, w: 3.4, h: 1.5, fill: { color: INK }, rectRadius: 0.08, shadow: mkShadow() });
  s.addText("ACIERTA", { x: M + 4.2, y: 2.18, w: 3.4, h: 0.5, fontSize: 22, bold: true, color: ORANGE, fontFace: HFONT, align: "center", margin: 0 });
  s.addText("El especialista ágil y cercano", { x: M + 4.2, y: 2.72, w: 3.4, h: 0.4, fontSize: 12, color: "C7CCDA", fontFace: BFONT, align: "center", margin: 0 });
  // value prop quote
  s.addShape(p.shapes.RECTANGLE, { x: M + 8.0, y: 1.95, w: W - 2 * M - 8.0, h: 1.5, fill: { color: PANEL } });
  s.addShape(p.shapes.RECTANGLE, { x: M + 8.0, y: 1.95, w: 0.1, h: 1.5, fill: { color: ORANGE } });
  s.addText([{ text: "Diferenciación SIN orfandad: ", options: { bold: true, color: INK } }, { text: "personalidad propia que siempre firma con el respaldo CAINCO.", options: { color: SLATE } }], { x: M + 8.3, y: 2.1, w: W - 2 * M - 8.5, h: 1.2, fontSize: 13, fontFace: BFONT, valign: "middle", margin: 0 });
  // big value proposition
  s.addShape(p.shapes.RECTANGLE, { x: M, y: 3.75, w: W - 2 * M, h: 1.35, fill: { color: INK }, shadow: mkShadow() });
  s.addText("\u201CEl conocimiento del tejido empresarial de CAINCO, puesto a trabajar dentro de tu empresa.\u201D", { x: M + 0.5, y: 3.85, w: W - 2 * M - 1, h: 1.15, fontSize: 21, bold: true, italic: true, color: LIGHT, fontFace: HFONT, valign: "middle", align: "center", margin: 0 });
  // shift line
  s.addText("Territorio de marca:", { x: M, y: 5.45, w: 3, h: 0.4, fontSize: 13, bold: true, color: INK, fontFace: BFONT, margin: 0 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.85, w: 4.6, h: 0.75, fill: { color: PANEL }, rectRadius: 0.06 });
  s.addText("DE  \u201Cagencia que llena vacantes\u201D", { x: M + 0.2, y: 5.85, w: 4.2, h: 0.75, fontSize: 13, color: TERRA, bold: true, fontFace: BFONT, valign: "middle", margin: 0 });
  iconBadge(s, ic.bolt, M + 4.85, 5.93, 0.6, ORANGE);
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M + 5.7, y: 5.85, w: 6.4, h: 0.75, fill: { color: INK }, rectRadius: 0.06 });
  s.addText("A  \u201Csocio de gestión de personas y de negocio\u201D", { x: M + 5.9, y: 5.85, w: 6.0, h: 0.75, fontSize: 13, color: LIGHT, bold: true, fontFace: BFONT, valign: "middle", margin: 0 });

  // ============ S6 — OBJETIVOS SMART ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 2 · Plan"); title(s, "Dos objetivos SMART con métricas defendibles");
  const objs = [
    { ic: ic.target, t: "Objetivo 1 — Diversificar ingresos", goal: "Llevar las líneas no-core (Familiares, Planificación, Asesoría Económica) al 25% de los leads calificados en 6 meses.",
      ac: "Campaña temática mensual por línea · 1 webinar/mes con CEBEC · landing por servicio.",
      kp: "% leads no-core · nº leads por línea · inscritos a webinar" },
    { ic: ic.chart, t: "Objetivo 2 — Construir la medición", goal: "Implementar embudo medible (lead\u2192SQL\u2192cierre) y reportar CAC, conversión y ROI mensual desde el mes 2.",
      ac: "CRM (HubSpot free) · UTMs en todo enlace · 1 WhatsApp Business · dashboard mensual.",
      kp: "CAC por servicio · tasa lead\u2192cierre · ROI por campaña" },
  ];
  const ocw = 5.85;
  objs.forEach((o, i) => {
    const x = M + i * (ocw + 0.43);
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.8, w: ocw, h: 4.85, fill: { color: PANEL }, shadow: mkShadow() });
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.8, w: ocw, h: 0.09, fill: { color: ORANGE } });
    iconBadge(s, o.ic, x + 0.35, 2.05, 0.62, INK);
    s.addText(o.t, { x: x + 1.1, y: 2.12, w: ocw - 1.3, h: 0.5, fontSize: 16, bold: true, color: INK, fontFace: BFONT, valign: "middle", margin: 0 });
    s.addText(o.goal, { x: x + 0.4, y: 2.85, w: ocw - 0.8, h: 1.1, fontSize: 13, color: "27324B", italic: true, fontFace: BFONT, margin: 0 });
    s.addText("ACCIONES CLAVE", { x: x + 0.4, y: 4.05, w: ocw - 0.8, h: 0.3, fontSize: 11, bold: true, color: ORANGE, charSpacing: 2, fontFace: BFONT, margin: 0 });
    s.addText(o.ac, { x: x + 0.4, y: 4.35, w: ocw - 0.8, h: 0.9, fontSize: 12, color: SLATE, fontFace: BFONT, margin: 0 });
    s.addText("KPIs", { x: x + 0.4, y: 5.35, w: ocw - 0.8, h: 0.3, fontSize: 11, bold: true, color: ORANGE, charSpacing: 2, fontFace: BFONT, margin: 0 });
    s.addText(o.kp, { x: x + 0.4, y: 5.65, w: ocw - 0.8, h: 0.85, fontSize: 12, color: SLATE, fontFace: BFONT, margin: 0 });
  });
  s.addText("Baseline honesto hoy: 0 métricas. El punto de partida es construir el sistema, no maquillarlo.", { x: M, y: 6.85, w: W - 2 * M, h: 0.35, fontSize: 12, italic: true, bold: true, color: TERRA, fontFace: BFONT, align: "center", margin: 0 });

  // ============ S7 — LINKEDIN CONTENIDOS ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 2 · Contenidos"); title(s, "LinkedIn: 4 pilares de contenido + segmentación");
  const pillars = [
    ["Inteligencia\neconómica", "Data CEBEC: dólar, inflación, sector. Autoridad.", "1/sem"],
    ["Gestión de\npersonas", "Tips de selección, costo de un mal hire, cultura.", "1/sem"],
    ["Empresa familiar\n& estrategia", "Sucesión, gobierno, casos. Nicho premium.", "1/2 sem"],
    ["Prueba social\n& marca", "Casos de éxito, testimonios, equipo, CTA.", "1/2 sem"],
  ];
  const pw = 2.86, pgap = 0.3;
  pillars.forEach(([h, d, f], i) => {
    const x = M + i * (pw + pgap);
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.8, w: pw, h: 2.55, fill: { color: PANEL }, shadow: mkShadow() });
    s.addShape(p.shapes.OVAL, { x: x + 0.25, y: 2.0, w: 0.5, h: 0.5, fill: { color: ORANGE } });
    s.addText("P" + (i + 1), { x: x + 0.25, y: 2.0, w: 0.5, h: 0.5, fontSize: 15, bold: true, color: LIGHT, fontFace: HFONT, align: "center", valign: "middle", margin: 0 });
    s.addText(h, { x: x + 0.25, y: 2.62, w: pw - 0.5, h: 0.7, fontSize: 14.5, bold: true, color: INK, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: x + 0.25, y: 3.35, w: pw - 0.5, h: 0.7, fontSize: 11, color: SLATE, fontFace: BFONT, margin: 0 });
    s.addText(f, { x: x + 0.25, y: 4.02, w: pw - 0.5, h: 0.3, fontSize: 11, bold: true, color: ORANGE, fontFace: BFONT, margin: 0 });
  });
  s.addText([{ text: "Frecuencia: ", options: { bold: true, color: INK } }, { text: "3-4 posts/semana · carrusel de datos como formato estrella + 1 video experto/mes.", options: { color: SLATE } }], { x: M, y: 4.55, w: W - 2 * M, h: 0.4, fontSize: 13, fontFace: BFONT, margin: 0 });
  // segmentation
  s.addText("Segmentación de mensajes por perfil:", { x: M, y: 5.1, w: 11, h: 0.35, fontSize: 13, bold: true, color: INK, fontFace: BFONT, margin: 0 });
  const seg = [
    ["PYME / familiar", "Continuidad y orden \u2192 Empresa Familiar + Estructura"],
    ["Corporativo", "Talento clave y velocidad \u2192 R&S + Evaluaciones"],
    ["C-level / dueño", "Decidir mejor \u2192 Inteligencia Económica"],
    ["RRHH", "Perfiles + Outplacement"],
  ];
  seg.forEach(([h, d], i) => {
    const x = M + i * (pw + pgap);
    s.addShape(p.shapes.RECTANGLE, { x, y: 5.5, w: pw, h: 1.2, fill: { color: INK } });
    s.addText(h, { x: x + 0.2, y: 5.6, w: pw - 0.4, h: 0.35, fontSize: 12.5, bold: true, color: ORANGE, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: x + 0.2, y: 5.95, w: pw - 0.4, h: 0.7, fontSize: 10.5, color: "C7CCDA", fontFace: BFONT, margin: 0 });
  });

  // ============ S8 — QUICK WINS ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 3 · Quick wins"); title(s, "3 acciones de impacto en los primeros 60 días");
  const qw = [
    [ic.brand, "Unificar la identidad", "1 sola landing, 1 WhatsApp Business y encabezados consistentes \u201CAcierta by CAINCO\u201D.", "Claridad + medición · costo casi cero"],
    [ic.chart, "Lanzar \u201CPulso Económico\u201D", "Reporte/webinar mensual con data CEBEC sobre dólar e inflación.", "Capta leads B2B con un activo que ya existe"],
    [ic.trophy, "Activar prueba social", "Campaña de testimonios y reseñas + 3 mini-casos de éxito en LinkedIn.", "Convierte reputación en activo de venta"],
  ];
  const qcw = 3.85, qgap = 0.38;
  qw.forEach(([icn, h, d, foot], i) => {
    const x = M + i * (qcw + qgap);
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.9, w: qcw, h: 4.4, fill: { color: PANEL }, shadow: mkShadow() });
    s.addText((i + 1).toString(), { x: x + 0.25, y: 2.05, w: 1.2, h: 1.0, fontSize: 54, bold: true, color: "E2E5EC", fontFace: HFONT, margin: 0 });
    iconBadge(s, icn, x + qcw - 1.05, 2.2, 0.7, ORANGE);
    s.addText(h, { x: x + 0.35, y: 3.2, w: qcw - 0.7, h: 0.6, fontSize: 17, bold: true, color: INK, fontFace: BFONT, margin: 0 });
    s.addText(d, { x: x + 0.35, y: 3.85, w: qcw - 0.7, h: 1.2, fontSize: 12.5, color: SLATE, fontFace: BFONT, margin: 0 });
    s.addShape(p.shapes.LINE, { x: x + 0.35, y: 5.45, w: qcw - 0.7, h: 0, line: { color: "D2D6DF", width: 1 } });
    s.addText(foot, { x: x + 0.35, y: 5.55, w: qcw - 0.7, h: 0.6, fontSize: 11.5, italic: true, bold: true, color: GREEN, fontFace: BFONT, margin: 0 });
  });

  // ============ S9 — ROADMAP ============
  s = p.addSlide(); s.background = { color: LIGHT };
  kicker(s, "Eje 3 · Hoja de ruta"); title(s, "Cronograma de 6 meses: hitos principales");
  const months = [
    ["M1", "Diagnóstico, auditoría, unificación de identidad y setup de CRM/UTMs."],
    ["M2", "Lanzamiento \u201CPulso Económico\u201D + parrilla LinkedIn + 1er dashboard a Gerencia."],
    ["M3", "Campaña de testimonios/casos + landings por servicio."],
    ["M4", "Campaña foco línea no-core #1: Empresa Familiar + webinar."],
    ["M5", "Campaña no-core #2: Planificación/Estructura \u201Cresiliencia en crisis\u201D."],
    ["M6", "Medición, optimización y reporte semestral con CAC/conversión/ROI."],
  ];
  const tlY = 3.7, n = months.length, usableW = W - 2 * M, step = usableW / n;
  s.addShape(p.shapes.LINE, { x: M + step / 2, y: tlY, w: usableW - step, h: 0, line: { color: "C9CEDA", width: 2 } });
  months.forEach(([m, d], i) => {
    const cx = M + step / 2 + i * step;
    const up = i % 2 === 0;
    // node
    s.addShape(p.shapes.OVAL, { x: cx - 0.42, y: tlY - 0.42, w: 0.84, h: 0.84, fill: { color: INK }, shadow: mkShadow() });
    s.addText(m, { x: cx - 0.42, y: tlY - 0.42, w: 0.84, h: 0.84, fontSize: 17, bold: true, color: ORANGE, fontFace: HFONT, align: "center", valign: "middle", margin: 0 });
    // card
    const cy = up ? tlY - 1.95 : tlY + 0.65;
    s.addShape(p.shapes.RECTANGLE, { x: cx - step / 2 + 0.15, y: cy, w: step - 0.3, h: 1.3, fill: { color: PANEL } });
    s.addShape(p.shapes.RECTANGLE, { x: cx - step / 2 + 0.15, y: cy, w: step - 0.3, h: 0.07, fill: { color: ORANGE } });
    s.addText(d, { x: cx - step / 2 + 0.3, y: cy + 0.15, w: step - 0.6, h: 1.05, fontSize: 11, color: "27324B", fontFace: BFONT, valign: "middle", margin: 0 });
    // connector
    s.addShape(p.shapes.LINE, { x: cx, y: up ? cy + 1.3 : tlY + 0.42, w: 0, h: up ? (tlY - 0.42 - (cy + 1.3)) : (cy - (tlY + 0.42)), line: { color: "C9CEDA", width: 1 } });
  });

  // ============ S10 — CRITERIOS DE ÉXITO (closing) ============
  s = p.addSlide(); s.background = { color: INK };
  s.addShape(p.shapes.OVAL, { x: -1.8, y: 4.6, w: 5.0, h: 5.0, fill: { color: "232C49" } });
  s.addText("CÓMO MEDIMOS EL ÉXITO", { x: M, y: 0.55, w: 11, h: 0.35, fontSize: 13, bold: true, color: ORANGE, charSpacing: 3, fontFace: BFONT, margin: 0 });
  s.addText("3 criterios para una Gerencia que exige datos", { x: M, y: 0.95, w: 12, h: 0.8, fontSize: 30, bold: true, color: LIGHT, fontFace: HFONT, margin: 0 });
  const crit = [
    ["Diversificación", "\u226525% de los leads calificados provienen de líneas no-core (hoy: dependencia del core)."],
    ["Sistema medible operando", "CAC, conversión y ROI reportados cada mes (hoy: 0 métricas)."],
    ["Eficiencia en crisis", "Costo por lead a la baja, con marketing mayoritariamente orgánico — defendible ante la escasez de divisas."],
  ];
  let cy2 = 2.15;
  crit.forEach(([h, d], i) => {
    s.addShape(p.shapes.OVAL, { x: M, y: cy2, w: 0.95, h: 0.95, fill: { color: ORANGE } });
    s.addText((i + 1).toString(), { x: M, y: cy2, w: 0.95, h: 0.95, fontSize: 36, bold: true, color: INK, fontFace: HFONT, align: "center", valign: "middle", margin: 0 });
    s.addText(h, { x: M + 1.3, y: cy2 + 0.02, w: 10.5, h: 0.5, fontSize: 20, bold: true, color: LIGHT, fontFace: HFONT, margin: 0 });
    s.addText(d, { x: M + 1.3, y: cy2 + 0.5, w: 10.8, h: 0.6, fontSize: 13.5, color: "C7CCDA", fontFace: BFONT, margin: 0 });
    cy2 += 1.45;
  });
  s.addShape(p.shapes.LINE, { x: M, y: 6.75, w: 2.2, h: 0, line: { color: ORANGE, width: 2.5 } });
  s.addText("Acierta by CAINCO — del marketing reactivo al crecimiento medible.", { x: M, y: 6.9, w: 12, h: 0.35, fontSize: 13, italic: true, color: "8E96AC", fontFace: BFONT, margin: 0 });

  const path = require("path");
  const outFile = path.join(__dirname, "output", "Plan_Marketing_Acierta_CAINCO.pptx");
  await p.writeFile({ fileName: outFile });
  console.log("OK deck escrito →", outFile);
})();
