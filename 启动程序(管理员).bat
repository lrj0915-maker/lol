@echo off
chcp 65001 >nul
echo ========================================
echo LOL战绩助手 - 管理员模式启动
echo ========================================
echo.

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [提示] 正在请求管理员权限...
    echo.
    
    REM 请求管理员权限重新运行
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [✓] 已获得管理员权限
echo [✓] 热键监听功能将正常工作
echo.
echo [启动] 正在启动程序...
echo.

python backend\main.py

echo.
echo 程序已退出
pause
