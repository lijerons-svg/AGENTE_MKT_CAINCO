/* Análisis: KPIs, gráficos y tablas responden a los mismos tres filtros de
   arriba — unidad, año y mes. Los gráficos de evolución también se recortan
   al período elegido: mostrar el histórico completo cuando el usuario
   filtró un mes contradice lo que pidió. */

function renderAnalisis() {
  renderChips('chips-unidad-analisis', unidadesConDatos(), estado.unidades, alCambiarFiltros);
  dropdownMultiple('drop-anio-analisis', ANIOS_DISPONIBLES, estado.anios, alCambiarFiltros);
  dropdownMultiple('drop-mes-analisis', MESES_DISPONIBLES, estado.meses, alCambiarFiltros, (m) => NOMBRES_MES[Number(m) - 1] || m);

  const organicoBase = filasDeUnidades('meta_organico');
  const adsBase = filasDeUnidades('meta_ads');

  let organico = filtrarPorAnioMes(organicoBase, 'fecha', estado.anios, estado.meses);
  let organicoPrevio = periodoAnterior(organicoBase, 'fecha', estado.anios, estado.meses);
  let ads = filtrarPorAnioMes(adsBase, 'fecha', estado.anios, estado.meses);
  let adsPrevio = periodoAnterior(adsBase, 'fecha', estado.anios, estado.meses);
  if (estado.busquedaAds) {
    const filtroCampana = (c) => (c.campana || '').toLowerCase().includes(estado.busquedaAds);
    ads = ads.filter(filtroCampana);
    adsPrevio = adsPrevio.filter(filtroCampana);
    // Un post orgánico no tiene un campo de "campaña" propio (no es pauta) —
    // se busca el mismo término en el texto de la publicación, para poder
    // ver el movimiento orgánico de un lanzamiento aunque ahí no exista
    // formalmente como campaña.
    const filtroTexto = (p) => (p.descripcion || '').toLowerCase().includes(estado.busquedaAds);
    organico = organico.filter(filtroTexto);
    organicoPrevio = organicoPrevio.filter(filtroTexto);
  }

  const unidadesTexto = estado.unidades.size ? [...estado.unidades].join(' · ') : 'todas las unidades';
  const notaBusqueda = estado.busquedaAds
    ? ` · Buscando "${estado.busquedaAds}" (en campaña de pauta y en texto de publicaciones orgánicas)`
    : '';
  document.getElementById('nota-organico').textContent =
    `${unidadesTexto} · ${etiquetaPeriodo(estado.anios, estado.meses)}${notaBusqueda}. ` +
    'Las variaciones comparan contra el período inmediatamente anterior de la misma extensión.';

  renderKpisOrganico(organico, organicoPrevio);
  renderChartOrganico(organico);
  renderChartFormatos(organico);
  renderDetalleOrganico(organico);

  renderKpisAds(ads, adsPrevio);
  renderChartAds(ads);
  renderDetalleAds(ads);
}

/* Texto único para explicar el engagement: aparece en el KPI del período y
   en la tabla de detalle, y tiene que decir exactamente lo mismo en ambos. */
const INFO_ENGAGEMENT = [
  '<strong>Cómo se calcula</strong>',
  '<code>engagement = interacciones ÷ visualizaciones × 100</code>',
  'Donde <strong>interacciones</strong> = reacciones + comentarios + compartidos, tal como los informa Meta por publicación.',
  '<br><strong>Por qué sobre visualizaciones y no sobre alcance</strong><br>',
  'Meta dejó de informar el alcance orgánico de Facebook (devuelve 0 aunque la publicación tenga miles de visualizaciones), ',
  'así que usarlo daría porcentajes falsos en la mayoría de las publicaciones.',
  '<br><br>Es un cálculo de este tablero: no coincide exactamente con el "engagement" que muestra Business Suite, que usa su propia definición.',
].join('');

