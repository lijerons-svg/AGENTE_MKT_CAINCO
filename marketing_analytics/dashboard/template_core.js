const DATA = __DATOS_DASHBOARD_JSON__;

const COLOR = {
  meta_organico: getComputedStyleVar('--series-meta-organico'),
  meta_ads: getComputedStyleVar('--series-meta-ads'),
  mailchimp: getComputedStyleVar('--series-mailchimp'),
  linkedin: getComputedStyleVar('--series-linkedin'),
};

function getComputedStyleVar(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

/* ---------- tema ---------- */
(function initTema() {
  const guardado = localStorage.getItem('rrss-tema');
  if (guardado) document.documentElement.dataset.theme = guardado;
  document.getElementById('toggle-tema').addEventListener('click', () => {
    const actual = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    const siguiente = actual === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = siguiente;
    localStorage.setItem('rrss-tema', siguiente);
    renderTodo();
  });
})();

/* ---------- utilidades ---------- */
const fmtNum = new Intl.NumberFormat('es-BO');
const fmtDec = new Intl.NumberFormat('es-BO', { maximumFractionDigits: 2 });

function sum(arr, clave) {
  return arr.reduce((acc, fila) => acc + (Number(fila[clave]) || 0), 0);
}

function uniqueSorted(arr, clave) {
  return [...new Set(arr.map((f) => f[clave]).filter(Boolean))].sort();
}

function crearOpciones(select, valores, etiqueta) {
  select.textContent = '';
  const def = document.createElement('option');
  def.value = '';
  def.textContent = etiqueta;
  select.appendChild(def);
  valores.forEach((v) => {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    select.appendChild(opt);
  });
}

function claveSemana(fechaISO) {
  const d = new Date(fechaISO + 'T00:00:00');
  const dia = (d.getUTCDay() + 6) % 7; // lunes = 0
  d.setUTCDate(d.getUTCDate() - dia);
  return d.toISOString().slice(0, 10);
}

function claveMes(fechaISO) {
  return fechaISO.slice(0, 7);
}

/* ---------- filtros ---------- */
function poblarFiltros() {
  crearOpciones(document.getElementById('f-perfil'), uniqueSorted(DATA.meta_organico, 'perfil'), 'Todos los perfiles');
  crearOpciones(
    document.getElementById('f-red'),
    uniqueSorted([...DATA.meta_organico, ...DATA.meta_ads], 'red'),
    'Todas las redes',
  );
  crearOpciones(document.getElementById('f-tipo'), uniqueSorted(DATA.meta_organico, 'tipo'), 'Todos los tipos');
  crearOpciones(
    document.getElementById('f-cuenta'),
    uniqueSorted(DATA.meta_ads, 'cuenta_publicitaria'),
    'Todas las cuentas',
  );
  crearOpciones(document.getElementById('f-campana'), uniqueSorted(DATA.meta_ads, 'campana'), 'Todas las campañas');

  const metricas = [
    ['organico_alcance', 'Alcance orgánico'],
    ['organico_interacciones', 'Interacciones orgánicas'],
    ['ads_gasto', 'Gasto (pauta)'],
    ['ads_clics', 'Clics (pauta)'],
    ['ads_resultados', 'Resultados (pauta)'],
    ['mailchimp_aperturas', 'Aperturas Mailchimp'],
    ['mailchimp_clics', 'Clics Mailchimp'],
  ];
  const selectMetrica = document.getElementById('evo-metrica');
  selectMetrica.textContent = '';
  metricas.forEach(([valor, etiqueta]) => {
    const opt = document.createElement('option');
    opt.value = valor;
    opt.textContent = etiqueta;
    selectMetrica.appendChild(opt);
  });
}

function leerFiltros() {
  return {
    desde: document.getElementById('f-desde').value || null,
    hasta: document.getElementById('f-hasta').value || null,
    perfil: document.getElementById('f-perfil').value,
    red: document.getElementById('f-red').value,
    tipo: document.getElementById('f-tipo').value,
    cuenta: document.getElementById('f-cuenta').value,
    campana: document.getElementById('f-campana').value,
  };
}

function enRango(fecha, desde, hasta) {
  if (desde && fecha < desde) return false;
  if (hasta && fecha > hasta) return false;
  return true;
}

function aplicarFiltros() {
  const f = leerFiltros();

  const organico = DATA.meta_organico.filter(
    (r) =>
      enRango(r.fecha, f.desde, f.hasta) &&
      (!f.perfil || r.perfil === f.perfil) &&
      (!f.red || r.red === f.red) &&
      (!f.tipo || r.tipo === f.tipo),
  );

  const ads = DATA.meta_ads.filter(
    (r) =>
      enRango(r.fecha, f.desde, f.hasta) &&
      (!f.red || r.red === f.red) &&
      (!f.cuenta || r.cuenta_publicitaria === f.cuenta) &&
      (!f.campana || r.campana === f.campana),
  );

  const mailchimp = DATA.mailchimp.filter((r) => enRango(r.fecha, f.desde, f.hasta));

  return { organico, ads, mailchimp, linkedin: DATA.linkedin };
}
