"""诊断脚本：枚举所有可见窗口，输出 hwnd/title/class/process 信息。
在封号弹窗出现时运行此脚本，查看弹窗的实际窗口属性。
用法: python backend/scripts/scan_windows.py
"""
import ctypes
import ctypes.wintypes

try:
    import psutil
except ImportError:
    psutil = None

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def main():
    windows = []

    def callback(hwnd, lparam):
        # 只看可见窗口
        if not user32.IsWindowVisible(hwnd):
            return True
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pname = ''
        if psutil:
            try:
                pname = psutil.Process(pid.value).name()
            except Exception:
                pname = '?'
        windows.append({
            'hwnd': hwnd,
            'title': title.value,
            'class': cls.value,
            'pid': pid.value,
            'process': pname,
        })
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)

    # 过滤：只显示有标题的，或者属于登录器/node 进程的
    keywords = ['登录', '_cache_', 'exe.exe', 'node', '信息', '查询', '提示', '封']
    print(f"\n=== 共 {len(windows)} 个可见窗口 ===\n")
    for w in windows:
        interesting = (
            w['title']
            or any(k in w['process'] for k in keywords)
        )
        if interesting:
            print(f"  hwnd={w['hwnd']:#010x}  pid={w['pid']:>6}  proc={w['process']:<30}  class={w['class']:<30}  title='{w['title']}'")

    # 也尝试 FindWindowW
    print("\n=== FindWindowW 测试 ===")
    for name in ['查询结果', '提示', '信息:', '信息', '信息：']:
        h = user32.FindWindowW(None, name)
        print(f"  FindWindowW(None, '{name}') -> {h:#010x if h else 'None'}")

    # 尝试 UIA
    print("\n=== UIA 测试 ===")
    try:
        import uiautomation as auto
        root = auto.GetRootControl()
        for win, depth in auto.WalkControl(root, maxDepth=2):
            name = win.Name or ''
            if any(k in name for k in ['信息', '查询', '封', '提示', '登录']):
                print(f"  depth={depth}  Name='{name}'  ControlType={win.ControlTypeName}  ClassName={win.ClassName}")
                # 读子元素
                for item, d2 in auto.WalkControl(win, maxDepth=10):
                    n = item.Name or ''
                    if n and len(n) > 1:
                        print(f"    sub depth={d2}  Name='{n}'  Type={item.ControlTypeName}")
    except Exception as e:
        print(f"  UIA 异常: {e}")

if __name__ == '__main__':
    main()
