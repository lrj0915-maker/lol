"""
封号弹窗检测调试工具
用于分析弹窗的窗口结构、类名、标题、内容等信息
"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# 定义回调函数类型
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def get_window_text(hwnd):
    """获取窗口标题"""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def get_class_name(hwnd):
    """获取窗口类名"""
    buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buff, 256)
    return buff.value

def get_window_rect(hwnd):
    """获取窗口位置和大小"""
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return {
        'left': rect.left,
        'top': rect.top,
        'right': rect.right,
        'bottom': rect.bottom,
        'width': rect.right - rect.left,
        'height': rect.bottom - rect.top
    }

def is_window_visible(hwnd):
    """检查窗口是否可见"""
    return user32.IsWindowVisible(hwnd)

def get_window_process_name(hwnd):
    """获取窗口所属进程名"""
    try:
        import psutil
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = psutil.Process(pid.value)
        return process.name()
    except Exception as e:
        return f"<error: {e}>"

def enum_child_windows(hwnd):
    """枚举所有子窗口"""
    children = []

    def callback(child_hwnd, lparam):
        child_info = {
            'hwnd': child_hwnd,
            'text': get_window_text(child_hwnd),
            'class': get_class_name(child_hwnd),
            'visible': is_window_visible(child_hwnd),
            'rect': get_window_rect(child_hwnd)
        }
        children.append(child_info)
        return True

    try:
        cb = WNDENUMPROC(callback)
        user32.EnumChildWindows(hwnd, cb, 0)
    except Exception as e:
        print(f"枚举子窗口失败: {e}")

    return children

def scan_all_windows():
    """扫描所有顶层窗口"""
    windows = []

    def callback(hwnd, lparam):
        if not is_window_visible(hwnd):
            return True

        title = get_window_text(hwnd)
        # 不跳过无标题窗口，全部记录

        window_info = {
            'hwnd': hwnd,
            'title': title if title else '<无标题>',
            'class': get_class_name(hwnd),
            'process': get_window_process_name(hwnd),
            'rect': get_window_rect(hwnd),
            'children': []
        }

        # 枚举所有窗口的子控件（不管标题是什么）
        window_info['children'] = enum_child_windows(hwnd)

        windows.append(window_info)
        return True

    try:
        cb = WNDENUMPROC(callback)
        user32.EnumWindows(cb, 0)
    except Exception as e:
        print(f"枚举窗口失败: {e}")

    return windows

def print_window_info(window_info, indent=0):
    """打印窗口信息"""
    prefix = "  " * indent
    print(f"{prefix}{'='*80}")
    print(f"{prefix}窗口句柄: {window_info['hwnd']}")
    print(f"{prefix}标题: {window_info['title']}")
    print(f"{prefix}类名: {window_info['class']}")
    print(f"{prefix}进程: {window_info.get('process', 'N/A')}")
    print(f"{prefix}位置: ({window_info['rect']['left']}, {window_info['rect']['top']})")
    print(f"{prefix}大小: {window_info['rect']['width']} x {window_info['rect']['height']}")

    if window_info.get('children'):
        print(f"{prefix}子窗口数量: {len(window_info['children'])}")
        print(f"{prefix}子窗口详情:")
        for i, child in enumerate(window_info['children'], 1):
            try:
                # 过滤掉特殊字符
                text = child['text'].encode('gbk', errors='ignore').decode('gbk')
                print(f"{prefix}  [{i}] 类名: {child['class']}, 文本: {text}, 可见: {child['visible']}")
            except Exception:
                print(f"{prefix}  [{i}] 类名: {child['class']}, 文本: <编码错误>, 可见: {child['visible']}")

def main():
    print("=" * 100)
    print("封号弹窗检测工具 - 完整扫描模式")
    print("=" * 100)
    print("\n开始扫描所有窗口...")

    windows = scan_all_windows()

    print(f"\n找到 {len(windows)} 个可见窗口\n")

    # 重点关注可能是封号弹窗的窗口
    suspicious_windows = []
    for win in windows:
        title_lower = win['title'].lower()
        keywords = ['查询', '结果', '信息', '提示', '警告', '封号', '处罚', '冻结', '封停', '登录', 'exe']
        # 检查标题或进程名
        process_lower = win['process'].lower()
        if any(kw in title_lower for kw in keywords) or any(kw in process_lower for kw in keywords):
            suspicious_windows.append(win)

    if suspicious_windows:
        print(f"找到 {len(suspicious_windows)} 个可疑窗口（标题或进程包含关键词）:\n")
        for win in suspicious_windows:
            print_window_info(win)
            print()
    else:
        print("未找到包含关键词的窗口")

    print("\n" + "=" * 100)
    print("所有窗口列表（包括子控件文本）:")
    print("=" * 100)
    for i, win in enumerate(windows, 1):
        print(f"\n[{i}] {win['title']} (进程: {win['process']})")
        if win['children']:
            child_texts = [c['text'] for c in win['children'] if c['text']]
            if child_texts:
                print(f"    子控件文本: {', '.join(child_texts[:10])}")  # 只显示前10个

    print("\n" + "=" * 100)
    print("扫描完成")

if __name__ == "__main__":
    main()
