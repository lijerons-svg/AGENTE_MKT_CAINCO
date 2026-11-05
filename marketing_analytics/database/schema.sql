-- Base histórica de Marketing Analytics.
-- `uid` es la clave de deduplicación: fuente|perfil|id_publicacion|id_campana|fecha

CREATE TABLE IF NOT EXISTS meta_organico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    perfil TEXT NOT NULL,
    pagina TEXT NOT NULL,
    red TEXT NOT NULL,
    fecha_publicacion TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    alcance INTEGER NOT NULL DEFAULT 0,
    visualizaciones INTEGER NOT NULL DEFAULT 0,
    total_clics INTEGER NOT NULL DEFAULT 0,
    clics_enlace INTEGER NOT NULL DEFAULT 0,
    reacciones INTEGER NOT NULL DEFAULT 0,
    comentarios INTEGER NOT NULL DEFAULT 0,
    compartidos INTEGER NOT NULL DEFAULT 0,
    total_interacciones INTEGER NOT NULL DEFAULT 0,
    id_publicacion_origen TEXT NOT NULL,
    imagen_url TEXT NOT NULL DEFAULT '',
    link TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meta_ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    cuenta_publicitaria TEXT NOT NULL,
    perfil_unidad TEXT NOT NULL,
    red TEXT NOT NULL,
    campana TEXT NOT NULL,
    fecha_publicacion TEXT NOT NULL,
    objetivo TEXT NOT NULL,
    moneda TEXT NOT NULL DEFAULT '',
    importe_gastado REAL NOT NULL DEFAULT 0,
    alcance INTEGER NOT NULL DEFAULT 0,
    impresiones INTEGER NOT NULL DEFAULT 0,
    clics INTEGER NOT NULL DEFAULT 0,
    ctr REAL NOT NULL DEFAULT 0,
    cpc REAL NOT NULL DEFAULT 0,
    resultados INTEGER NOT NULL DEFAULT 0,
    id_campana_origen TEXT NOT NULL,
    pagina_origen_id TEXT NOT NULL DEFAULT '',
    conversaciones_iniciadas INTEGER NOT NULL DEFAULT 0,
    fecha_inicio_campana TEXT,
    fecha_fin_campana TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mailchimp_campanas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    id_campana_origen TEXT NOT NULL,
    nombre_campana TEXT NOT NULL DEFAULT '',
    fecha_envio TEXT NOT NULL,
    destinatarios INTEGER NOT NULL DEFAULT 0,
    entregas INTEGER NOT NULL DEFAULT 0,
    tasa_apertura REAL NOT NULL DEFAULT 0,
    aperturas_unicas INTEGER NOT NULL DEFAULT 0,
    aperturas_totales INTEGER NOT NULL DEFAULT 0,
    tasa_clics REAL NOT NULL DEFAULT 0,
    clics_unicos INTEGER NOT NULL DEFAULT 0,
    clics_totales INTEGER NOT NULL DEFAULT 0,
    tasa_rebote REAL NOT NULL DEFAULT 0,
    rebotes INTEGER NOT NULL DEFAULT 0,
    bajas INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mailchimp_enlaces_whatsapp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_campana_origen TEXT NOT NULL,
    url TEXT NOT NULL,
    clics INTEGER NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (id_campana_origen, url)
);

-- Sin conector activo aún (LinkedIn fuera de alcance por ahora); se deja
-- la tabla lista para no requerir una migración cuando se active.
CREATE TABLE IF NOT EXISTS linkedin_organico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    pagina TEXT NOT NULL,
    fecha_publicacion TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    impresiones INTEGER NOT NULL DEFAULT 0,
    alcance INTEGER NOT NULL DEFAULT 0,
    clics INTEGER NOT NULL DEFAULT 0,
    reacciones INTEGER NOT NULL DEFAULT 0,
    comentarios INTEGER NOT NULL DEFAULT 0,
    compartidos INTEGER NOT NULL DEFAULT 0,
    interacciones INTEGER NOT NULL DEFAULT 0,
    id_publicacion_origen TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calendario_publicaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    id_origen TEXT NOT NULL,
    fecha_publicacion TEXT,
    perfil TEXT NOT NULL DEFAULT '',
    bu TEXT NOT NULL DEFAULT '',
    campana_evento TEXT NOT NULL DEFAULT '',
    tipo TEXT NOT NULL DEFAULT '',
    canal TEXT NOT NULL DEFAULT '',
    formato TEXT NOT NULL DEFAULT '',
    objetivo TEXT NOT NULL DEFAULT '',
    descripcion_copy TEXT NOT NULL DEFAULT '',
    estado TEXT NOT NULL DEFAULT '',
    responsable TEXT NOT NULL DEFAULT '',
    inversion_usd REAL NOT NULL DEFAULT 0,
    link_publicacion TEXT NOT NULL DEFAULT '',
    vobo_gcri TEXT NOT NULL DEFAULT '',
    notas TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS control_perfiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    perfil TEXT NOT NULL,
    red TEXT NOT NULL,
    anio_mes TEXT NOT NULL,
    seguidores INTEGER NOT NULL DEFAULT 0,
    seguidores_ganados INTEGER NOT NULL DEFAULT 0,
    publicaciones_mes INTEGER NOT NULL DEFAULT 0,
    likes_mes INTEGER NOT NULL DEFAULT 0,
    visualizaciones_mes INTEGER NOT NULL DEFAULT 0,
    comentarios_mes INTEGER NOT NULL DEFAULT 0,
    compartidos_mes INTEGER NOT NULL DEFAULT 0,
    interacciones_mes INTEGER NOT NULL DEFAULT 0,
    tasa_engagement REAL NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ejecuciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT,
    tiempo_ejecucion_seg REAL,
    estado TEXT NOT NULL DEFAULT 'en_progreso',
    registros_descargados INTEGER NOT NULL DEFAULT 0,
    registros_nuevos INTEGER NOT NULL DEFAULT 0,
    registros_actualizados INTEGER NOT NULL DEFAULT 0,
    registros_descartados INTEGER NOT NULL DEFAULT 0,
    errores TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL REFERENCES ejecuciones (id),
    nivel TEXT NOT NULL,
    fuente TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
