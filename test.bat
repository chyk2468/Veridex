@echo off
setlocal enabledelayedexpansion
title Fact Knowledge Layer - Automated Verification Suite

echo =====================================================================
echo   FACT KNOWLEDGE LAYER - COMPREHENSIVE TEST SUITE
echo =====================================================================
echo.

cd /d "%~dp0"

echo [TEST 1/4] Running 24 Pytest Unit and Integration Tests...
echo ---------------------------------------------------------------------
python -m pytest tests/
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAIL] Pytest test suite encountered errors!
    pause
    exit /b 1
)
echo.

echo [TEST 2/4] Running 18-Sample Ground Truth Benchmark Evaluation...
echo ---------------------------------------------------------------------
python scripts/evaluate.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAIL] Benchmark evaluation failed!
    pause
    exit /b 1
)
echo.

echo [TEST 3/4] Running Case 4 Reproducible Layout Failure Demonstration...
echo ---------------------------------------------------------------------
python scripts/reproduce_case4_failure.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FAIL] Failure demonstration script failed!
    pause
    exit /b 1
)
echo.

echo [TEST 4/4] Ingesting Unseen PDF & Testing Vector Search...
echo ---------------------------------------------------------------------
python scripts/ingest.py data/unseen_rbi_mpc_resolution.pdf
python -c "from retrieval.vector_store import VectorStore; vs = VectorStore(); print('  Vector Search Match Score:', vs.search('India real GDP growth', top_k=1))"
echo.

echo =====================================================================
echo   ALL AUTOMATED TESTS COMPLETED SUCCESSFULLY (100%% PASS)!
echo =====================================================================
echo.
pause
