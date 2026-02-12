@echo off
setlocal

echo Installing Tesseract OCR for Windows...
echo.

REM Check if Tesseract is already installed
where tesseract >nul 2>&1
if %errorlevel% == 0 (
    echo Tesseract is already installed in PATH.
    echo Skipping installation.
    goto :check_installation
)

echo Downloading and installing Tesseract OCR...
echo Please note: This script will attempt to install Tesseract from the official source.
echo.

REM Check architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=64
) else (
    set ARCH=32
)

echo Detected architecture: %ARCH%-bit
echo.

REM Download link for Tesseract (this is a placeholder - in practice, you'd need to use PowerShell or similar)
echo Please visit: https://github.com/UB-Mannheim/tesseract/wiki
echo Download the appropriate installer for your system.
echo After installation, please restart this application.
echo.
echo Manual installation steps:
echo 1. Go to https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Download the installer (e.g., tesseract-ocr-setup-*.exe)
echo 3. Run the installer with default settings
echo 4. Add the installation directory to your system PATH
echo    (usually C:\Program Files\Tesseract-OCR or similar)
echo 5. Restart this application
echo.

:check_installation
echo.
echo Verifying installation...
where tesseract >nul 2>&1
if %errorlevel% == 0 (
    echo SUCCESS: Tesseract is available in PATH.
    tesseract --version
) else (
    echo WARNING: Tesseract is not available in PATH.
    echo Please follow the manual installation steps above.
)

echo.
echo Installation check complete.
pause