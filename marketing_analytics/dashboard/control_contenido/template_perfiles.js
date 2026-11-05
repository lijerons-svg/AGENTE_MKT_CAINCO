/* Control de Perfiles: la unidad se elige con chips (no dropdown) y las
   métricas que ya viven en Análisis no se repiten acá — esta pestaña
   responde "cómo está compuesta y cómo evoluciona la unidad", no "cuánto
   rindió el contenido". */

function renderPerfiles() {
  if (!estado.unidadPerfiles || !DATA.unidades[estado.unidadPerfiles]) {
    estado.unidadPerfiles = UNIDADES[0] || null;
  }
  renderChipsUnico('chips-unidad-perfiles', UNIDADES, estado.unidadPerfiles, (u) => {
    estado.unidadPerfiles = u;
    renderPerfiles();
  });
  if (!estado.unidadPerfiles) return;

  const datos = DATA.unidades[estado.unidadPerfiles];
  document.getElementById('titulo-unidad-perfiles').textContent = estado.unidadPerfiles;

  renderTarjetasPerfil(datos);
  renderComparacionRedes(datos);
  renderEvolucionSeguidores(datos);
  renderRankingUnidades();
  renderHistoricoUnidad(datos);
}

function renderTarjetasPerfil(datos) {
  const cont = document.getElementById('lista-perfiles-unidad');
  cont.textContent = '';
  if (!datos.perfiles.length) {
    cont.innerHTML = '<p class="vacio">Sin perfiles configurados para esta unidad.</p>';
    return;
  }

  const ultimoMes = datos.control_perfiles_red.map((f) => f.anio_mes).sort().pop();
  const porRed = {};
  datos.control_perfiles_red
    .filter((f) => f.anio_mes === ultimoMes)
    .forEach((f) => {
      porRed[f.red] = f;
    });

  datos.perfiles.forEach((p) => {
    const plataforma = clasePlataforma(p.red);
    const stats = porRed[p.red];
    const posts = datos.meta_organico.filter((o) => o.red === p.red);
    const ultima = posts.reduce((max, o) => (o.fecha > max ? o.fecha : max), '');
    const dias = diasDesde(ultima);
    const color = dias === null ? 'rojo' : dias <= 7 ? 'verde' : dias <= 14 ? 'amarillo' : 'rojo';

    const card = document.createElement('div');
    card.className = `card-perfil ${plataforma}`;
    card.innerHTML =
      `<div class="card-perfil-cabecera">
         ${iconoPlataforma(plataforma, 'grande')}
         <div>
           <strong>${p.nombre}</strong>
           <span class="nota">${NOMBRE_PLATAFORMA[plataforma] || p.red}</span>
         </div>
       </div>
       <div style="margin-bottom:var(--sp-3)">
         <span class="badge-salud ${color}"><span class="punto-salud ${color}"></span>${
        ultima ? 'Última: ' + fechaLegible(ultima) : 'Sin publicaciones'
      }</span>
       </div>`;

    const grid = document.createElement('div');
    grid.className = 'card-perfil-stats';
    const items = stats
      ? [
          ['Seguidores', fmtNum.format(stats.seguidores)],
          ['Ganados en el mes', (stats.seguidores_ganados >= 0 ? '+' : '') + fmtNum.format(stats.seguidores_ganados)],
          ['Publicaciones', fmtNum.format(posts.length)],
          ['Interacciones', fmtNum.format(sum(posts, 'total_interacciones'))],
        ]
      : [
          ['Publicaciones', fmtNum.format(posts.length)],
          ['Interacciones', fmtNum.format(sum(posts, 'total_interacciones'))],
        ];
    grid.innerHTML = items.map(([e, v]) => `<div><span>${e}</span><strong>${v}</strong></div>`).join('');
    card.appendChild(grid);
    cont.appendChild(card);
  });
}

/* Barras agrupadas en vez de tortas: comparar dos redes en cinco métricas
   con cinco donas obliga a leer cinco gráficos; acá se lee uno solo.
   Cada métrica se normaliza al 100% porque las escalas no son comparables
   (seguidores vs. publicaciones), y el valor real va en el hover. */
