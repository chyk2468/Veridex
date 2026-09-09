@echo off
setlocal enabledelayedexpansion
title Fact Knowledge Layer - Superjoin Submission

echo =====================================================================
echo   FACT KNOWLEDGE LAYER - SUPERJOIN VIT 2026 SUBMISSION
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python
set "PYTHON_EXE=python"
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else (
        echo [ERROR] Python is not found in PATH.
        echo Please ensure Python 3.10+ is installed.
        pause
        exit /b 1
    )
)

:: 2. Check for .env file
if not exist .env (
    if exist .env.example (
        echo [INFO] Creating .env from template .env.example...
        copy .env.example .env >nul
    )
)

:: 3. Create required directories
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
if not exist data\processed mkdir data\processed

:: 4. Free up ports 8000 and 8501 if previously occupied by background instances
echo [1/3] Checking and clearing port conflicts on 8000 and 8501...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 5. Launch FastAPI Backend
echo [2/3] Launching FastAPI REST Backend on http://127.0.0.1:8000 ...
start "Fact Knowledge Layer - FastAPI (8000)" cmd /k "cd /d "%~dp0" && "%PYTHON_EXE%" -m uvicorn app.api:app --host 127.0.0.1 --port 8000"

:: Brief pause to let API bind
timeout /t 2 /nobreak >nul

:: 6. Launch Streamlit UI
echo [3/3] Launching Streamlit Explorer on http://localhost:8501 ...
start "Fact Knowledge Layer - Streamlit (8501)" cmd /k "cd /d "%~dp0" && "%PYTHON_EXE%" -m streamlit run app/ui.py --server.port 8501"

echo.
echo =====================================================================
echo   SERVICES LAUNCHED SUCCESSFULLY!
echo   - Streamlit Web UI:     http://localhost:8501
echo   - FastAPI Interactive:  http://127.0.0.1:8000/docs
echo   - FastAPI Base API:     http://127.0.0.1:8000
echo =====================================================================
echo.
echo Press any key to close this launcher (the 2 service windows will stay active).
pause >nul
