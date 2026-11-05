/* Mailchimp. Los KPIs se agrupan en tasas (cómo rindió) y volúmenes
   (cuánto se movió), porque son dos lecturas distintas: una compara
   períodos y la otra dimensiona el esfuerzo. */

function renderMailchimp() {
  const todas = DATA.mailchimp || [];
  dropdownMultiple('drop-anio-mailchimp', ANIOS_DISPONIBLES, estado.anios, alCambiarFiltros);
  dropdownMultiple('drop-mes-mailchimp', MESES_DISPONIBLES, estado.meses, alCambiarFiltros, (m) => NOMBRES_MES[Number(m) - 1] || m);

  const titulo = document.getElementById('titulo-mailchimp');
  if (titulo && !titulo.querySelector('.icono-plataforma')) {
    titulo.insertAdjacentHTML('afterbegin', iconoPlataforma('mailchimp', 'grande'));
  }

  // El filtro de unidad existe en las otras dos pestañas, pero la API de
  // campañas de Mailchimp no asocia cada envío a una unidad de negocio: no
  // hay dato con el cual filtrar. Se deja el lugar del filtro con la
  // explicación, en vez de un control que aparente funcionar y no haga nada.
  const contUnidad = document.getElementById('chips-unidad-mailchimp');
  if (contUnidad) {
    contUnidad.innerHTML =
      '<span class="vacio" style="padding:0">No aplica: Mailchimp no asocia los envíos a una unidad. Los datos son globales de la organización.</span>';
  }

  let filas = filtrarPorAnioMes(todas, 'fecha', estado.anios, estado.meses);
  let previas = periodoAnterior(todas, 'fecha', estado.anios, estado.meses);
  if (estado.busquedaMailchimp) {
    const filtroCampana = (m) => (m.nombre_campana || '').toLowerCase().includes(estado.busquedaMailchimp);
    filas = filas.filter(filtroCampana);
    previas = previas.filter(filtroCampana);
  }

  renderKpisMailchimp(filas, previas);
  renderEmbudoMailchimp(filas);
  renderTablaMailchimp(filas);
}

function agregadosMailchimp(filas) {
  const destinatarios = sum(filas, 'destinatarios');
  const entregas = sum(filas, 'entregas');
  const aperturasUnicas = sum(filas, 'aperturas_unicas');
  const clicsUnicos = sum(filas, 'clics_unicos');
  const clicsTotales = sum(filas, 'clics_totales');
  const rebotes = sum(filas, 'rebotes');
  const bajas = sum(filas, 'bajas');
  const clicsWhatsapp = sum(filas, 'clics_whatsapp');
  return {
    envios: filas.length,
    destinatarios,
    entregas,
    aperturasUnicas,
    clicsUnicos,
    clicsTotales,
    rebotes,
    bajas,
    clicsWhatsapp,
    openRate: pct(aperturasUnicas, entregas),
    clickRate: pct(clicsUnicos, entregas),
    ctor: pct(clicsUnicos, aperturasUnicas),
    bounceRate: pct(rebotes, destinatarios),
    bajaRate: pct(bajas, entregas),
    entregaRate: pct(entregas, destinatarios),
  };
}

function renderKpisMailchimp(filas, previas) {
  const a = agregadosMailchimp(filas);
  const p = agregadosMailchimp(previas);
  const cont = document.getElementById('kpis-mailchimp');
  cont.textContent = '';

  kpi(cont, 'Open Rate', fmtDec.format(a.openRate) + '%', {
    delta: variacion(a.openRate, p.openRate),
    nota: 'Aperturas únicas sobre entregados',
    plataforma: 'mailchimp',
    nivelRef: nivel('openRate', a.openRate),
    info: infoReferencia('openRate', 'aperturas únicas ÷ entregados × 100'),
  });
  kpi(cont, 'Click Rate', fmtDec.format(a.clickRate) + '%', {
    delta: variacion(a.clickRate, p.clickRate),
    nota: 'Clics únicos sobre entregados',
    nivelRef: nivel('clickRate', a.clickRate),
    info: infoReferencia('clickRate', 'clics únicos ÷ entregados × 100'),
  });
  kpi(cont, 'CTOR', fmtDec.format(a.ctor) + '%', {
    delta: variacion(a.ctor, p.ctor),
    nota: 'De los que abrieron, cuántos hicieron clic',
    nivelRef: nivel('ctor', a.ctor),
    info: infoReferencia('ctor', 'clics únicos ÷ aperturas únicas × 100'),
  });
  kpi(cont, 'Bounce Rate', fmtDec.format(a.bounceRate) + '%', {
    delta: variacion(a.bounceRate, p.bounceRate),
    invertir: true,
    nota: 'Correos rebotados sobre enviados',
    nivelRef: nivel('bounceRate', a.bounceRate),
    info: infoReferencia('bounceRate', 'rebotes ÷ enviados × 100'),
  });
  kpi(cont, 'Tasa de bajas', fmtDec.format(a.bajaRate) + '%', {
    delta: variacion(a.bajaRate, p.bajaRate),
    invertir: true,
    nota: `${fmtNum.format(a.bajas)} desuscripciones en el período`,
    nivelRef: nivel('bajaRate', a.bajaRate),
    info: infoReferencia('bajaRate', 'bajas ÷ entregados × 100'),
  });
  kpi(cont, 'Envíos', fmtNum.format(a.envios), {
    delta: variacion(a.envios, p.envios),
    nota: 'Campañas enviadas en el período',
  });
  kpi(cont, 'Entregados', fmtNum.format(a.entregas), {
    delta: variacion(a.entregas, p.entregas),
    nota: `${fmtDec1.format(a.entregaRate)}% de los ${fmtNum.format(a.destinatarios)} enviados`,
  });
  kpi(cont, 'Clics al WhatsApp', fmtNum.format(a.clicsWhatsapp), {
    delta: variacion(a.clicsWhatsapp, p.clicsWhatsapp),
    nota: `${fmtDec1.format(pct(a.clicsWhatsapp, a.clicsTotales))}% de los clics totales`,
  });
}

