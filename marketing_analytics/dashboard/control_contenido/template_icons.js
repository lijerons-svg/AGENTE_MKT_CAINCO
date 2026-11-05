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

/* Logo oficial de Mailchimp (Freddie), provisto por la usuaria — reemplaza
   la reconstrucción a mano en SVG por el ícono real de la marca. Se
   embebe como PNG en base64 (128x128, fondo amarillo de marca ya
   incluido) para no depender de ningún archivo externo ni de conexión a
   internet al abrir el HTML. */
const _MAILCHIMP_LOGO_B64 = "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";
function _svgMailchimp() {
  return (
    `<img src="data:image/png;base64,${_MAILCHIMP_LOGO_B64}" alt="Mailchimp" ` +
    'style="border-radius:18.75%;object-fit:cover;" />'
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
