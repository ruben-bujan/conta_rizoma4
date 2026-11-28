# Preguntas frecuentes — conta-rizoma4

**¿Requiere rizoma4?** Sí, como servicio HTTP (localhost:8000) y pip install -e para parsers.contrato_dominio.

**¿Qué BD necesita?** MariaDB (seed PGC) + PostgreSQL (operativo/multi-tenant).

**¿Cómo cambio puertos/credenciales?** Via config/conta_config.json (admin) o variables de entorno.

**¿Los tests fallan por PostgreSQL?** Requiere rol `rizoma` y seed. Ver README.

**¿Se puede instalar offline?** Sí, con fuentes y dependencias cacheadas.
