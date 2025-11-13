@echo off
REM Backup to GitHub - creates a backup branch and pushes to GitHub
REM This ensures backup is stored remotely

echo ========================================
echo Backup to GitHub
echo ========================================
echo.

REM Get current date for backup branch name
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%b-%%a)

set backup_branch=backup/local-%mydate%

echo Creating backup branch: %backup_branch%
echo.

REM Check if we're in a git repository
git status >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Not a git repository!
    echo.
    pause
    exit /b 1
)

REM Save current branch
for /f "tokens=*" %%a in ('git branch --show-current') do set current_branch=%%a
echo Current branch: %current_branch%

REM Check for uncommitted changes
git diff-index --quiet HEAD -- >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: You have uncommitted changes!
    echo.
    set /p commit_first="Commit changes first? (yes/no): "

    if /i "!commit_first!"=="yes" (
        set /p commit_msg="Enter commit message: "
        git add .
        git commit -m "!commit_msg!"

        if %errorLevel% neq 0 (
            echo Failed to commit changes!
            pause
            exit /b 1
        )
    ) else (
        echo Continuing without committing...
    )
)

echo.
echo Creating backup branch from %current_branch%...

REM Create backup branch
git checkout -b %backup_branch% 2>nul
if %errorLevel% neq 0 (
    REM Branch might already exist, try to switch to it
    git checkout %backup_branch%
    git merge %current_branch% --no-edit
)

REM Create backup info file
echo ======================================== > BACKUP_INFO.txt
echo Automatic Backup Information >> BACKUP_INFO.txt
echo ======================================== >> BACKUP_INFO.txt
echo. >> BACKUP_INFO.txt
echo Date: %date% %time% >> BACKUP_INFO.txt
echo Branch: %backup_branch% >> BACKUP_INFO.txt
echo Source: %current_branch% >> BACKUP_INFO.txt
echo Type: Local automatic backup >> BACKUP_INFO.txt
echo. >> BACKUP_INFO.txt
echo Last commit: >> BACKUP_INFO.txt
git log -1 --pretty=format:"Commit: %%H%%nAuthor: %%an%%nDate: %%ad%%nMessage: %%s" >> BACKUP_INFO.txt
echo. >> BACKUP_INFO.txt
echo. >> BACKUP_INFO.txt
echo Restore instructions: >> BACKUP_INFO.txt
echo 1. git checkout %backup_branch% >> BACKUP_INFO.txt
echo 2. git checkout -b restored-from-backup >> BACKUP_INFO.txt
echo 3. Verify and merge to main if needed >> BACKUP_INFO.txt
echo ======================================== >> BACKUP_INFO.txt

REM Add backup info
git add BACKUP_INFO.txt
git commit -m "🔄 Local backup - %mydate%" >nul 2>&1

echo.
echo Pushing backup to GitHub...

REM Push to GitHub
git push origin %backup_branch% --force

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ Backup created successfully!
    echo ========================================
    echo.
    echo Branch: %backup_branch%
    echo Pushed to: GitHub
    echo.
    echo To restore this backup:
    echo   git checkout %backup_branch%
    echo.
    echo To view all backups on GitHub:
    echo   https://github.com/maftuliv/virtual-tryon-app/branches
    echo.
) else (
    echo.
    echo ❌ Failed to push to GitHub!
    echo Check your internet connection and git credentials.
    echo.
)

REM Return to original branch
echo Returning to original branch: %current_branch%
git checkout %current_branch%

REM Clean up backup info from main branch
if exist BACKUP_INFO.txt (
    del BACKUP_INFO.txt >nul 2>&1
)

echo.
pause
