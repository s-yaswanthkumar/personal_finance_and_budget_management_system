@echo off
setlocal

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

echo ===============================================================
echo  Stopping Dockerized Predictive Budget Management System
echo ===============================================================
echo.

docker compose down

echo.
echo All containers stopped and removed. Volumes (database state) preserved.
echo (To also delete database volume data, run: docker compose down -v)
echo.
pause
