"""独立的区域选择工具 - 双击运行"""
import sys
import os
import json
import time

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import tkinter as tk
    from tkinter import messagebox
    import mss
    from PIL import Image, ImageTk
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("缺少依赖", f"请安装依赖: {e}")
    sys.exit(1)

def select_region():
    """全屏区域选择"""
    result = {'success': False, 'region': None}
    
    # 截取全屏
    with mss.mss() as sct:
        primary = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        screenshot = sct.grab(primary)
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        screen_width = primary['width']
        screen_height = primary['height']
    
    # 创建全屏窗口
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.config(cursor='cross')
    
    # 显示截图
    photo = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    
    # 半透明遮罩
    canvas.create_rectangle(0, 0, screen_width, screen_height, 
                           fill='black', stipple='gray50', tags='overlay')
    
    # 提示文字
    canvas.create_text(screen_width // 2, 50,
        text="拖动鼠标框选识别区域，松开保存 | 按 ESC 取消",
        fill='#4ecca3', font=('Microsoft YaHei', 20, 'bold'))
    
    start_x = start_y = 0
    rect_id = None
    
    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y,
                                         outline='#4ecca3', width=3)
    
    def on_drag(event):
        nonlocal rect_id
        x1, y1 = min(start_x, event.x), min(start_y, event.y)
        x2, y2 = max(start_x, event.x), max(start_y, event.y)
        
        if rect_id:
            canvas.coords(rect_id, x1, y1, x2, y2)
        
        canvas.delete('overlay')
        canvas.create_rectangle(0, 0, screen_width, y1, fill='black', stipple='gray50', tags='overlay')
        canvas.create_rectangle(0, y2, screen_width, screen_height, fill='black', stipple='gray50', tags='overlay')
        canvas.create_rectangle(0, y1, x1, y2, fill='black', stipple='gray50', tags='overlay')
        canvas.create_rectangle(x2, y1, screen_width, y2, fill='black', stipple='gray50', tags='overlay')
        canvas.tag_raise(rect_id)
    
    def on_release(event):
        nonlocal result
        x1, y1 = min(start_x, event.x), min(start_y, event.y)
        x2, y2 = max(start_x, event.x), max(start_y, event.y)
        width, height = x2 - x1, y2 - y1
        
        if width > 10 and height > 10:
            result = {
                'success': True,
                'region': {'x': x1, 'y': y1, 'width': width, 'height': height}
            }
        root.destroy()
    
    def on_escape(event):
        root.destroy()
    
    canvas.bind('<ButtonPress-1>', on_press)
    canvas.bind('<B1-Motion>', on_drag)
    canvas.bind('<ButtonRelease-1>', on_release)
    root.bind('<Escape>', on_escape)
    
    root.deiconify()
    root.attributes('-topmost', True)
    root.focus_force()
    root.mainloop()
    
    return result

def main():
    # 直接开始选择，不等待
    result = select_region()
    
    if result['success']:
        region = result['region']
        
        # 保存到配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            if 'jungle_monitor' not in config:
                config['jungle_monitor'] = {}
            config['jungle_monitor']['region'] = region
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            pass

if __name__ == '__main__':
    main()
