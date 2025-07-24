@echo off
REM Frontend Deployment Script for Windows
REM Usage: deploy.bat [environment] [platform]
REM Example: deploy.bat production netlify

setlocal enabledelayedexpansion

REM Default values
set ENVIRONMENT=%1
set PLATFORM=%2

if "%ENVIRONMENT%"=="" set ENVIRONMENT=production
if "%PLATFORM%"=="" set PLATFORM=netlify

echo 🚀 Starting deployment for %ENVIRONMENT% environment to %PLATFORM%...

REM Validate environment
if not "%ENVIRONMENT%"=="development" if not "%ENVIRONMENT%"=="staging" if not "%ENVIRONMENT%"=="production" (
    echo ❌ Invalid environment. Use: development, staging, or production
    exit /b 1
)

REM Clean previous build
echo 🧹 Cleaning previous build...
call npm run clean

REM Install dependencies
echo 📦 Installing dependencies...
call npm ci

REM Run linting
echo 🔍 Running linting...
call npm run lint

REM Build for specified environment
echo 🔨 Building for %ENVIRONMENT%...
if "%ENVIRONMENT%"=="development" (
    call npm run build:dev
) else if "%ENVIRONMENT%"=="staging" (
    call npm run build:staging
) else if "%ENVIRONMENT%"=="production" (
    call npm run build:production
)

REM Deploy to specified platform
echo 🚀 Deploying to %PLATFORM%...
if "%PLATFORM%"=="netlify" (
    where netlify >nul 2>nul
    if !errorlevel! equ 0 (
        netlify deploy --prod --dir=dist
    ) else (
        echo ❌ Netlify CLI not found. Install with: npm install -g netlify-cli
        exit /b 1
    )
) else if "%PLATFORM%"=="vercel" (
    where vercel >nul 2>nul
    if !errorlevel! equ 0 (
        vercel --prod
    ) else (
        echo ❌ Vercel CLI not found. Install with: npm install -g vercel
        exit /b 1
    )
) else if "%PLATFORM%"=="github-pages" (
    echo 📄 For GitHub Pages, push to main branch or use GitHub Actions
    echo 📁 Build files are ready in ./dist directory
) else if "%PLATFORM%"=="manual" (
    echo 📁 Build completed! Files are ready in ./dist directory
    echo 📋 Upload the contents of ./dist to your hosting provider
) else (
    echo ❌ Unsupported platform. Use: netlify, vercel, github-pages, or manual
    exit /b 1
)

echo ✅ Deployment completed successfully!

REM Show build info
echo.
echo 📊 Build Information:
echo Environment: %ENVIRONMENT%
echo Platform: %PLATFORM%
echo Build contents:
dir dist\

endlocal