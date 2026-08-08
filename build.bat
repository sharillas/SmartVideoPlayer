@echo off
echo ============================================
echo  SmartVideoPlayer v1.0.1 - Build Script
echo ============================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller --no-cache-dir
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install PyInstaller
    exit /b 1
)

echo.
echo [2/3] Building executable...
pyinstaller --onefile --windowed --name SmartVideoPlayer --add-data "smartplayer;smartplayer" run.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo Executable: dist\SmartVideoPlayer.exe
echo.
echo Copy dist\SmartVideoPlayer.exe to any Windows PC to run.
pause
