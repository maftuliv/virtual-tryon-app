@echo off
REM Automatic backup script - keeps only last 3 backups
REM Runs every 3 days via Windows Task Scheduler

echo ========================================
echo Automatic Backup - Virtual Try-On
echo ========================================
echo.

REM Get current date and time
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%b-%%a)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set mytime=%mytime: =0%

REM Create backup name with date
set backupname=auto_backup_%mydate%
set backuppath=..\project-backups\%backupname%

echo Creating automatic backup: %backupname%
echo Time: %date% %time%
echo.

REM Create backup directory
if not exist "..\project-backups" mkdir "..\project-backups"

REM Remove old backup with same name if exists
if exist "%backuppath%" (
    echo Removing old backup with same name...
    rmdir /S /Q "%backuppath%"
)

REM Create new backup
mkdir "%backuppath%"

echo Copying files...
xcopy /E /I /H /Y /EXCLUDE:backup_exclude.txt . "%backuppath%" >nul

REM Create backup info
echo Backup created: %date% %time% > "%backuppath%\backup_info.txt"
echo Type: Automatic backup (3-day rotation) >> "%backuppath%\backup_info.txt"
echo Project: Virtual Try-On >> "%backuppath%\backup_info.txt"
echo. >> "%backuppath%\backup_info.txt"
git log -1 --pretty=format:"Last commit: %%H%%nAuthor: %%an%%nDate: %%ad%%nMessage: %%s" >> "%backuppath%\backup_info.txt" 2>nul

REM Keep only last 3 automatic backups
echo.
echo Cleaning old backups (keeping last 3)...

REM Count automatic backups
set count=0
for /d %%d in (..\project-backups\auto_backup_*) do set /a count+=1

REM If more than 3, delete oldest
if %count% GTR 3 (
    REM Get list sorted by date and delete oldest
    for /f "skip=3 delims=" %%d in ('dir /b /ad /o-d ..\project-backups\auto_backup_*') do (
        echo Deleting old backup: %%d
        rmdir /S /Q "..\project-backups\%%d"
    )
)

echo.
echo ========================================
echo Automatic backup completed!
echo Location: %backuppath%
echo Kept backups: 3 latest
echo ========================================
echo.

REM Log to file
echo [%date% %time%] Automatic backup completed: %backupname% >> ..\project-backups\backup_log.txt

exit /b 0
