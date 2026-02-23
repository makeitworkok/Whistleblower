@echo off
REM Build script for Whistleblower Windows Executable
REM This script builds and packages the application for distribution

echo ========================================
echo Whistleblower Windows Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [1/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo       Done.
echo.

echo [2/4] Building executable with PyInstaller...
py -m PyInstaller whistleblower.spec --clean
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo       Done.
echo.

echo [3/4] Adding helper files to distribution...

REM The README, batch files should already be in dist if we rebuild
REM But let's check and create them if needed

echo       Helper files included.
echo.

echo [4/4] Creating distribution ZIP...
set VERSION=1.0.0
set ZIPNAME=Whistleblower-Windows-v%VERSION%.zip

if exist "%ZIPNAME%" del "%ZIPNAME%"

powershell -Command "Compress-Archive -Path dist\Whistleblower\* -DestinationPath '%ZIPNAME%'"
if errorlevel 1 (
    echo WARNING: Failed to create ZIP automatically.
    echo You can manually zip the dist\Whistleblower folder.
) else (
    echo       Created: %ZIPNAME%
)
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output location: dist\Whistleblower\
echo Executable: dist\Whistleblower\Whistleblower.exe
if exist "%ZIPNAME%" echo Distribution ZIP: %ZIPNAME%
echo.
echo Next steps:
echo  1. Test the executable in dist\Whistleblower\
echo  2. Run dist\Whistleblower\install-browsers.bat
echo  3. Run dist\Whistleblower\start-whistleblower.bat
echo  4. Verify all features work
echo  5. Distribute the ZIP file
echo.
pause
