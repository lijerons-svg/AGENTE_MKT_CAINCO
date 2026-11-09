const DATA = __DATOS_CONTROL_CONTENIDO_JSON__;

const fmtNum = new Intl.NumberFormat('es-BO');
const fmtDec = new Intl.NumberFormat('es-BO', { maximumFractionDigits: 2 });
const fmtDec1 = new Intl.NumberFormat('es-BO', { maximumFractionDigits: 1 });

const NOMBRES_MES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];
const MES_CORTO = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const NOMBRES_DIA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

/* Un Set vacío significa "todos" en cada filtro: evita tener que mantener
   sincronizado un estado "todo seleccionado" cuando cambian los datos. */
const estado = {
  unidadPerfiles: null, // Control de Perfiles: selección única, pestaña aparte
  // Filtros compartidos por Análisis y Mailchimp: elegir un período en una
  // pestaña lo mantiene al cambiar de pestaña, en vez de obligar a repetir
  // la misma selección dos veces.
  unidades: new Set(),
  anios: new Set(),
  meses: new Set(),
  // Búsqueda de campaña: independiente por pestaña (pauta y email son
  // campañas distintas, buscar en una no tiene por qué filtrar la otra).
  busquedaAds: '',
  busquedaMailchimp: '',
};

/* Cualquier cambio en un filtro compartido repinta ambas pestañas que lo
   usan, para que no queden desincronizadas al cambiar de pestaña. */
function alCambiarFiltros() {
  renderAnalisis();
  renderMailchimp();
}

/* ---------- utilidades ---------- */
function sum(arr, clave) {
  return arr.reduce((acc, fila) => acc + (Number(fila[clave]) || 0), 0);
}

function claveMes(fechaISO) {
  return (fechaISO || '').slice(0, 7);
}

function anioDe(fechaISO) {
  return (fechaISO || '').slice(0, 4);
}

function mesDe(fechaISO) {
  return (fechaISO || '').slice(5, 7);
}

function hoyISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function fechaLegible(fechaISO) {
  if (!fechaISO) return '—';
  const [a, m, d] = fechaISO.slice(0, 10).split('-');
  return `${Number(d)} ${MES_CORTO[Number(m) - 1] || ''} ${a}`;
}

function mesLegible(anioMes) {
  if (!anioMes) return '—';
  const [a, m] = anioMes.split('-');
  return `${MES_CORTO[Number(m) - 1] || m} ${a}`;
}

function diasDesde(fechaISO) {
  if (!fechaISO) return null;
  return Math.floor((new Date(hoyISO()) - new Date(fechaISO.slice(0, 10))) / 86400000);
}

function pct(parte, total) {
  return total > 0 ? (parte / total) * 100 : 0;
}

function claseEstado(valor) {
  return (valor || '').toLowerCase().replace(/\s+/g, '_').replace(/[^a-z_]/g, '');
}

