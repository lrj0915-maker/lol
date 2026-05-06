@echo off
setlocal
cd /d "%~dp0"

if exist "dist\LOL战绩助手\LOL战绩助手.exe" (
    start "" "%~dp0dist\LOL战绩助手\LOL战绩助手.exe"
    exit /b 0
)

if exist "backend\main.py" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo 未找到 Python，请先安装 Python，或先执行打包生成 exe。
        pause
        exit /b 1
    )
    python "backend\main.py"
    exit /b %errorlevel%
)

echo 未找到可执行程序或 Python 入口。
pause
exit /b 1
