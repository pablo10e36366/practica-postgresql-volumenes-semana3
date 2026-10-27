# PostgreSQL y volúmenes Docker — Semana 3

Práctica de **Pablo Ortega**, Desarrollo de Software, Instituto Sudamericano, para Tendencias Tecnológicas.

**[Abrir el informe completo con las capturas](informe.md)**

## Objetivo y resultado

Se ejecutaron dos pruebas reales con PostgreSQL 16: al sustituir server_db1 sin reutilizar el volumen anterior, test no apareció; al sustituir server_db2 montando el mismo volumen pgdata, se conservaron la base, la tabla y dos registros. El volumen persistente no se eliminó. La imagen oficial también crea volúmenes anónimos: la primera prueba compara su reutilización, no una supuesta destrucción de todos los datos.

## Archivos

- `informe.md`: los diez apartados del docente, fundamentos, procedimiento y bibliografía APA.
- `evidencias/`: 14 capturas reales, salidas TXT, un diagrama conceptual, resultados JSON y registro de comandos.
- `scripts/`: SQL, ejecución completa y consulta de resultados.
- `.env.example`: nombre de la variable de contraseña, sin un secreto.

## Consultar el trabajo en este equipo

La carpeta es `C:\Users\pablo\practica_postgresql_volumenes`. Docker Desktop debe estar iniciado.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\consultar-resultados.ps1
```

Los puertos usados son 127.0.0.1:5433 y 127.0.0.1:5434. Para entrar al cliente de la base persistente:

```powershell
docker exec -it server_db2 psql -U postgres -d test
```

El cliente interno usa la autenticación local de la imagen. Para conectar desde otro cliente se necesita la contraseña de `.env.local`, que permanece sólo en el equipo y no se publica.

## Reproducir en un entorno sin esos nombres ocupados

Requisitos: Docker Desktop funcionando con contenedores Linux, Python 3 y Pillow para capturas opcionales. Si no hay una consola Windows real, se guardan TXT y JSON; las capturas se pueden tomar manualmente. Ubuntu WSL 2 también se verificó, aunque el script principal se ejecuta desde Windows.

```powershell
python -m pip install Pillow
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ejecutar-practica.ps1
```

El script comprueba que server_db1, server_db2 y pgdata estén libres; si alguno existe, se detiene. Genera una contraseña aleatoria en `.env.local` si falta y no la muestra. No borra volúmenes, usa etiquetas para comprobar propiedad antes de retirar contenedores y sólo publica puertos en localhost. **No vuelvas a ejecutar la práctica sobre los resultados existentes de este equipo**; para mostrarlos usa el script de consulta.

El parámetro técnico `--reuse-owned-empty-volume` se utilizó únicamente en la repetición documentada de este mismo ensayo, conservando pgdata después de corregir la captura. Exige la etiqueta de este trabajo; no vacía ni borra un volumen. La ejecución se detendría si la base test ya existiera al intentar crearla. No se requiere para reproducir desde cero.

## Evidencias y alcance

Las capturas se tomaron durante la ejecución real de los comandos. Se recortó solamente el marco de la ventana para evitar mostrar el escritorio. Los registros TXT y JSON conservan las instrucciones, entradas SQL y salidas. `resultados.json` contiene siete comprobaciones exitosas y los identificadores antes/después. `creacion-original-pgdata.txt` registra su primera creación; el volumen se conservó al repetir la captura.

No se generó audio MP3. La contraseña local, respaldos de preparación, credenciales de GitHub y archivos auxiliares están excluidos del repositorio.