function getComputedStyleVar(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

/* ---------- filtro año + mes (compartido por Análisis y Mailchimp) ----------
   Los meses se listan como 01..12 y no como "2026-07": así el filtro de mes
   sigue teniendo sentido cuando hay varios años seleccionados. */
function filtrarPorAnioMes(filas, campoFecha, setAnios, setMeses) {
  return filas.filter((f) => {
    const fecha = f[campoFecha];
    if (!fecha) return false;
    if (setAnios.size && !setAnios.has(anioDe(fecha))) return false;
    if (setMeses.size && !setMeses.has(mesDe(fecha))) return false;
    return true;
  });
}

/* Período inmediatamente anterior al filtrado, para poder comparar. Si el
   usuario eligió meses sueltos, se compara contra la misma cantidad de meses
   previos al primero elegido. */
function periodoAnterior(filas, campoFecha, setAnios, setMeses) {
  const mesesEnFiltro = [
    ...new Set(filtrarPorAnioMes(filas, campoFecha, setAnios, setMeses).map((f) => claveMes(f[campoFecha]))),
  ].sort();
  if (!mesesEnFiltro.length) return [];
  const todos = [...new Set(filas.map((f) => claveMes(f[campoFecha])).filter(Boolean))].sort();
  const primero = todos.indexOf(mesesEnFiltro[0]);
  if (primero <= 0) return [];
  const previos = todos.slice(Math.max(0, primero - mesesEnFiltro.length), primero);

  // Si se filtró un único mes y es el mes calendario en curso (todavía no
  // cerró), el mes de comparación se recorta al mismo día — comparar lo
  // que va del mes contra un mes anterior completo siempre muestra una
  // caída, exista o no una caída real.
  const unicoMesFiltrado = mesesEnFiltro.length === 1 ? mesesEnFiltro[0] : null;
  const hoy = hoyISO();
  if (unicoMesFiltrado === claveMes(hoy) && previos.length === 1) {
    const diaHoy = Number(hoy.slice(8, 10));
    return filtrarMesConCorte(filas, campoFecha, previos[0], Math.min(diaHoy, ultimoDiaDelMes(previos[0])));
  }

  const set = new Set(previos);
  return filas.filter((f) => set.has(claveMes(f[campoFecha])));
}

function etiquetaPeriodo(setAnios, setMeses) {
  const anios = [...setAnios].sort();
  const meses = [...setMeses].sort();
  if (!anios.length && !meses.length) return 'todo el histórico';
  const partes = [];
  if (meses.length) partes.push(meses.map((m) => MES_CORTO[Number(m) - 1]).join(', '));
  if (anios.length) partes.push(anios.join(', '));
  return partes.join(' · ');
}

/* Nombre sugerido del PDF al imprimir: el navegador arma el nombre de
   archivo a partir de document.title, así que "Mailchimp, mes de julio"
   tiene que quedar reflejado ahí y no solo "Control de Contenido · CAINCO"
   para todas las exportaciones. */
function tituloParaImprimir() {
  const tabActivo = document.querySelector('.tab-btn.activo');
  // Acotado a la pestaña activa: las sub-pestañas de Análisis existen en el
  // DOM aunque esa pestaña no sea la que está a la vista.
  const subtabActivo = document.querySelector('.tab-panel.activo .subtab-btn.activo');
  const partes = [];
  if (tabActivo) partes.push(tabActivo.textContent.trim());
  if (subtabActivo) partes.push(subtabActivo.textContent.trim());
  partes.push(etiquetaPeriodo(estado.anios, estado.meses));
  return `${partes.join(' - ')} - CAINCO`;
}

/* ---------- chips ---------- */
function renderChips(contenedorId, valores, seleccion, onChange, etiquetar) {
  const cont = document.getElementById(contenedorId);
  if (!cont) return;
  cont.textContent = '';
  if (!valores.length) {
    cont.innerHTML = '<span class="vacio">Sin datos</span>';
    return;
  }
  const todos = document.createElement('button');
  todos.type = 'button';
  todos.className = 'chip-filtro chip-todos' + (seleccion.size ? '' : ' activo');
  todos.textContent = 'Todos';
  todos.addEventListener('click', () => {
    seleccion.clear();
    onChange();
  });
  cont.appendChild(todos);

  valores.forEach((valor) => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip-filtro' + (seleccion.has(valor) ? ' activo' : '');
    chip.textContent = etiquetar ? etiquetar(valor) : valor;
    chip.addEventListener('click', () => {
      if (seleccion.has(valor)) seleccion.delete(valor);
      else seleccion.add(valor);
      onChange();
    });
    cont.appendChild(chip);
  });
}

/* Lista desplegable de selección múltiple con opción "Todos".
   Los meses y años como chips ocupaban dos renglones enteros de filtros;
   plegados dejan la barra en una sola línea y el resumen del botón dice qué
   hay elegido sin tener que abrirla. */
