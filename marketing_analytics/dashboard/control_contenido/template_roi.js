/* ---------- ROI ----------
   Lee DATA.roi_eventos ("Resumen por Evento" de ROI_Resultados.xlsx, ya
   cruzado con "ROI Resultados" en Python para calcular el rango de meses
   de cada evento — ver leer_resumen_por_evento en
   reports/roi_resultados_builder.py). Copia el formato y la forma de
   mostrar los datos del artefacto de mockup ROI que Sandy aprobó: Leads,
   Subscribers, Revenue, Costo por lead, % de conversión y ROI son "—"
   (pendiente) cuando el evento todavía no tiene esos datos cargados a
   mano, nunca un cero — un cero sí es un dato real (evento cancelado o
   con conversión 0%). */

function roiEventoCompleto(ev) {
  return ev.leads !== null && ev.leads !== undefined
    && ev.subscribers !== null && ev.subscribers !== undefined
    && ev.revenue !== null && ev.revenue !== undefined;
}

function roiOrdenMesTexto(texto) {
  const partes = String(texto || '').split(' ');
  const mes = NOMBRES_MES.indexOf(partes[0]);
  const anio = Number(partes[1]) || 0;
  return anio * 12 + (mes === -1 ? 0 : mes + 1);
}

function roiValoresUnidad() {
  return [...new Set((DATA.roi_eventos || []).map((ev) => ev.unidad).filter(Boolean))].sort();
}

function roiValoresMes() {
  const todos = new Set();
  (DATA.roi_eventos || []).forEach((ev) => (ev.meses || []).forEach((m) => todos.add(m)));
  return [...todos].sort((a, b) => roiOrdenMesTexto(a) - roiOrdenMesTexto(b));
}

function roiFilasFiltradas() {
  return (DATA.roi_eventos || []).filter((ev) => {
    if (estado.unidadesRoi.size && !estado.unidadesRoi.has(ev.unidad)) return false;
    if (estado.mesesRoi.size && !(ev.meses || []).some((m) => estado.mesesRoi.has(m))) return false;
    if (estado.busquedaRoi && !String(ev.nombre_evento || '').toLowerCase().includes(estado.busquedaRoi)) return false;
    return true;
  });
}

function renderFiltrosRoi() {
  renderChips('chips-unidad-roi', roiValoresUnidad(), estado.unidadesRoi, () => renderRoi());
  dropdownMultiple('drop-mes-roi', roiValoresMes(), estado.mesesRoi, () => renderRoi(), null, 'Todos');
}

function renderKpisRoi(filas) {
  const cont = document.getElementById('kpis-roi');
  if (!cont) return;
  cont.textContent = '';

  const completos = filas.filter(roiEventoCompleto);
  const inversionTotal = sum(filas, 'inversion_total');
  const inversionCompleta = sum(completos, 'inversion_total');
  const revenueTotal = sum(completos, 'revenue');
  const leadsTotal = sum(completos, 'leads');
  const roiGlobal = inversionCompleta > 0 ? ((revenueTotal - inversionCompleta) / inversionCompleta) * 100 : null;

  kpi(cont, 'Inversión total', '$' + fmtDec.format(inversionTotal), {
    nota: `${fmtNum.format(filas.length)} evento${filas.length === 1 ? '' : 's'} en el período filtrado`,
  });
  kpi(cont, 'Revenue', revenueTotal ? '$' + fmtDec.format(revenueTotal) : '—', {
    nota: `${fmtNum.format(completos.length)} evento${completos.length === 1 ? '' : 's'} con Leads, Subscribers y Revenue cargados`,
  });
  kpi(cont, 'Leads', completos.length ? fmtNum.format(leadsTotal) : '—');
  kpi(cont, 'ROI global', roiGlobal === null ? '—' : `${roiGlobal > 0 ? '+' : ''}${fmtDec1.format(roiGlobal)}%`, {
    nivelRef: roiGlobal === null ? undefined : (roiGlobal > 0 ? 'bueno' : 'malo'),
    info: 'ROI global = (Revenue − Inversión) ÷ Inversión, sumado solo sobre los eventos con Leads, Subscribers y Revenue cargados. Los eventos sin esos datos todavía no entran en la cuenta — no se les asume un ROI de 0%.',
  });
}

