@echo off
echo ========================================
echo   Wiki Monitor Build (Launcher Version)
echo ========================================
echo.

echo [1/3] Compiling launcher only...
pyinstaller --onefile --noconsole --name wiki_monitor --icon=NONE launcher.py
echo.

if exist wiki_monitor.exe (
    echo [2/3] Backup old file...
    set dt=%date:~2,2%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
    set dt=%dt: =0%
    ren wiki_monitor.exe wiki_monitor.exe.%dt%
) else (
    echo [2/3] No backup needed
)
echo.

echo [3/3] Cleanup...
move /Y dist\wiki_monitor.exe .
rmdir /S /Q dist
rmdir /S /Q build
del /Q wiki_monitor.spec
echo.

echo ========================================
echo   Done!
echo ========================================
echo.
echo ** 주의 **
echo monitor_tray.py와 config.py 파일은
echo wiki_monitor.exe와 같은 폴더에 있어야 합니다!
echo.
pause
