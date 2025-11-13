@echo off
REM Setup GitHub Actions automatic backup
REM Enables cloud-based backup that runs even when PC is off

echo ========================================
echo Setup GitHub Actions Backup
echo ========================================
echo.

echo This will enable automatic cloud backup via GitHub Actions.
echo.
echo Features:
echo - Runs every 3 days at 2:00 AM UTC (even when PC is off)
echo - Stores backups as Git branches on GitHub
echo - Keeps last 3 backups automatically
echo - No local computer required!
echo.

set /p confirm="Continue? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo Checking GitHub Actions workflow file...

if not exist ".github\workflows\auto-backup.yml" (
    echo ERROR: Workflow file not found!
    echo Please ensure .github\workflows\auto-backup.yml exists
    pause
    exit /b 1
)

echo ✅ Workflow file found
echo.

echo Committing GitHub Actions workflow...

git add .github\workflows\auto-backup.yml

git commit -m "🤖 Add GitHub Actions automatic backup workflow

- Runs every 3 days automatically
- Creates backup branches
- Keeps last 3 backups
- Works without local computer" 2>nul

echo.
echo Pushing to GitHub...

git push origin main

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ GitHub Actions Backup Setup Complete!
    echo ========================================
    echo.
    echo Next steps:
    echo.
    echo 1. Go to your GitHub repository:
    echo    https://github.com/maftuliv/virtual-tryon-app
    echo.
    echo 2. Click on "Actions" tab
    echo.
    echo 3. Enable GitHub Actions if prompted
    echo.
    echo 4. You should see "Automatic Backup to GitHub" workflow
    echo.
    echo 5. Click on it to view status and history
    echo.
    echo To test manually:
    echo - Go to Actions tab
    echo - Click "Automatic Backup to GitHub"
    echo - Click "Run workflow" button
    echo - Select "main" branch
    echo - Click "Run workflow"
    echo.
    echo Automatic schedule:
    echo - Every 3 days at 2:00 AM UTC
    echo - Keeps last 3 backups
    echo - No computer needed!
    echo.
) else (
    echo.
    echo ❌ Failed to push to GitHub!
    echo Please check your internet connection and try again.
    echo.
)

pause
