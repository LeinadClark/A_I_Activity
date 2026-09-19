@echo off
title UPHSD CCS - AI OBE Syllabus Generator (Desktop App)
cls
echo ===========================================================================
echo   UPHSD College of Computer Studies - AI OBE Syllabus Generator
echo   Native Desktop GUI Application
echo ===========================================================================
echo.

:: Automatically resolve directory whether run from root or subdirectory
if exist "%~dp0A.I Activity\desktop_gui.py" (
    cd /d "%~dp0A.I Activity"
) else (
    cd /d "%~dp0"
)

:: Verify Ollama is running, if not start in background
echo [1/2] Checking local Ollama AI Engine...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [OLLAMA] Starting Ollama background daemon on localhost:11434...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start "" /b "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start "" /b ollama serve
    )
    timeout /t 3 /nobreak >nul
) else (
    echo [OLLAMA] Service active and ready.
)

echo [2/2] Launching Native Python Desktop GUI...
echo.
python desktop_gui.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error code.
    pause
)
