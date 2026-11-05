/* Iconos de plataforma con la forma real de cada marca (cuadrado redondeado
   para Facebook, Instagram y Mailchimp), no una insignia genérica.

   El de Instagram lleva un degradado, y un degradado SVG se referencia por
   id. Con varios iconos en la página todos apuntaban al mismo id: cuando el
   primero se quitaba del DOM en un repintado, los demás se quedaban sin
   relleno y desaparecían. Por eso el id se genera único en cada llamada. */
let _contadorIconos = 0;

function _svgFacebook() {
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    '<rect width="512" height="512" rx="96" fill="#3b5998"/>' +
    '<path d="M341 176h-46c-11 0-17 7-17 18v38h63l-8 62h-55v168h-66V294h-56v-62h56v-45c0-46 27-79 78-79h51z" fill="#fff"/>' +
    '</svg>'
  );
}

function _svgInstagram() {
  const id = 'ig-grad-' + (_contadorIconos += 1);
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    `<defs><linearGradient id="${id}" x1="0%" y1="100%" x2="70%" y2="0%">` +
    '<stop offset="0%" stop-color="#f9ce34"/><stop offset="20%" stop-color="#ee8c34"/>' +
    '<stop offset="45%" stop-color="#dc2f6d"/><stop offset="75%" stop-color="#b12ba8"/>' +
    '<stop offset="100%" stop-color="#7d2ae8"/></linearGradient></defs>' +
    `<rect width="512" height="512" rx="118" fill="url(#${id})"/>` +
    '<rect x="96" y="96" width="320" height="320" rx="86" fill="none" stroke="#fff" stroke-width="34"/>' +
    '<circle cx="256" cy="256" r="82" fill="none" stroke="#fff" stroke-width="34"/>' +
    '<circle cx="374" cy="139" r="27" fill="#fff"/>' +
    '</svg>'
  );
}

/* Freddie, la mascota de Mailchimp: cabeza negra sobre amarillo, orejas a
   los costados, gorra ladeada con visera, ojos guiñados y sonrisa ancha.
   Simplificado para que siga siendo reconocible a 13px. */
function _svgMailchimp() {
  const negro = '#241c1c';
  const amarillo = '#ffe01b';
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    `<rect width="512" height="512" rx="96" fill="${amarillo}"/>` +
    // orejas
    `<ellipse cx="126" cy="286" rx="34" ry="42" fill="${negro}"/>` +
    `<ellipse cx="386" cy="286" rx="34" ry="42" fill="${negro}"/>` +
    // cabeza
    `<ellipse cx="256" cy="292" rx="126" ry="132" fill="${negro}"/>` +
    // gorra: copa ladeada + visera hacia la izquierda
    `<path d="M142 196c14-64 60-100 118-100s100 34 114 92c-32-34-74-52-118-52-42 0-84 22-114 60z" fill="${negro}"/>` +
    `<path d="M144 190c-40-6-70-26-66-50 4-22 34-30 66-20" fill="${negro}"/>` +
    // ojos guiñados
    `<path d="M186 272c12-14 32-14 44 0" fill="none" stroke="${amarillo}" stroke-width="20" stroke-linecap="round"/>` +
    `<path d="M282 272c12-14 32-14 44 0" fill="none" stroke="${amarillo}" stroke-width="20" stroke-linecap="round"/>` +
    // hocico: sonrisa ancha con la línea de la boca
    `<path d="M172 328c0 52 38 84 84 84s84-32 84-84z" fill="${amarillo}"/>` +
    `<path d="M180 348h152" fill="none" stroke="${negro}" stroke-width="14" stroke-linecap="round"/>` +
    '</svg>'
  );
}

function _svgLinkedin() {
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    '<rect width="512" height="512" rx="96" fill="#0a66c2"/>' +
    '<rect x="112" y="200" width="62" height="196" fill="#fff"/>' +
    '<circle cx="143" cy="140" r="38" fill="#fff"/>' +
    '<path d="M216 200h60v28h1c9-16 30-33 68-33 72 0 85 44 85 101v100h-62V308c0-31-1-71-45-71-45 0-52 34-52 69v90h-55z" fill="#fff"/>' +
    '</svg>'
  );
}

function _svgTiktok() {
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    '<rect width="512" height="512" rx="96" fill="#010101"/>' +
    '<path d="M320 112v186a52 52 0 1 1-42-51v-46a97 97 0 1 0 81 95V208c17 13 38 20 60 20v-46c-38 0-68-28-72-70z" fill="#25f4ee" transform="translate(-9,-9)"/>' +
    '<path d="M320 112v186a52 52 0 1 1-42-51v-46a97 97 0 1 0 81 95V208c17 13 38 20 60 20v-46c-38 0-68-28-72-70z" fill="#fe2c55" transform="translate(9,9)"/>' +
    '<path d="M320 112v186a52 52 0 1 1-42-51v-46a97 97 0 1 0 81 95V208c17 13 38 20 60 20v-46c-38 0-68-28-72-70z" fill="#fff"/>' +
    '</svg>'
  );
}

function _svgOtro() {
  return (
    '<svg viewBox="0 0 512 512" width="18" height="18">' +
    '<rect width="512" height="512" rx="96" fill="#8a8b93"/>' +
    '<circle cx="256" cy="256" r="70" fill="#fff"/>' +
    '</svg>'
  );
}

const ICONOS_PLATAFORMA = {
  facebook: _svgFacebook,
  instagram: _svgInstagram,
  linkedin: _svgLinkedin,
  mailchimp: _svgMailchimp,
  tiktok: _svgTiktok,
  otro: _svgOtro,
};

/* tamano: '' (18px) | 'chico' (13px) | 'grande' (40px) | 'xl' (52px).
   El tamaño real lo fija el CSS, no el atributo del SVG. */
function iconoPlataforma(clave, tamano) {
  const generar = ICONOS_PLATAFORMA[clave] || ICONOS_PLATAFORMA.otro;
  return `<span class="icono-plataforma${tamano ? ' ' + tamano : ''}">${generar()}</span>`;
}

function colorPlataforma(texto) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue('--plataforma-' + clasePlataforma(texto))
    .trim();
}

function clasePlataforma(texto) {
  const t = (texto || '').toLowerCase();
  if (t.includes('facebook') || t === 'fb') return 'facebook';
  if (t.includes('instagram') || t === 'ig') return 'instagram';
  if (t.includes('linkedin')) return 'linkedin';
  if (t.includes('tiktok')) return 'tiktok';
  if (t.includes('mailchimp') || t.includes('mail')) return 'mailchimp';
  return 'otro';
}

const NOMBRE_PLATAFORMA = {
  facebook: 'Facebook',
  instagram: 'Instagram',
  linkedin: 'LinkedIn',
  mailchimp: 'Mailchimp',
  tiktok: 'TikTok',
  otro: 'Otro canal',
};
