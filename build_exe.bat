@echo off
echo [ImageCutter Build Script]
echo.
echo Cleaning up old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.
echo Building EXE...
python -m PyInstaller --onefile --noconsole --name imageCutter imageCutter.py
echo.
echo Done! The executable is in the 'dist' folder.
echo Remember to keep 'set.json' in the same folder as the exe.
echo.
pause