function dropdownMultiple(contenedorId, valores, seleccion, onChange, etiquetar, etiquetaVacia) {
  const cont = document.getElementById(contenedorId);
  if (!cont) return;
  cont.textContent = '';
  cont.className = 'dropdown-multi';
  if (!valores.length) {
    cont.innerHTML = '<span class="vacio" style="padding:0">Sin datos</span>';
    return;
  }
  const texto = (v) => (etiquetar ? etiquetar(v) : v);

  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'dropdown-boton' + (seleccion.size ? ' con-seleccion' : '');
  const elegidos = valores.filter((v) => seleccion.has(v));
  boton.innerHTML =
    `<span>${
      !elegidos.length ? etiquetaVacia || 'Todos'
        : elegidos.length <= 3 ? elegidos.map(texto).join(', ')
          : `${elegidos.length} seleccionados`
    }</span><span class="dropdown-flecha">▾</span>`;

  const panel = document.createElement('div');
  panel.className = 'dropdown-panel';

  const opcionTodos = document.createElement('label');
  opcionTodos.className = 'dropdown-opcion' + (seleccion.size ? '' : ' activa');
  opcionTodos.innerHTML = `<input type="checkbox" ${seleccion.size ? '' : 'checked'} /><span>Todos</span>`;
  opcionTodos.querySelector('input').addEventListener('change', () => {
    seleccion.clear();
    onChange();
  });
  panel.appendChild(opcionTodos);

  valores.forEach((valor) => {
    const opcion = document.createElement('label');
    const activa = seleccion.has(valor);
    opcion.className = 'dropdown-opcion' + (activa ? ' activa' : '');
    opcion.innerHTML = `<input type="checkbox" ${activa ? 'checked' : ''} /><span>${texto(valor)}</span>`;
    opcion.querySelector('input').addEventListener('change', () => {
      if (seleccion.has(valor)) seleccion.delete(valor);
      else seleccion.add(valor);
      onChange();
    });
    panel.appendChild(opcion);
  });

  boton.addEventListener('click', (ev) => {
    ev.stopPropagation();
    const abierto = panel.classList.contains('visible');
    document.querySelectorAll('.dropdown-panel.visible').forEach((p) => p.classList.remove('visible'));
    if (!abierto) panel.classList.add('visible');
  });
  panel.addEventListener('click', (ev) => ev.stopPropagation());

  cont.appendChild(boton);
  cont.appendChild(panel);
}

document.addEventListener('click', () => {
  document.querySelectorAll('.dropdown-panel.visible').forEach((p) => p.classList.remove('visible'));
});

/* Chips de selección única (sin "Todos"): reemplazan al dropdown de unidad. */
function renderChipsUnico(contenedorId, valores, valorActual, onChange) {
  const cont = document.getElementById(contenedorId);
  if (!cont) return;
  cont.textContent = '';
  valores.forEach((valor) => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip-filtro' + (valor === valorActual ? ' activo' : '');
    chip.textContent = valor;
    chip.addEventListener('click', () => onChange(valor));
    cont.appendChild(chip);
  });
}


/* Etiqueta de red con fondo de marca, para tablas con muchas filas. */
function pillRed(texto) {
  const clase = clasePlataforma(texto);
  return `<span class="pill ${clase}">${NOMBRE_PLATAFORMA[clase] || texto}</span>`;
}

/* ---------- KPIs ---------- */
/* opciones: { nota, delta, deltaEtiqueta, invertir, plataforma, chico } */
function kpi(cont, etiqueta, valor, opciones) {
  const o = opciones || {};
  const div = document.createElement('div');
  div.className = 'kpi' + (o.plataforma ? ' ' + o.plataforma : '');

  const etq = document.createElement('div');
  etq.className = 'etiqueta';
  etq.innerHTML = (o.plataforma ? iconoPlataforma(o.plataforma, 'chico') : '') + etiqueta;
  // Métricas calculadas por el tablero (no publicadas tal cual por Meta o
  // Mailchimp) llevan un "?" con la fórmula exacta: sin eso, un número
  // derivado se confunde con un dato oficial de la plataforma.
  if (o.info) {
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'btn-info';
    boton.textContent = '?';
    boton.setAttribute('aria-label', 'Cómo se calcula ' + etiqueta);
    const pop = document.createElement('div');
    pop.className = 'popover';
    pop.innerHTML = o.info;
    boton.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const abierto = pop.classList.contains('visible');
      document.querySelectorAll('.popover.visible').forEach((p) => p.classList.remove('visible'));
      if (!abierto) pop.classList.add('visible');
    });
    etq.appendChild(boton);
    div.appendChild(pop);
  }
  div.appendChild(etq);

  const val = document.createElement('div');
  // nivelRef pinta el valor según la referencia de industria; es distinto
  // del delta, que solo dice si mejoró o empeoró respecto al mes anterior.
  val.className = 'valor' + (o.chico ? ' chico' : '') + (o.nivelRef ? ' nivel-' + o.nivelRef : '');
  val.textContent = valor;
  div.appendChild(val);

  if (o.delta !== null && o.delta !== undefined && Number.isFinite(o.delta)) {
    const d = document.createElement('div');
    // "invertir" es para métricas donde subir es malo (CPC, bajas, rebotes).
    const bueno = o.invertir ? o.delta < 0 : o.delta > 0;
    const clase = Math.abs(o.delta) < 0.05 ? 'neutro' : bueno ? 'mejor' : 'peor';
    const flecha = Math.abs(o.delta) < 0.05 ? '·' : o.delta > 0 ? '↑' : '↓';
    d.className = 'delta ' + clase;
    d.textContent = `${flecha} ${o.delta > 0 ? '+' : ''}${fmtDec1.format(o.delta)}% ${o.deltaEtiqueta || 'vs. período anterior'}`;
    div.appendChild(d);
  }

  if (o.nota) {
    const n = document.createElement('div');
    n.className = 'nota';
    n.textContent = o.nota;
    div.appendChild(n);
  }
  cont.appendChild(div);
  return div;
}

