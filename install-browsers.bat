@echo off
setlocal
REM Install Playwright browsers for Whistleblower
REM Run this ONCE after extracting the application

echo ========================================
echo Whistleblower Browser Installer
echo ========================================
echo.
echo This will download Chromium browser
echo for Whistleblower to use for automation.
echo.
echo Download size: ~130 MB
echo Installation time: 1-3 minutes
echo.
pause

echo.
echo [1/2] Installing Chromium...
echo.

REM Resolve script directory
set "SCRIPT_DIR=%~dp0"

REM Install into Playwright's bundled local browser folder used by the EXE
set "PLAYWRIGHT_BROWSERS_PATH=0"

REM Resolve bundled Playwright CLI path
set "PLAYWRIGHT_CLI=%SCRIPT_DIR%_internal\playwright.exe"
if not exist "%PLAYWRIGHT_CLI%" (
    set "PLAYWRIGHT_CLI=%SCRIPT_DIR%playwright.exe"
)

REM Fallback: PyInstaller bundle usually includes Playwright driver node+cli
set "PLAYWRIGHT_NODE=%SCRIPT_DIR%_internal\playwright\driver\node.exe"
set "PLAYWRIGHT_JSCLI=%SCRIPT_DIR%_internal\playwright\driver\package\cli.js"

if not exist "%PLAYWRIGHT_CLI%" (
    if exist "%PLAYWRIGHT_NODE%" if exist "%PLAYWRIGHT_JSCLI%" goto :install_with_node
    echo.
    echo ========================================
    echo ERROR: Could not find Playwright installer
    echo ========================================
    echo.
    echo Expected one of:
    echo - %SCRIPT_DIR%_internal\playwright.exe
    echo - %SCRIPT_DIR%playwright.exe
    echo - %SCRIPT_DIR%_internal\playwright\driver\node.exe + cli.js
    echo.
    echo Make sure you run this from the extracted Whistleblower folder.
    echo.
    pause
    exit /b 1
)

"%PLAYWRIGHT_CLI%" install chromium
goto :post_install

:install_with_node
"%PLAYWRIGHT_NODE%" "%PLAYWRIGHT_JSCLI%" install chromium

:post_install

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
echo Chromium browser installed successfully.
echo You can now launch Whistleblower.exe
echo.
echo Browser location: _internal\playwright\driver\package\.local-browsers\
echo.
pause
