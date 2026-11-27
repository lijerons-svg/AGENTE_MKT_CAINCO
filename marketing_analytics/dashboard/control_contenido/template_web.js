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

/* Nombres de canal tal como los agrupa GA4 ("Default channel group") —
   siempre en inglés, no configurable desde acá. Se traducen solo para
   mostrar; cualquier canal nuevo que GA4 agregue y no esté en este mapa
   se muestra tal cual (en inglés) en vez de romper. */
const WEB_CANAL_ES = {
  'Direct': 'Directo',
  'Organic Search': 'Búsqueda orgánica',
  'Organic Social': 'Redes sociales orgánicas',
  'Paid Social': 'Redes sociales pagas',
  'Paid Search': 'Búsqueda paga',
  'Organic Video': 'Video orgánico',
  'Paid Video': 'Video pago',
  'Display': 'Display',
  'Affiliates': 'Afiliados',
  'Email': 'Email',
  'Referral': 'Referidos',
  'Audio': 'Audio',
  'SMS': 'SMS',
  'Mobile Push Notifications': 'Notificaciones push',
  'Organic Shopping': 'Shopping orgánico',
  'Paid Shopping': 'Shopping pago',
  'Cross-network': 'Red cruzada',
  'Paid Other': 'Pago (otro)',
  'Unassigned': 'Sin asignar',
  'AI Assistant': 'Asistente de IA',
  'AI Overview': 'Resumen de IA',
  'AI Search': 'Búsqueda con IA',
};

function webCanalEs(canal) {
  return WEB_CANAL_ES[canal] || canal;
}

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
  return filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
}

function webFiltrarPagina(filas) {
  return estado.paginaWeb ? filas.filter((f) => f.pagina === estado.paginaWeb) : filas;
}

function webCanalesFiltrados() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.canales || []);
  const porPeriodo = filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
  return webFiltrarPagina(porPeriodo);
}

function webEventosFiltrados() {
  const porUnidad = webFiltrarUnidad(DATA.ga4.eventos || []);
  const porPeriodo = filtrarPorAnioMes(porUnidad, 'fecha', estado.aniosWeb, estado.mesesWeb);
  return webFiltrarPagina(porPeriodo).filter((f) => WEB_EVENTOS_CTA.includes(f.evento));
}

function renderFiltrosWeb() {
  renderChips('chips-unidad-web', webValoresUnidad(), estado.unidadesWeb, () => renderWeb());
  const todasLasFilas = DATA.ga4.diarias || [];
  const anios = [...new Set(todasLasFilas.map((f) => anioDe(f.fecha)))].filter(Boolean).sort();
  const meses = [...new Set(todasLasFilas.map((f) => mesDe(f.fecha)))].filter(Boolean).sort();
  dropdownMultiple('drop-anio-web', anios, estado.aniosWeb, () => renderWeb(), null, 'Todos');
  dropdownMultiple('drop-mes-web', meses, estado.mesesWeb, () => renderWeb(), (m) => MES_CORTO[Number(m) - 1] || m, 'Todos');
  renderFiltroPaginaWeb();
}

/* Se elige con el buscador de arriba (autocompletar, ver
   renderSugerenciasPaginaWeb) o haciendo clic en una fila de "Páginas más
   visitadas" (ver renderTablaWebPaginas) — acá solo se muestra la
   selección actual, con una "x" para sacarla. */
function renderFiltroPaginaWeb() {
  const cont = document.getElementById('filtro-pagina-web');
  if (!cont) return;
  cont.textContent = '';
  if (!estado.paginaWeb) {
    cont.innerHTML = '<span class="vacio" style="padding:0">Ninguna página seleccionada</span>';
    return;
  }
  const chip = document.createElement('button');
  chip.type = 'button';
  chip.className = 'chip-filtro activo';
  chip.textContent = estado.paginaWeb + ' ✕';
  chip.addEventListener('click', () => {
    estado.paginaWeb = null;
    renderWeb();
  });
  cont.appendChild(chip);
}

/* Autocompletar: no hay forma práctica de mostrar cientos de páginas como
   chips, así que se escribe y se eligen las coincidencias más cercanas de
   una lista acotada — mismo mecanismo visual que dropdownMultiple
   (.dropdown-panel/.dropdown-opcion), pero manejado a mano acá porque no
   es una selección múltiple sino autocompletar + elegir una sola. */
