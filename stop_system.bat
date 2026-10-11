@echo off
echo =======================================================
echo Stopping AI-Powered Personal Finance System Servers...
echo =======================================================
echo.

echo Stopping processes listening on Port 8000 (FastAPI)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo Terminating PID %%a on Port 8000...
    taskkill /F /T /PID %%a >nul 2>&1
)

echo.
echo Stopping processes listening on Port 5173 (React Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /R /C:":5173 .*LISTENING"') do (
    echo Terminating PID %%a on Port 5173...
    taskkill /F /T /PID %%a >nul 2>&1
)

echo.
echo =======================================================
echo Server shutdown completed!
echo Note: PostgreSQL and MongoDB background services remain intact.
echo =======================================================
pause
