@echo off
setlocal enabledelayedexpansion
title Fact Knowledge Layer - Superjoin Submission

echo =====================================================================
echo   FACT KNOWLEDGE LAYER - SUPERJOIN VIT 2026 SUBMISSION
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    pause
    exit /b 1
)

:: 2. Check for .env file
if not exist .env (
    if exist .env.example (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

:: 3. Create required data directories
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
if not exist data\processed mkdir data\processed

:: 4. Verify core libraries
echo [1/3] Verifying runtime dependencies...
python -c "import streamlit, fastapi, pymupdf, pdfplumber, faiss, sentence_transformers; print('  [OK] All core dependencies verified.')"
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Missing dependencies detected. Installing from requirements.txt...
    pip install -r requirements.txt
)

echo.
echo [2/3] Starting FastAPI REST Backend on http://localhost:8000 ...
start "Fact Knowledge Layer - FastAPI (Port 8000)" cmd /k "python -m uvicorn app.api:app --host 0.0.0.0 --port 8000"

echo [3/3] Starting Streamlit Interactive UI on http://localhost:8501 ...
start "Fact Knowledge Layer - Streamlit (Port 8501)" cmd /k "python -m streamlit run app/ui.py --server.port 8501"

echo.
echo =====================================================================
echo   SERVICES LAUNCHED SUCCESSFULLY!
echo   - Streamlit Web UI:     http://localhost:8501
echo   - FastAPI Interactive:  http://localhost:8000/docs
echo   - FastAPI Base API:     http://localhost:8000
echo =====================================================================
echo.
echo Press any key to close this launcher window (services will continue running).
pause >nul
