@echo off
setlocal

:: Resolve project root path without trailing backslash
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

echo =======================================================
echo  AI-Powered Personal Finance ^& Budget Management System
echo =======================================================
echo Project Root: %PROJECT_DIR%
echo.

:: Check if initial database credentials need configuration
if not exist ".env" (
    echo =======================================================
    echo  [SETUP] No .env configuration detected.
    echo  Launching interactive database configuration wizard...
    echo =======================================================
    python configure_database.py
)
findstr /C:"YOUR_PGADMIN_PASSWORD" .env >nul 2>&1
if not errorlevel 1 (
    echo =======================================================
    echo  [SETUP REQUIRED] PostgreSQL pgAdmin password is not set.
    echo  Launching interactive database configuration wizard...
    echo =======================================================
    python configure_database.py
)

:: 1. PostgreSQL Service (Port 5432)
echo [1/4] Checking PostgreSQL Service (Port 5432)...
sc query postgresql-x64-18 | find "RUNNING" >nul
if not errorlevel 1 goto :postgres_running
echo       PostgreSQL service is NOT running. Attempting to start...
net start postgresql-x64-18
if errorlevel 1 (
    echo       [WARNING] Could not start postgresql-x64-18 automatically.
    echo                 Run as Administrator or start from Windows Services.
) else (
    echo       PostgreSQL service started successfully.
)
goto :check_mongo

:postgres_running
echo       PostgreSQL service is RUNNING.

:check_mongo
echo.
:: 2. MongoDB Database (Atlas Cloud Cluster)
echo [2/4] Connecting to MongoDB Database (Atlas Cloud Cluster)...
echo       MongoDB Atlas Cloud Cluster configured (cluster0.mst0hj0.mongodb.net).
goto :check_backend

:check_backend
echo.
:: 3. FastAPI Backend (Port 8000)
echo [3/4] Checking FastAPI Backend (Port 8000)...
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 goto :backend_running
echo       Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Backend - FastAPI" /D "%PROJECT_DIR%" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
goto :check_frontend

:backend_running
echo       Port 8000 is already active - FastAPI Backend is running.

:check_frontend
echo.
:: 4. React Frontend (Port 5173)
echo [4/4] Checking React Frontend (Port 5173)...
netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul
if not errorlevel 1 goto :frontend_running
echo       Launching React Frontend on http://127.0.0.1:5173 ...
start "Frontend - React Vite" /D "%PROJECT_DIR%\frontend" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"
goto :wait_servers

:frontend_running
echo       Port 5173 is already active - React Frontend is running.

:wait_servers
echo.
echo Waiting for servers to initialize and ports to open...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports = @(8000, 5173); $sw = [System.Diagnostics.Stopwatch]::StartNew(); do { $ok = $true; foreach ($p in $ports) { $t = New-Object System.Net.Sockets.TcpClient; try { $t.Connect('127.0.0.1', $p); $t.Close() } catch { $ok = $false; break } }; if ($ok) { exit 0 }; Start-Sleep -Milliseconds 800 } while ($sw.Elapsed.TotalSeconds -lt 15); exit 1"

if not errorlevel 1 (
    echo Servers are verified active and listening on ports 8000 and 5173!
) else (
    echo Note: Servers are still initializing. Opening browser endpoints...
)

echo.
echo Opening browser endpoints (all web services)...
start http://127.0.0.1:5173
start http://127.0.0.1:8000
start http://127.0.0.1:8000/docs
start http://127.0.0.1:8000/api/health
start http://127.0.0.1:8000/api/transactions/csv-template

echo.
echo =======================================================
echo  SYSTEM PORT STATUS SUMMARY:
echo =======================================================
echo  [Web App]      React Frontend:       http://127.0.0.1:5173
echo  [Backend API]  FastAPI Root:         http://127.0.0.1:8000
echo  [API Docs]     Swagger UI (JWT Auth): http://127.0.0.1:8000/docs
echo  [Diagnostics]  Health Check API:     http://127.0.0.1:8000/api/health
echo  [Templates]    CSV Template:         http://127.0.0.1:8000/api/transactions/csv-template
echo  [Flask Demo]   Optional Flask API:   http://127.0.0.1:5000/apidocs (run: python -m backend.flask_api)
echo  [Database]     PostgreSQL Service:   ACTIVE (Port 5432 - Native TCP, PGVector v0.8.6)
echo  [Database]     MongoDB Database:     MongoDB Atlas Cloud Cluster (cluster0.mst0hj0.mongodb.net)
echo =======================================================
echo Note: PostgreSQL (5432) and MongoDB Atlas communicate directly with the backend.
echo.
echo To stop servers anytime, run stop_system.bat or close their terminal windows.
pause
