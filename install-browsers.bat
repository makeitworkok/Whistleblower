@echo off
REM Install Playwright browsers for Whistleblower
REM Run this ONCE after extracting the application

echo ========================================
echo Whistleblower Browser Installer
echo ========================================
echo.
echo This will download Microsoft Edge (Chromium) browser
echo for Whistleblower to use for automation.
echo.
echo Download size: ~130 MB
echo Installation time: 1-3 minutes
echo.
pause

echo.
echo [1/2] Installing Microsoft Edge (Chromium)...
echo.

REM Set the browser install path to the current directory
set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers

REM Install Edge (Chromium-based, works best on Windows)
_internal\playwright.exe install msedge

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Browser installation failed
    echo ========================================
    echo.
    echo Common fixes:
    echo - Check internet connection
    echo - Run as Administrator
    echo - Temporarily disable antivirus
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Verifying installation...
echo.

REM Create a marker file to indicate browsers are installed
echo %date% %time% > .browsers_installed

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Microsoft Edge browser installed successfully.
echo You can now launch Whistleblower.exe
echo.
echo Browser location: playwright_browsers\
echo.
pause
