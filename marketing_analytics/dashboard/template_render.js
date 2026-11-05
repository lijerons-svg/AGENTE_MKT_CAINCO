/* ---------- KPIs ---------- */
function agruparPorMoneda(ads) {
  const grupos = {};
  ads.forEach((r) => {
    const moneda = r.moneda || 'N/D';
    grupos[moneda] = grupos[moneda] || { gasto: 0, clics: 0 };
    grupos[moneda].gasto += Number(r.importe_gastado) || 0;
    grupos[moneda].clics += Number(r.clics) || 0;
  });
  return grupos;
}

function renderKPIs(slice) {
  const cont = document.getElementById('kpis');
  cont.textContent = '';

  const alcanceOrganico = sum(slice.organico, 'alcance');
  const alcanceAds = sum(slice.ads, 'alcance');
  const impresionesAds = sum(slice.ads, 'impresiones');
  const engagement = sum(slice.organico, 'total_interacciones');
  const clicsAds = sum(slice.ads, 'clics');
  const resultadosAds = sum(slice.ads, 'resultados');
  const ctr = impresionesAds > 0 ? (clicsAds / impresionesAds) * 100 : 0;
  const aperturasMailchimp = sum(slice.mailchimp, 'aperturas_totales');
  const clicsMailchimp = sum(slice.mailchimp, 'clics_totales');
  const porMoneda = agruparPorMoneda(slice.ads);
  const monedas = Object.keys(porMoneda);

  const tiles = [
    { etiqueta: 'Alcance (orgánico + pauta)', valor: fmtNum.format(alcanceOrganico + alcanceAds) },
    { etiqueta: 'Impresiones (pauta)', valor: fmtNum.format(impresionesAds) },
    { etiqueta: 'Engagement (orgánico)', valor: fmtNum.format(engagement), nota: 'Reacciones + comentarios + compartidos' },
    { etiqueta: 'CTR (pauta)', valor: fmtDec.format(ctr) + '%' },
    { etiqueta: 'Resultados (pauta)', valor: fmtNum.format(resultadosAds) },
    { etiqueta: 'Aperturas Mailchimp', valor: fmtNum.format(aperturasMailchimp) },
    { etiqueta: 'Clics Mailchimp', valor: fmtNum.format(clicsMailchimp) },
  ];

  if (monedas.length <= 1) {
    const moneda = monedas[0] || '';
    const g = porMoneda[moneda] || { gasto: 0, clics: 0 };
    tiles.splice(4, 0, { etiqueta: 'Gasto (pauta)', valor: fmtDec.format(g.gasto) + (moneda ? ' ' + moneda : '') });
    tiles.splice(4, 0, {
      etiqueta: 'CPC (pauta)',
      valor: g.clics > 0 ? fmtDec.format(g.gasto / g.clics) + (moneda ? ' ' + moneda : '') : '—',
    });
  } else {
    const detalleGasto = monedas.map((m) => `${fmtDec.format(porMoneda[m].gasto)} ${m}`).join(' · ');
    const detalleCpc = monedas
      .map((m) => `${porMoneda[m].clics > 0 ? fmtDec.format(porMoneda[m].gasto / porMoneda[m].clics) : '—'} ${m}`)
      .join(' · ');
    tiles.splice(4, 0, { etiqueta: 'Gasto (pauta)', valor: detalleGasto, multi: true, nota: 'Monedas mezcladas: no se suman entre sí' });
    tiles.splice(4, 0, { etiqueta: 'CPC (pauta)', valor: detalleCpc, multi: true, nota: 'Una cifra por moneda' });
  }

  tiles.forEach((t) => {
    const div = document.createElement('div');
    div.className = 'kpi';
    const etq = document.createElement('div');
    etq.className = 'etiqueta';
    etq.textContent = t.etiqueta;
    const val = document.createElement('div');
    val.className = 'valor' + (t.multi ? ' multi' : '');
    val.textContent = t.valor;
    div.appendChild(etq);
    div.appendChild(val);
    if (t.nota) {
      const nota = document.createElement('div');
      nota.className = 'nota';
      nota.textContent = t.nota;
      div.appendChild(nota);
    }
    cont.appendChild(div);
  });
}

