@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Building WhiskDesktop x64 for Windows
echo ========================================
echo.

:: Check Python
python --version
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.9+ from python.org
    pause
    exit /b 1
)

:: Project directory
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

:: Install dependencies
echo.
echo [1/5] Installing dependencies...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

:: Run tests
echo.
echo [2/5] Running tests...
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo [WARNING] Some tests failed. Continue anyway?
    pause
)

:: Clean
echo.
echo [3/5] Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Build with PyInstaller
echo.
echo [4/5] Building with PyInstaller (x64)...
python -m PyInstaller build.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo PyInstaller build complete: dist\WhiskDesktop\WhiskDesktop.exe

:: Build installer with Inno Setup
echo.
echo [5/5] Creating x64_setup.exe with Inno Setup...

:: Find Inno Setup compiler
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>&1
    if !errorlevel! equ 0 (
        set "ISCC=iscc"
    )
)

if "!ISCC!" == "" (
    echo [WARNING] Inno Setup not found!
    echo Download from: https://jrsoftware.org/isdl.php
    echo After installing, run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scripts\installer.iss
    echo.
    echo PyInstaller output is ready at: dist\WhiskDesktop\
    pause
    exit /b 0
)

"!ISCC!" scripts\installer.iss

if errorlevel 1 (
    echo [ERROR] Inno Setup build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE!
echo  Installer: dist\x64_setup.exe
echo  Portable:  dist\WhiskDesktop\WhiskDesktop.exe
echo ============================================
echo.
pause
