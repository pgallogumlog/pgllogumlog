@echo off
echo ========================================
echo Killing ALL Python processes...
echo ========================================
taskkill /F /IM python.exe /T 2>nul
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Clearing Python cache...
echo ========================================
cd C:\Users\PeteG\PycharmProjects\learnClaude\workflow_system
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo ========================================
echo Activating virtual environment...
echo ========================================
cd C:\Users\PeteG\PycharmProjects\learnClaude
call venv\Scripts\activate.bat

echo.
echo ========================================
echo Starting FRESH server on port 8000...
echo ========================================
cd workflow_system
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 --reload

pause
