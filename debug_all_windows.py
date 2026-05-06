"""
扫描所有窗口（包括子窗口）
"""
import ctypes
from ctypes import wintypes
import psutil

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def get_window_text(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def get_class_name(hwnd):
    buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buff, 256)
    return buff.value

def get_window_process_name(hwnd):
    try:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = psutil.Process(pid.value)
        return process.name()
    except Exception:
        return "<unknown>"

def is_window_visible(hwnd):
    return user32.IsWindowVisible(hwnd)

all_windows = []

def enum_callback(hwnd, lparam):
    """枚举所有窗口（包括不可见的）"""
    title = get_window_text(hwnd)
    class_name = get_class_name(hwnd)
    process = get_window_process_name(hwnd)
    visible = is_window_visible(hwnd)

    # 只记录有标题的窗口
    if title:
        all_windows.append({
            'hwnd': hwnd,
            'title': title,
            'class': class_name,
            'process': process,
            'visible': visible
        })

    return True

print("=" * 100)
print("扫描所有窗口（包括子窗口和不可见窗口）")
print("=" * 100)

# 枚举所有顶层窗口
cb = WNDENUMPROC(enum_callback)
user32.EnumWindows(cb, 0)

print(f"\n找到 {len(all_windows)} 个有标题的窗口\n")

# 查找包含关键词的窗口
keywords = ['查询', '结果', '信息', '提示', '警告', '封号', '处罚', '冻结', '封停', '登录']
suspicious = []

for win in all_windows:
    title_lower = win['title'].lower()
    process_lower = win['process'].lower()

    if any(kw in title_lower for kw in keywords) or any(kw in process_lower for kw in keywords):
        suspicious.append(win)

if suspicious:
    print(f"找到 {len(suspicious)} 个可疑窗口:\n")
    for win in suspicious:
        print(f"标题: {win['title']}")
        print(f"类名: {win['class']}")
        print(f"进程: {win['process']}")
        print(f"可见: {win['visible']}")
        print(f"句柄: {win['hwnd']}")
        print("-" * 80)
else:
    print("未找到包含关键词的窗口")

print("\n所有窗口列表:")
print("=" * 100)
for i, win in enumerate(all_windows, 1):
    visible_str = "可见" if win['visible'] else "隐藏"
    print(f"[{i}] {win['title']} ({win['process']}) - {visible_str}")

print("\n扫描完成")
