# Mostrar los resultados con pgAdmin 4

1. Iniciar Docker Desktop y abrir pgAdmin 4.
2. Registrar dos conexiones nuevas con estos parámetros:

| Parámetro | Primera prueba | Prueba persistente |
|---|---|---|
| Nombre descriptivo | Semana3_server_db1 | Semana3_server_db2 |
| Host | 127.0.0.1 | 127.0.0.1 |
| Puerto | 5433 | 5434 |
| Base de mantenimiento | postgres | test |
| Usuario | postgres | postgres |
| Contraseña | La de `.env.local` | La de `.env.local` |

La contraseña permanece en el equipo; no incluirla en una captura ni en GitHub. No es necesario guardar la contraseña en pgAdmin.

3. En la primera conexión, seleccionar `Databases > postgres`, abrir Query Tool y ejecutar:

```sql
SELECT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'test'
) AS test_disponible;
```

El resultado es `false`: ese contenedor nuevo no monta el almacenamiento anterior.

4. En la segunda conexión, seleccionar `Databases > test`, abrir Query Tool y ejecutar:

```sql
SELECT id, fullname, status
FROM customer
ORDER BY id;
```

El resultado son los dos clientes conservados en `pgdata`. Abrir Query Tool no vuelve a crear ni insertar datos.

Las capturas gráficas de la entrega se tomaron con una sesión de pgAdmin y una base de configuración aisladas dentro de `.local`. Los ajustes y conexiones anteriores del usuario no se modificaron. La sesión auxiliar se cerró después de comprobar las consultas. Para repetirlo en la aplicación habitual, registrar estas dos conexiones como se indica arriba.
