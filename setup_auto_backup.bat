@echo off
REM Setup automatic backup task in Windows Task Scheduler
REM Run this script as Administrator

echo ========================================
echo Setup Automatic Backup Task
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

echo This will create a scheduled task to run backup every 3 days.
echo.
set /p confirm="Continue? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo Creating scheduled task...

REM Get current directory
set SCRIPT_PATH=%~dp0auto_backup.bat

REM Create scheduled task
schtasks /Create ^
    /TN "VirtualTryOn_AutoBackup" ^
    /TR "\"%SCRIPT_PATH%\"" ^
    /SC DAILY ^
    /MO 3 ^
    /ST 02:00 ^
    /RL HIGHEST ^
    /F

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Success! Automatic backup configured.
    echo ========================================
    echo.
    echo Task Name: VirtualTryOn_AutoBackup
    echo Schedule: Every 3 days at 2:00 AM
    echo Script: %SCRIPT_PATH%
    echo.
    echo To view the task:
    echo - Open Task Scheduler
    echo - Look for "VirtualTryOn_AutoBackup"
    echo.
    echo To test now:
    echo - Run auto_backup.bat manually
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task!
    echo.
)

pause
