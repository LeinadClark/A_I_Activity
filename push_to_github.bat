@echo off
title Push UPHSD OBE Syllabus Generator to GitHub
cls
echo ===========================================================================
echo   UPHSD Molino Campus - College of Computer Studies
echo   GitHub Repository Upload & Sync Tool
echo ===========================================================================
echo.

:: Ensure Git is in PATH
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"

cd /d "%~dp0"

echo [1/3] Checking Git Status...
git status
echo.

echo ===========================================================================
echo   Choose an Upload Method:
echo   [1] Connect to an existing GitHub Repository URL (Recommended)
echo   [2] Login via GitHub CLI (gh auth login) and create repo automatically
echo ===========================================================================
set /p opt="Select option [1 or 2] (Default: 1): "

if "%opt%"=="2" (
    echo.
    echo [2/3] Authenticating with GitHub...
    gh auth login
    echo.
    echo [3/3] Creating and pushing repository to your GitHub...
    gh repo create UPHSD-AI-OBE-Syllabus-Generator --public --source="." --remote=origin --push
    goto done
)

:manual_url
echo.
echo Please create a new empty repository on github.com (do not check README/license).
set /p repourl="Paste your GitHub Repository URL (e.g., https://github.com/Username/repo.git): "

if "%repourl%"=="" (
    echo Error: No URL provided.
    pause
    exit /b 1
)

echo.
echo [2/3] Adding remote origin...
git remote remove origin >nul 2>&1
git remote add origin %repourl%

echo [3/3] Pushing main branch to GitHub...
git push -u origin main

:done
echo.
if %errorlevel% equ 0 (
    echo ===========================================================================
    echo [SUCCESS] Your solo activity is now live on GitHub!
    echo All CI/CD workflows and automated tests are running in GitHub Actions.
    echo ===========================================================================
) else (
    echo.
    echo [NOTE] If prompted for credentials, enter your GitHub Username and a
    echo Personal Access Token (PAT) with 'repo' scope as your password.
)
echo.
pause
