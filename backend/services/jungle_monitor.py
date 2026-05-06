"""野怪监控服务 - Tesseract OCR 版本"""
import os
import time
import threading

from config import config as app_config
from logger import get_logger

log = get_logger('JungleMonitor')

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None
    log.warning("cv2/numpy未安装，野怪监控功能不可用")

# 可选依赖检查
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    log.warning("pytesseract未安装，野怪监控功能不可用")

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    log.warning("mss未安装，野怪监控功能不可用")

try:
    from services.audio_manager import audio_manager
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    log.warning("audio_manager未找到，语音播报功能不可用")


# 野怪关键词映射 - 完整版
# 注意：关键词按优先级排序，越具体的越靠前
JUNGLE_CAMPS = {
    # 蓝色方野怪（蓝Buff必须包含"蓝"字）
    '蓝Buff': ['蓝Buff', '蓝buff', '蓝哨兵', '哨兵'],
    '魔沼蛙': ['魔沼', '沼蛙', '蛙', 'Gromp'],
    
    # 红色方野怪（红Buff必须包含"红"字）
    '红Buff': ['红Buff', '红buff', '红棘', '棘背'],
    '锋喙鸟': ['锋喙', '喙鸟', '鸟', 'F6', '六鸟', '迅捷'],
    
    # 中立小野怪
    '三狼': ['三狼', '狼', '暗影狼'],
    '石甲虫': ['石甲', '甲虫', '石头', '石头人', 'Krug'],
    
    # 河道野怪
    '河道蟹': ['河道', '道蟹', '蟹', '迅捷蟹', '螃蟹'],
    
    # 史诗野怪 - 注意：大龙必须在小龙前面匹配，且不使用"龙"作为关键词
    '大龙': ['大龙', 'Baron'],  # 只识别"大龙"和英文"Baron"，不识别"男爵"、"纳什"等
    '小龙': ['小龙', '元素', '亚龙', 'Drake'],  # 不使用单独的"龙"，避免误匹配
    '峡谷先锋': ['峡谷', '先锋', 'Herald', '先锋虫'],
    
    # 特殊野怪
    '虚空巢虫': ['虚空', '巢虫', '潮虫', 'Grub', '虫子', 'Voidgrub'],
}

# 中立野怪（不分己方敌方）
NEUTRAL_CAMPS = {'小龙', '大龙', '峡谷先锋', '虚空巢虫'}

PREFIXES = {
    '己方': ['己方', '己', '我方', '我'],
    '敌方': ['敌方', '敌'],
    '上路': ['上路', '上'],
    '下路': ['下路', '下'],
}


