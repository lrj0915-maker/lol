"""测试游戏内聊天 - 使用 pydirectinput"""
import time
import pydirectinput

print("5秒后发送消息，请切换到LOL游戏窗口...")
time.sleep(5)

print("按Enter打开聊天框")
pydirectinput.press('enter')
time.sleep(0.3)

print("输入 /all 123")
pydirectinput.typewrite('/all 123', interval=0.05)
time.sleep(0.3)

print("按Enter发送")
pydirectinput.press('enter')

print("完成!")