function renderChartRoiUnidad(filas) {
  const completos = filas.filter(roiEventoCompleto);
  const porUnidad = {};
  completos.forEach((ev) => {
    const u = ev.unidad || '(Sin unidad)';
    const acc = porUnidad[u] || { inversion: 0, revenue: 0 };
    acc.inversion += Number(ev.inversion_total) || 0;
    acc.revenue += Number(ev.revenue) || 0;
    porUnidad[u] = acc;
  });

  const filasOrdenadas = Object.keys(porUnidad)
    .map((u) => ({
      unidad: u,
      roi: porUnidad[u].inversion > 0 ? ((porUnidad[u].revenue - porUnidad[u].inversion) / porUnidad[u].inversion) * 100 : 0,
    }))
    .sort((a, b) => a.roi - b.roi); // ascendente: Plotly dibuja barras horizontales de abajo hacia arriba

  const verde = getComputedStyleVar('--salud-verde');
  const rojo = getComputedStyleVar('--salud-rojo');

  graficar(
    'chart-roi-unidad',
    [{
      type: 'bar',
      orientation: 'h',
      x: filasOrdenadas.map((f) => f.roi),
      y: filasOrdenadas.map((f) => f.unidad),
      marker: { color: filasOrdenadas.map((f) => (f.roi >= 0 ? verde : rojo)) },
      hovertemplate: '%{y}: %{x:.1f}%<extra></extra>',
    }],
    { xaxis: { title: 'ROI (%)' } },
    'No hay eventos con Leads, Subscribers y Revenue cargados en el período filtrado.',
  );
}

function roiCeldaDinero(valor) {
  if (valor === null || valor === undefined) return '—';
  return `<span class="cifra-dinero">$${fmtDec.format(Number(valor) || 0)}</span>`;
}

function roiCeldaRoi(valor) {
  if (valor === null || valor === undefined) return '—';
  const positivo = valor >= 0;
  return `<span class="badge-salud ${positivo ? 'verde' : 'rojo'}">${positivo ? '+' : ''}${fmtDec1.format(valor * 100)}%</span>`;
}

function renderTablaRoi(filas) {
  tablaInteractiva(
    'tabla-roi-eventos',
    filas,
    [
      { clave: 'nombre_evento', etiqueta: 'Evento', largo: true },
      { clave: 'unidad', etiqueta: 'Unidad', render: (f) => f.unidad || '—' },
      // `clave` apunta a mes_orden (sortable, cronológico) pero se muestra
      // el rango legible — mismo patrón que vigenciaCampana en Análisis.
      { clave: 'mes_orden', etiqueta: 'Mes', render: (f) => f.mes || '—' },
      { clave: 'inversion_total', etiqueta: 'Inversión', tipo: 'moneda', render: (f) => roiCeldaDinero(f.inversion_total) },
      { clave: 'leads', etiqueta: 'Leads', tipo: 'num', render: (f) => (f.leads === null || f.leads === undefined ? '—' : fmtNum.format(f.leads)) },
      { clave: 'subscribers', etiqueta: 'Subscribers', tipo: 'num', render: (f) => (f.subscribers === null || f.subscribers === undefined ? '—' : fmtNum.format(f.subscribers)) },
      { clave: 'revenue', etiqueta: 'Revenue', tipo: 'moneda', render: (f) => roiCeldaDinero(f.revenue) },
      { clave: 'costo_por_lead', etiqueta: 'Costo/lead', tipo: 'moneda', render: (f) => (f.costo_por_lead === null || f.costo_por_lead === undefined ? '—' : '$' + fmtDec.format(f.costo_por_lead)) },
      { clave: 'conversion', etiqueta: '% conversión', tipo: 'pct', render: (f) => (f.conversion === null || f.conversion === undefined ? '—' : fmtDec1.format(f.conversion * 100) + '%') },
      {
        clave: 'roi', etiqueta: 'ROI', tipo: 'pct', render: (f) => roiCeldaRoi(f.roi),
        info: '<strong>ROI</strong> = (Revenue − Inversión) ÷ Inversión. "—" cuando el evento todavía no tiene Leads, Subscribers y Revenue cargados — no es un ROI de 0%.',
      },
    ],
    { ordenInicial: 'inversion_total', dirInicial: 'desc' },
  );
}

function renderRoi() {
  if (!DATA.roi_eventos) return; // corridas viejas, antes de este tab, no traen la clave
  renderFiltrosRoi();
  const filas = roiFilasFiltradas();
  renderKpisRoi(filas);
  renderChartRoiUnidad(filas);
  renderTablaRoi(filas);
}