function variacion(actual, anterior) {
  if (!anterior) return null;
  return ((actual - anterior) / anterior) * 100;
}

/* ---------- gráficos ---------- */
function layoutBase(extra) {
  const fondo = getComputedStyleVar('--surface-1');
  const texto = getComputedStyleVar('--text-secondary');
  const grid = getComputedStyleVar('--gridline');
  return Object.assign(
    {
      paper_bgcolor: fondo,
      plot_bgcolor: fondo,
      font: { color: texto, family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: 12 },
      margin: { t: 12, r: 20, b: 42, l: 56 },
      xaxis: { gridcolor: grid, zerolinecolor: grid, automargin: true },
      yaxis: { gridcolor: grid, zerolinecolor: grid, automargin: true },
      legend: { orientation: 'h', y: -0.22 },
      hoverlabel: { bgcolor: fondo, bordercolor: grid, font: { color: getComputedStyleVar('--text-primary') } },
    },
    extra,
  );
}

function plotlyConfig() {
  return { displayModeBar: false, responsive: true };
}

/* Esquinas redondeadas en las barras: acompaña el resto del sistema (todo
   el tablero usa radios de 8-16px) y evita el look de planilla. Plotly lo
   soporta desde la 2.27 vía marker.cornerradius. */
const RADIO_BARRA = 5;
function redondearBarras(trazas) {
  trazas.forEach((t) => {
    if (t.type === 'bar') {
      t.marker = Object.assign({ cornerradius: RADIO_BARRA }, t.marker);
    }
  });
  return trazas;
}

/* Plotly llega por CDN: si no cargó (sin internet, CDN bloqueado), el resto
   del tablero tiene que seguir funcionando en vez de romperse entero. */
function hayPlotly() {
  return typeof Plotly !== 'undefined';
}

/* Un contenedor de gráfico mide 320-340px de alto; cuando en su lugar va un
   aviso de una línea, ese alto deja un hueco enorme. Se guarda el alto
   original para restaurarlo al volver a dibujar. */
function altoGrafico(cont, restaurar) {
  if (cont.dataset.altoOriginal === undefined) cont.dataset.altoOriginal = cont.style.height || '';
  cont.style.height = restaurar ? cont.dataset.altoOriginal : 'auto';
}

function mensajeGrafico(id, texto) {
  const cont = document.getElementById(id);
  if (!cont) return;
  if (hayPlotly()) Plotly.purge(cont);
  altoGrafico(cont, false);
  cont.innerHTML = `<p class="vacio">${texto}</p>`;
}

function graficar(id, trazas, layoutExtra, mensajeVacio) {
  const cont = document.getElementById(id);
  if (!cont) return null;
  if (!hayPlotly()) {
    altoGrafico(cont, false);
    cont.innerHTML = '<p class="vacio">No se pudo cargar la librería de gráficos (requiere conexión a internet).</p>';
    return null;
  }
  if (!trazas.length || trazas.every((t) => !(t.x || t.y || []).length)) {
    mensajeGrafico(id, mensajeVacio || 'Sin datos en el período seleccionado.');
    return null;
  }
  cont.textContent = '';
  altoGrafico(cont, true);
  Plotly.newPlot(cont, redondearBarras(trazas), layoutBase(layoutExtra || {}), plotlyConfig());
  return cont;
}

/* ---------- tabla ordenable + paginada ----------
   columnas: [{ clave, etiqueta, tipo: 'num'|'pct'|'moneda'|'texto', ancho }]
   opciones: { porPagina, ordenInicial, filtros: [{ id, etiqueta, clave }], buscarEn } */
