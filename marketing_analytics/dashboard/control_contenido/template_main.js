document.getElementById('generado-en').textContent =
  'Actualizado el ' + new Date(DATA.generado_en).toLocaleString('es-BO');

initTabs();
initSubTabs();
initBuscadoresCampana();
renderAll();

// Imprimir/"Guardar como PDF" exporta solo la pestaña y sub-pestaña activas
// (el CSS de impresión no toca .activo, así que ya filtra solo). Falta que
// las tablas paginadas traigan todas sus filas filtradas en vez de solo la
// página visible (ver window.MODO_IMPRESION en tablaInteractiva), y que el
// nombre sugerido del PDF diga qué es en vez de "Control de Contenido"
// para cualquier pestaña — el navegador arma ese nombre a partir del título.
let _tituloOriginal = document.title;
window.addEventListener('beforeprint', () => {
  window.MODO_IMPRESION = true;
  renderAll();
  _tituloOriginal = document.title;
  document.title = tituloParaImprimir();
});
window.addEventListener('afterprint', () => {
  window.MODO_IMPRESION = false;
  renderAll();
  document.title = _tituloOriginal;
});
