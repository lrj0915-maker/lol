"""测试游戏内聊天 - 使用底层 SendInput"""
import time
import ctypes
from ctypes import wintypes

# 定义常量
INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

# 扫描码映射
SCAN_CODES = {
    'enter': 0x1C,
    '/': 0x35,
    'a': 0x1E,
    'l': 0x26,
    ' ': 0x39,
    '1': 0x02,
    '2': 0x03,
    '3': 0x04,
}

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

def press_key(scan_code):
    """按下并释放按键"""
    extra = ctypes.c_ulong(0)
    ii_ = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=ctypes.pointer(extra)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(ii_), ctypes.sizeof(ii_))
    time.sleep(0.05)
    ii_.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
    ctypes.windll.user32.SendInput(1, ctypes.byref(ii_), ctypes.sizeof(ii_))
    time.sleep(0.05)

def type_string(text):
    """输入字符串"""
    for char in text:
        if char in SCAN_CODES:
            press_key(SCAN_CODES[char])
        time.sleep(0.05)

print("5秒后发送消息，请切换到LOL游戏窗口...")
time.sleep(5)

print("按Enter打开聊天框")
press_key(SCAN_CODES['enter'])
time.sleep(0.3)

print("输入 /all 123")
type_string("/all 123")
time.sleep(0.3)

print("按Enter发送")
press_key(SCAN_CODES['enter'])

print("完成!")