class JungleMonitorServiceTesseract:
    """野怪监控服务 - 使用 Tesseract OCR"""

    def __init__(self):
        self._running = False
        self._thread = None
        self._last_messages = {}  # 防重复
        self._msg_lock = threading.RLock()  # 保护 _last_messages
        self._state_lock = threading.RLock()  # 保护 _running 状态
        self._logs = []  # 识别记录
        self._callback = None  # 前端回调

        # 加载或初始化 auto_start 配置
        auto_start_value = app_config.get('jungle_monitor.auto_start')
        if auto_start_value is None:
            # 首次运行，使用默认值并保存
            self._auto_start = True
            app_config.set('jungle_monitor.auto_start', True)
        else:
            self._auto_start = auto_start_value

        # Tesseract 配置
        self._tesseract_config = '--psm 6 --oem 1 -l chi_sim'

        # 默认配置
        self._config = {
            'region': {'x': 50, 'y': 50, 'width': 400, 'height': 80},
            'interval': 500,  # ms
            'duplicate_interval': 5,  # 秒
            'notify_mode': 'both',  # text, voice, both
            'require_side_for_camps': True,  # 非中立野怪必须识别归属方
            'auto_start': self._auto_start,  # 进入游戏自动启动，结束自动停止
        }

        # 从 Config 单例加载保存的配置
        self._load_config()
    
    def _load_config(self):
        """从 Config 单例加载设置"""
        try:
            jungle_config = app_config.get('jungle_monitor', {})
            if jungle_config:
                if 'region' in jungle_config:
                    self._config['region'] = jungle_config['region']
                    log.debug("已加载保存的区域: %s", jungle_config['region'])
                for key in ['interval', 'duplicate_interval', 'notify_mode', 'require_side_for_camps', 'auto_start']:
                    if key in jungle_config:
                        self._config[key] = jungle_config[key]
                if 'auto_start' in jungle_config:
                    self._auto_start = bool(jungle_config['auto_start'])
        except Exception as e:
            log.debug("加载配置失败: %s", e)
    
    def _save_config(self):
        """通过 Config 单例保存配置"""
        try:
            app_config.set('jungle_monitor', self._config)
            log.debug("配置已保存")
        except Exception as e:
            log.debug("保存配置失败: %s", e)
    
    def init_ocr(self):
        """初始化 Tesseract OCR"""
        if not HAS_TESSERACT:
            return False
        
        try:
            # 查找 Tesseract 安装路径
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'D:\Program Files\Tesseract-OCR\tesseract.exe',
            ]
            
            tesseract_found = False
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    log.debug("找到 Tesseract: %s", path)
                    break
            
            if not tesseract_found:
                log.info("未找到 Tesseract，请安装后重试")
                return False
            
            # 测试是否可用
            pytesseract.get_tesseract_version()
            log.info("Tesseract OCR 初始化完成")
            return True
            
        except Exception as e:
            log.debug("Tesseract 初始化失败: %s", e)
            return False
    
    def check_audio_status(self):
        """检查音频文件状态"""
        if not HAS_AUDIO:
            return {'available': False, 'error': 'audio_manager未找到'}
        
        status = audio_manager.get_audio_status()
        return {
            'available': True,
            'complete': status['complete'],
            'existing': status['existing'],
            'missing_count': status['missing_count'],
            'missing_files': status['missing_files']
        }
    
    def set_config(self, config):
        """设置配置"""
        clean_config = dict(config)
        clean_config.pop('text_send_mode', None)
        if 'auto_start' in clean_config:
            self._auto_start = bool(clean_config['auto_start'])
            clean_config['auto_start'] = self._auto_start
        self._config.update(clean_config)
        # 保存到文件
        self._save_config()
    
    def get_config(self):
        """获取配置"""
        return self._config.copy()

    @property
    def auto_start(self):
        """是否启用自动启停"""
        return self._auto_start

    @auto_start.setter
    def auto_start(self, value):
        """设置自动启停"""
        self._auto_start = bool(value)
        self._config['auto_start'] = self._auto_start
        self._save_config()
    
    def set_callback(self, callback):
        """设置前端回调"""
        self._callback = callback
    
    def get_logs(self):
        """获取识别记录"""
        return self._logs[-50:]  # 最近50条
    
    def clear_logs(self):
        """清空记录"""
        self._logs = []
    
    def get_cached_message(self):
        """获取缓存的消息"""
        return None
    
    def send_cached_message(self):
        """发送缓存的消息"""
        return {'success': False, 'error': '手动热键发送功能已移除'}
    
    def start(self):
        """开始监控"""
        with self._state_lock:
            if not HAS_MSS or not HAS_TESSERACT:
                log.info("缺少必要依赖(mss/pytesseract)，无法启动")
                return False

            if self._running:
                log.debug("野怪监控已在运行，跳过启动")
                return False

            if not self.init_ocr():
                return False

            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            log.info("监控已启动")
            return True
    
    def stop(self):
        """停止监控"""
        with self._state_lock:
            if not self._running:
                log.debug("野怪监控未运行，跳过停止")
                return False

            self._running = False

        # 在锁外等待线程结束，避免死锁
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

        log.info("监控已停止")
        return True
    
    def is_running(self):
        """是否运行中"""
        with self._state_lock:
            return self._running
    
    def _preprocess_lol_alert(self, img):
        """专门针对LOL游戏提示的图像预处理
        
        特点：
        - 暗色背景
        - 白色/黄色文字
        - 可能有阴影/描边
        """
        # 转灰度
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # 放大3倍（提高小字识别率）
        scale = 3
        enlarged = cv2.resize(gray, None, fx=scale, fy=scale, 
                             interpolation=cv2.INTER_CUBIC)
        
        # 提取亮色文字（白色/黄色）
        _, bright_mask = cv2.threshold(enlarged, 100, 255, cv2.THRESH_BINARY)
        
        # 形态学操作 - 连接断开的笔画
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        connected = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel)
        
        # 去除小噪点
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(connected, cv2.MORPH_OPEN, kernel_open)
        
        return cleaned
    
    def _monitor_loop(self):
        """监控循环"""
        if not HAS_MSS:
            log.info("缺少 mss 依赖，无法启动监控")
            return
        
        import mss
        with mss.mss() as sct:
            while self._running:
                try:
                    # 截取指定区域
                    region = self._config['region']
                    monitor = {
                        'left': region['x'],
                        'top': region['y'],
                        'width': region['width'],
                        'height': region['height']
                    }
                    
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # OCR 识别
                    result = self._ocr_image(img)
                    
                    if result:
                        self._handle_detection(result)
                    
                except Exception as e:
                    log.debug("监控错误: %s", e)
                
                time.sleep(self._config['interval'] / 1000)
    
    def _ocr_image(self, img):
        """OCR识别图像 - Tesseract版本"""
        if not HAS_TESSERACT:
            return None
        
        try:
            # 确保图像有效
            if img is None or img.size == 0:
                return None
            
            # 预处理
            processed = self._preprocess_lol_alert(img)
            
            # Tesseract 识别
            text = pytesseract.image_to_string(processed, 
                                              config=self._tesseract_config)
            
            # 清理文本
            text = text.replace('\n', '').replace('\r', '').replace(' ', '').strip()
            
            if not text:
                return None
            
            # 解析野怪提示
            return self._parse_jungle_alert(text)
            
        except Exception as e:
            log.debug("OCR错误: %s", e)
            return None
    
    def _parse_jungle_alert(self, text):
        """解析野怪提示 - 优先匹配具体关键字"""
        if not text:
            return None
        
        # 过滤不需要的提示
        # 1. 包含"巨龙" - 巨龙刷新提示
        if '巨龙' in text:
            return None
        
        # 2. 包含"刷新" - 刷新提示
        if '刷新' in text:
            return None
        
        # 3. 包含"击杀" - 击杀提示（己方击杀）
        if '击杀' in text:
            return None
        
        # 提取野怪名 - 按优先级匹配
        camp_standard = None
        
        # 特殊处理1：红蓝Buff必须包含颜色
        if 'Buff' in text or 'buff' in text:
            if '蓝' in text:
                camp_standard = '蓝Buff'
            elif '红' in text:
                camp_standard = '红Buff'
            # 如果只有Buff没有颜色，不匹配
        
        # 特殊处理2：大龙和小龙 - 大龙必须优先匹配
        if not camp_standard:
            # 先检查是否是大龙
            if '大龙' in text or 'Baron' in text:
                camp_standard = '大龙'
            # 再检查是否是小龙
            elif '小龙' in text or '元素' in text or '亚龙' in text or 'Drake' in text:
                camp_standard = '小龙'
        
        # 如果不是Buff也不是龙，按正常流程匹配
        if not camp_standard:
            for standard_name, keywords in JUNGLE_CAMPS.items():
                # 跳过已经处理过的
                if 'Buff' in standard_name or '龙' in standard_name:
                    continue
                
                for keyword in keywords:
                    if keyword in text:
                        camp_standard = standard_name
                        break
                if camp_standard:
                    break
        
        if not camp_standard:
            return None
        
        # 提取前缀
        prefix_standard = ""
        for standard_prefix, keywords in PREFIXES.items():
            for keyword in keywords:
                if keyword in text:
                    prefix_standard = standard_prefix
                    break
            if prefix_standard:
                break
        
        return {
            'prefix': prefix_standard,
            'camp': camp_standard,
            'raw_text': text
        }
    
    def _handle_detection(self, detection):
        """处理检测结果"""
        prefix = detection['prefix']
        camp = detection['camp']
        
        # 检查是否需要归属方前缀
        require_side = self._config.get('require_side_for_camps', True)
        is_neutral = camp in NEUTRAL_CAMPS
        
        # 如果是非中立野怪且开启了"必须识别归属方"，但没有识别到前缀，则跳过
        if require_side and not is_neutral and not prefix:
            log_entry = {
                'time': time.strftime('%H:%M:%S'),
                'message': f"{camp}被打（未识别归属方，已跳过）",
                'text_sent': False,
                'voice_sent': False,
                'skipped': True,
                'reason': '未识别归属方'
            }
            self._logs.append(log_entry)
            if len(self._logs) > 200:
                self._logs = self._logs[-100:]
            self._notify_frontend(log_entry)
            log.debug("跳过播报: %s (未识别归属方)", camp)
            return
        
        # 生成消息
        if prefix:
            message = f"{prefix}{camp}被打"
            voice_text = f"{prefix}{camp}"
        else:
            message = f"{camp}被打"
            voice_text = camp
        
        # 防重复检查
        now = time.time()
        msg_key = message
        with self._msg_lock:
            if msg_key in self._last_messages:
                if now - self._last_messages[msg_key] < self._config['duplicate_interval']:
                    return
            
            self._last_messages[msg_key] = now
            
            # 清理过期的防重复条目
            dup_ttl = self._config['duplicate_interval'] * 2
            expired_keys = [k for k, ts in self._last_messages.items() if now - ts > dup_ttl]
            for k in expired_keys:
                del self._last_messages[k]
        
        # 根据模式处理
        mode = self._config['notify_mode']
        text_sent = False
        voice_sent = False
        
        # 语音播放（根据notify_mode配置）
        if mode in ['voice', 'both']:
            voice_sent = self._speak(voice_text)
        
        # 文字发送（即时发送）
        if mode in ['text', 'both']:
            text_sent = self._send_team_chat(message)
        
        # 记录日志
        log_entry = {
            'time': time.strftime('%H:%M:%S'),
            'message': message,
            'text_sent': text_sent,
            'voice_sent': voice_sent,
            'skipped': False
        }
        self._logs.append(log_entry)
        # 限制日志大小，超过 200 条截断为最近 100 条
        if len(self._logs) > 200:
            self._logs = self._logs[-100:]
        self._notify_frontend(log_entry)
        
        status = "已发送" if text_sent else "未发送"
        log.debug("检测到: %s, 文字:%s, 语音:%s", message, status, voice_sent)
    
    def _send_team_chat(self, message):
        """发送队伍聊天"""
        try:
            import subprocess
            import shutil
            
            ahk_exe = self._find_ahk_exe()
            script_dir = os.path.dirname(os.path.dirname(__file__))
            ahk_script = os.path.join(script_dir, 'scripts', 'send_team_chat.ahk')
            
            if not ahk_exe:
                return False
            
            if not os.path.exists(ahk_script):
                return False
            
            # 添加警告符号
            full_message = f"⚠ {message}"
            
            result = subprocess.run([ahk_exe, ahk_script, full_message],
                                   capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
            
        except Exception as e:
            log.debug("发送失败: %s", e)
            return False
    
    @staticmethod
    def _find_ahk_exe():
        """自动探测 AutoHotkey 可执行文件路径"""
        import shutil
        
        path_exe = shutil.which('AutoHotkey64.exe') or shutil.which('AutoHotkey32.exe') or shutil.which('AutoHotkey.exe')
        if path_exe:
            return path_exe
        
        candidates = [
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe',
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe',
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey.exe',
            r'C:\Program Files\AutoHotkey\AutoHotkey.exe',
            r'C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe',
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        return None
    
    def _speak(self, text):
        """语音播报 - 使用预录音频"""
        if not HAS_AUDIO:
            log.debug("音频管理器不可用")
            return False
        
        try:
            # 使用音频管理器播放
            return audio_manager.play_by_text(text)
        except Exception as e:
            log.debug("语音播报失败: %s", e)
            return False
    
    def _notify_frontend(self, log_entry):
        """通知前端"""
        if self._callback:
            try:
                self._callback(log_entry)
            except Exception:
                pass
    def test_ocr(self, image_path=None):
        """测试OCR识别"""
        if not HAS_TESSERACT:
            return {'success': False, 'error': 'pytesseract未安装'}
        
        if not self.init_ocr():
            return {'success': False, 'error': 'OCR未初始化'}
        
        try:
            if image_path and os.path.exists(image_path):
                # 测试指定图片
                img = cv2.imread(image_path)
                if img is None:
                    return {'success': False, 'error': f'无法读取图片: {image_path}'}
            else:
                # 截取当前区域
                if not HAS_MSS:
                    return {'success': False, 'error': 'mss未安装'}
                
                import mss
                with mss.mss() as sct:
                    region = self._config['region']
                    monitor = {
                        'left': region['x'],
                        'top': region['y'],
                        'width': region['width'],
                        'height': region['height']
                    }
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 预处理
            processed = self._preprocess_lol_alert(img)
            
            # Tesseract 识别
            raw_text = pytesseract.image_to_string(processed, 
                                                  config=self._tesseract_config)
            raw_text = raw_text.replace('\n', '').replace('\r', '').replace(' ', '').strip()
            
            result = self._parse_jungle_alert(raw_text)
            
            if result:
                return {
                    'success': True,
                    'detected': True,
                    'prefix': result['prefix'],
                    'camp': result['camp'],
                    'raw_text': result['raw_text']
                }
            else:
                return {
                    'success': True,
                    'detected': False,
                    'message': '未检测到野怪提示',
                    'raw_text': raw_text
                }
                
        except Exception as e:
            import traceback
            return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}


# 全局实例
jungle_monitor = JungleMonitorServiceTesseract()
