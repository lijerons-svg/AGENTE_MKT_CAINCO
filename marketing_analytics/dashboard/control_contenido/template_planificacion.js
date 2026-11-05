/* Planificación. Los KPIs y los gráficos responden a los filtros de unidad,
   año y mes; el calendario se navega aparte con las flechas pero respeta el
   filtro de unidad y los canales activos de la leyenda. */

const CANALES_LEYENDA = ['facebook', 'instagram', 'linkedin', 'mailchimp', 'tiktok'];

function datosPlanificacion() {
  return {
    unidades: estado.unidades.size ? [...estado.unidades] : UNIDADES,
    calendario: filasDeUnidades('calendario'),
  };
}

function renderPlanificacion() {
  renderChips('chips-unidad-planificacion', unidadesConDatos(), estado.unidades, alCambiarFiltros);
  dropdownMultiple('drop-anio-planificacion', ANIOS_DISPONIBLES, estado.anios, alCambiarFiltros);
  dropdownMultiple('drop-mes-planificacion', MESES_DISPONIBLES, estado.meses, alCambiarFiltros, (m) => NOMBRES_MES[Number(m) - 1] || m);

  const datos = datosPlanificacion();
  const seleccion = filtrarPorAnioMes(datos.calendario, 'fecha_publicacion', estado.anios, estado.meses);

  document.getElementById('nota-filtros-planificacion').textContent =
    `Los indicadores muestran ${etiquetaPeriodo(estado.anios, estado.meses)}. El calendario de abajo se navega por mes con las flechas y respeta el filtro de unidad.`;

  renderKpisPlanificacion(seleccion);
  renderChartCanales(seleccion);
  renderChartUnidades(seleccion);
  renderLeyendaCalendario();
  renderCalendarioGrilla(datos);
}

/* Los seis estados del planner, en el orden real del flujo de trabajo:
   una publicación nace pendiente y termina publicada o cancelada. */
const ESTADOS_PLANNER = [
  ['pendiente', 'Pendientes', 'Todavía sin producir'],
  ['en_produccion', 'En producción', 'Pieza en proceso de armado'],
  ['aprobado', 'Aprobadas', 'Listas, esperando fecha'],
  ['programado', 'Programadas', 'Con fecha asignada'],
  ['publicado', 'Publicadas', 'Ya salieron'],
  ['cancelado', 'Canceladas', 'Descartadas del plan'],
];

function renderKpisPlanificacion(filas) {
  const hoy = hoyISO();
  const porEstado = {};
  ESTADOS_PLANNER.forEach(([clave]) => {
    porEstado[clave] = 0;
  });
  let sinEstado = 0;
  let atrasadas = 0;
  filas.forEach((c) => {
    const e = claseEstado(c.estado);
    if (porEstado[e] !== undefined) porEstado[e] += 1;
    else sinEstado += 1;
    if (e !== 'publicado' && e !== 'cancelado' && c.fecha_publicacion && c.fecha_publicacion <= hoy) atrasadas += 1;
  });

  const vencidas = filas.filter((c) => c.fecha_publicacion && c.fecha_publicacion <= hoy);
  const cumplimiento = vencidas.length
    ? pct(vencidas.filter((c) => claseEstado(c.estado) === 'publicado').length, vencidas.length)
    : null;

  const cont = document.getElementById('kpis-planificacion');
  cont.textContent = '';
  kpi(cont, 'Planificadas', fmtNum.format(filas.length), { nota: 'Total en el período filtrado' });
  ESTADOS_PLANNER.forEach(([clave, etiqueta, nota]) => {
    kpi(cont, etiqueta, fmtNum.format(porEstado[clave]), {
      nota: filas.length ? `${nota} · ${fmtDec1.format(pct(porEstado[clave], filas.length))}% del total` : nota,
    });
  });
  if (sinEstado) {
    kpi(cont, 'Sin estado', fmtNum.format(sinEstado), { nota: 'No tienen estado cargado en el planner' });
  }
  kpi(cont, 'Atrasadas', fmtNum.format(atrasadas), { nota: 'Fecha vencida y todavía sin publicar' });
  kpi(cont, 'Cumplimiento', cumplimiento === null ? '—' : fmtDec1.format(cumplimiento) + '%', {
    nota: vencidas.length
      ? `${fmtNum.format(vencidas.length)} publicaciones con fecha ya cumplida`
      : 'Sin fechas vencidas en el período',
    info:
      '<strong>Cómo se calcula</strong>' +
      '<code>publicadas ÷ publicaciones con fecha ya vencida × 100</code>' +
      'Solo entran las que ya deberían haber salido: lo que todavía no le llegó la fecha no cuenta como incumplido.',
  });
}

function renderChartCanales(filas) {
  const porCanal = {};
  filas.forEach((c) => {
    const canal = clasePlataforma(c.canal);
    porCanal[canal] = (porCanal[canal] || 0) + 1;
  });
  const canales = Object.keys(porCanal).sort((a, b) => porCanal[b] - porCanal[a]);

  graficar(
    'chart-canales',
    [
      {
        y: canales.map((c) => NOMBRE_PLATAFORMA[c] || c).reverse(),
        x: canales.map((c) => porCanal[c]).reverse(),
        type: 'bar',
        orientation: 'h',
        marker: { color: canales.map((c) => colorPlataforma(c)).reverse() },
        text: canales.map((c) => fmtNum.format(porCanal[c])).reverse(),
        textposition: 'auto',
      },
    ],
    { showlegend: false, margin: { t: 10, r: 20, b: 40, l: 90 } },
    'Sin publicaciones planificadas en la selección.',
  );
}

