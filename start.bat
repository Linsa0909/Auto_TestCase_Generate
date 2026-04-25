@echo off
chcp 65001 >nul 2>&1
echo.
echo  ========================================
echo    Test Case Intelligence v1.0
echo  ========================================
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

:: Install Python dependencies
echo [1/4] Installing Python dependencies...
pip install -r backend\requirements.txt -q 2>nul

:: Install Playwright browsers
echo [2/4] Installing Playwright browser...
python -m playwright install chromium >nul 2>&1

:: Install Node dependencies and build
echo [3/4] Building frontend...
cd frontend
call npm install --silent 2>nul
call npm run build >nul 2>&1
cd ..

:: Create output directory
if not exist "backend\output" mkdir "backend\output"

:: Start server
echo [4/4] Starting server...
echo.
echo   Frontend: http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop
echo.

:: Open browser after short delay
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
