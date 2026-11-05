/* Resumen ejecutivo. Responde, en orden de lectura:
   1) ¿cómo estamos? (Health Score + KPIs con variación)
   2) ¿dónde actuar? (salud de perfiles, ordenada por urgencia)
   3) ¿qué está funcionando? (insights y destacados) */

function renderResumen() {
  const mtd = mesActualYAnteriorMTD();
  renderHealthScore(mtd.mesActual);
  renderKpisResumen(mtd);
  renderSaludPerfiles();
  renderInsights(mtd.mesActual, mtd.mesPrevio);
}

function renderHealthScore(mes) {
  const h = healthScore();
  const cont = document.getElementById('health-score');
  const color =
    h.score >= 70 ? getComputedStyleVar('--salud-verde')
      : h.score >= 45 ? getComputedStyleVar('--salud-amarillo')
        : getComputedStyleVar('--salud-rojo');
  const circunferencia = 2 * Math.PI * 46;
  const avance = (h.score / 100) * circunferencia;
  const lectura =
    h.score >= 70 ? 'La operación está sana: la mayoría de las unidades publica con regularidad.'
      : h.score >= 45 ? 'Hay margen de mejora: varias unidades bajaron el ritmo o el engagement.'
        : 'Requiere atención: buena parte de las unidades está inactiva o con bajo rendimiento.';

  cont.innerHTML =
    `<div class="health-aro">
       <svg viewBox="0 0 100 100" width="108" height="108">
         <circle cx="50" cy="50" r="46" fill="none" stroke="${getComputedStyleVar('--gridline')}" stroke-width="8"/>
         <circle cx="50" cy="50" r="46" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"
                 stroke-dasharray="${avance} ${circunferencia}"/>
       </svg>
       <div class="health-num"><strong>${h.score}</strong><span>de 100</span></div>
     </div>
     <div class="health-texto">
       <h2>Estado general · ${mesLegible(mes)}</h2>
       <p>${lectura}</p>
       <div class="health-desglose">
         <div><strong>${h.activos} / ${h.totalUnidades}</strong>unidades activas (≤7 días)</div>
         <div><strong>${h.promedioUnidades}</strong>puntaje medio por unidad</div>
         <div><strong>${h.cumplimiento === null ? '—' : fmtDec1.format(h.cumplimiento) + '%'}</strong>cumplimiento del planner</div>
       </div>
     </div>`;
}

function renderKpisResumen(mtd) {
  const { mesActual, mesPrevio, diaCorteActual, diaCortePrevio, enCurso } = mtd;
  const posts = publicacionesGlobales();
  const delMes = filtrarMesConCorte(posts, 'fecha', mesActual, diaCorteActual);
  const delPrevio = filtrarMesConCorte(posts, 'fecha', mesPrevio, diaCortePrevio);

  const interaccionesMes = sum(delMes, 'total_interacciones');
  const interaccionesPrevio = sum(delPrevio, 'total_interacciones');
  const vistasMes = sum(delMes, 'visualizaciones');
  const vistasPrevio = sum(delPrevio, 'visualizaciones');

  const campanas = filtrarMesConCorte(campanasGlobales(), 'fecha', mesActual, diaCorteActual);
  const nombresCampana = new Set(campanas.map((c) => c.campana));
  const unidadesConPauta = [...new Set(campanas.map((c) => c._unidad))].sort();

  const envios = filtrarMesConCorte(DATA.mailchimp || [], 'fecha', mesActual, diaCorteActual);
  const enviosPrevio = filtrarMesConCorte(DATA.mailchimp || [], 'fecha', mesPrevio, diaCortePrevio);

  // "vs. lo que va de agosto" cuando el mes en curso está a medias, para
  // que quede claro que no se compara contra el mes completo.
  const etiquetaDelta = enCurso ? `vs. lo que va de ${mesLegible(mesPrevio)}` : `vs. ${mesLegible(mesPrevio)}`;

  const kpis = document.getElementById('kpis-resumen');
  kpis.textContent = '';
  kpi(kpis, 'Publicaciones', fmtNum.format(delMes.length), {
    delta: variacion(delMes.length, delPrevio.length),
    deltaEtiqueta: etiquetaDelta,
    nota: 'Contenido orgánico publicado en el mes',
  });
  kpi(kpis, 'Interacciones', fmtNum.format(interaccionesMes), {
    delta: variacion(interaccionesMes, interaccionesPrevio),
    deltaEtiqueta: etiquetaDelta,
    nota: 'Reacciones + comentarios + compartidos',
  });
  kpi(kpis, 'Visualizaciones', fmtNum.format(vistasMes), {
    delta: variacion(vistasMes, vistasPrevio),
    deltaEtiqueta: etiquetaDelta,
    nota: 'Veces que se vio el contenido',
  });
  kpi(kpis, 'Campañas de pauta', fmtNum.format(nombresCampana.size), {
    nota: unidadesConPauta.length
      ? `Unidades: ${unidadesConPauta.join(' · ')}`
      : 'Ninguna unidad con pauta este mes',
  });
  kpi(kpis, 'Envíos de Mailchimp', fmtNum.format(envios.length), {
    delta: variacion(envios.length, enviosPrevio.length),
    deltaEtiqueta: etiquetaDelta,
    nota: 'Campañas de correo enviadas en el mes',
    plataforma: 'mailchimp',
  });
}

