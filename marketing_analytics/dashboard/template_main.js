/* ---------- orquestación ---------- */
function renderTodo() {
  const slice = aplicarFiltros();
  renderKPIs(slice);
  renderComparativo(slice);
  renderEvolucion(slice);
  renderTopPublicaciones(slice);
  renderTopCampanas(slice);
  renderTopPerfiles(slice);
}

function init() {
  document.getElementById('generado-en').textContent = 'Generado: ' + new Date(DATA.generado_en).toLocaleString('es-BO');
  poblarFiltros();

  ['f-desde', 'f-hasta', 'f-perfil', 'f-red', 'f-tipo', 'f-cuenta', 'f-campana'].forEach((id) => {
    document.getElementById(id).addEventListener('change', renderTodo);
  });
  document.getElementById('evo-metrica').addEventListener('change', renderTodo);
  document.getElementById('evo-granularidad').addEventListener('change', renderTodo);
  document.getElementById('limpiar-filtros').addEventListener('click', () => {
    ['f-desde', 'f-hasta', 'f-perfil', 'f-red', 'f-tipo', 'f-cuenta', 'f-campana'].forEach((id) => {
      document.getElementById(id).value = '';
    });
    renderTodo();
  });

  renderTodo();
}

init();