/* ---------- orgánico ---------- */
function renderKpisOrganico(filas, previas) {
  const cont = document.getElementById('kpis-analisis-organico');
  cont.textContent = '';

  const fb = filas.filter((p) => clasePlataforma(p.red) === 'facebook');
  const ig = filas.filter((p) => clasePlataforma(p.red) === 'instagram');
  const repartoTexto = filas.length
    ? `${fmtDec1.format(pct(fb.length, filas.length))}% Facebook · ${fmtDec1.format(pct(ig.length, filas.length))}% Instagram`
    : 'Sin publicaciones';

  const vistas = sum(filas, 'visualizaciones');
  const interacciones = sum(filas, 'total_interacciones');
  const vistasPrev = sum(previas, 'visualizaciones');
  const interaccionesPrev = sum(previas, 'total_interacciones');

  const conVistas = filas.filter((p) => p.visualizaciones > 0);
  const engMedio = conVistas.length ? conVistas.reduce((a, p) => a + engagementPost(p), 0) / conVistas.length : 0;
  const conVistasPrev = previas.filter((p) => p.visualizaciones > 0);
  const engMedioPrev = conVistasPrev.length ? conVistasPrev.reduce((a, p) => a + engagementPost(p), 0) / conVistasPrev.length : 0;

  // Frecuencia: publicaciones por semana dentro del rango real de fechas
  // cubierto por el filtro (no por semanas calendario completas).
  const fechas = filas.map((p) => p.fecha).sort();
  const semanas = fechas.length
    ? Math.max(1, (new Date(fechas[fechas.length - 1]) - new Date(fechas[0])) / (7 * 86400000))
    : 1;

  kpi(cont, 'Publicaciones', fmtNum.format(filas.length), {
    delta: variacion(filas.length, previas.length),
    nota: repartoTexto,
  });
  kpi(cont, 'Visualizaciones', fmtNum.format(vistas), {
    delta: variacion(vistas, vistasPrev),
    nota: `Promedio ${fmtNum.format(filas.length ? Math.round(vistas / filas.length) : 0)} por publicación`,
  });
  kpi(cont, 'Interacciones', fmtNum.format(interacciones), {
    delta: variacion(interacciones, interaccionesPrev),
    nota: `Promedio ${fmtNum.format(filas.length ? Math.round(interacciones / filas.length) : 0)} por publicación`,
  });
  kpi(cont, 'Engagement medio', fmtDec.format(engMedio) + '%', {
    delta: variacion(engMedio, engMedioPrev),
    nota: 'Promedio del engagement de cada publicación',
    info: INFO_ENGAGEMENT,
  });
  kpi(cont, 'Frecuencia', fmtDec1.format(filas.length / semanas), {
    nota: 'Publicaciones por semana en el período',
    info:
      'Cuántas publicaciones por semana se hicieron dentro del período filtrado.' +
      '<code>publicaciones ÷ semanas entre la primera y la última</code>' +
      'Se cuentan las semanas realmente cubiertas por las publicaciones, no las del mes calendario.',
  });
}

function renderChartOrganico(filas) {
  const porMes = {};
  filas.forEach((p) => {
    const m = claveMes(p.fecha);
    const acc = (porMes[m] = porMes[m] || { vistas: 0, interacciones: 0, n: 0 });
    acc.vistas += Number(p.visualizaciones) || 0;
    acc.interacciones += Number(p.total_interacciones) || 0;
    acc.n += 1;
  });
  const meses = Object.keys(porMes).sort();

  graficar(
    'chart-organico',
    [
      {
        x: meses.map(mesLegible),
        y: meses.map((m) => porMes[m].vistas),
        name: 'Visualizaciones',
        type: 'bar',
        marker: { color: getComputedStyleVar('--cainco-azul') },
      },
      {
        x: meses.map(mesLegible),
        y: meses.map((m) => porMes[m].interacciones),
        name: 'Interacciones',
        type: 'scatter',
        mode: 'lines+markers',
        yaxis: 'y2',
        line: { color: getComputedStyleVar('--cainco-naranja'), width: 3 },
        marker: { size: 7 },
      },
    ],
    {
      margin: { t: 10, r: 56, b: 40, l: 60 },
      yaxis: { title: 'Visualizaciones' },
      yaxis2: { title: 'Interacciones', overlaying: 'y', side: 'right', gridcolor: 'rgba(0,0,0,0)' },
    },
  );
}

