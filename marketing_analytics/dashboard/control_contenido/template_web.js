/* ---------- WEB (Google Analytics 4) ----------
   Lee DATA.ga4 (diarias/paginas/canales/eventos — ver
   data_builder.py:_construir_datos_ga4). "Unidad" acá es un sitio/propiedad
   (ej. "CAINCO Sitio Principal"), no un perfil de Facebook/Instagram, así
   que los filtros son propios de este tab (no comparten estado con
   Análisis/Mailchimp), aunque sí reusan filtrarPorAnioMes porque, a
   diferencia de ROI, esto es tráfico día a día real. */

/* Eventos que valen la pena mostrar como "interacción" (CTA): el resto de
   lo que manda GA4 automáticamente (page_view, session_start, scroll,
   user_engagement, video_*, etc.) es ruido de medición, no una acción real
   de la persona. Ajustar esta lista si el sitio instrumenta eventos
   nuevos — no hace falta tocar nada más del código. */
const WEB_EVENTOS_CTA = [
  'contact_link_click', 'btn_consultas', 'icono_ecommerce_click',
  'form_submit', 'file_download', 'outbound_link_click',
];

function webValoresUnidad() {
  return [...new Set((DATA.ga4.diarias || []).map((f) => f.unidad).filter(Boolean))].sort();
}

function webFiltrarUnidad(filas) {
  return estado.unidadesWeb.size ? filas.filter((f) => estado.unidadesWeb.has(f.unidad)) : filas;
}

function webDiariasFiltradas() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.diarias || []);
  return filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
}

function webPaginasFiltradas() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.paginas || []);
  const porPeriodo = filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
  if (!estado.busquedaWeb) return porPeriodo;
  return porPeriodo.filter((f) => String(f.pagina || '').toLowerCase().includes(estado.busquedaWeb));
}

function webCanalesFiltrados() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.canales || []);
  return filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
}

function webEventosFiltrados() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.eventos || []);
  const porPeriodo = filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
  return porPeriodo.filter((f) => WEB_EVENTOS_CTA.includes(f.evento));
}

function renderFiltrosWeb() {
  renderChips('chips-unidad-web', webValoresUnidad(), estado.unidadesWeb, () => renderWeb());
  const todasLasFilas = DATA.ga4.diarias || [];
  const anios = [...new Set(todasLasFilas.map((f) => anioDe(f.fecha)))].filter(Boolean).sort();
  const meses = [...new Set(todasLasFilas.map((f) => mesDe(f.fecha)))].filter(Boolean).sort();
  dropdownMultiple('drop-anio-web', anios, estado.aniosWeb, () => renderWeb(), null, 'Todos');
  dropdownMultiple('drop-mes-web', meses, estado.mesesWeb, () => renderWeb(), (m) => MES_CORTO[Number(m) - 1] || m, 'Todos');
}

function renderKpisWeb(diarias, paginas, eventos) {
  const cont = document.getElementById('kpis-web');
  if (!cont) return;
  cont.textContent = '';

  kpi(cont, 'Sesiones', fmtNum.format(sum(diarias, 'sesiones')));
  kpi(cont, 'Usuarios', fmtNum.format(sum(diarias, 'usuarios_totales')));
  kpi(cont, 'Usuarios nuevos', fmtNum.format(sum(diarias, 'usuarios_nuevos')));
  kpi(cont, 'Vistas de página', fmtNum.format(sum(paginas, 'vistas_pagina')));
  kpi(cont, 'Interacciones (CTA)', fmtNum.format(sum(eventos, 'conteo')), {
    info: 'Suma de clics en botones de contacto/consultas/ecommerce, formularios enviados, descargas y clics a links externos — no incluye vistas de página ni otros eventos automáticos de medición.',
  });
}

function renderChartWebEvolucion(diarias) {
  const porDia = {};
  diarias.forEach((f) => {
    porDia[f.fecha] = (porDia[f.fecha] || 0) + (Number(f.sesiones) || 0);
  });
  const fechas = Object.keys(porDia).sort();

  graficar(
    'chart-web-evolucion',
    [{
      type: 'scatter',
      mode: 'lines',
      line: { shape: 'spline', smoothing: 0.4, width: 3, color: getComputedStyleVar('--accent') },
      fill: 'tozeroy',
      x: fechas,
      y: fechas.map((f) => porDia[f]),
    }],
    {},
    'Sin sesiones en el período filtrado.',
  );
}

function renderChartWebCanales(canales) {
  const porCanal = {};
  canales.forEach((f) => {
    porCanal[f.canal] = (porCanal[f.canal] || 0) + (Number(f.sesiones) || 0);
  });
  const filas = Object.entries(porCanal).sort((a, b) => a[1] - b[1]); // asc: Plotly dibuja de abajo hacia arriba

  graficar(
    'chart-web-canales',
    [{
      type: 'bar',
      orientation: 'h',
      x: filas.map((f) => f[1]),
      y: filas.map((f) => f[0]),
      marker: { color: getComputedStyleVar('--accent') },
    }],
    { xaxis: { title: 'Sesiones' } },
    'Sin datos de canal en el período filtrado.',
  );
}

function renderTablaWebEventos(eventos) {
  const porEvento = {};
  eventos.forEach((f) => {
    porEvento[f.evento] = (porEvento[f.evento] || 0) + (Number(f.conteo) || 0);
  });
  const filas = Object.entries(porEvento).map(([evento, conteo]) => ({ evento, conteo }));

  tablaInteractiva(
    'tabla-web-eventos',
    filas,
    [
      { clave: 'evento', etiqueta: 'Evento' },
      { clave: 'conteo', etiqueta: 'Veces', tipo: 'num' },
    ],
    { ordenInicial: 'conteo', dirInicial: 'desc', porPagina: 10 },
  );
}

function renderTablaWebPaginas(paginas) {
  const porPagina = {};
  paginas.forEach((f) => {
    const clave = `${f.unidad}|${f.pagina}`;
    const acc = porPagina[clave] || { unidad: f.unidad, pagina: f.pagina, sesiones: 0, vistas_pagina: 0 };
    acc.sesiones += Number(f.sesiones) || 0;
    acc.vistas_pagina += Number(f.vistas_pagina) || 0;
    porPagina[clave] = acc;
  });
  const filas = Object.values(porPagina);

  tablaInteractiva(
    'tabla-web-paginas',
    filas,
    [
      { clave: 'pagina', etiqueta: 'Página', largo: true },
      { clave: 'unidad', etiqueta: 'Sitio' },
      { clave: 'sesiones', etiqueta: 'Sesiones', tipo: 'num' },
      { clave: 'vistas_pagina', etiqueta: 'Vistas', tipo: 'num' },
    ],
    { ordenInicial: 'sesiones', dirInicial: 'desc' },
  );
}

function renderWeb() {
  if (!DATA.ga4) return; // corridas viejas, antes de este tab, no traen la clave
  renderFiltrosWeb();
  const diarias = webDiariasFiltradas();
  const paginas = webPaginasFiltradas();
  const canales = webCanalesFiltrados();
  const eventos = webEventosFiltrados();

  renderKpisWeb(diarias, paginas, eventos);
  renderChartWebEvolucion(diarias);
  renderChartWebCanales(canales);
  renderTablaWebEventos(eventos);
  renderTablaWebPaginas(paginas);
}