/* Embudo horizontal: enviados → entregados → abiertos → clics, cada paso
   con su porcentaje de retención. Reemplaza al gráfico de destinatarios vs.
   bajas, que mezclaba dos escalas sin relación entre sí. */
function renderEmbudoMailchimp(filas) {
  const a = agregadosMailchimp(filas);
  const pasos = [
    ['Enviados', a.destinatarios, null],
    ['Entregados', a.entregas, a.destinatarios],
    ['Abiertos', a.aperturasUnicas, a.entregas],
    ['Con clic', a.clicsUnicos, a.aperturasUnicas],
    ['Bajas', a.bajas, a.entregas],
  ];
  if (!a.destinatarios) {
    graficar('chart-mailchimp-embudo', [], {}, 'Sin envíos en el período seleccionado.');
    return;
  }

  const colores = [
    getComputedStyleVar('--cainco-azul-claro'),
    getComputedStyleVar('--cainco-azul-claro'),
    getComputedStyleVar('--cainco-cian'),
    getComputedStyleVar('--cainco-verde'),
    getComputedStyleVar('--salud-rojo'),
  ];

  graficar(
    'chart-mailchimp-embudo',
    [
      {
        y: pasos.map(([n]) => n).reverse(),
        x: pasos.map(([, v]) => v).reverse(),
        customdata: pasos.map(([, v, base]) => (base ? fmtDec1.format(pct(v, base)) + '% del paso anterior' : 'base')).reverse(),
        type: 'bar',
        orientation: 'h',
        marker: { color: colores.reverse() },
        text: pasos.map(([, v]) => fmtNum.format(v)).reverse(),
        textposition: 'auto',
        hovertemplate: '%{y}: %{x:,}<br>%{customdata}<extra></extra>',
      },
    ],
    { showlegend: false, margin: { t: 10, r: 20, b: 40, l: 90 } },
  );
}

function renderTablaMailchimp(filas) {
  const conTasas = filas.map((c) =>
    Object.assign({}, c, {
      _fecha: fechaLegible(c.fecha),
      openRate: pct(c.aperturas_unicas, c.entregas),
      clickRate: pct(c.clics_unicos, c.entregas),
      ctor: pct(c.clics_unicos, c.aperturas_unicas),
      nombre: c.nombre_campana || '(sin nombre)',
    }),
  );

  agregarInfo(
    document.getElementById('subtitulo-campanas-mailchimp'),
    '<strong>Cómo se leen los colores</strong>' +
      `<code>Open Rate — ${REFERENCIAS.openRate.texto}</code>` +
      `<code>Click Rate — ${REFERENCIAS.clickRate.texto}</code>` +
      `<code>CTOR — ${REFERENCIAS.ctor.texto}</code>` +
      'Se comparan contra promedios publicados de email marketing, no contra tus otros envíos.',
  );

  tablaInteractiva(
    'tabla-mailchimp',
    conTasas,
    [
      { clave: 'nombre', etiqueta: 'Campaña', largo: true },
      { clave: 'fecha', etiqueta: 'Fecha', render: (f) => f._fecha },
      { clave: 'entregas', etiqueta: 'Entregados', tipo: 'num' },
      {
        clave: 'openRate',
        etiqueta: 'Open Rate',
        tipo: 'pct',
        render: (f) => celdaNivel('openRate', f.openRate, fmtDec.format(f.openRate) + '%'),
      },
      {
        clave: 'clickRate',
        etiqueta: 'Click Rate',
        tipo: 'pct',
        render: (f) => celdaNivel('clickRate', f.clickRate, fmtDec.format(f.clickRate) + '%'),
      },
      {
        clave: 'ctor',
        etiqueta: 'CTOR',
        tipo: 'pct',
        render: (f) => celdaNivel('ctor', f.ctor, fmtDec.format(f.ctor) + '%'),
      },
      { clave: 'clics_totales', etiqueta: 'Clics', tipo: 'num' },
      { clave: 'clics_whatsapp', etiqueta: 'Clics WhatsApp', tipo: 'num' },
      { clave: 'bajas', etiqueta: 'Bajas', tipo: 'num' },
    ],
    {
      // La búsqueda por campaña ya vive arriba, en la barra de filtros
      // (afecta también los KPIs y el embudo, no solo esta tabla).
      porPagina: 15,
      ordenInicial: 'fecha',
      dirInicial: 'desc',
    },
  );
}
