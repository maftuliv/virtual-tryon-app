@echo off
REM Remove automatic backup task from Windows Task Scheduler
REM Run this script as Administrator

echo ========================================
echo Remove Automatic Backup Task
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click on this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo This will remove the scheduled backup task.
echo.
set /p confirm="Continue? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Removal cancelled.
    pause
    exit /b 0
)

echo.
echo Removing scheduled task...

schtasks /Delete /TN "VirtualTryOn_AutoBackup" /F

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Automatic backup task removed successfully!
    echo ========================================
    echo.
) else (
    echo.
    echo Task not found or already removed.
    echo.
)

pause