/* Formato vs. engagement: la barra dice cuánto se publica de cada formato y
   el punto dice cuánto rinde. Juntos responden "¿estamos publicando lo que
   funciona?", que es la pregunta útil. */
function renderChartFormatos(filas) {
  const porFormato = {};
  filas.forEach((p) => {
    const f = formatoPost(p);
    const acc = (porFormato[f] = porFormato[f] || { n: 0, eng: [] });
    acc.n += 1;
    if (p.visualizaciones > 0) acc.eng.push(engagementPost(p));
  });
  const formatos = Object.keys(porFormato).sort((a, b) => porFormato[b].n - porFormato[a].n);

  graficar(
    'chart-formatos',
    [
      {
        x: formatos,
        y: formatos.map((f) => porFormato[f].n),
        name: 'Publicaciones',
        type: 'bar',
        marker: { color: getComputedStyleVar('--cainco-azul') },
      },
      {
        x: formatos,
        y: formatos.map((f) =>
          porFormato[f].eng.length ? porFormato[f].eng.reduce((a, b) => a + b, 0) / porFormato[f].eng.length : 0,
        ),
        name: 'Engagement medio',
        type: 'scatter',
        mode: 'markers',
        yaxis: 'y2',
        marker: { size: 13, color: getComputedStyleVar('--cainco-naranja'), symbol: 'diamond' },
        hovertemplate: '%{x}: %{y:.2f}%<extra></extra>',
      },
    ],
    {
      margin: { t: 10, r: 56, b: 40, l: 50 },
      yaxis: { title: 'Publicaciones' },
      yaxis2: { title: 'Engagement', overlaying: 'y', side: 'right', ticksuffix: '%', gridcolor: 'rgba(0,0,0,0)' },
    },
  );
}

function renderDetalleOrganico(filas) {
  const conEngagement = filas.map((p) =>
    Object.assign({}, p, {
      _engagement: engagementPost(p),
      _formato: formatoPost(p),
      _red: NOMBRE_PLATAFORMA[clasePlataforma(p.red)] || p.red,
      _fecha: fechaLegible(p.fecha),
    }),
  );

  tablaInteractiva(
    'detalle-organico',
    conEngagement,
    [
      { clave: 'fecha', etiqueta: 'Fecha', render: (f) => f._fecha },
      {
        clave: '_red',
        etiqueta: 'Red',
        render: (f) => pillRed(f.red),
      },
      { clave: '_formato', etiqueta: 'Formato' },
      { clave: 'perfil', etiqueta: 'Perfil' },
      { clave: 'descripcion', etiqueta: 'Descripción', largo: true },
      { clave: 'visualizaciones', etiqueta: 'Visualizaciones', tipo: 'num' },
      { clave: 'total_interacciones', etiqueta: 'Interacciones', tipo: 'num' },
      { clave: 'comentarios', etiqueta: 'Comentarios', tipo: 'num' },
      { clave: 'compartidos', etiqueta: 'Compartidos', tipo: 'num' },
      { clave: '_engagement', etiqueta: 'Engagement', tipo: 'pct' },
    ],
    {
      // Sin buscador propio: el único buscador de la pestaña es el de
      // "Campaña" de la barra de filtros de arriba, para no tener dos cajas
      // de búsqueda con alcance distinto compitiendo por la misma pestaña.
      porPagina: 15,
      ordenInicial: 'fecha',
      dirInicial: 'desc',
      filtros: [
        { clave: '_red', etiqueta: 'Todas las redes' },
        { clave: '_formato', etiqueta: 'Todos los formatos' },
        { clave: 'perfil', etiqueta: 'Todos los perfiles' },
      ],
    },
  );
}

