@echo off
REM Copyright (c) 2025-2026 Chris Favre - MIT License
REM See LICENSE file for full terms
REM Create Windows installer ZIP
REM This script packages the built application for distribution

echo ========================================
echo Creating Whistleblower Installer ZIP
echo ========================================
echo.

REM Check if executable exists
if not exist "dist\Whistleblower\Whistleblower.exe" (
    echo ERROR: dist\Whistleblower\Whistleblower.exe not found
    echo Run build-windows-exe.bat first
    pause
    exit /b 1
)

set VERSION=1.0.2
set ZIPNAME=Whistleblower-Windows-v%VERSION%.zip
set TEMP_DIR=dist\temp-package

echo [1/4] Creating package directory...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

echo [2/4] Copying files...
xcopy /E /I /Y "dist\Whistleblower" "%TEMP_DIR%\Whistleblower"
copy /Y "README.md" "%TEMP_DIR%\"
copy /Y "LICENSE" "%TEMP_DIR%\"
copy /Y "install-browsers.bat" "%TEMP_DIR%\Whistleblower\"

REM Create a simple launcher batch file
echo @echo off > "%TEMP_DIR%\Start-Whistleblower.bat"
echo cd Whistleblower >> "%TEMP_DIR%\Start-Whistleblower.bat"
echo Whistleblower.exe >> "%TEMP_DIR%\Start-Whistleblower.bat"

echo [3/4] Creating ZIP file...
if exist "dist\%ZIPNAME%" del "dist\%ZIPNAME%"

REM Use PowerShell to create ZIP
powershell -command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath 'dist\%ZIPNAME%' -CompressionLevel Optimal"

if errorlevel 1 (
    echo ERROR: Failed to create ZIP file
    pause
    exit /b 1
)

echo [4/4] Cleaning up...
rmdir /s /q "%TEMP_DIR%"

echo.
echo ========================================
echo Installer Created Successfully!
echo ========================================
echo.
echo Package: dist\%ZIPNAME%
echo.
echo Distribution contents:
echo   - Whistleblower\ - Application folder
echo   - Start-Whistleblower.bat - Quick launcher
echo   - README.md - Documentation
echo   - LICENSE - License file
echo.

pause
