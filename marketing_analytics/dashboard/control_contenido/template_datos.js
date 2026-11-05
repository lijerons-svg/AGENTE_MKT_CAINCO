/* Derivaciones de dominio compartidas por todas las pestañas.
   Todo sale de DATA (lo que ya está en la base): acá no se inventa ninguna
   métrica, solo se combinan las existentes. */

const UNIDADES = Object.keys(DATA.unidades).sort();

/* Engagement de una publicación: interacciones sobre visualizaciones.
   No se usa alcance porque Meta dejó de informarlo en Facebook (devuelve 0
   incluso en publicaciones con miles de visualizaciones), así que mezclarlo
   daría porcentajes falsos para media base de datos. */
function engagementPost(p) {
  return p.visualizaciones > 0 ? (p.total_interacciones / p.visualizaciones) * 100 : 0;
}

/* Publicaciones de todas las unidades, cada una marcada con su unidad. */
function publicacionesGlobales() {
  return UNIDADES.flatMap((u) =>
    DATA.unidades[u].meta_organico.map((p) => Object.assign({ _unidad: u }, p)),
  );
}

function campanasGlobales() {
  return UNIDADES.flatMap((u) =>
    DATA.unidades[u].meta_ads.map((c) => Object.assign({ _unidad: u }, c)),
  );
}

function calendarioGlobal() {
  return UNIDADES.flatMap((u) =>
    DATA.unidades[u].calendario.map((c) => Object.assign({ _unidad: u }, c)),
  );
}

/* Años y meses disponibles considerando TODAS las fuentes. Se calculan una
   sola vez y globalmente para que el filtro de período sea idéntico en
   Análisis y Mailchimp: si cada pestaña listara solo sus propias fechas,
   los mismos chips mostrarían opciones distintas. */
const _FECHAS_GLOBALES = [
  ...publicacionesGlobales().map((p) => p.fecha),
  ...campanasGlobales().map((c) => c.fecha),
  ...calendarioGlobal().map((c) => c.fecha_publicacion),
  ...(DATA.mailchimp || []).map((m) => m.fecha),
].filter(Boolean);

const ANIOS_DISPONIBLES = [...new Set(_FECHAS_GLOBALES.map(anioDe))].sort().reverse();
const MESES_DISPONIBLES = [...new Set(_FECHAS_GLOBALES.map(mesDe))].sort();

/* Unidades que sí tienen contenido propio (orgánico, pauta o planner). Las
   configuradas pero sin un solo registro solo ensucian el filtro. */
function unidadesConDatos() {
  return UNIDADES.filter((u) => {
    const d = DATA.unidades[u];
    return d.meta_organico.length || d.meta_ads.length || d.calendario.length;
  });
}

/* Filtra por las unidades elegidas (vacío = todas) y devuelve las filas
   marcadas con su unidad de origen. */
function filasDeUnidades(clave) {
  const seleccion = estado.unidades.size ? [...estado.unidades] : UNIDADES;
  return seleccion.flatMap((u) =>
    (DATA.unidades[u]?.[clave] || []).map((r) => Object.assign({ _unidad: u }, r)),
  );
}

/* Formato normalizado de una publicación. Facebook y Instagram nombran los
   tipos distinto (imagen/album/video vs FEED/REELS); se unifican para poder
   compararlos en un mismo gráfico. */
const FORMATOS = {
  imagen: 'Imagen',
  album: 'Carrusel',
  video: 'Video',
  link: 'Enlace',
  status: 'Texto',
  feed: 'Feed',
  reels: 'Reel',
  story: 'Historia',
  carousel_album: 'Carrusel',
  image: 'Imagen',
};
function formatoPost(p) {
  return FORMATOS[(p.tipo || '').toLowerCase()] || (p.tipo || 'Sin tipo');
}

/* Meses con datos en todo el tablero, para ubicar "el mes actual" cuando el
   mes calendario todavía no tiene publicaciones. */
function ultimoMesConDatos() {
  const meses = publicacionesGlobales().map((p) => claveMes(p.fecha)).filter(Boolean);
  return meses.length ? meses.sort().pop() : claveMes(hoyISO());
}

