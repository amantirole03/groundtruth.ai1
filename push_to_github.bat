@echo off
setlocal
echo ========================================================
echo GroundTruth.ai - GitHub Push Helper
echo ========================================================
echo.

set GIT_EXE=C:\Users\amant\.gemini\antigravity\scratch\git\cmd\git.exe
cd /d "C:\Users\amant\.gemini\antigravity\scratch\groundtruth-ai"

echo Verifying git status...
"%GIT_EXE%" status --short
echo.
echo Pushing branch 'main' to https://github.com/amantirole03/groundtruth.ai1.git...
echo (When prompted, enter your GitHub Username and Personal Access Token or Password)
echo.

"%GIT_EXE%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo SUCCESS: Repository successfully pushed to GitHub!
    echo URL: https://github.com/amantirole03/groundtruth.ai1
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Push encountered an error. 
    echo Please ensure:
    echo 1. The repository 'groundtruth.ai1' has been created on GitHub at https://github.com/new
    echo 2. Your Personal Access Token has 'repo' write permissions.
    echo ========================================================
)

echo.
pause
