@echo off
REM Restore script for Virtual Try-On project
REM Restores project from a backup

echo ========================================
echo Virtual Try-On Project Restore
echo ========================================
echo.

REM Check if backup directory exists
if not exist "..\project-backups" (
    echo ERROR: No backups found!
    echo Backup directory does not exist: ..\project-backups
    echo.
    pause
    exit /b 1
)

echo Available backups:
echo.
dir /b /ad "..\project-backups"
echo.

set /p backupname="Enter backup folder name to restore (or 'cancel' to exit): "

if /i "%backupname%"=="cancel" (
    echo Restore cancelled.
    pause
    exit /b 0
)

set backuppath=..\project-backups\%backupname%

if not exist "%backuppath%" (
    echo ERROR: Backup folder not found: %backuppath%
    echo.
    pause
    exit /b 1
)

echo.
echo WARNING: This will overwrite current files!
echo Current project will be backed up to: backup_before_restore
echo.
set /p confirm="Are you sure you want to restore? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo Creating safety backup of current state...
call backup.bat
echo.

echo Restoring from backup: %backupname%
echo.

REM Restore files
xcopy /E /I /H /Y "%backuppath%\*" .

echo.
echo ========================================
echo Restore completed successfully!
echo ========================================
echo.

REM Show backup info
if exist "%backuppath%\backup_info.txt" (
    echo Backup information:
    type "%backuppath%\backup_info.txt"
    echo.
)

pause
