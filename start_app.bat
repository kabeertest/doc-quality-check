@echo off
setlocal enabledelayedexpansion

REM Batch file to start, monitor, and restart the document quality validation app
title Document Quality Checker App Manager

REM Configuration
set APP_PORT=8501
set APP_NAME=Document Quality Validator
set PYTHON_SCRIPT=app.py

echo ================================================
echo  Document Quality Validation App Manager
echo ================================================
echo.

:menu
echo Available options:
echo 1. Start the app
echo 2. Stop the app  
echo 3. Restart the app
echo 4. Check app status
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "!choice!"=="1" goto start
if "!choice!"=="2" goto stop
if "!choice!"=="3" goto restart
if "!choice!"=="4" goto status
if "!choice!"=="5" goto exit

echo Invalid choice. Please enter 1-5.
echo.
goto menu

:start
echo.
echo Starting !APP_NAME!...
echo.

REM Kill any existing streamlit processes first
call :stop_streamlit

REM Change to the app directory
cd /d "%~dp0"

REM Start the Streamlit app in the background
echo Launching the app on port !APP_PORT!...
start "StreamlitApp" cmd /c "python -m streamlit run !PYTHON_SCRIPT! --server.port=!APP_PORT! --browser.serverAddress=localhost --server.headless=true"

REM Wait a moment for the app to start
timeout /t 5 /nobreak >nul

REM Open the browser
echo Opening the app in your default browser...
start http://localhost:!APP_PORT!

echo.
echo !APP_NAME! should now be running at http://localhost:!APP_PORT!
echo.
goto menu

:stop
echo.
echo Stopping !APP_NAME!...
call :stop_streamlit
echo App has been stopped.
echo.
goto menu

:restart
echo.
echo Restarting !APP_NAME!...
call :stop_streamlit
timeout /t 2 /nobreak >nul
goto start

:status
echo.
echo Checking status of !APP_NAME!...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "streamlit" >nul
if "%ERRORLEVEL%"=="0" (
    echo !APP_NAME! is RUNNING on port !APP_PORT!
) else (
    echo !APP_NAME! is NOT RUNNING
)
echo.
goto menu

:stop_streamlit
REM Function to stop streamlit processes
echo Terminating any existing Streamlit processes...
for /f "tokens=2" %%i in ('tasklist /FI "WINDOWTITLE eq *streamlit*" /FO CSV ^| find /V "PID"') do (
    taskkill /f /pid %%i 2>nul
)
taskkill /f /im streamlit.exe 2>nul
REM Also kill any Python processes that might be running the app
for /f "skip=3 tokens=2" %%i in ('netstat -ano ^| findstr :!APP_PORT!') do (
    taskkill /f /pid %%i 2>nul
)
timeout /t 2 /nobreak >nul
exit /b

:exit
echo.
echo Exiting the !APP_NAME! manager.
echo.
pause