function renderSugerenciasPaginaWeb(filtro) {
  const panel = document.getElementById('sugerencias-pagina-web');
  if (!panel) return;
  panel.textContent = '';

  if (!filtro) {
    panel.classList.remove('visible');
    return;
  }

  const todasLasPaginas = [...new Set((DATA.ga4.paginas || []).map((f) => f.pagina))];
  const coincidencias = todasLasPaginas.filter((p) => p.toLowerCase().includes(filtro)).sort().slice(0, 8);

  if (!coincidencias.length) {
    panel.innerHTML = '<div class="dropdown-opcion" style="cursor:default">Sin resultados</div>';
  } else {
    coincidencias.forEach((pagina) => {
      const opcion = document.createElement('div');
      opcion.className = 'dropdown-opcion';
      opcion.textContent = pagina;
      opcion.addEventListener('click', () => {
        estado.paginaWeb = pagina;
        document.getElementById('buscar-pagina-web').value = '';
        panel.classList.remove('visible');
        renderWeb();
      });
      panel.appendChild(opcion);
    });
  }
  panel.classList.add('visible');
}

function renderKpisWeb(diarias, paginas, eventos) {
  const cont = document.getElementById('kpis-web');
  if (!cont) return;
  cont.textContent = '';

  // Con una página seleccionada, Sesiones/Usuarios/Usuarios nuevos/Vistas
  // de página pasan a ser SOLO de esa página (el dato por página de GA4
  // ya trae estas 4 métricas).
  const paginaSeleccionada = estado.paginaWeb ? paginas.filter((f) => f.pagina === estado.paginaWeb) : null;
  const fuente = paginaSeleccionada || diarias;

  kpi(cont, 'Sesiones', fmtNum.format(sum(fuente, 'sesiones')));
  kpi(cont, 'Usuarios', fmtNum.format(sum(fuente, 'usuarios_totales')));
  kpi(cont, 'Usuarios nuevos', fmtNum.format(sum(fuente, 'usuarios_nuevos')));
  kpi(cont, 'Vistas de página', fmtNum.format(sum(paginaSeleccionada || paginas, 'vistas_pagina')));
  // `eventos` ya viene filtrado por la página seleccionada (ver
  // webEventosFiltrados), así que esta suma también es solo de esa página.
  kpi(cont, 'Interacciones (CTA)', fmtNum.format(sum(eventos, 'conteo')), {
    info: 'Suma de clics en botones de contacto/consultas/ecommerce, formularios enviados, descargas y clics a links externos — no incluye vistas de página ni otros eventos automáticos de medición.',
  });
}

function renderChartWebEvolucion(diarias, paginas) {
  // Con una página seleccionada, el gráfico pasa a mostrar la evolución de
  // ESA página puntual (ej. una landing), no el total del sitio.
  const fuente = estado.paginaWeb ? paginas.filter((f) => f.pagina === estado.paginaWeb) : diarias;
  const subtitulo = document.getElementById('subtitulo-evolucion-web');
  if (subtitulo) {
    subtitulo.textContent = estado.paginaWeb
      ? `Por día, solo para "${estado.paginaWeb}".`
      : 'Por día, dentro del período filtrado.';
  }

  const porDia = {};
  fuente.forEach((f) => {
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
  const subtitulo = document.getElementById('subtitulo-canales-web');
  if (subtitulo) {
    subtitulo.textContent = estado.paginaWeb
      ? `Sesiones por canal de adquisición, solo para "${estado.paginaWeb}".`
      : 'Sesiones por canal de adquisición.';
  }

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
      y: filas.map((f) => webCanalEs(f[0])),
      text: filas.map((f) => fmtNum.format(f[1])),
      textposition: 'auto',
      marker: { color: getComputedStyleVar('--accent') },
    }],
    { xaxis: { title: 'Sesiones' } },
    'Sin datos de canal en el período filtrado.',
  );
}

function renderTablaWebEventos(eventos) {
  const subtitulo = document.getElementById('subtitulo-eventos-web');
  if (subtitulo) {
    subtitulo.textContent = estado.paginaWeb
      ? `Clics, formularios y descargas, solo para "${estado.paginaWeb}".`
      : 'Clics, formularios y descargas del período filtrado.';
  }

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
    {
      ordenInicial: 'sesiones',
      dirInicial: 'desc',
      onFilaClick: (fila) => {
        estado.paginaWeb = estado.paginaWeb === fila.pagina ? null : fila.pagina; // clic de nuevo = deseleccionar
        renderWeb();
      },
      esFilaActiva: (fila) => fila.pagina === estado.paginaWeb,
    },
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
  renderChartWebEvolucion(diarias, paginas);
  renderChartWebCanales(canales);
  renderTablaWebEventos(eventos);
  renderTablaWebPaginas(paginas);
}
