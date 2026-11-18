@echo off
setlocal enabledelayedexpansion
title GroundTruth.ai - GitHub Push Tool
echo ======================================================================
echo           GroundTruth.ai - GitHub Push & Vercel Setup
echo ======================================================================
echo Target GitHub Account: amantirole03
echo Target Repository:     groundtruth.ai1
echo Target URL:            https://github.com/amantirole03/groundtruth.ai1
echo ======================================================================
echo.

set GIT_EXE=C:\Users\amant\.gemini\antigravity\scratch\git\cmd\git.exe
cd /d "C:\Users\amant\.gemini\antigravity\scratch\groundtruth-ai"

echo [STEP 1] If you haven't created the repository on GitHub yet:
echo          Opening GitHub in your browser to create 'groundtruth.ai1'...
echo.
set /p CREATE_CONFIRM="Open https://github.com/new to create 'groundtruth.ai1' now? (Y/N, default Y): "
if /i not "%CREATE_CONFIRM%"=="N" (
    start https://github.com/new?name=groundtruth.ai1
    echo.
    echo Please make sure the repository name is set to: groundtruth.ai1
    echo Keep it Public or Private, do NOT initialize with README/license.
    echo Click 'Create repository' on the GitHub page.
    echo.
    pause
)

echo.
echo ======================================================================
echo [STEP 2] Choose how you want to push:
echo 1. Standard Push (Git will prompt for browser login / credentials)
echo 2. Quick Push using Personal Access Token (PAT)
echo ======================================================================
set /p PUSH_CHOICE="Select option (1 or 2): "

if "%PUSH_CHOICE%"=="2" (
    echo.
    echo Paste your GitHub Personal Access Token (starts with ghp_... or github_pat_...):
    set /p GITHUB_TOKEN="Token: "
    if defined GITHUB_TOKEN (
        echo Pushing to GitHub using provided token...
        "%GIT_EXE%" push https://amantirole03:!GITHUB_TOKEN!@github.com/amantirole03/groundtruth.ai1.git main --set-upstream
    ) else (
        echo No token provided. Running standard push...
        "%GIT_EXE%" push -u origin main
    )
) else (
    echo.
    echo Pushing to https://github.com/amantirole03/groundtruth.ai1.git...
    "%GIT_EXE%" push -u origin main
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo SUCCESS: All code has been pushed to GitHub!
    echo Repository: https://github.com/amantirole03/groundtruth.ai1
    echo.
    echo NEXT STEP - CONNECT TO VERCEL:
    echo 1. Go to https://vercel.com/new
    echo 2. Import 'amantirole03/groundtruth.ai1'
    echo 3. Root package.json and vercel.json are already configured.
    echo 4. Click 'Deploy'!
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo PUSH FAILED:
    echo Most common causes:
    echo 1. The repository 'groundtruth.ai1' has not been created yet on GitHub.
    echo    Please create it at: https://github.com/new (Repository name: groundtruth.ai1)
    echo 2. Missing GitHub authentication token or permission.
    echo ======================================================================
)

echo.
pause
