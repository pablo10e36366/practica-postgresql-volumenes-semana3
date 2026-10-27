$ErrorActionPreference = 'Stop'
docker ps --filter 'label=edu.practica=postgresql-volumenes-semana3-pablo-ortega' --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker exec server_db1 psql -X -U postgres -d postgres -c "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname='test') AS test_disponible;"
docker exec server_db2 psql -X -U postgres -d test -c 'SELECT id, fullname, status FROM customer ORDER BY id;'
docker inspect server_db2 --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}'
docker volume inspect pgdata --format 'Nombre={{.Name}} Controlador={{.Driver}}'
