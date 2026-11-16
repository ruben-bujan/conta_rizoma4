CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id   VARCHAR(50) PRIMARY KEY,
    email        VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre       VARCHAR(255) NOT NULL,
    rol          VARCHAR(20) NOT NULL,
    empresa_id   VARCHAR(50) NOT NULL,
    activo       BOOLEAN DEFAULT TRUE,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