/* ---------- Meta Ads ---------- */
/* En campañas de reconocimiento Meta define "Resultados" como el alcance
   mismo, así que dividirlo por clics da porcentajes absurdos (se vieron
   88.000%). La tasa de conversión solo se calcula sobre campañas cuyo
   objetivo sí es una acción (tráfico, leads, ventas, mensajes). */
const OBJETIVOS_DE_ALCANCE = ['OUTCOME_AWARENESS', 'REACH', 'BRAND_AWARENESS'];

function esObjetivoDeAlcance(objetivo) {
  return OBJETIVOS_DE_ALCANCE.includes((objetivo || '').toUpperCase());
}

function agregadosAds(filas) {
  const gasto = sum(filas, 'importe_gastado');
  const impresiones = sum(filas, 'impresiones');
  const alcance = sum(filas, 'alcance');
  const clics = sum(filas, 'clics');
  const resultados = sum(filas, 'resultados');

  const accionables = filas.filter((r) => !esObjetivoDeAlcance(r.objetivo));
  const clicsAcc = sum(accionables, 'clics');
  const resultadosAcc = sum(accionables, 'resultados');
  const gastoAcc = sum(accionables, 'importe_gastado');

  const objetivos = [...new Set(filas.map((r) => r.objetivo).filter(Boolean))];

  return {
    gasto,
    impresiones,
    alcance,
    clics,
    resultados,
    objetivos,
    soloAlcance: filas.length > 0 && accionables.length === 0,
    ctr: pct(clics, impresiones),
    cpc: clics > 0 ? gasto / clics : 0,
    cpm: impresiones > 0 ? (gasto / impresiones) * 1000 : 0,
    // Frecuencia: cuántas veces vio el anuncio, en promedio, cada persona
    // alcanzada. Por encima de ~3 suele indicar saturación de la audiencia.
    frecuencia: alcance > 0 ? impresiones / alcance : 0,
    conversion: clicsAcc > 0 ? pct(resultadosAcc, clicsAcc) : null,
    costoResultado: resultadosAcc > 0 ? gastoAcc / resultadosAcc : resultados > 0 ? gasto / resultados : 0,
    monedas: [...new Set(filas.map((r) => r.moneda).filter(Boolean))],
  };
}

/* Importes chicos (costo por resultado de campañas masivas) se van a 0 con
   dos decimales; se muestran con la precisión que haga falta para que el
   número siga diciendo algo. */
function fmtMoneda(valor) {
  const v = Number(valor) || 0;
  if (v !== 0 && Math.abs(v) < 0.01) return v.toFixed(4).replace('.', ',');
  return fmtDec.format(v);
}

/* Símbolo en vez de la columna "Moneda" aparte — con una sola cuenta
   publicitaria casi siempre es la misma moneda en todas las filas, así que
   una columna entera para eso era ancho de más; el símbolo alcanza y es
   más legible en el propio número. Si aparece una moneda sin símbolo
   conocido, se muestra su código tal cual (nunca se oculta el dato). */
const SIMBOLO_MONEDA = { USD: '$', BOB: 'Bs' };
function fmtInversionConSimbolo(f) {
  const simbolo = SIMBOLO_MONEDA[(f.moneda || '').toUpperCase()] || f.moneda || '';
  return `${simbolo} ${fmtMoneda(f.gasto)}`.trim();
}

