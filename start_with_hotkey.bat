@echo off
chcp 65001 >nul
echo ========================================
echo LOL战绩助手 - 启动（含热键监听）
echo ========================================
echo.

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 未以管理员权限运行
    echo [提示] 热键监听器需要管理员权限才能工作
    echo [提示] 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo [1/2] 启动热键监听器（F9发送野怪消息）...
start "野怪监听热键" pythonw jungle_hotkey_listener.py

timeout /t 2 /nobreak >nul

echo [2/2] 启动主程序...
python backend\main.py

echo.
echo 程序已退出
pause
