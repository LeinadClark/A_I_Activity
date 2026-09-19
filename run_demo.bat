@echo off
title UPHSD CCS - OBE Syllabus Generator Demo
cls
echo ===========================================================================
echo   UPHSD College of Computer Studies - AI-Powered OBE Syllabus Generator
echo   Interactive Dynamic Pipeline Demo
echo ===========================================================================
echo.

:: Automatically resolve directory whether run from root or subdirectory
if exist "%~dp0A.I Activity\run_demo.py" (
    cd /d "%~dp0A.I Activity"
) else (
    cd /d "%~dp0"
)

:: Verify Ollama daemon is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting local Ollama background daemon on localhost:11434...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start "" /b "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start "" /b ollama serve
    )
    timeout /t 3 /nobreak >nul
)

python run_demo.py --interactive --open

echo.
pause
