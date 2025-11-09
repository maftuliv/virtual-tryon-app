@echo off
echo ============================================
echo Virtual Try-On Server Launcher
echo ============================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Update pip first
echo Updating pip...
python -m pip install --upgrade pip

REM Check if requirements are installed
echo Checking dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install --no-cache-dir -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        echo Trying alternative installation...
        pip install Flask Flask-CORS Pillow requests gradio-client
        if errorlevel 1 (
            echo Error: Installation failed. Please install manually.
            pause
            exit /b 1
        )
    )
)

REM Start the server
echo.
echo ============================================
echo Starting Flask server...
echo ============================================
echo.
echo Server will be available at:
echo   - http://localhost:5000
echo   - http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

python backend\app.py

pause
