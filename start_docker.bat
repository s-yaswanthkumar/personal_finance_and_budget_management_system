@echo off
setlocal

:: Resolve project root path
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

echo ===============================================================
echo  AI Predictive Budget Management System - Docker Launcher
echo ===============================================================
echo Project Root: %PROJECT_DIR%
echo.

:: 1. Verify Docker Engine status
echo [1/4] Checking Docker Engine daemon...
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ready

echo       Docker Engine is not responding. Attempting to start Docker Desktop...
start "" "C:\Users\%USERNAME%\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"

echo       Waiting for Docker daemon to become responsive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$sw = [System.Diagnostics.Stopwatch]::StartNew(); do { docker info >$null 2>&1; if ($LASTEXITCODE -eq 0) { exit 0 }; Start-Sleep -Seconds 2 } while ($sw.Elapsed.TotalSeconds -lt 45); exit 1"
if errorlevel 1 (
    echo       [ERROR] Could not connect to Docker Engine.
    echo               Please ensure Docker Desktop is running and try again.
    pause
    exit /b 1
)

:docker_ready
echo       Docker Engine is active and healthy!
echo.

:: Check if initial database credentials need configuration
findstr /C:"YOUR_PGADMIN_PASSWORD" .env.docker >nul 2>&1
if not errorlevel 1 (
    echo ===============================================================
    echo  [SETUP REQUIRED] PostgreSQL pgAdmin password is not set in .env.docker.
    echo  Launching interactive database configuration wizard...
    echo ===============================================================
    python configure_database.py
)

:: 2. Build and start containers with Docker Compose
echo [2/4] Building and starting containerized services with Docker Compose...
docker compose --env-file .env.docker up --build -d

if errorlevel 1 (
    echo [ERROR] Docker Compose build or startup failed. Inspect logs above.
    pause
    exit /b 1
)

echo.
:: 3. Wait for services to become healthy
echo [3/4] Waiting for backend and database healthchecks to report healthy...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$sw = [System.Diagnostics.Stopwatch]::StartNew(); do { $res = (docker compose ps --format json | ConvertFrom-Json); $unhealthy = $res | Where-Object { $_.Health -and $_.Health -ne 'healthy' }; if (-not $unhealthy -and $res.Count -ge 3) { exit 0 }; Start-Sleep -Seconds 2 } while ($sw.Elapsed.TotalSeconds -lt 60); exit 0"

echo.
:: 4. Summary & Endpoints
echo ===============================================================
echo  DOCKER CONTAINER SYSTEM STATUS SUMMARY:
echo ===============================================================
echo  [Web App]      React Frontend (Nginx): http://localhost:5173
echo  [Web App Alt]  Alternative Web Port:   http://localhost:8080
echo  [Backend API]  FastAPI Root:           http://localhost:8000
echo  [Swagger UI]   Interactive API Docs:   http://localhost:8000/docs
echo  [Diagnostics]  Health Check:           http://localhost:8000/api/health
echo  [Database]     Postgres (PGVector):    localhost:5433 (Container: budget-postgres)
echo  [Database]     MongoDB:                MongoDB Atlas Cloud Cluster
echo ===============================================================
echo.
echo Launching web browser endpoints...
start http://localhost:5173
start http://localhost:8000/docs
start http://localhost:8000/api/health

echo.
echo To view live logs:    docker compose logs -f
echo To stop containers:   docker compose down (or run stop_docker.bat)
echo.
pause
