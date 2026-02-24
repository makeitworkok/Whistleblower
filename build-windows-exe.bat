@echo off
REM Build script for Whistleblower Windows Executable
REM This script builds and packages the application for Windows distribution
REM
REM Requirements:
REM   - Python 3.12+
REM   - PyInstaller
REM   - Pillow

echo ========================================
echo Whistleblower Windows Build Script
echo ========================================
echo.

REM Check if Python is installed
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.12+
    pause
    exit /b 1
)

echo [1/6] Python version:
py --version
echo.

REM Check if PyInstaller is installed
echo [2/6] Checking PyInstaller...
py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo       PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo       PyInstaller ready.
echo.

REM Check if Pillow is installed
echo [3/6] Checking Pillow...
py -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo       Pillow not found. Installing...
    pip install Pillow
    if errorlevel 1 (
        echo ERROR: Failed to install Pillow
        pause
        exit /b 1
    )
)
echo       Pillow ready.
echo.

REM Create icons
echo [4/6] Generating application icons...
cd assets
py create_icon.py
if errorlevel 1 (
    echo ERROR: Failed to create icons
    cd ..
    pause
    exit /b 1
)
cd ..
echo       Icons created.
echo.
echo [5/6] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo       Done.
echo.

echo [6/6] Building executable with PyInstaller...
echo       This may take a few minutes...
py -m PyInstaller whistleblower.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check build\whistleblower\warn-whistleblower.txt for details
    pause
    exit /b 1
)
echo       Done.
echo.

echo ========================================
echo Build Successful!
echo ========================================
echo.
echo Application: dist\Whistleblower\
echo Executable: dist\Whistleblower\Whistleblower.exe
echo.
echo To create installer ZIP:
echo   Run create-installer.bat
echo.
echo To test:
echo   dist\Whistleblower\Whistleblower.exe
echo.

pause

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
