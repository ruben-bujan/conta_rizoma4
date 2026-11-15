-- DDL: preparar multi-moneda y multi-PGC. Idempotente.

-- 1. asiento_contable: moneda funcional del asiento
ALTER TABLE asiento_contable
    ADD COLUMN IF NOT EXISTS moneda VARCHAR(3) NOT NULL DEFAULT 'EUR';

-- 2. pgc_cuenta: marco contable (default PGC_ES)
ALTER TABLE pgc_cuenta
    ADD COLUMN IF NOT EXISTS marco_contable VARCHAR(20) NOT NULL DEFAULT 'PGC_ES';

-- 3. Tipos de cambio (cargados desde BCE o YAML)
CREATE TABLE IF NOT EXISTS tipos_cambio (
    fecha   DATE NOT NULL,
    par     VARCHAR(7) NOT NULL,  -- 'USD_EUR', 'GBP_EUR', ...
    tasa    NUMERIC(18, 8) NOT NULL,
    fuente  VARCHAR(20) NOT NULL DEFAULT 'BCE',
    PRIMARY KEY (fecha, par)
);
CREATE INDEX IF NOT EXISTS idx_tipos_fecha ON tipos_cambio(fecha);

-- 4. Mapeo de cuentas entre PGCs (preparado, vacío)
CREATE TABLE IF NOT EXISTS mapeo_cuentas (
    marco_origen   VARCHAR(20) NOT NULL,
    cuenta_origen  VARCHAR(20) NOT NULL,
    marco_destino  VARCHAR(20) NOT NULL,
    cuenta_destino VARCHAR(20) NOT NULL,
    factor_conversion NUMERIC(10, 6) NOT NULL DEFAULT 1.0,
    PRIMARY KEY (marco_origen, cuenta_origen, marco_destino)
);
