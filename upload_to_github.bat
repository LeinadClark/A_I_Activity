@echo off
title Upload to GitHub (LeinadClark/A_I_Activity)
cls
echo ===========================================================================
echo   Uploading A.I Activity to https://github.com/LeinadClark/A_I_Activity.git
echo ===========================================================================
echo.

set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
if exist "%~dp0A.I Activity" (
    cd /d "%~dp0A.I Activity"
) else (
    cd /d "%~dp0"
)

:: Check if already logged in
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo [Step 1/2] One-Time GitHub Login:
    echo A browser window will open to authorize with your GitHub account.
    echo.
    gh auth login --web -p https
)

echo.
echo [Step 2/2] Pushing all files, schemas, and CI/CD workflows to GitHub...
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ===========================================================================
    echo [SUCCESS] Your repository is now live on GitHub!
    echo URL: https://github.com/LeinadClark/A_I_Activity
    echo All automated CI/CD tests and syllabi compilation are running in GitHub!
    echo ===========================================================================
) else (
    echo.
    echo If you see an authentication error, you can also paste a GitHub Personal
    echo Access Token (PAT) when prompted for your password.
)
echo.
pause