function renderKpisAds(filas, previas) {
  const a = agregadosAds(filas);
  const p = agregadosAds(previas);
  const sufijo = a.monedas.length === 1 ? ' ' + a.monedas[0] : '';
  const notaMoneda = a.monedas.length > 1 ? 'Monedas mezcladas: valor sin convertir' : null;

  const progreso = document.getElementById('kpis-analisis-ads-progreso');
  progreso.textContent = '';
  kpi(progreso, 'Inversión', fmtMoneda(a.gasto) + sufijo, {
    delta: variacion(a.gasto, p.gasto),
    nota: notaMoneda || 'Total gastado en el período',
  });
  kpi(progreso, 'Impresiones', fmtNum.format(a.impresiones), {
    delta: variacion(a.impresiones, p.impresiones),
    nota: 'Veces que se mostró el anuncio',
  });
  kpi(progreso, 'Alcance', fmtNum.format(a.alcance), {
    delta: variacion(a.alcance, p.alcance),
    nota: 'Personas distintas alcanzadas',
  });
  kpi(progreso, 'Frecuencia', fmtDec.format(a.frecuencia), {
    delta: variacion(a.frecuencia, p.frecuencia),
    invertir: true,
    nota: 'Impresiones por persona. Sobre 3 suele saturar',
  });
  kpi(progreso, 'CPM', a.impresiones ? fmtMoneda(a.cpm) + sufijo : '—', {
    delta: variacion(a.cpm, p.cpm),
    invertir: true,
    nota: notaMoneda || 'Costo por mil impresiones',
  });

  const conversion = document.getElementById('kpis-analisis-ads-conversion');
  conversion.textContent = '';
  kpi(conversion, 'Clics', fmtNum.format(a.clics), {
    delta: variacion(a.clics, p.clics),
    nota: 'Clics totales sobre el anuncio',
  });
  kpi(conversion, 'CTR', fmtDec.format(a.ctr) + '%', {
    delta: variacion(a.ctr, p.ctr),
    nota: 'Clics sobre impresiones',
  });
  kpi(conversion, 'CPC', a.clics ? fmtMoneda(a.cpc) + sufijo : '—', {
    delta: variacion(a.cpc, p.cpc),
    invertir: true,
    nota: notaMoneda || 'Costo por clic',
  });
  kpi(conversion, 'Resultados', fmtNum.format(a.resultados), {
    delta: variacion(a.resultados, p.resultados),
    nota: a.soloAlcance
      ? 'Objetivo de reconocimiento: el resultado es el alcance'
      : 'Según el objetivo de cada campaña',
  });
  kpi(conversion, 'Tasa de conversión', a.conversion === null ? 'No aplica' : fmtDec.format(a.conversion) + '%', {
    delta: a.conversion === null ? null : variacion(a.conversion, p.conversion),
    chico: a.conversion === null,
    nota: a.conversion === null
      ? 'Todas las campañas del período buscan alcance, no una acción medible'
      : 'Resultados sobre clics, solo en campañas orientadas a acción',
  });
  kpi(conversion, 'Costo por resultado', a.resultados ? fmtMoneda(a.costoResultado) + sufijo : '—', {
    delta: variacion(a.costoResultado, p.costoResultado),
    invertir: true,
    nota: notaMoneda || 'Inversión dividida por resultados',
  });
}

/* Antes eran tres series diarias superpuestas con doble eje, ilegibles con
   cientos de puntos. Ahora se agrega por mes: barras de inversión, barras
   de clics y el CTR como línea — que es la lectura de eficiencia. */
function renderChartAds(filas) {
  const porMes = {};
  filas.forEach((c) => {
    const m = claveMes(c.fecha);
    const acc = (porMes[m] = porMes[m] || { gasto: 0, clics: 0, impresiones: 0 });
    acc.gasto += Number(c.importe_gastado) || 0;
    acc.clics += Number(c.clics) || 0;
    acc.impresiones += Number(c.impresiones) || 0;
  });
  const meses = Object.keys(porMes).sort();

  graficar(
    'chart-ads',
    [
      {
        x: meses.map(mesLegible),
        y: meses.map((m) => porMes[m].gasto),
        name: 'Inversión',
        type: 'bar',
        marker: { color: getComputedStyleVar('--cainco-azul') },
      },
      {
        x: meses.map(mesLegible),
        y: meses.map((m) => porMes[m].clics),
        name: 'Clics',
        type: 'bar',
        marker: { color: getComputedStyleVar('--cainco-cian') },
      },
      {
        x: meses.map(mesLegible),
        y: meses.map((m) => pct(porMes[m].clics, porMes[m].impresiones)),
        name: 'CTR',
        type: 'scatter',
        mode: 'lines+markers',
        yaxis: 'y2',
        line: { color: getComputedStyleVar('--cainco-verde'), width: 3 },
        marker: { size: 7 },
        hovertemplate: 'CTR %{y:.2f}%<extra></extra>',
      },
    ],
    {
      barmode: 'group',
      margin: { t: 10, r: 56, b: 40, l: 60 },
      yaxis: { title: 'Inversión / clics' },
      yaxis2: { title: 'CTR', overlaying: 'y', side: 'right', ticksuffix: '%', gridcolor: 'rgba(0,0,0,0)' },
    },
    'Sin campañas de pauta en el período seleccionado.',
  );
}