function tablaInteractiva(contenedor, filas, columnasOriginal, opciones) {
  const o = opciones || {};
  const cont = typeof contenedor === 'string' ? document.getElementById(contenedor) : contenedor;
  if (!cont) return;

  // Orden de columnas elegido a mano por quien mira el tablero (botón "⋮"
  // en cada encabezado) — se guarda por navegador, no viaja entre personas
  // ni se pierde al volver a generar el reporte, igual que el tema.
  const claveOrden = 'orden-cols-' + (typeof contenedor === 'string' ? contenedor : cont.id);
  let columnas = columnasOriginal;
  try {
    const guardado = JSON.parse(localStorage.getItem(claveOrden) || 'null');
    if (Array.isArray(guardado)) {
      const porClave = Object.fromEntries(columnasOriginal.map((c) => [c.clave, c]));
      const reordenadas = guardado.map((clave) => porClave[clave]).filter(Boolean);
      const faltantes = columnasOriginal.filter((c) => !guardado.includes(c.clave));
      if (reordenadas.length) columnas = [...reordenadas, ...faltantes];
    }
  } catch (e) { /* localStorage puede fallar en navegación privada: se usa el orden por defecto */ }

  function moverColumna(clave, destino) {
    const idx = columnas.findIndex((c) => c.clave === clave);
    if (idx === -1) return;
    const [col] = columnas.splice(idx, 1);
    if (destino === 'inicio') columnas.unshift(col);
    else columnas.push(col);
    try {
      localStorage.setItem(claveOrden, JSON.stringify(columnas.map((c) => c.clave)));
    } catch (e) { /* ídem: si falla, el orden nuevo igual se ve hasta recargar la página */ }
    pintar();
  }

  const estadoTabla = {
    orden: o.ordenInicial || null,
    dir: o.dirInicial || 'desc',
    pagina: 0,
    busqueda: '',
    filtros: {},
  };
  const porPagina = o.porPagina || 15;

  cont.textContent = '';
  const barra = document.createElement('div');
  barra.className = 'barra-tabla';
  cont.appendChild(barra);

  if (o.buscarEn) {
    const input = document.createElement('input');
    input.type = 'search';
    input.className = 'buscador';
    input.placeholder = o.placeholder || 'Buscar...';
    input.addEventListener('input', () => {
      estadoTabla.busqueda = input.value.trim().toLowerCase();
      estadoTabla.pagina = 0;
      pintar();
    });
    barra.appendChild(input);
  }

  (o.filtros || []).forEach((f) => {
    const valores = [...new Set(filas.map((r) => r[f.clave]).filter(Boolean))].sort();
    if (valores.length < 2) return;
    const select = document.createElement('select');
    select.className = 'select-filtro';
    const opt0 = document.createElement('option');
    opt0.value = '';
    opt0.textContent = f.etiqueta;
    select.appendChild(opt0);
    valores.forEach((v) => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });
    select.addEventListener('change', () => {
      estadoTabla.filtros[f.clave] = select.value;
      estadoTabla.pagina = 0;
      pintar();
    });
    barra.appendChild(select);
  });

  const scroll = document.createElement('div');
  scroll.className = 'tabla-scroll';
  cont.appendChild(scroll);
  const pie = document.createElement('div');
  pie.className = 'tabla-pie';
  cont.appendChild(pie);

  function formatear(valor, tipo) {
    if (valor === null || valor === undefined || valor === '') return tipo && tipo !== 'texto' ? '0' : '';
    if (tipo === 'num') return fmtNum.format(Number(valor) || 0);
    if (tipo === 'pct') return fmtDec.format(Number(valor) || 0) + '%';
    if (tipo === 'moneda') return fmtDec.format(Number(valor) || 0);
    return String(valor);
  }

  function visibles() {
    let r = filas;
    if (estadoTabla.busqueda) {
      r = r.filter((fila) =>
        o.buscarEn.some((clave) => String(fila[clave] || '').toLowerCase().includes(estadoTabla.busqueda)),
      );
    }
    Object.entries(estadoTabla.filtros).forEach(([clave, valor]) => {
      if (valor) r = r.filter((fila) => fila[clave] === valor);
    });
    if (estadoTabla.orden) {
      const col = columnas.find((c) => c.clave === estadoTabla.orden);
      const signo = estadoTabla.dir === 'asc' ? 1 : -1;
      r = [...r].sort((a, b) => {
        const va = a[estadoTabla.orden];
        const vb = b[estadoTabla.orden];
        if (col && col.tipo && col.tipo !== 'texto') return signo * ((Number(va) || 0) - (Number(vb) || 0));
        return signo * String(va || '').localeCompare(String(vb || ''));
      });
    }
    return r;
  }

  function pintar() {
    // Los popover de encabezado viven en document.body, no en el <th> que
    // se recrea en cada redibujado — sin este borrado se acumularían de a
    // uno por cada ordenamiento/filtro/página.
    document.querySelectorAll(`[data-grupo-popover="${claveOrden}"]`).forEach((p) => p.remove());

    const datos = visibles();
    // En modo impresión (ver template_main.js) se ignora la paginación: el
    // PDF tiene que traer todas las filas, no solo la página que estaba
    // visible en pantalla al momento de imprimir.
    const porPaginaEfectiva = window.MODO_IMPRESION ? datos.length || 1 : porPagina;
    const paginas = Math.max(1, Math.ceil(datos.length / porPaginaEfectiva));
    estadoTabla.pagina = Math.min(estadoTabla.pagina, paginas - 1);
    const pagina = datos.slice(estadoTabla.pagina * porPaginaEfectiva, (estadoTabla.pagina + 1) * porPaginaEfectiva);

    scroll.textContent = '';
    if (!datos.length) {
      scroll.innerHTML = '<p class="vacio">Sin resultados.</p>';
      pie.textContent = '';
      return;
    }

    const tabla = document.createElement('table');
    tabla.className = 'tabla' + (o.claseExtra ? ' ' + o.claseExtra : '');
    const thead = document.createElement('thead');
    const trHead = document.createElement('tr');
    columnas.forEach((c) => {
      const th = document.createElement('th');
      const etiqueta = document.createElement('span');
      etiqueta.textContent = c.etiqueta;
      th.appendChild(etiqueta);
      th.className = 'ordenable' + (estadoTabla.orden === c.clave ? ' ' + estadoTabla.dir : '');
      if (c.tipo && c.tipo !== 'texto') th.style.textAlign = 'right';
      th.addEventListener('click', () => {
        if (estadoTabla.orden === c.clave) {
          estadoTabla.dir = estadoTabla.dir === 'asc' ? 'desc' : 'asc';
        } else {
          estadoTabla.orden = c.clave;
          estadoTabla.dir = c.tipo && c.tipo !== 'texto' ? 'desc' : 'asc';
        }
        pintar();
      });
      trHead.appendChild(th);
      // agregarInfo/agregarMenuColumna detienen la propagación del click de
      // sus propios botones, así que no disparan el ordenamiento de la
      // columna (eso lo maneja el listener de más arriba, sobre todo el th).
      if (c.info) agregarInfo(th, c.info, claveOrden);
      agregarMenuColumna(th, c.clave, moverColumna, claveOrden);
    });
    thead.appendChild(trHead);
    tabla.appendChild(thead);

    const tbody = document.createElement('tbody');
    pagina.forEach((fila) => {
      const tr = document.createElement('tr');
      columnas.forEach((c) => {
        const td = document.createElement('td');
        const bruto = fila[c.clave];
        if (c.render) {
          td.innerHTML = c.render(fila);
        } else {
          td.textContent = formatear(bruto, c.tipo);
        }
        if (c.tipo && c.tipo !== 'texto') {
          td.className = 'num';
        } else if (c.largo && bruto) {
          td.className = 'texto-largo';
          td.title = String(bruto);
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tabla.appendChild(tbody);
    scroll.appendChild(tabla);

    pie.textContent = '';
    const info = document.createElement('span');
    info.textContent = `${fmtNum.format(datos.length)} fila${datos.length === 1 ? '' : 's'}`;
    pie.appendChild(info);
    if (paginas > 1) {
      const nav = document.createElement('div');
      nav.className = 'paginador';
      const anterior = document.createElement('button');
      anterior.type = 'button';
      anterior.textContent = '‹';
      anterior.disabled = estadoTabla.pagina === 0;
      anterior.addEventListener('click', () => {
        estadoTabla.pagina -= 1;
        pintar();
      });
      const texto = document.createElement('span');
      texto.textContent = `${estadoTabla.pagina + 1} / ${paginas}`;
      const siguiente = document.createElement('button');
      siguiente.type = 'button';
      siguiente.textContent = '›';
      siguiente.disabled = estadoTabla.pagina >= paginas - 1;
      siguiente.addEventListener('click', () => {
        estadoTabla.pagina += 1;
        pintar();
      });
      nav.appendChild(anterior);
      nav.appendChild(texto);
      nav.appendChild(siguiente);
      pie.appendChild(nav);
    }
  }

  pintar();
}

/* ---------- ranking ---------- */
/* items: [{ nombre, meta, valor, valorTexto, sub, plataforma, proporcion }] */
function renderRanking(contenedorId, items, mensajeVacio) {
  const cont = document.getElementById(contenedorId);
  if (!cont) return;
  cont.textContent = '';
  if (!items.length) {
    cont.innerHTML = `<p class="vacio">${mensajeVacio || 'Sin datos suficientes.'}</p>`;
    return;
  }
  const max = Math.max(...items.map((i) => Number(i.valor) || 0), 1);
  const lista = document.createElement('div');
  lista.className = 'ranking';
  items.forEach((item, i) => {
    const fila = document.createElement('div');
    fila.className = 'ranking-item';
    const proporcion = item.proporcion !== undefined ? item.proporcion : ((Number(item.valor) || 0) / max) * 100;
    fila.innerHTML =
      `<span class="ranking-pos">${i + 1}</span>` +
      `<div class="ranking-cuerpo">` +
      `<div class="ranking-nombre">${item.plataforma ? iconoPlataforma(item.plataforma, 'chico') : ''}${item.nombre}</div>` +
      (item.meta ? `<div class="ranking-meta">${item.meta}</div>` : '') +
      `<div class="ranking-barra"><i style="width:${Math.max(2, proporcion)}%${item.color ? ';background:' + item.color : ''}"></i></div>` +
      `</div>` +
      `<div class="ranking-valor">${item.valorTexto}${item.sub ? `<small>${item.sub}</small>` : ''}</div>`;
    lista.appendChild(fila);
  });
  cont.appendChild(lista);
}

/* ---------- tema ---------- */
(function initTema() {
  const guardado = localStorage.getItem('control-contenido-tema');
  if (guardado) document.documentElement.dataset.theme = guardado;
  document.getElementById('toggle-tema').addEventListener('click', () => {
    const actual = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    const siguiente = actual === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = siguiente;
    localStorage.setItem('control-contenido-tema', siguiente);
    renderAll(); // los gráficos leen colores de variables CSS: hay que redibujarlos
  });
})();

/* Mismo "?" que el de los KPIs, para explicar una métrica desde cualquier
   otro punto de la interfaz (títulos de panel, encabezados, etc.). */
/* Los popover de info/menú de columna se cuelgan de document.body (no del
   botón que los abre): dentro de un <th> con position:sticky dentro de un
   contenedor con overflow-x:auto, un popover posicionado relativo al propio
   botón terminaba recortado/tapado por esa combinación (texto de la tabla
   "entreverado" con el del popover). Flotando en position:fixed, calculado
   a partir de getBoundingClientRect() del botón, queda siempre arriba de
   todo y nunca se recorta. */
function _posicionarPopoverFlotante(boton, pop) {
  const r = boton.getBoundingClientRect();
  const ancho = pop.offsetWidth || 230;
  let left = r.left;
  const maxLeft = window.innerWidth - ancho - 8;
  if (left > maxLeft) left = Math.max(8, maxLeft);
  pop.style.left = `${left}px`;
  pop.style.top = `${r.bottom + 6}px`;
}

function _cerrarPopoversFlotantes() {
  document.querySelectorAll('.popover-flotante.visible').forEach((p) => p.classList.remove('visible'));
}

/* Un click en cualquier lado, o hacer scroll, cierra los popovers abiertos
   (al hacer scroll, uno fixed se queda "pegado" en el lugar viejo si no se
   cierra). `true` = fase de captura, para enterarse también del scroll
   dentro de contenedores internos (ej. la tabla), no solo de la página. */
document.addEventListener('click', _cerrarPopoversFlotantes);
window.addEventListener('scroll', _cerrarPopoversFlotantes, true);

/* `grupoLimpieza`: id opcional para que quien arma una tabla (que se vuelve
   a dibujar entera en cada ordenamiento/filtro/página) pueda borrar los
   popover viejos antes de recrear los encabezados — si no, cada redibujado
   sumaría uno más a document.body sin fin. Los demás usos (tarjetas KPI,
   subtítulos de panel) no lo necesitan: su contenedor no se recrea, así
   que el chequeo de "ya tiene botón" de abajo alcanza. */
function agregarInfo(contenedor, texto, grupoLimpieza) {
  if (!contenedor || contenedor.querySelector('.btn-info')) return;
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'btn-info';
  boton.textContent = '?';
  boton.setAttribute('aria-label', 'Cómo se calcula');
  const pop = document.createElement('div');
  pop.className = 'popover popover-flotante';
  pop.innerHTML = texto;
  if (grupoLimpieza) pop.dataset.grupoPopover = grupoLimpieza;
  document.body.appendChild(pop);
  boton.addEventListener('click', (ev) => {
    ev.stopPropagation();
    const abierto = pop.classList.contains('visible');
    _cerrarPopoversFlotantes();
    if (!abierto) {
      pop.classList.add('visible');
      _posicionarPopoverFlotante(boton, pop);
    }
  });
  contenedor.appendChild(boton);
}

/* Botón "⋮" en cada encabezado de tablaInteractiva: abre un menú chico con
   "Mover al inicio" / "Mover al final". Reordenar así, en vez de arrastrar
   y soltar, evita que un click accidental mueva una columna sin querer —
   acá hace falta abrir el menú y elegir, a propósito. */
function agregarMenuColumna(th, clave, onMover, grupoLimpieza) {
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'btn-mover';
  boton.textContent = '⋮';
  boton.setAttribute('aria-label', 'Mover columna');
  const menu = document.createElement('div');
  menu.className = 'popover popover-flotante menu-columna';
  if (grupoLimpieza) menu.dataset.grupoPopover = grupoLimpieza;

  const opcion = (texto, destino) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = texto;
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      menu.classList.remove('visible');
      onMover(clave, destino);
    });
    return btn;
  };
  menu.appendChild(opcion('« Mover al inicio', 'inicio'));
  menu.appendChild(opcion('Mover al final »', 'fin'));
  document.body.appendChild(menu);

  boton.addEventListener('click', (ev) => {
    ev.stopPropagation();
    const abierto = menu.classList.contains('visible');
    _cerrarPopoversFlotantes();
    if (!abierto) {
      menu.classList.add('visible');
      _posicionarPopoverFlotante(boton, menu);
    }
  });
  th.appendChild(boton);
}

/* ---------- tabs ---------- */
function initTabs() {
  const botones = document.querySelectorAll('.tab-btn');
  botones.forEach((btn) => {
    btn.addEventListener('click', () => {
      botones.forEach((b) => b.classList.remove('activo'));
      document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('activo'));
      btn.classList.add('activo');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('activo');
      // Plotly no dimensiona bien lo que estaba oculto: se fuerza el resize.
      window.dispatchEvent(new Event('resize'));
    });
  });
}