/* ---------- comparativo Meta vs LinkedIn ---------- */
function renderComparativo(slice) {
  const interaccionesMeta = sum(slice.organico, 'total_interacciones');
  const interaccionesLinkedin = sum(slice.linkedin, 'interacciones');

  const trazo = {
    x: ['Meta', 'LinkedIn'],
    y: [interaccionesMeta, interaccionesLinkedin],
    type: 'bar',
    marker: { color: [COLOR.meta_organico, COLOR.linkedin] },
    hovertemplate: '%{x}: %{y:,.0f} interacciones<extra></extra>',
  };

  Plotly.react('chart-comparativo', [trazo], layoutBase({ yaxis: { title: 'Interacciones' } }), plotlyConfig());

  const nota = document.getElementById('nota-linkedin');
  nota.textContent =
    slice.linkedin.length === 0
      ? 'LinkedIn: conector pendiente de aprobación por parte de LinkedIn (Community Management API). Se muestra en 0 hasta que se active — no es un dato real medido.'
      : '';
}

/* ---------- evolución ---------- */
function agregarSerieTemporal(filas, claveFecha, claveValor, granularidad) {
  const claveFn = granularidad === 'dia' ? (f) => f : granularidad === 'semana' ? claveSemana : claveMes;
  const acumulado = {};
  filas.forEach((f) => {
    if (!f[claveFecha]) return;
    const clave = claveFn(f[claveFecha]);
    acumulado[clave] = (acumulado[clave] || 0) + (Number(f[claveValor]) || 0);
  });
  const claves = Object.keys(acumulado).sort();
  return { x: claves, y: claves.map((c) => acumulado[c]) };
}

const METRICA_EVOLUCION = {
  organico_alcance: { fuente: 'organico', campo: 'alcance', color: COLOR.meta_organico },
  organico_interacciones: { fuente: 'organico', campo: 'total_interacciones', color: COLOR.meta_organico },
  ads_gasto: { fuente: 'ads', campo: 'importe_gastado', color: COLOR.meta_ads },
  ads_clics: { fuente: 'ads', campo: 'clics', color: COLOR.meta_ads },
  ads_resultados: { fuente: 'ads', campo: 'resultados', color: COLOR.meta_ads },
  mailchimp_aperturas: { fuente: 'mailchimp', campo: 'aperturas_totales', color: COLOR.mailchimp },
  mailchimp_clics: { fuente: 'mailchimp', campo: 'clics_totales', color: COLOR.mailchimp },
};

function renderEvolucion(slice) {
  const metricaId = document.getElementById('evo-metrica').value;
  const granularidad = document.getElementById('evo-granularidad').value;
  const spec = METRICA_EVOLUCION[metricaId];
  const filas = slice[spec.fuente];

  const serie = agregarSerieTemporal(filas, 'fecha', spec.campo, granularidad);

  const trazo = {
    x: serie.x,
    y: serie.y,
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: spec.color, width: 2 },
    marker: { size: 6 },
    hovertemplate: '%{x}: %{y:,.2f}<extra></extra>',
  };

  Plotly.react('chart-evolucion', [trazo], layoutBase({ xaxis: { title: 'Fecha' } }), plotlyConfig());
}

/* ---------- tops ---------- */
function renderTopPublicaciones(slice) {
  const top = [...slice.organico].sort((a, b) => b.total_interacciones - a.total_interacciones).slice(0, 10);
  const etiquetas = top.map((r) => `${r.perfil} · ${r.fecha}`);

  const trazo = {
    x: top.map((r) => r.total_interacciones),
    y: etiquetas,
    type: 'bar',
    orientation: 'h',
    marker: { color: COLOR.meta_organico },
    hovertemplate: '%{y}: %{x:,.0f} interacciones<extra></extra>',
  };
  Plotly.react(
    'chart-top-publicaciones',
    [trazo],
    layoutBase({ xaxis: { title: 'Interacciones' }, margin: { l: 220 } }),
    plotlyConfig(),
  );

  renderTablaDetalle(top);
}