function campanasAgrupadas(filas) {
  // Se agrupa por campaña + red, no solo por campaña: una campaña con
  // ubicación automática (Facebook + Instagram) es, contablemente, dos
  // inversiones separadas — mezclarlas en una sola fila esconde cuánto se
  // gastó realmente en cada red.
  const porCampana = {};
  filas.forEach((c) => {
    const clave = c.campana + '|' + c.red;
    const acc = (porCampana[clave] = porCampana[clave] || {
      campana: c.campana,
      red: c.red,
      moneda: c.moneda,
      objetivo: c.objetivo,
      gasto: 0, impresiones: 0, alcance: 0, clics: 0, resultados: 0, conversaciones: 0,
      // Fechas de la campaña (constantes para todas sus filas diarias), no
      // algo que tenga sentido sumar.
      fechaInicio: c.fecha_inicio_campana || null,
      fechaFin: c.fecha_fin_campana || null,
    });
    acc.gasto += Number(c.importe_gastado) || 0;
    acc.impresiones += Number(c.impresiones) || 0;
    acc.alcance += Number(c.alcance) || 0;
    acc.clics += Number(c.clics) || 0;
    acc.resultados += Number(c.resultados) || 0;
    acc.conversaciones += Number(c.conversaciones_iniciadas) || 0;
  });
  return Object.values(porCampana).map((c) =>
    Object.assign(c, {
      cpc: c.clics > 0 ? c.gasto / c.clics : 0,
      frecuencia: c.alcance > 0 ? c.impresiones / c.alcance : 0,
    }),
  );
}

/* Meta usa decenas de códigos de objetivo internos para lo mismo que Ads
   Manager muestra con un nombre legible — se traduce acá solo para mostrar;
   uno no mapeado se muestra tal cual (nunca se oculta un dato). */
const OBJETIVO_LEGIBLE = {
  OUTCOME_TRAFFIC: 'Tráfico', LINK_CLICKS: 'Tráfico',
  OUTCOME_LEADS: 'Leads', LEAD_GENERATION: 'Leads',
  OUTCOME_SALES: 'Ventas', CONVERSIONS: 'Ventas',
  OUTCOME_ENGAGEMENT: 'Interacción', POST_ENGAGEMENT: 'Interacción',
  OUTCOME_AWARENESS: 'Reconocimiento', BRAND_AWARENESS: 'Reconocimiento', REACH: 'Alcance',
  MESSAGES: 'Mensajes',
  OUTCOME_APP_PROMOTION: 'Promoción de app',
};

function objetivoLegible(objetivo) {
  return OBJETIVO_LEGIBLE[(objetivo || '').toUpperCase()] || objetivo || '—';
}

/* dd/mm, no el "1 jul 2026" de fechaLegible (compartida con el resto del
   tablero) — pedido puntual para esta columna, más corto y fácil de leer
   de un vistazo en una tabla con muchas columnas numéricas. */
function fechaCorta(fechaISO) {
  if (!fechaISO) return null;
  const [, m, d] = fechaISO.slice(0, 10).split('-');
  return `${d}/${m}`;
}

/* Fecha inicio y fin van juntas en una sola columna ("01/07 – 31/07") para
   que la tabla entre en pantalla sin scroll horizontal — separar cada una
   no suma información, solo ancho. */
function vigenciaCampana(f) {
  if (!f.fechaInicio && !f.fechaFin) return '—';
  const inicio = fechaCorta(f.fechaInicio) || '—';
  const fin = f.fechaFin ? fechaCorta(f.fechaFin) : 'en curso';
  return `${inicio} – ${fin}`;
}


