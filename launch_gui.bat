@echo off
title UPHSD CCS - Streamlit Web Dashboard
cls
echo ===========================================================================
echo   Launching UPHSD OBE Syllabus Generator Web Application...
echo ===========================================================================
echo.

:: Automatically resolve directory whether run from root or subdirectory
if exist "%~dp0A.I Activity\app.py" (
    cd /d "%~dp0A.I Activity"
) else (
    cd /d "%~dp0"
)

streamlit run app.py

echo.
pause