function renderComparacionRedes(datos) {
  const ultimoMes = datos.control_perfiles_red.map((f) => f.anio_mes).sort().pop();
  const filas = datos.control_perfiles_red.filter((f) => f.anio_mes === ultimoMes);

  if (filas.length < 2) {
    mensajeGrafico('chart-comparacion-redes', 'Esta unidad tiene un solo perfil activo: no hay comparación entre redes.');
    return;
  }

  const metricas = [
    ['seguidores', 'Seguidores'],
    ['publicaciones_mes', 'Publicaciones'],
    ['interacciones_mes', 'Interacciones'],
    ['visualizaciones_mes', 'Visualizaciones'],
    ['tasa_engagement', 'Engagement'],
  ];
  const etiquetas = metricas.map(([, e]) => e);
  const totales = metricas.map(([campo]) => filas.reduce((a, f) => a + (Number(f[campo]) || 0), 0));

  const trazas = filas.map((f) => ({
    y: etiquetas,
    x: metricas.map(([campo], i) => (totales[i] > 0 ? ((Number(f[campo]) || 0) / totales[i]) * 100 : 0)),
    customdata: metricas.map(([campo]) =>
      campo === 'tasa_engagement' ? fmtDec.format((Number(f[campo]) || 0) * 100) + '%' : fmtNum.format(Number(f[campo]) || 0),
    ),
    name: NOMBRE_PLATAFORMA[clasePlataforma(f.red)] || f.red,
    type: 'bar',
    orientation: 'h',
    marker: { color: colorPlataforma(f.red) },
    hovertemplate: '%{fullData.name}: %{customdata} (%{x:.1f}%)<extra></extra>',
  }));

  graficar('chart-comparacion-redes', trazas, {
    barmode: 'stack',
    margin: { t: 10, r: 20, b: 40, l: 110 },
    xaxis: { ticksuffix: '%', range: [0, 100], gridcolor: getComputedStyleVar('--gridline') },
    legend: { orientation: 'h', y: -0.18 },
  });
}

function renderEvolucionSeguidores(datos) {
  const mensual = [...datos.control_perfiles].sort((a, b) => a.anio_mes.localeCompare(b.anio_mes));

  if (mensual.length < 2) {
    const unico = mensual[0];
    mensajeGrafico(
      'chart-seguidores',
      unico
        ? `Solo hay un mes cargado (${mesLegible(unico.anio_mes)}: ${fmtNum.format(unico.seguidores)} seguidores). La evolución aparece cuando haya al menos dos snapshots mensuales.`
        : 'Sin snapshots mensuales todavía.',
    );
    return;
  }

  const variaciones = mensual.map((f, i) =>
    i === 0 ? 0 : ((f.seguidores - mensual[i - 1].seguidores) / (mensual[i - 1].seguidores || 1)) * 100,
  );

  graficar(
    'chart-seguidores',
    [
      {
        x: mensual.map((f) => mesLegible(f.anio_mes)),
        y: mensual.map((f) => f.seguidores),
        customdata: variaciones.map((v) => (v >= 0 ? '+' : '') + fmtDec1.format(v) + '%'),
        name: 'Seguidores',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: getComputedStyleVar('--accent'), width: 3 },
        marker: { size: 8 },
        hovertemplate: '%{x}<br>%{y:,} seguidores (%{customdata})<extra></extra>',
      },
    ],
    { showlegend: false, yaxis: { title: 'Seguidores' } },
  );
}

function renderRankingUnidades() {
  const scores = scoresUnidades();
  renderRanking(
    'ranking-unidades',
    scores.map((s) => ({
      nombre: s.unidad,
      meta: s.dias === null
        ? 'Sin publicaciones registradas'
        : `${fmtNum.format(s.publicaciones || 0)} publicaciones este mes · engagement ${fmtDec.format(s.engMedio || 0)}% · última hace ${s.dias} días`,
      valor: s.score,
      valorTexto: String(s.score),
      sub: 'de 100',
      proporcion: s.score,
      color:
        s.score >= 70 ? getComputedStyleVar('--salud-verde')
          : s.score >= 45 ? getComputedStyleVar('--salud-amarillo')
            : getComputedStyleVar('--salud-rojo'),
    })),
  );
}

function renderHistoricoUnidad(datos) {
  const mensual = [...datos.control_perfiles]
    .sort((a, b) => b.anio_mes.localeCompare(a.anio_mes))
    .map((f) => Object.assign({ mes: mesLegible(f.anio_mes), engagement: (Number(f.tasa_engagement) || 0) * 100 }, f));

  tablaInteractiva(
    'tabla-control-perfiles',
    mensual,
    [
      { clave: 'mes', etiqueta: 'Mes' },
      { clave: 'seguidores', etiqueta: 'Seguidores', tipo: 'num' },
      { clave: 'seguidores_ganados', etiqueta: 'Ganados', tipo: 'num' },
      { clave: 'publicaciones_mes', etiqueta: 'Publicaciones', tipo: 'num' },
      { clave: 'visualizaciones_mes', etiqueta: 'Visualizaciones', tipo: 'num' },
      { clave: 'interacciones_mes', etiqueta: 'Interacciones', tipo: 'num' },
      { clave: 'engagement', etiqueta: 'Engagement', tipo: 'pct' },
    ],
    { porPagina: 12, ordenInicial: 'anio_mes', dirInicial: 'desc' },
  );
}