function renderSaludPerfiles() {
  const filas = saludPerfiles().map((s) => ({
    unidad: s.unidad,
    fecha: s.post ? s.post.fecha : '',
    fechaTexto: s.post ? fechaLegible(s.post.fecha) : 'Sin publicaciones',
    red: s.post ? s.post.red : '',
    dias: s.dias ?? 9999,
    color: s.color,
    etiqueta: s.etiqueta,
  }));

  tablaInteractiva(
    'tabla-salud-perfiles',
    filas,
    [
      { clave: 'unidad', etiqueta: 'Unidad' },
      {
        clave: 'fechaTexto',
        etiqueta: 'Última publicación',
        render: (f) => f.fechaTexto,
      },
      {
        clave: 'red',
        etiqueta: 'Red',
        render: (f) => (f.red ? pillRed(f.red) : '—'),
      },
      {
        clave: 'dias',
        etiqueta: 'Días sin publicar',
        tipo: 'num',
        render: (f) => (f.dias >= 9999 ? '—' : fmtNum.format(f.dias)),
      },
      {
        clave: 'etiqueta',
        etiqueta: 'Estado',
        render: (f) => `<span class="badge-salud ${f.color}"><span class="punto-salud ${f.color}"></span>${f.etiqueta}</span>`,
      },
    ],
    // Mejor a peor: menos días sin publicar primero.
    { porPagina: 20, ordenInicial: 'dias', dirInicial: 'asc' },
  );
}

/* ---------- insights ----------
   Cada función devuelve { texto, tono } o null. Devolver null cuando no
   alcanzan los datos es deliberado: un insight a medias confunde más que
   la ausencia del insight. */

function insightDistribucionRed(mes) {
  const delMes = publicacionesGlobales().filter((p) => claveMes(p.fecha) === mes);
  if (delMes.length < 10) return null;
  const porRed = {};
  delMes.forEach((p) => {
    const r = clasePlataforma(p.red);
    porRed[r] = (porRed[r] || 0) + 1;
  });
  const orden = Object.entries(porRed).sort((a, b) => b[1] - a[1]);
  if (orden.length < 2) return null;
  const [red, n] = orden[0];
  const porcentaje = pct(n, delMes.length);
  if (porcentaje < 55) return null;
  return {
    texto: `<strong>${NOMBRE_PLATAFORMA[red] || red}</strong> concentró el ${fmtDec1.format(porcentaje)}% de las publicaciones del mes (${n} de ${delMes.length}).`,
    tono: porcentaje > 80 ? 'peor' : '',
  };
}

function insightFormatoGanador(mes) {
  const delMes = publicacionesGlobales().filter((p) => claveMes(p.fecha) === mes && p.visualizaciones > 0);
  if (delMes.length < 10) return null;
  const porFormato = {};
  delMes.forEach((p) => {
    const f = formatoPost(p);
    (porFormato[f] = porFormato[f] || []).push(engagementPost(p));
  });
  const medias = Object.entries(porFormato)
    .filter(([, v]) => v.length >= 3)
    .map(([f, v]) => [f, v.reduce((a, b) => a + b, 0) / v.length])
    .sort((a, b) => b[1] - a[1]);
  if (medias.length < 2) return null;
  const [mejor, peor] = [medias[0], medias[medias.length - 1]];
  if (peor[1] <= 0) return null;
  const veces = mejor[1] / peor[1];
  if (veces < 1.3) return null;
  return {
    texto: `Los <strong>${mejor[0]}</strong> generan ${fmtDec1.format(veces)} veces más engagement que los <strong>${peor[0]}</strong> (${fmtDec.format(mejor[1])}% vs. ${fmtDec.format(peor[1])}%).`,
    tono: 'mejor',
  };
}

function insightUnidadMasActiva(mes) {
  const delMes = publicacionesGlobales().filter((p) => claveMes(p.fecha) === mes);
  if (delMes.length < 10) return null;
  const porUnidad = {};
  delMes.forEach((p) => {
    porUnidad[p._unidad] = (porUnidad[p._unidad] || 0) + 1;
  });
  const orden = Object.entries(porUnidad).sort((a, b) => b[1] - a[1]);
  if (orden.length < 2) return null;
  const [unidad, n] = orden[0];
  return {
    texto: `<strong>${unidad}</strong> publicó el ${fmtDec1.format(pct(n, delMes.length))}% del contenido del mes (${n} publicaciones).`,
    tono: '',
  };
}