function renderChartUnidades(filas) {
  const porUnidad = {};
  filas.forEach((c) => {
    porUnidad[c._unidad] = (porUnidad[c._unidad] || 0) + 1;
  });
  const unidades = Object.keys(porUnidad).sort((a, b) => porUnidad[b] - porUnidad[a]).slice(0, 12);

  graficar(
    'chart-unidades-planificacion',
    [
      {
        y: unidades.map((u) => recortar(u, 26)).reverse(),
        x: unidades.map((u) => porUnidad[u]).reverse(),
        type: 'bar',
        orientation: 'h',
        marker: { color: getComputedStyleVar('--accent') },
        text: unidades.map((u) => fmtNum.format(porUnidad[u])).reverse(),
        textposition: 'auto',
      },
    ],
    { showlegend: false, margin: { t: 10, r: 20, b: 40, l: 150 } },
    'Sin publicaciones planificadas en la selección.',
  );
}

/* Leyenda interactiva: cada botón muestra u oculta ese canal en el
   calendario, que es donde la saturación de tarjetas realmente estorba. */
function renderLeyendaCalendario() {
  const cont = document.getElementById('leyenda-calendario');
  cont.textContent = '';
  CANALES_LEYENDA.forEach((canal) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip-filtro' + (estado.canalesOcultos.has(canal) ? ' inactivo' : '');
    btn.innerHTML = `<i style="background:var(--calendario-${canal})"></i>${NOMBRE_PLATAFORMA[canal]}`;
    btn.addEventListener('click', () => {
      if (estado.canalesOcultos.has(canal)) estado.canalesOcultos.delete(canal);
      else estado.canalesOcultos.add(canal);
      renderPlanificacion();
    });
    cont.appendChild(btn);
  });
}

function renderCalendarioGrilla(datos) {
  document.getElementById('cal-mes-actual').textContent = `${NOMBRES_MES[estado.calMes]} ${estado.calAnio}`;
  const anioMes = anioMesNavegado();
  const cont = document.getElementById('calendario-grilla');
  cont.textContent = '';

  NOMBRES_DIA.forEach((n) => {
    const div = document.createElement('div');
    div.className = 'calendario-dia-nombre';
    div.textContent = n;
    cont.appendChild(div);
  });

  const primerDia = new Date(estado.calAnio, estado.calMes, 1);
  const offset = (primerDia.getDay() + 6) % 7; // lunes = 0
  const diasEnMes = new Date(estado.calAnio, estado.calMes + 1, 0).getDate();
  const hoy = hoyISO();

  const porDia = {};
  datos.calendario
    .filter((c) => c.fecha_publicacion && claveMes(c.fecha_publicacion) === anioMes)
    .filter((c) => !estado.canalesOcultos.has(clasePlataforma(c.canal)))
    .forEach((c) => {
      (porDia[c.fecha_publicacion] = porDia[c.fecha_publicacion] || []).push(c);
    });

  for (let i = 0; i < offset; i += 1) {
    const celda = document.createElement('div');
    celda.className = 'calendario-celda fuera-de-mes';
    cont.appendChild(celda);
  }

  for (let dia = 1; dia <= diasEnMes; dia += 1) {
    const fecha = `${anioMes}-${String(dia).padStart(2, '0')}`;
    const celda = document.createElement('div');
    celda.className = 'calendario-celda' + (fecha === hoy ? ' hoy' : '');
    const num = document.createElement('span');
    num.className = 'num-dia';
    num.textContent = dia;
    celda.appendChild(num);

    (porDia[fecha] || []).forEach((c) => {
      const plataforma = clasePlataforma(c.canal);
      const est = claseEstado(c.estado);
      const atrasada = est !== 'publicado' && est !== 'cancelado' && fecha <= hoy;
      const item = document.createElement('div');
      item.className = `calendario-item ${plataforma} ${est}${atrasada ? ' atrasado' : ''}`;
      item.title = `${c.campana_evento || c.descripcion_copy || ''}\n${NOMBRE_PLATAFORMA[plataforma] || c.canal} · ${c.estado || 'sin estado'}${
        atrasada ? ' · ATRASADA' : ''
      }\n${c._unidad}`;
      const linea1 = document.createElement('div');
      linea1.className = 'ci-linea1';
      linea1.innerHTML = iconoPlataforma(plataforma, 'chico') + `<span>${NOMBRE_PLATAFORMA[plataforma] || c.canal || '—'}</span>`;
      const linea2 = document.createElement('div');
      linea2.className = 'ci-linea2';
      linea2.textContent = c.campana_evento || c.tipo || '—';
      item.appendChild(linea1);
      item.appendChild(linea2);
      if (datos.unidades.length > 1) {
        const linea3 = document.createElement('div');
        linea3.className = 'ci-linea3';
        linea3.textContent = c._unidad;
        item.appendChild(linea3);
      }
      celda.appendChild(item);
    });
    cont.appendChild(celda);
  }
}
