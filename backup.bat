@echo off
REM Backup script for Virtual Try-On project
REM Creates a timestamped backup of the entire project

echo ========================================
echo Virtual Try-On Project Backup
echo ========================================
echo.

REM Get current date and time for backup folder name
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%b-%%a)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set mytime=%mytime: =0%

REM Create backup folder name
set backupname=backup_%mydate%_%mytime%
set backuppath=..\project-backups\%backupname%

echo Creating backup: %backupname%
echo.

REM Create backup directory
if not exist "..\project-backups" mkdir "..\project-backups"
mkdir "%backuppath%"

echo Copying files...

REM Copy entire project (excluding node_modules, venv, and large folders)
xcopy /E /I /H /Y /EXCLUDE:backup_exclude.txt . "%backuppath%"

REM Create backup info file
echo Backup created: %date% %time% > "%backuppath%\backup_info.txt"
echo Project: Virtual Try-On >> "%backuppath%\backup_info.txt"
echo. >> "%backuppath%\backup_info.txt"

REM Get git info if available
git log -1 --pretty=format:"Last commit: %%H%%nAuthor: %%an%%nDate: %%ad%%nMessage: %%s" >> "%backuppath%\backup_info.txt" 2>nul

echo.
echo ========================================
echo Backup completed successfully!
echo Location: %backuppath%
echo ========================================
echo.

REM Count files
for /f %%A in ('dir /a-d /s /b "%backuppath%" ^| find /c /v ""') do set filecount=%%A
echo Total files backed up: %filecount%
echo.

pause