/* Sub-pestañas dentro de una pestaña principal (Análisis: Orgánico/Pauta).
   Clases separadas de .tab-btn/.tab-panel para que no interfieran con la
   navegación principal — un click en una sub-pestaña no debe desactivar
   las pestañas de arriba. */
function initSubTabs() {
  document.querySelectorAll('.subtab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const grupo = btn.dataset.subtabGrupo;
      document.querySelectorAll(`.subtab-btn[data-subtab-grupo="${grupo}"]`).forEach((b) => b.classList.remove('activo'));
      document.querySelectorAll(`.subtab-panel[data-subtab-grupo="${grupo}"]`).forEach((p) => p.classList.remove('activo'));
      btn.classList.add('activo');
      document.getElementById('subtab-' + btn.dataset.subtab).classList.add('activo');
      window.dispatchEvent(new Event('resize'));
    });
  });
}

/* Los buscadores de campaña (Análisis-Pauta y Mailchimp) están fijos en el
   HTML, no se recrean en cada render — si se recrearan, perderían el foco
   con cada letra tipeada. Se conectan una sola vez acá. */
function initBuscadoresCampana() {
  const inputAds = document.getElementById('buscar-campana-analisis');
  if (inputAds) {
    inputAds.addEventListener('input', () => {
      estado.busquedaAds = inputAds.value.trim().toLowerCase();
      renderAnalisis();
    });
  }
  const inputMailchimp = document.getElementById('buscar-campana-mailchimp');
  if (inputMailchimp) {
    inputMailchimp.addEventListener('input', () => {
      estado.busquedaMailchimp = inputMailchimp.value.trim().toLowerCase();
      renderMailchimp();
    });
  }
}

function renderAll() {
  renderResumen();
  renderPerfiles();
  renderAnalisis();
  renderMailchimp();
}
