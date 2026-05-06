@echo off
setlocal
cd /d "%~dp0"

set "APP_DIR=%~dp0"
set "EXE_PATH=%APP_DIR%dist\LOL战绩助手\LOL战绩助手.exe"
set "PY_PATH=%APP_DIR%backend\main.py"

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
    exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
    echo 未找到 Python。
    echo 如果你已经打包过，请检查 %EXE_PATH%
    pause
    exit /b 1
)

python "%PY_PATH%"
exit /b %errorlevel%