function renderTopCampanas(slice) {
  const top = [...slice.ads].sort((a, b) => b.resultados - a.resultados).slice(0, 10);
  const etiquetas = top.map((r) => `${r.campana} (${r.moneda})`);

  const trazo = {
    x: top.map((r) => r.resultados),
    y: etiquetas,
    type: 'bar',
    orientation: 'h',
    marker: { color: COLOR.meta_ads },
    hovertemplate: '%{y}: %{x:,.0f} resultados<extra></extra>',
  };
  Plotly.react(
    'chart-top-campanas',
    [trazo],
    layoutBase({ xaxis: { title: 'Resultados' }, margin: { l: 220 } }),
    plotlyConfig(),
  );
}

function renderTopPerfiles(slice) {
  const acumulado = {};
  slice.organico.forEach((r) => {
    acumulado[r.perfil] = (acumulado[r.perfil] || 0) + (Number(r.total_interacciones) || 0);
  });
  const top = Object.entries(acumulado)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const trazo = {
    x: top.map(([, v]) => v),
    y: top.map(([k]) => k),
    type: 'bar',
    orientation: 'h',
    marker: { color: COLOR.meta_organico },
    hovertemplate: '%{y}: %{x:,.0f} interacciones<extra></extra>',
  };
  Plotly.react(
    'chart-top-perfiles',
    [trazo],
    layoutBase({ xaxis: { title: 'Interacciones acumuladas' }, margin: { l: 180 } }),
    plotlyConfig(),
  );
}

/* ---------- tabla de detalle (accesibilidad: equivalente en tabla) ---------- */
function renderTablaDetalle(filas) {
  const cont = document.getElementById('tabla-detalle-organico');
  cont.textContent = '';
  const tabla = document.createElement('table');
  tabla.className = 'tabla-detalle';

  const encabezados = ['Perfil', 'Página', 'Red', 'Fecha', 'Tipo', 'Alcance', 'Interacciones'];
  const thead = document.createElement('thead');
  const trEnc = document.createElement('tr');
  encabezados.forEach((h) => {
    const th = document.createElement('th');
    th.textContent = h;
    trEnc.appendChild(th);
  });
  thead.appendChild(trEnc);
  tabla.appendChild(thead);

  const tbody = document.createElement('tbody');
  filas.forEach((r) => {
    const tr = document.createElement('tr');
    [r.perfil, r.pagina, r.red, r.fecha, r.tipo].forEach((valor) => {
      const td = document.createElement('td');
      td.textContent = valor;
      tr.appendChild(td);
    });
    [r.alcance, r.total_interacciones].forEach((valor) => {
      const td = document.createElement('td');
      td.className = 'num';
      td.textContent = fmtNum.format(valor);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tabla.appendChild(tbody);
  cont.appendChild(tabla);
}

/* ---------- layout compartido de Plotly ---------- */
function layoutBase(extra) {
  const fondo = getComputedStyleVar('--surface-1');
  const textoSecundario = getComputedStyleVar('--text-secondary');
  const grid = getComputedStyleVar('--gridline');
  return Object.assign(
    {
      paper_bgcolor: fondo,
      plot_bgcolor: fondo,
      font: { color: textoSecundario, family: 'system-ui, -apple-system, "Segoe UI", sans-serif' },
      margin: { t: 20, r: 20, b: 40, l: 60 },
      xaxis: { gridcolor: grid, zerolinecolor: grid },
      yaxis: { gridcolor: grid, zerolinecolor: grid },
      showlegend: false,
    },
    extra,
  );
}

function plotlyConfig() {
  return { responsive: true, displaylogo: false };
}
