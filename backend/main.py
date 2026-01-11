"""应用入口"""
import os
import sys
import subprocess
import time
import socket
import atexit

# 添加 backend 目录到路径
backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 打包后需要添加 _MEIPASS 路径
if getattr(sys, 'frozen', False):
    meipass = sys._MEIPASS
    backend_in_meipass = os.path.join(meipass, 'backend')
    if os.path.exists(backend_in_meipass) and backend_in_meipass not in sys.path:
        sys.path.insert(0, backend_in_meipass)

import webview

# 延迟导入 bridge，确保路径已设置
from bridge import Bridge

# 全局变量保存 dev server 进程
_dev_server_process = None


def is_port_open(port, host='127.0.0.1'):
    """检查端口是否已打开"""
    # 尝试 IPv4 和 IPv6
    for addr in [(host, port), ('::1', port)]:
        try:
            if addr[0] == '::1':
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(addr)
            sock.close()
            if result == 0:
                return True
        except:
            pass
    return False


def find_available_port():
    """查找 Vite 使用的端口（5173-5180）"""
    for port in range(5173, 5181):
        if is_port_open(port):
            return port
    return None


def start_dev_server(frontend_dir):
    """启动 Vite dev server"""
    global _dev_server_process
    
    # 如果端口已经打开，说明 dev server 已在运行
    existing_port = find_available_port()
    if existing_port:
        print(f'Dev server 已在运行 (端口 {existing_port})')
        return existing_port
    
    print('正在启动 Vite dev server...')
    
    try:
        # 直接使用 npx vite，更可靠
        if sys.platform == 'win32':
            _dev_server_process = subprocess.Popen(
                'npx vite',
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            _dev_server_process = subprocess.Popen(
                ['npx', 'vite'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        
        # 等待 dev server 启动（最多 30 秒）
        print('等待 dev server 启动...')
        for i in range(60):
            port = find_available_port()
            if port:
                print(f'Dev server 启动成功! (端口 {port})')
                return port
            
            # 检查进程是否还在运行
            if _dev_server_process.poll() is not None:
                # 进程已退出，读取输出
                output = _dev_server_process.stdout.read().decode('utf-8', errors='ignore')
                print(f'Dev server 进程异常退出:\n{output}')
                return None
            
            time.sleep(0.5)
            if i % 10 == 9:
                print(f'  已等待 {(i+1)//2} 秒...')
        
        print('Dev server 启动超时（30秒）')
        return None
        
    except Exception as e:
        print(f'启动 dev server 失败: {e}')
        import traceback
        traceback.print_exc()
        return None


def cleanup_dev_server():
    """清理 dev server 进程"""
    global _dev_server_process
    if _dev_server_process:
        try:
            if sys.platform == 'win32':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(_dev_server_process.pid)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                _dev_server_process.terminate()
            print('Dev server 已关闭')
        except:
            pass


def get_frontend_path():
    """获取前端文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包后
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.dirname(__file__))
    
    return os.path.join(base_path, 'frontend', 'dist', 'index.html')


def main():
    bridge = Bridge()
    
    frontend_path = get_frontend_path()
    
    # 开发环境使用 dev server
    if not os.path.exists(frontend_path):
        # 获取 frontend 目录
        base_path = os.path.dirname(os.path.dirname(__file__))
        frontend_dir = os.path.join(base_path, 'frontend')
        
        # 自动启动 dev server
        port = start_dev_server(frontend_dir)
        if not port:
            print('警告: Dev server 未能启动，请手动运行 npm run dev')
            port = 5173  # 默认端口
        
        # 注册退出时清理
        atexit.register(cleanup_dev_server)
        
        url = f'http://localhost:{port}'
    else:
        url = f'file:///{frontend_path}'
    
    window = webview.create_window(
        title='LOL 战绩助手',
        url=url,
        width=1200,
        height=800,
        min_size=(1000, 700),
        js_api=bridge,
        frameless=False,
        easy_drag=False
    )
    
    bridge.set_window(window)
    
    # 窗口加载完成后尝试连接
    def on_loaded():
        bridge.connect()
    
    window.events.loaded += on_loaded
    
    webview.start(debug=False)


if __name__ == '__main__':
    main()
