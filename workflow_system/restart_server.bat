@echo off
echo Killing all old server processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /PID 154880 2>nul
taskkill /F /PID 185308 2>nul
taskkill /F /PID 183600 2>nul
taskkill /F /PID 180776 2>nul
taskkill /F /PID 193384 2>nul

timeout /t 2 /nobreak >nul

echo Starting fresh server with latest code...
cd C:\Users\PeteG\PycharmProjects\learnClaude\workflow_system
start "Workflow Server" cmd /k "python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo Server restarted! Please wait 5 seconds for it to initialize, then run your test.
