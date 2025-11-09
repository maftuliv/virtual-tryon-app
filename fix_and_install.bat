@echo off
echo ============================================
echo   АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ И УСТАНОВКА
echo ============================================
echo.

cd /d "%~dp0"

echo [1/6] Проверка Python...
python --version
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)
echo OK
echo.

echo [2/6] Удаление старого venv (если есть)...
if exist "venv\" (
    rmdir /s /q venv
    echo Удалено
) else (
    echo Не требуется
)
echo.

echo [3/6] Создание нового виртуального окружения...
python -m venv venv
if errorlevel 1 (
    echo ОШИБКА: Не удалось создать venv
    pause
    exit /b 1
)
echo OK
echo.

echo [4/6] Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ОШИБКА: Не удалось активировать venv
    pause
    exit /b 1
)
echo OK
echo.

echo [5/6] Обновление pip...
python -m pip install --upgrade pip setuptools wheel
echo OK
echo.

echo [6/6] Установка зависимостей...
echo Это может занять несколько минут...
pip install --no-cache-dir Flask Flask-CORS Pillow requests gradio-client numpy
if errorlevel 1 (
    echo.
    echo ОШИБКА при установке!
    echo Попытка альтернативной установки...
    pip install Flask Flask-CORS Pillow requests
    if errorlevel 1 (
        echo ОШИБКА: Не удалось установить зависимости
        pause
        exit /b 1
    )
)
echo OK
echo.

echo ============================================
echo   УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!
echo ============================================
echo.
echo Проверка установленных пакетов:
pip list
echo.
echo ============================================
echo   ЧТО ДЕЛАТЬ ДАЛЬШЕ:
echo ============================================
echo.
echo 1. Запустите сервер:
echo    start_server.bat
echo.
echo 2. Откройте интерфейс:
echo    frontend\index.html
echo.
echo ИЛИ запустите:
echo    start_frontend.bat
echo.
echo ============================================
pause
