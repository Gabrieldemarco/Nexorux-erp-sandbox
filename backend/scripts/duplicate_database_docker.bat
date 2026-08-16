@echo off
REM Script para duplicar base de datos en Docker y cambiar nombre a nexorux-erp-sandbox

echo ==========================================
echo  DUPLICACION DE BASE DE DATOS DOCKER
echo ==========================================
echo.

REM 1. Iniciar Docker Desktop
echo [1/7] Iniciando Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Esperando a que Docker Desktop inicie...
timeout /t 15

REM 2. Esperar a que Docker esté listo
echo [2/7] Esperando a que Docker esté listo...
timeout /t 10

REM 3. Iniciar contenedores PostgreSQL
echo [3/7] Iniciando contenedores PostgreSQL...
cd "C:\Users\Usuario\Desktop\nexorux-erp-Sandbox"
docker-compose up -d postgres postgres-sandbox
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron iniciar los contenedores
    pause
    exit /b 1
)
echo Contenedores iniciados
echo.

REM 4. Crear backup de la base original
echo [4/7] Creando backup de base de datos original...
docker exec nexorux-postgres pg_dump -U nexorux nexorux_dev > backup_nexorux_dev.sql
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el backup
    pause
    exit /b 1
)
echo Backup creado exitosamente
echo.

REM 5. Restaurar backup en la nueva base
echo [5/7] Restaurando backup en la nueva base de datos...
docker exec -i nexorux-postgres-sandbox psql -U nexorux nexorux_erp_sandbox < backup_nexorux_dev.sql
if %errorlevel% neq 0 (
    echo ERROR: No se pudo restaurar el backup
    pause
    exit /b 1
)
echo Backup restaurado exitosamente
echo.

REM 6. Actualizar configuracion en .env
echo [6/7] Actualizando configuracion en .env...
cd backend
powershell -Command "(Get-Content .env) -replace 'nexorux_dev', 'nexorux_erp_sandbox' -replace '5432', '5433' | Set-Content .env"
if %errorlevel% neq 0 (
    echo WARNING: No se pudo actualizar .env automaticamente
    echo Por favor actualiza DATABASE_URL en .env manualmente a:
    echo DATABASE_URL=postgresql+asyncpg://nexorux:nexorux123@localhost:5433/nexorux_erp_sandbox
)
echo Configuracion actualizada
echo.

REM 7. Ejecutar migration en la nueva base
echo [7/7] Ejecutando migration de Alembic en la nueva base...
python -m alembic upgrade head
if %errorlevel% neq 0 (
    echo ERROR: No se pudo ejecutar la migration
    pause
    exit /b 1
)
echo Migration ejecutada exitosamente
echo.

echo.
echo ==========================================
echo  DUPLICACION COMPLETADA EXITOSAMENTE
echo ==========================================
echo.
echo Base de datos original: nexorux_dev (intacta, puerto 5432)
echo Base de datos nueva: nexorux_erp_sandbox (con cambios, puerto 5433)
echo.
echo Ya puedes iniciar la aplicacion con la nueva base de datos.
echo.
echo Para volver a la base original, ejecuta:
echo   docker-compose down
echo   Modifica .env para usar nexorux_dev y puerto 5432
echo   docker-compose up -d postgres
pause