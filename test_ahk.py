"""测试 AHK 发送游戏内聊天"""
import subprocess
import os
import time

# AHK 路径
ahk_exe = r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe"
script_path = os.path.join(os.path.dirname(__file__), "backend", "scripts", "send_chat.ahk")

message = "/all 123"

print(f"AHK: {ahk_exe}")
print(f"脚本: {script_path}")
print(f"消息: {message}")
print("\n5秒后发送，请切换到LOL游戏窗口...")

time.sleep(5)

result = subprocess.run([ahk_exe, script_path, message], capture_output=True, text=True)
print(f"返回码: {result.returncode}")
print(f"stdout: {result.stdout}")
print(f"stderr: {result.stderr}")