function insightEngagementMensual(mes, previo) {
  const posts = publicacionesGlobales();
  const media = (filas) => {
    const conVistas = filas.filter((p) => p.visualizaciones > 0);
    return conVistas.length ? conVistas.reduce((a, p) => a + engagementPost(p), 0) / conVistas.length : 0;
  };
  const actual = media(posts.filter((p) => claveMes(p.fecha) === mes));
  const anterior = media(posts.filter((p) => claveMes(p.fecha) === previo));
  if (!actual || !anterior) return null;
  const delta = ((actual - anterior) / anterior) * 100;
  if (Math.abs(delta) < 5) return null;
  return {
    texto: `El engagement medio por publicación ${delta > 0 ? 'subió' : 'bajó'} <strong>${fmtDec1.format(Math.abs(delta))}%</strong> respecto a ${mesLegible(previo)} (${fmtDec.format(anterior)}% → ${fmtDec.format(actual)}%).`,
    tono: delta > 0 ? 'mejor' : 'peor',
  };
}

function insightRedSinPublicar() {
  const porRed = {};
  publicacionesGlobales().forEach((p) => {
    const r = clasePlataforma(p.red);
    if (!porRed[r] || p.fecha > porRed[r]) porRed[r] = p.fecha;
  });
  const dormidas = Object.entries(porRed)
    .map(([red, fecha]) => ({ red, dias: diasDesde(fecha) }))
    .filter((r) => r.dias > 14)
    .sort((a, b) => b.dias - a.dias);
  if (!dormidas.length) return null;
  const d = dormidas[0];
  return {
    texto: `<strong>${NOMBRE_PLATAFORMA[d.red] || d.red}</strong> lleva ${d.dias} días sin publicaciones en ninguna unidad.`,
    tono: 'peor',
  };
}

function insightUnidadesInactivas() {
  const rojas = saludPerfiles().filter((s) => s.color === 'rojo');
  if (!rojas.length) return null;
  return {
    texto:
      rojas.length === 1
        ? `<strong>${rojas[0].unidad}</strong> no publica hace más de 14 días.`
        : `<strong>${rojas.length} unidades</strong> llevan más de 14 días sin publicar: ${rojas.map((r) => r.unidad).join(', ')}.`,
    tono: 'peor',
  };
}

function insightCrecimientoSeguidores() {
  const filas = UNIDADES.flatMap((u) => DATA.unidades[u].control_perfiles_red.map((f) => Object.assign({ _unidad: u }, f)));
  if (!filas.length) return null;
  const ultimo = filas.map((f) => f.anio_mes).sort().pop();
  const delMes = filas.filter((f) => f.anio_mes === ultimo && Number(f.seguidores_ganados) > 0);
  if (!delMes.length) return null;
  const mejor = delMes.sort((a, b) => b.seguidores_ganados - a.seguidores_ganados)[0];
  return {
    texto: `<strong>${mejor._unidad}</strong> en ${NOMBRE_PLATAFORMA[clasePlataforma(mejor.red)] || mejor.red} sumó ${fmtNum.format(mejor.seguidores_ganados)} seguidores en ${mesLegible(ultimo)}, el mayor crecimiento del período.`,
    tono: 'mejor',
  };
}

function insightPlanner() {
  const hoy = hoyISO();
  const vencidas = calendarioGlobal().filter((c) => c.fecha_publicacion && c.fecha_publicacion <= hoy);
  if (vencidas.length < 10) return null;
  const atrasadas = vencidas.filter((c) => claseEstado(c.estado) !== 'publicado' && claseEstado(c.estado) !== 'cancelado');
  if (!atrasadas.length) return null;
  return {
    texto: `Hay <strong>${atrasadas.length} publicaciones atrasadas</strong> en el planner: fecha vencida y todavía sin marcar como publicadas.`,
    tono: 'peor',
  };
}

function renderInsights(mes, previo) {
  const cont = document.getElementById('lista-insights');
  cont.textContent = '';
  const insights = [
    insightEngagementMensual(mes, previo),
    insightFormatoGanador(mes),
    insightDistribucionRed(mes),
    insightUnidadMasActiva(mes),
    insightCrecimientoSeguidores(),
    insightUnidadesInactivas(),
    insightRedSinPublicar(),
    insightPlanner(),
  ].filter(Boolean);

  if (!insights.length) {
    cont.innerHTML = '<p class="vacio">Todavía no hay suficiente histórico para sacar conclusiones.</p>';
    return;
  }
  const ul = document.createElement('ul');
  ul.className = 'lista-insights';
  insights.forEach((i) => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="marca ${i.tono}"></span><span>${i.texto}</span>`;
    ul.appendChild(li);
  });
  cont.appendChild(ul);
}
