"""检查是否以管理员权限运行"""
import sys
import ctypes


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """请求管理员权限重新运行"""
    if sys.platform != 'win32':
        return False
    
    try:
        # 获取当前脚本路径
        script = sys.argv[0]
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # 请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script}" {params}',
            None, 
            1
        )
        return True
    except Exception:
        return False


if __name__ == '__main__':
    if is_admin():
        print("✓ 已以管理员权限运行")
    else:
        print("✗ 未以管理员权限运行")
        print("提示：热键监听功能需要管理员权限")
