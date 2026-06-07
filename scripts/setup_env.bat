@echo off
REM ============================================================
REM  VoiceGuard — Full Setup Script (Windows)
REM  Usage: scripts\setup_env.bat
REM  Run from the project root directory.
REM ============================================================
setlocal EnableDelayedExpansion

echo.
echo  +----------------------------------------------+
echo  ^|  VoiceGuard Compliance Intelligence Setup    ^|
echo  +----------------------------------------------+
echo.

REM ── Step 1: Check Python ─────────────────────────────────────────────────────
echo [1/6] Checking Python...
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Python not found. Install Python 3.10+ from python.org
    pause & exit /b 1
)

REM ── Step 2: Install dependencies ─────────────────────────────────────────────
echo.
echo [2/6] Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: pip install failed. Check requirements.txt.
    pause & exit /b 1
)
echo   OK: Dependencies installed

REM ── Step 3: Check .env file ───────────────────────────────────────────────────
echo.
echo [3/6] Checking .env configuration...
if not exist ".env" (
    echo   WARNING: .env file not found. Creating template...
    (
        echo # VoiceGuard -- Environment Configuration
        echo OPENAI_API_KEY=sk-...your-key-here...
        echo # VOICEGUARD_DB_URL=sqlite:///./memory_store/compliance.db
        echo # CHROMA_DIR=./memory_store/chroma_db
    ) > .env
    echo   WARNING: Edit .env and add your real OPENAI_API_KEY before starting.
) else (
    echo   OK: .env file found
)

REM ── Step 4: Create required directories ──────────────────────────────────────
echo.
echo [4/6] Creating required directories...
if not exist "memory_store" mkdir memory_store
if not exist "reports"      mkdir reports
if not exist "data\uploads" mkdir data\uploads
echo   OK: Directories ready

REM ── Step 5: Initialise SQLite + ChromaDB ─────────────────────────────────────
echo.
echo [5/6] Initialising memory (SQLite + ChromaDB)...
python scripts\init_memory.py
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: init_memory.py failed. Make sure all deps are installed.
    pause & exit /b 1
)

REM ── Step 6: Seed demo data ────────────────────────────────────────────────────
echo.
echo [6/6] Seeding demo data (2 Finance incidents)...
python scripts\seed_demo_data.py
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: seed_demo_data.py failed.
    pause & exit /b 1
)

REM ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  +----------------------------------------------+
echo  ^|          Setup complete!                     ^|
echo  +----------------------------------------------+
echo.
echo  Start the server with:
echo    uvicorn api.main:app --reload --port 8000
echo.
echo  Then open:
echo    http://localhost:8000/static/dashboard.html   ^<-- Compliance Dashboard
echo    http://localhost:8000/static/index.html       ^<-- Basic Detector
echo    http://localhost:8000/docs                    ^<-- API Docs (Swagger)
echo.

pause
