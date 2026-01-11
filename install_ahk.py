"""自动下载安装 AutoHotKey v2"""
import os
import sys
import urllib.request
import subprocess
import tempfile

AHK_URL = "https://www.autohotkey.com/download/ahk-v2.exe"
AHK_INSTALLER = "ahk-v2-setup.exe"

def main():
    print("正在下载 AutoHotKey v2...")
    
    # 下载到临时目录
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, AHK_INSTALLER)
    
    try:
        urllib.request.urlretrieve(AHK_URL, installer_path)
        print(f"下载完成: {installer_path}")
    except Exception as e:
        print(f"下载失败: {e}")
        return False
    
    print("正在安装 AutoHotKey v2 (静默安装)...")
    try:
        # 静默安装
        result = subprocess.run([installer_path, '/silent'], 
                               capture_output=True, timeout=120)
        if result.returncode == 0:
            print("安装成功!")
            return True
        else:
            print(f"安装失败，返回码: {result.returncode}")
            # 尝试普通安装
            print("尝试普通安装，请在弹出窗口中点击安装...")
            subprocess.run([installer_path])
            return True
    except Exception as e:
        print(f"安装出错: {e}")
        return False
    finally:
        # 清理安装文件
        try:
            os.remove(installer_path)
        except:
            pass

if __name__ == '__main__':
    success = main()
    if success:
        print("\nAutoHotKey 安装完成！现在可以使用游戏内嘲讽功能了。")
    else:
        print("\n安装失败，请手动从 https://www.autohotkey.com 下载安装")
    input("按回车键退出...")
