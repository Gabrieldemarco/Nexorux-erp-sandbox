@echo off
REM Script para duplicar base de datos y cambiar nombre a nexorux-erp-sandbox

echo Iniciando duplicacion de base de datos...
echo.

REM 1. Crear backup de la base original
echo [1/5] Creando backup de base de datos original...
pg_dump -U nexorux -h localhost nexorux_dev > backup_nexorux_dev.sql
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el backup
    pause
    exit /b 1
)
echo Backup creado exitosamente
echo.

REM 2. Crear nueva base de datos
echo [2/5] Creando nueva base de datos nexorux-erp-sandbox...
psql -U nexorux -h localhost -c "CREATE DATABASE \"nexorux-erp-sandbox\";"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear la nueva base de datos
    echo Intentando continuar si ya existe...
)
echo Base de datos creada o ya existe
echo.

REM 3. Restaurar backup en la nueva base
echo [3/5] Restaurando backup en la nueva base de datos...
psql -U nexorux -h localhost "nexorux-erp-sandbox" < backup_nexorux_dev.sql
if %errorlevel% neq 0 (
    echo ERROR: No se pudo restaurar el backup
    pause
    exit /b 1
)
echo Backup restaurado exitosamente
echo.

REM 4. Actualizar configuracion en .env
echo [4/5] Actualizando configuracion en .env...
cd backend
powershell -Command "(Get-Content .env) -replace 'nexorux_dev', 'nexorux-erp-sandbox' | Set-Content .env"
if %errorlevel% neq 0 (
    echo WARNING: No se pudo actualizar .env automaticamente
    echo Por favor actualiza DATABASE_URL en .env manualmente
)
echo Configuracion actualizada
echo.

REM 5. Ejecutar migration en la nueva base
echo [5/5] Ejecutando migration de Alembic...
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
echo Base de datos original: nexorux_dev (intacta)
echo Base de datos nueva: nexorux-erp-sandbox (con cambios)
echo.
echo Ya puedes iniciar la aplicacion con la nueva base de datos.
pause