@echo off
echo ============================================
echo Virtual Try-On Frontend Launcher
echo ============================================
echo.
echo Starting local web server...
echo.
echo Frontend will be available at:
echo   - http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

cd frontend
python -m http.server 8080

pause
