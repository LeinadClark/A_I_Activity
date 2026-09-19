@echo off
title UPHSD CCS - Verification Test Suite
cls
echo ===========================================================================
echo   Running Automated Quality Assurance Test Suite (Milestones 1 and 2)...
echo ===========================================================================
echo.

:: Automatically resolve directory whether run from root or subdirectory
if exist "%~dp0A.I Activity\test_system.py" (
    cd /d "%~dp0A.I Activity"
) else (
    cd /d "%~dp0"
)

python test_system.py

echo.
pause