function renderDetalleAds(filas) {
  const campanas = campanasAgrupadas(filas);
  agregarInfo(
    document.getElementById('subtitulo-campanas'),
    '<strong>Cómo se leen los colores</strong>' +
      `<code>Frecuencia — ${REFERENCIAS.frecuencia.texto}</code>` +
      'El resto de las columnas no lleva color: no existe una referencia de industria comparable ' +
      'entre monedas y objetivos distintos, así que pintarlas daría una señal falsa.',
  );

  tablaInteractiva(
    'detalle-ads',
    campanas,
    [
      {
        clave: 'campana', etiqueta: 'Campaña', largo: true,
        info: 'Nombre de la campaña tal cual está en Meta Ads Manager.',
      },
      {
        clave: 'red', etiqueta: 'Red', render: (f) => (f.red ? pillRed(f.red) : '—'),
        info: 'Red donde se mostró el anuncio (Facebook, Instagram, Audience Network, etc.), según el desglose de Meta.',
      },
      {
        clave: 'gasto', etiqueta: 'Inversión', tipo: 'moneda', render: fmtInversionConSimbolo,
        info: 'Monto gastado en esta campaña durante el período filtrado, con el símbolo de su moneda de facturación.',
      },
      {
        clave: 'impresiones', etiqueta: 'Impr.', tipo: 'num',
        info: '<strong>Impresiones</strong> — veces que el anuncio se mostró en pantalla. Una misma persona puede verlo más de una vez.',
      },
      {
        clave: 'alcance', etiqueta: 'Alcance', tipo: 'num',
        info: 'Personas distintas que vieron el anuncio al menos una vez.',
      },
      {
        clave: 'frecuencia',
        etiqueta: 'Frec.',
        tipo: 'moneda',
        render: (f) => celdaNivel('frecuencia', f.frecuencia, fmtDec.format(f.frecuencia)),
        info: `<strong>Frecuencia</strong> — Impresiones ÷ Alcance: cuántas veces vio el anuncio, en promedio, cada persona alcanzada. ${REFERENCIAS.frecuencia.texto}`,
      },
      {
        clave: 'clics', etiqueta: 'Clics', tipo: 'num',
        info: '<strong>Todos</strong> los clics del anuncio (me gusta, comentarios, compartir, ver foto, clic al link, etc.) — no solo el clic final al destino.',
      },
      {
        clave: 'cpc', etiqueta: 'CPC', tipo: 'moneda', render: (f) => fmtMoneda(f.cpc),
        info: '<strong>CPC</strong> — Inversión ÷ Clics: costo promedio de cada clic (de cualquier tipo, ver columna "Clics").',
      },
      {
        clave: 'objetivo', etiqueta: 'Objetivo', render: (f) => objetivoLegible(f.objetivo),
        info: 'El objetivo configurado para la campaña en Meta Ads Manager (tráfico, mensajes, leads, ventas, reconocimiento, etc.).',
      },
      {
        clave: 'conversaciones', etiqueta: 'Convers.', tipo: 'num',
        info: '<strong>Conversación iniciada</strong> — clics reales en "Enviar mensaje" que abren WhatsApp, Messenger o Instagram Direct. Se cuenta siempre, sin importar el objetivo de la campaña.',
      },
      {
        // `clave` apunta a la fecha de inicio real (ordenable); el texto
        // combinado con la fecha de fin se arma aparte, solo para mostrar.
        clave: 'fechaInicio', etiqueta: 'Vigencia', render: vigenciaCampana,
        info: 'Fecha de inicio y fin con las que se programó la campaña en Meta Ads Manager (no el día puntual de esta fila). "En curso" si no tiene fecha de fin configurada.',
      },
    ],
    {
      // La búsqueda por campaña ya vive arriba, en la barra de filtros
      // (afecta también los KPIs y el gráfico, no solo esta tabla).
      porPagina: 15,
      ordenInicial: 'gasto',
      dirInicial: 'desc',
      claseExtra: 'tabla-compacta',
    },
  );
}