function mesAnteriorA(anioMes) {
  const [a, m] = anioMes.split('-').map(Number);
  const d = new Date(a, m - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function ultimoDiaDelMes(anioMes) {
  const [a, m] = anioMes.split('-').map(Number);
  return new Date(a, m, 0).getDate();
}

/* Mes en curso vs. el mismo tramo del mes anterior (mismo día de corte),
   no el mes anterior completo — comparar el 23 de septiembre contra los
   31 días completos de agosto siempre muestra una caída, exista o no una
   caída real. Si el mes calendario en curso todavía no tiene ningún dato
   (recién empezó y no hubo sync), se cae al último mes cerrado completo
   contra el anterior a ese, sin recorte — ahí sí corresponde comparar
   meses completos porque ambos ya cerraron. */
function mesActualYAnteriorMTD() {
  const hoy = hoyISO();
  const mesCalendarioActual = claveMes(hoy);
  const hayDatosEsteMes =
    publicacionesGlobales().some((p) => claveMes(p.fecha) === mesCalendarioActual) ||
    campanasGlobales().some((c) => claveMes(c.fecha) === mesCalendarioActual) ||
    (DATA.mailchimp || []).some((m) => claveMes(m.fecha) === mesCalendarioActual);

  if (hayDatosEsteMes) {
    const diaHoy = Number(hoy.slice(8, 10));
    const mesPrevio = mesAnteriorA(mesCalendarioActual);
    return {
      mesActual: mesCalendarioActual,
      mesPrevio,
      diaCorteActual: diaHoy,
      diaCortePrevio: Math.min(diaHoy, ultimoDiaDelMes(mesPrevio)),
      enCurso: true,
    };
  }
  const mesActual = ultimoMesConDatos();
  return { mesActual, mesPrevio: mesAnteriorA(mesActual), diaCorteActual: 31, diaCortePrevio: 31, enCurso: false };
}

/* Filas de un mes puntual, recortadas hasta un día de corte (inclusive). */
function filtrarMesConCorte(filas, campoFecha, anioMes, diaCorte) {
  return filas.filter((f) => {
    const fecha = f[campoFecha];
    return fecha && claveMes(fecha) === anioMes && Number(fecha.slice(8, 10)) <= diaCorte;
  });
}

/* ---------- referencias de industria ----------
   Umbrales publicados para promedios multi-industria de Meta Ads y email
   marketing. Sirven para saber si un número es bueno en términos absolutos,
   no solo comparado con el resto de las campañas propias. `invertir` marca
   las métricas donde menos es mejor (rebotes, bajas, saturación). */
const REFERENCIAS = {
  ctr: { bueno: 1.0, malo: 0.5, texto: 'Promedio multi-industria en Meta Ads: ~0,9%. Verde ≥1%, rojo <0,5%.' },
  conversion: { bueno: 10, malo: 3, texto: 'De cada 100 clics, cuántos terminaron en el resultado buscado. Verde ≥10%, rojo <3%.' },
  frecuencia: { bueno: 2, malo: 3, invertir: true, texto: 'Veces que cada persona vio el anuncio. Sobre 3 la audiencia se satura. Verde <2, rojo >3.' },
  openRate: { bueno: 25, malo: 15, texto: 'Promedio de email marketing: 21-25%. Verde ≥25%, rojo <15%.' },
  clickRate: { bueno: 3, malo: 1, texto: 'Promedio de email marketing: ~2,5%. Verde ≥3%, rojo <1%.' },
  ctor: { bueno: 14, malo: 8, texto: 'De los que abrieron, cuántos clickearon. Promedio: 10-14%. Verde ≥14%, rojo <8%.' },
  bounceRate: { bueno: 2, malo: 5, invertir: true, texto: 'Sobre 5% indica una lista desactualizada. Verde <2%, rojo >5%.' },
  bajaRate: { bueno: 0.2, malo: 0.5, invertir: true, texto: 'Desuscripciones por envío. Verde <0,2%, rojo >0,5%.' },
};

/* Devuelve 'bueno' | 'medio' | 'malo' | 'neutro' según la referencia. */
function nivel(clave, valor) {
  const r = REFERENCIAS[clave];
  if (!r || valor === null || valor === undefined || !Number.isFinite(valor)) return 'neutro';
  if (r.invertir) {
    if (valor === 0) return 'neutro';
    return valor < r.bueno ? 'bueno' : valor > r.malo ? 'malo' : 'medio';
  }
  return valor >= r.bueno ? 'bueno' : valor < r.malo ? 'malo' : 'medio';
}

/* Celda de tabla con punto de color según la referencia. */
function celdaNivel(clave, valor, texto) {
  return `<span class="celda-nivel ${nivel(clave, valor)}">${texto}</span>`;
}

function infoReferencia(clave, extra) {
  const r = REFERENCIAS[clave];
  return (
    '<strong>Referencia de industria</strong>' +
    (extra ? `<code>${extra}</code>` : '') +
    (r ? r.texto : '') +
    '<br><br>El color compara contra ese promedio publicado, no contra tus otras campañas.'
  );
}

/* Estado de actividad por unidad, criterio único reutilizado por el Resumen
   y por el ranking: verde ≤7 días, amarillo ≤14, rojo después. */
function saludPerfiles() {
  return UNIDADES.map((unidad) => {
    const posts = DATA.unidades[unidad].meta_organico;
    const ultima = posts.reduce((max, p) => (p.fecha > max.fecha ? p : max), { fecha: '' });
    if (!ultima.fecha) {
      return { unidad, post: null, dias: null, color: 'rojo', etiqueta: 'Sin datos' };
    }
    const dias = diasDesde(ultima.fecha);
    const color = dias <= 7 ? 'verde' : dias <= 14 ? 'amarillo' : 'rojo';
    const etiqueta = dias <= 7 ? 'Activo' : dias <= 14 ? 'Atención' : 'Inactivo';
    return { unidad, post: ultima, dias, color, etiqueta };
  }).sort((a, b) => (b.dias ?? 9999) - (a.dias ?? 9999));
}

/* Puntaje 0-100 por unidad. Pondera cuatro cosas que un community manager
   mira para decidir dónde poner esfuerzo; los pesos son una convención del
   tablero (no una métrica de Meta) y se explican en pantalla. */
function scoreUnidad(unidad) {
  const posts = DATA.unidades[unidad].meta_organico;
  if (!posts.length) {
    return {
      unidad, score: 0, actividad: 0, engagement: 0, consistencia: 0, volumen: 0,
      publicaciones: 0, engMedio: 0, dias: null,
    };
  }

  const mes = ultimoMesConDatos();
  const delMes = posts.filter((p) => claveMes(p.fecha) === mes);
  const ultima = posts.reduce((max, p) => (p.fecha > max ? p.fecha : max), '');
  const dias = diasDesde(ultima) ?? 999;

  // Actividad (35): cuánto hace que publicó. 0 días = 35 pts, 21+ días = 0.
  const actividad = Math.max(0, 1 - dias / 21) * 35;
  // Engagement (30): promedio del mes, con 2% como referencia de "muy bueno".
  const engMedio = delMes.length ? delMes.reduce((a, p) => a + engagementPost(p), 0) / delMes.length : 0;
  const engagement = Math.min(1, engMedio / 2) * 30;
  // Consistencia (20): semanas del mes con al menos una publicación.
  const semanas = new Set(delMes.map((p) => Math.ceil(Number(p.fecha.slice(8, 10)) / 7)));
  const consistencia = Math.min(1, semanas.size / 4) * 20;
  // Volumen (15): 12 publicaciones al mes como referencia de ritmo sostenido.
  const volumen = Math.min(1, delMes.length / 12) * 15;

  return {
    unidad,
    score: Math.round(actividad + engagement + consistencia + volumen),
    actividad: Math.round(actividad),
    engagement: Math.round(engagement),
    consistencia: Math.round(consistencia),
    volumen: Math.round(volumen),
    publicaciones: delMes.length,
    engMedio,
    dias,
  };
}

function scoresUnidades() {
  return UNIDADES.map(scoreUnidad).sort((a, b) => b.score - a.score);
}

/* Health Score global: promedio de los puntajes por unidad, más el
   cumplimiento del planner. Da una sola cifra para "¿cómo estamos?". */
function healthScore() {
  const scores = scoresUnidades().filter((s) => s.publicaciones !== undefined);
  const conDatos = scores.filter((s) => s.score > 0);
  const promedio = conDatos.length ? conDatos.reduce((a, s) => a + s.score, 0) / conDatos.length : 0;

  const hoy = hoyISO();
  const vencidas = calendarioGlobal().filter((c) => c.fecha_publicacion && c.fecha_publicacion <= hoy);
  const publicadas = vencidas.filter((c) => claseEstado(c.estado) === 'publicado').length;
  const cumplimiento = vencidas.length ? (publicadas / vencidas.length) * 100 : null;

  const activos = saludPerfiles().filter((s) => s.color === 'verde').length;
  const totalUnidades = UNIDADES.length;

  // El planner pesa un cuarto del total cuando hay datos; si no hay planner
  // cargado, el score es solo el promedio de unidades (no se penaliza).
  const score = cumplimiento === null ? promedio : promedio * 0.75 + cumplimiento * 0.25;

  return {
    score: Math.round(score),
    promedioUnidades: Math.round(promedio),
    cumplimiento,
    activos,
    totalUnidades,
    inactivos: totalUnidades - activos,
  };
}
