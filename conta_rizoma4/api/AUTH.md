# Administración de usuarios y permisos de API

## Primer administrador

El endpoint HTTP `/auth/registro` no permite autoalta ni crear administradores. Durante el despliegue inicial, provisiona el primer usuario administrador desde la máquina de administración:

```bash
python scripts/crear_admin_inicial.py \
  --usuario-id ADMIN-1 --email admin@example.org \
  --nombre "Administración" --empresa-id EMPRESA-1 --confirmar
```

El script pide la contraseña por consola, exige una empresa configurada, serializa el bootstrap y falla si ya existe un administrador. Requiere las variables de conexión PostgreSQL del proyecto.

## Altas ordinarias

Un administrador autenticado puede crear usuarios `aux_obra`, `visador` o `aprobador`. La empresa se toma de la sesión del administrador, no del cuerpo HTTP. El endpoint rechaza campos extra, contraseñas inferiores a 12 caracteres y cualquier rol fuera de esa lista. Las altas adicionales de administradores requieren un procedimiento local de administración, nunca el endpoint público.

Los tokens identifican al usuario y exponen `actor_id`; en cada petición se vuelve a leer de PostgreSQL el estado activo, rol y empresa actuales. Los claims antiguos del token no conservan permisos revocados.

Los roles de la API se mapean al dominio contable en `conta_rizoma4/api/deps.py`: `aux_obra` → `AUXILIAR`, `visador` → `JEFE_CONTABILIDAD`, `aprobador` → `SUBDIRECTOR` y `admin` → `ADMIN`. Con este mapeo, `aux_obra` no puede registrar asientos en el núcleo porque `ASIENTO_DIARIO` exige `JEFE_CONTABILIDAD` según `gobernanza/matriz_competencias.md`.

Configura `CONTA_JWT_SECRET` con al menos 32 bytes aleatorios en cualquier despliegue persistente o con más de un proceso. Si no se configura en desarrollo, se genera un secreto aleatorio solo para ese proceso: al reiniciar, los tokens anteriores dejan de servir. No se usa un secreto conocido por defecto.

La API no habilita CORS entre orígenes por defecto. Si el frontend o un cliente vive en otro origen, configura `CONTA_API_CORS_ORIGINS` con una lista separada por comas de orígenes concretos; el middleware no acepta cookies ni credenciales de navegador.

Visar requiere `visador` (o administrador) y registra el ID autenticado. Aprobar requiere `aprobador` (o administrador), registra su ID autenticado y exige que sea distinto del creador y del visador. El cliente no puede declarar la identidad de ninguno de esos actores.
