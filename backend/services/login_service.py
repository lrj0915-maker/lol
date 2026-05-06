"""登录服务 - 通过 Win32 自动化操控 jicheng 登录器"""
import os
import time
import subprocess
import threading
import ctypes
import ctypes.wintypes

try:
    import psutil
except ImportError:
    psutil = None

# 28 个大区（顺序必须与 jicheng 登录器 ComboBox 一致）
SERVER_LIST = [
    '艾欧尼亚', '祖安', '诺克萨斯', '班德尔城', '皮尔特沃夫',
    '战争学院', '巨神峰', '雷瑟守备', '钢铁烈阳', '裁决之地',
    '黑色玫瑰', '暗影岛', '均衡教派', '水晶之痕', '影流',
    '守望之海', '征服之海', '卡拉曼达', '皮城警备', '比尔吉沃特',
    '德玛西亚', '弗雷尔卓德', '无畏先锋', '恕瑞玛', '扭曲丛林',
    '巨龙之巢', '教育网专区', '男爵领域',
]

# Win32 常量
WM_SETTEXT = 0x000C
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
BM_CLICK = 0x00F5
CB_SETCURSEL = 0x014E
CB_GETCURSEL = 0x0147
SW_RESTORE = 9
SW_HIDE = 0

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SendMessageW = user32.SendMessageW
SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_ulonglong, ctypes.c_void_p]
SendMessageW.restype = ctypes.c_longlong

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.c_void_p]
SetForegroundWindow.restype = ctypes.wintypes.BOOL

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
FindWindowW.restype = ctypes.wintypes.HWND

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

# 设置常用 Win32 函数的参数类型，避免 64 位系统上的溢出
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindowVisible.restype = ctypes.wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
user32.EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
user32.EnumWindows.restype = ctypes.wintypes.BOOL
user32.EnumChildWindows.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.wintypes.LPARAM]
user32.EnumChildWindows.restype = ctypes.wintypes.BOOL
user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
user32.ShowWindow.restype = ctypes.wintypes.BOOL
user32.GetWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
user32.GetWindow.restype = ctypes.c_void_p
user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.GetWindowRect.restype = ctypes.wintypes.BOOL

# 验证码窗口关键词
CAPTCHA_KEYWORDS = ['验证', 'captcha', 'tcaptcha', '安全验证', '滑块']
CAPTCHA_TEXT_HINTS = [
    '选择符合描述的图片',
    '请选择',
    '请完成验证',
    '拖动滑块',
    '点击相同',
    '依次点击',
    '请在下图中',
    '请点击',
]


def _get_text(hwnd):
    length = SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, None)
    if length <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(length + 2)
    SendMessageW(hwnd, WM_GETTEXT, length + 1, buf)
    return buf.value


def _set_text(hwnd, text):
    buf = ctypes.create_unicode_buffer(text)
    SendMessageW(hwnd, WM_SETTEXT, 0, buf)


def detect_game_path() -> str:
    """自动检测英雄联盟安装路径"""
    candidates = [
        r'E:\WeGameApps\英雄联盟',
        r'D:\WeGameApps\英雄联盟',
        r'C:\WeGameApps\英雄联盟',
        r'F:\WeGameApps\英雄联盟',
        r'E:\英雄联盟',
        r'D:\英雄联盟',
        r'D:\Program Files\WeGameApps\英雄联盟',
        r'E:\Program Files\WeGameApps\英雄联盟',
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return ''


class LoginService:
    """登录服务：后台线程执行 Win32 自动化登录"""

    def __init__(self, jicheng_dir: str):
        self._jicheng_dir = os.path.abspath(jicheng_dir)
        self._thread = None
        self._status = 'idle'       # idle / logging_in / success / failed / banned / password_leaked
        self._phase = 'idle'
        self._message = ''
        self._progress = 0          # 0-100
        self._ban_info = ''         # 封号原始文本
        self._ban_detected = False  # 封号检测标志位，防止重复处理
        self._lock = threading.Lock()
        self._on_success_callback = None
        self._on_ban_callback = None

    def set_success_callback(self, cb):
        """登录成功后的回调（用于触发 Bridge.connect）"""
        self._on_success_callback = cb

    def set_ban_callback(self, cb):
        """封号检测后的回调（用于推送封号信息到前端）"""
        self._on_ban_callback = cb

    @property
    def is_busy(self):
        return self._status == 'logging_in'

    def get_status(self) -> dict:
        with self._lock:
            result = {
                'status': self._status,
                'phase': self._phase,
                'message': self._message,
                'progress': self._progress,
            }
            if self._ban_info:
                result['ban_info'] = self._ban_info
            return result

    def _update(self, status: str, message: str, progress: int, ban_info: str = '', phase: str | None = None):
        with self._lock:
            self._status = status
            self._phase = phase or status
            self._message = message
            self._progress = progress
            if ban_info:
                self._ban_info = ban_info
            # 封号状态时设置标志位
            if status == 'banned':
                self._ban_detected = True
        # 封号状态变更时触发回调（锁外调用，避免死锁）
        if status == 'banned' and ban_info and self._on_ban_callback:
            try:
                self._on_ban_callback(ban_info)
            except Exception:
                pass

    def _detect_login_result(self, hwnd, setsoft_path: str, exclude_hwnd=None):
        """统一检测登录阶段的封号/失败结果，避免不同阶段时序不一致。"""
        ban_detail = self._read_ban_dialog(exclude_hwnd=exclude_hwnd)
        if ban_detail:
            return 'banned', ban_detail

        result_text = self._read_setsoft_result(setsoft_path)
        if not result_text:
            result_text = self._read_launcher_result(hwnd)
        if not result_text:
            return None, ''

        result_lower = result_text.lower()
        password_leak_keywords = ['密码已泄露', '密码已泄漏', '密码泄露', '密码泄漏']
        ban_keywords = ['封', '冻结', '限制', '禁止', '封号', '封停', '处罚', '违规']
        fail_keywords = ['失败', '错误', '密码', '不正确', '过期', '异常']

        if any(kw in result_text for kw in password_leak_keywords):
            return 'password_leaked', result_text
        if any(kw in result_lower for kw in ban_keywords):
            return 'banned', result_text
        if any(kw in result_lower for kw in fail_keywords):
            return 'failed', result_text
        return None, result_text

    def _handle_login_result(self, status: str, detail: str, hwnd, logger_instance=None):
        """统一处理登录阶段检测到的终态结果。"""
        if status == 'banned':
            self._update('banned', f'账号异常: {detail}', 0, ban_info=detail)
            time.sleep(0.5)
            try:
                self._read_ban_dialog(exclude_hwnd=hwnd)
                if logger_instance:
                    logger_instance.info("已尝试销毁封号弹窗")
            except Exception as e:
                if logger_instance:
                    logger_instance.warning("销毁封号弹窗失败: %s", e)
            self._kill_launcher_processes()
            return True

        if status == 'failed':
            self._kill_launcher_processes()
            self._update('failed', f'登录失败: {detail}', 0)
            return True

        if status == 'password_leaked':
            self._kill_launcher_processes()
            self._update(
                'password_leaked',
                '检测到密码泄露，已自动关闭登录器和游戏',
                0,
            )
            return True

        return False

    def _wait_for_success_stability(self, hwnd, setsoft_path: str, logger_instance=None, seconds: float = 8.0):
        """客户端启动后先短暂观察，避免封号结果晚半拍时误判成功。"""
        deadline = time.time() + max(0.0, seconds)
        while time.time() < deadline:
            if self._ban_detected:
                self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
                return False

            detected_status, detected_detail = self._detect_login_result(
                hwnd,
                setsoft_path,
                exclude_hwnd=hwnd,
            )
            if detected_status:
                if logger_instance:
                    logger_instance.info(
                        "成功前稳定观察期检测到结果: status=%s, detail=%s",
                        detected_status,
                        detected_detail[:200],
                    )
                self._handle_login_result(detected_status, detected_detail, hwnd, logger_instance)
                return False

            self._hide_launcher_popups(hwnd)
            time.sleep(0.5)

        return True

    def start_login(self, qq: str, password: str, server_index: int, game_path: str) -> dict:
        # 如果正在登录，先强制重置状态，允许再次登录
        if self.is_busy:
            self._update('idle', '', 0)
        self._ban_info = ''
        self._ban_detected = False  # 重置封号标志

        if not os.path.isdir(self._jicheng_dir):
            return {'success': False, 'message': f'jicheng 目录不存在: {self._jicheng_dir}'}
        if not qq or not password:
            return {'success': False, 'message': '账号或密码不能为空'}

        self._update('logging_in', '准备登录...', 5, phase='preparing')
        self._thread = threading.Thread(
            target=self._login_worker,
            args=(qq, password, server_index, game_path),
            daemon=True,
        )
        self._thread.start()
        return {'success': True, 'message': '登录已启动'}

    def _login_worker(self, qq: str, password: str, server_index: int, game_path: str):
        try:
            self._do_login(qq, password, server_index, game_path)
        except Exception as e:
            from logger import get_logger
            get_logger('LoginService').error("登录异常: %s", e, exc_info=True)
            self._update('failed', f'登录异常: {e}', 0, phase='failed')

    def _do_login(self, qq: str, password: str, server_index: int, game_path: str):
        from logger import get_logger
        _log = get_logger('LoginService')
        
        if not psutil:
            self._update('failed', 'psutil 未安装', 0, phase='failed')
            return

        # Step 1: Kill existing（登录器 + Riot + LOL 客户端 + 游戏进程）
        self._update('logging_in', '关闭已有进程...', 10, phase='preparing')
        kill_names = ['登录', '_cache_登录', '_cache_exe', 'exe.exe',
                      'RiotClientServices', 'RiotClientUx', 'RiotClientCrashHandler',
                      'LeagueClient', 'LeagueClientUx', 'LeagueCrashHandler',
                      'League of Legends']
        for p in psutil.process_iter(['name', 'pid']):
            try:
                name = p.info['name'] or ''
                if any(k in name for k in kill_names):
                    p.kill()
            except Exception:
                pass
        time.sleep(3)

        # Step 2: Start launcher
        self._update('logging_in', '启动登录器...', 20, phase='launching')

        # 检查封号标志
        if self._ban_detected:
            self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
            return

        main_exe = os.path.join(self._jicheng_dir, '._cache_登录器.exe')
        if not os.path.exists(main_exe):
            main_exe = os.path.join(self._jicheng_dir, '登录器.exe')
        if not os.path.exists(main_exe):
            self._update('failed', '登录器.exe 不存在', 0, phase='failed')
            return

        try:
            # 使用 STARTUPINFO 隐藏启动，避免窗口闪现
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = SW_HIDE
            subprocess.Popen([main_exe], cwd=self._jicheng_dir, startupinfo=si)
        except Exception as e:
            self._update('failed', f'启动登录器失败: {e}', 0, phase='failed')
            return

        # Step 3: Find window and hide it
        self._update('logging_in', '等待登录器窗口...', 30, phase='launching')

        # 检查封号标志
        if self._ban_detected:
            self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
            return

        hwnd = self._find_launcher_window(timeout=15)
        if not hwnd:
            self._update('failed', '未找到登录器窗口', 0, phase='failed')
            return

        # 确保窗口隐藏（STARTUPINFO 已指定隐藏，此处为兜底）
        user32.ShowWindow(hwnd, SW_HIDE)

        # Step 4: Set controls (SendMessage 不需要窗口可见)
        self._update('logging_in', '填写登录信息...', 40, phase='filling_credentials')

        # 检查封号标志
        if self._ban_detected:
            self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
            return

        children = self._get_children(hwnd)
        edits = sorted([c for c in children if c['class'] == 'Edit'], key=lambda x: x['rect'][1])
        login_btn = next((c['hwnd'] for c in children if c['class'] == 'Button' and c['text'] == '登录'), None)
        server_combo = next((c['hwnd'] for c in children if c['class'] == 'ComboBox'), None)

        if len(edits) < 3 or not login_btn or not server_combo:
            self._update('failed', '登录器控件识别失败', 0, phase='failed')
            return

        account_edit = edits[0]['hwnd']
        password_edit = edits[1]['hwnd']
        path_edit = edits[2]['hwnd']

        _set_text(account_edit, qq)
        _set_text(password_edit, password)
        _set_text(path_edit, game_path)

        # 读取 ComboBox 实际选项，按大区名称匹配（而非硬编码 index）
        CB_GETCOUNT = 0x0146
        CB_GETLBTEXT = 0x0148
        CB_GETLBTEXTLEN = 0x0149
        combo_count = SendMessageW(server_combo, CB_GETCOUNT, 0, None)
        target_name = SERVER_LIST[server_index] if 0 <= server_index < len(SERVER_LIST) else ''
        matched_index = server_index  # 默认用传入的 index

        if target_name and combo_count > 0:
            from logger import get_logger
            _slog = get_logger('LoginService')
            for ci in range(combo_count):
                text_len = SendMessageW(server_combo, CB_GETLBTEXTLEN, ci, None)
                if text_len > 0:
                    buf = ctypes.create_unicode_buffer(text_len + 2)
                    SendMessageW(server_combo, CB_GETLBTEXT, ci, buf)
                    if buf.value.strip() == target_name:
                        matched_index = ci
                        _slog.debug("大区匹配: '%s' -> ComboBox index %d", target_name, ci)
                        break
            else:
                _slog.warning("大区 '%s' 未在 ComboBox 中找到，使用默认 index %d", target_name, server_index)

        SendMessageW(server_combo, CB_SETCURSEL, matched_index, None)

        # Step 5: Click login
        self._update('logging_in', '点击登录...', 50, phase='submitting')
        procs_before = set()
        for p in psutil.process_iter(['pid']):
            try:
                procs_before.add(p.info['pid'])
            except Exception:
                pass

        setsoft_path = os.path.join(self._jicheng_dir, 'data', 'setsoft.ini')
        # 在点击登录前先清空旧结果，避免新结果刚写入就被后续清空覆盖。
        self._write_setsoft_result(setsoft_path, '')

        SendMessageW(login_btn, BM_CLICK, 0, None)

        # 点击登录后立即隐藏登录器窗口
        time.sleep(0.3)
        user32.ShowWindow(hwnd, SW_HIDE)

        # Step 6: Monitor — 同时监控 setsoft.ini 的结果字段
        self._update('logging_in', 'QQ 认证中...', 55, phase='authenticating')
        rc_started = False
        lc_started = False
        captcha_shown = False

        # 首次立即检测，避免首个封号弹窗/结果出现在第一次轮询之前而被漏掉。
        immediate_status, immediate_detail = self._detect_login_result(
            hwnd,
            setsoft_path,
            exclude_hwnd=hwnd,
        )
        if immediate_status and self._handle_login_result(immediate_status, immediate_detail, hwnd, _log):
            return

        for i in range(120):
            time.sleep(1)
            sec = i + 1

            # 检查封号标志（最高优先级）
            if self._ban_detected:
                self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
                return

            # --- 检查封号弹窗（每秒检测一次，纯 Win32）---
            ban_detail = self._read_ban_dialog(exclude_hwnd=hwnd)
            if ban_detail:
                from logger import get_logger
                get_logger('LoginService').info("检测到封号弹窗，终止登录流程: %s", ban_detail[:200])
                # 先更新状态并触发回调（推送到前端）
                self._update('banned', '账号封号', 0, ban_info=ban_detail)
                # 等待回调执行完成
                time.sleep(0.5)
                # 再终止进程
                self._kill_launcher_processes()
                return

            # --- 检查 setsoft.ini 结果字段（封号/失败检测）---
            result_text = self._read_setsoft_result(setsoft_path)
            # 也尝试从登录器窗口的 Static/Label 控件读取结果
            if not result_text:
                result_text = self._read_launcher_result(hwnd)

            if result_text:
                result_lower = result_text.lower()
                # 封号/冻结/限制等关键词
                ban_keywords = ['封', '冻结', '限制', '禁止', '封号', '封停', '处罚', '违规']
                fail_keywords = ['失败', '错误', '密码', '不正确', '过期', '异常']
                if any(kw in result_lower for kw in ban_keywords):
                    # 先更新状态并触发回调（推送到前端）
                    self._update('banned', f'账号异常: {result_text}', 0, ban_info=result_text)
                    # 等待回调执行完成
                    time.sleep(0.5)
                    # 销毁封号弹窗（如果存在）
                    try:
                        self._read_ban_dialog(exclude_hwnd=hwnd)
                        _log.info("已尝试销毁封号弹窗")
                    except Exception as e:
                        _log.warning("销毁封号弹窗失败: %s", e)
                    # 再终止进程
                    self._kill_launcher_processes()
                    return
                if any(kw in result_lower for kw in fail_keywords):
                    self._kill_launcher_processes()
                    self._update('failed', f'登录失败: {result_text}', 0)
                    return

            detected_status, detected_detail = self._detect_login_result(
                hwnd,
                setsoft_path,
                exclude_hwnd=hwnd,
            )
            if detected_status:
                _log.info("检测到登录结果: status=%s, detail=%s", detected_status, detected_detail[:200])
                if self._handle_login_result(detected_status, detected_detail, hwnd, _log):
                    return

            # --- 验证码窗口检测 ---
            captcha_hwnd = self._find_captcha_window(exclude_hwnd=hwnd)
            if captcha_hwnd:
                if not captcha_shown:
                    captcha_shown = True
                # 确保验证码窗口可见并置顶
                user32.ShowWindow(captcha_hwnd, SW_RESTORE)
                user32.SetForegroundWindow(captcha_hwnd)
                # 显示验证码后再次隐藏登录器主窗口（防止被连带显示）
                try:
                    if user32.IsWindowVisible(hwnd):
                        user32.ShowWindow(hwnd, SW_HIDE)
                except Exception:
                    pass
                self._update('logging_in', '请完成验证码', 55, phase='waiting_captcha')
                continue
            else:
                if captcha_shown:
                    # 验证码窗口消失，说明用户已完成验证
                    captcha_shown = False
                    self._update('logging_in', '验证码已完成，等待认证...', 60, phase='authenticating')
                    
                    # 验证码完成后，立即检测登录结果（可能验证失败）
                    time.sleep(2)  # 等待2秒让结果写入
                    detected_status, detected_detail = self._detect_login_result(
                        hwnd,
                        setsoft_path,
                        exclude_hwnd=hwnd,
                    )
                    if detected_status:
                        _log.info("验证码完成后检测到结果: status=%s, detail=%s", detected_status, detected_detail[:200])
                        if self._handle_login_result(detected_status, detected_detail, hwnd, _log):
                            return

            # 持续确保登录器主窗口隐藏
            try:
                if user32.IsWindowVisible(hwnd):
                    user32.ShowWindow(hwnd, SW_HIDE)
            except Exception:
                pass

            # --- 隐藏登录器的非验证码弹窗 ---
            self._hide_launcher_popups(hwnd)

            # Update progress
            if sec <= 20:
                self._update('logging_in', 'QQ 认证中...', 55 + sec, phase='authenticating')
            elif sec <= 40:
                self._update('logging_in', '等待游戏客户端启动...', 75 + (sec - 20) // 2, phase='waiting_client')
            else:
                self._update('logging_in', '等待游戏客户端...', min(95, 85 + (sec - 40) // 4), phase='waiting_client')

            # Check RC
            if not rc_started:
                for p in psutil.process_iter(['name', 'pid']):
                    try:
                        if p.info['name'] == 'RiotClientServices.exe' and p.info['pid'] not in procs_before:
                            rc_started = True
                            self._update('logging_in', 'Riot Client 已启动，等待游戏客户端...', 85, phase='waiting_client')
                    except Exception:
                        pass

            # Check LeagueClient
            if rc_started and not lc_started:
                for p in psutil.process_iter(['name', 'pid']):
                    try:
                        if p.info['name'] == 'LeagueClientUx.exe' and p.info['pid'] not in procs_before:
                            lc_started = True
                    except Exception:
                        pass

            if lc_started:
                # 最后一次检查封号标志
                if self._ban_detected:
                    self._update('banned', '检测到封号，终止登录', 0, ban_info=self._ban_info)
                    return

                # 在标记成功前，再次检查封号弹窗（可能在客户端启动瞬间出现）
                ban_detail = self._read_ban_dialog(exclude_hwnd=hwnd)
                if ban_detail:
                    from logger import get_logger
                    get_logger('LoginService').info("客户端启动后检测到封号弹窗: %s", ban_detail[:200])
                    # 先更新状态并触发回调（推送到前端）
                    self._update('banned', '账号封号', 0, ban_info=ban_detail)
                    # 等待回调执行完成
                    time.sleep(0.5)
                    # 再终止进程
                    self._kill_launcher_processes()
                    return

                if not self._wait_for_success_stability(hwnd, setsoft_path, _log, seconds=8.0):
                    return

                # Hide launcher window
                try:
                    user32.ShowWindow(hwnd, SW_HIDE)
                except Exception:
                    pass
                # 先标记成功并触发连接回调
                self._update('success', '登录成功，正在连接客户端...', 100, phase='launcher_success')
                if self._on_success_callback:
                    try:
                        self._on_success_callback()
                    except Exception:
                        pass
                # 启动后台线程持续监控封号弹窗（弹窗可能延迟很久才出现）
                threading.Thread(
                    target=self._post_login_ban_monitor,
                    args=(hwnd,),
                    daemon=True,
                ).start()
                return

        # 超时：清理登录器进程
        self._kill_launcher_processes()
        self._update('failed', '登录超时（120秒）', 0, phase='failed')

    def _post_login_ban_monitor(self, exclude_hwnd=None):
        """登录成功后持续监控封号弹窗（后台线程，持续 90 秒）。

        封号弹窗可能在客户端完全加载后才出现，延迟可达数十秒。
        如果检测到封号，更新状态为 banned 并杀掉所有相关进程。
        """
        from logger import get_logger
        _log = get_logger('BanMonitor')
        _log.info("启动登录后封号监控（90秒）")
        for i in range(90):
            time.sleep(1)
            # 如果用户已手动开始新的登录，停止监控
            if self._status == 'logging_in':
                _log.debug("检测到新登录流程，停止封号监控")
                return
            try:
                ban_detail = self._read_ban_dialog(exclude_hwnd=exclude_hwnd)
                if ban_detail:
                    _log.info("登录后检测到封号弹窗（第%d秒）: %s", i + 1, ban_detail[:200])
                    # 先更新状态并触发回调（推送到前端）
                    self._update('banned', '账号封号', 0, ban_info=ban_detail)
                    # 等待回调执行完成
                    time.sleep(0.5)
                    # 再终止进程
                    self._kill_launcher_processes()
                    return
            except Exception as e:
                _log.debug("封号监控异常: %s", e)
        _log.debug("封号监控结束，未检测到封号弹窗")

    def focus_captcha_window(self) -> dict:
        hwnd = self._find_captcha_window()
        if not hwnd:
            return {'success': False, 'message': '当前没有检测到验证码窗口'}
        try:
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
            return {'success': True, 'message': '已尝试将验证码窗口置前'}
        except Exception as exc:
            return {'success': False, 'message': f'置前验证码窗口失败: {exc}'}

    def _kill_launcher_processes(self, hwnd=None):
        """关闭窗口 + 杀进程树，默认2次重试。有 hwnd 时先发 WM_CLOSE。"""
        from logger import get_logger
        from ctypes import windll
        _log = get_logger("KillProc")
        kill_names = ["登录", "_cache_登录", "_cache_exe", "exe.exe",
                      "RiotClientServices", "RiotClientUx", "RiotClientCrashHandler",
                      "RiotClientUxRender",
                      "LeagueClient", "LeagueClientUx", "LeagueClientCrashHandler",
                      "LeagueClientUxRender", "League of Legends"]
        WM_CLOSE = 0x0010

        for attempt in range(2):
            if attempt == 0:
                target = hwnd
                if target is None:
                    target = self._find_launcher_window(timeout=1)
                if target:
                    try:
                        windll.user32.SendMessageW(target, WM_CLOSE, 0, 0)
                        _log.debug("WM_CLOSE sent")
                    except Exception:
                        pass

            killed = []
            found = False
            for p in psutil.process_iter(["name", "pid"]):
                try:
                    name = p.info["name"] or ""
                    if any(k in name for k in kill_names):
                        found = True
                        pid = p.info["pid"]
                        try:
                            subprocess.call(
                                ["taskkill", "/F", "/T", "/PID", str(pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
                            )
                        except Exception:
                            pass
                        try:
                            if p.is_running():
                                p.kill()
                                p.wait(timeout=1)
                        except Exception:
                            pass
                        killed.append(f"{name}({pid})")
                except Exception:
                    pass

            if killed:
                _log.info(f"第{attempt+1}次关闭，已终止: {', '.join(killed)}")
            if not found:
                _log.info("所有目标进程已终止")
                break
            if attempt == 0:
                time.sleep(0.8)

    def _hide_launcher_popups(self, main_hwnd):
        """隐藏登录器进程的所有可见弹窗（验证码窗口除外）"""
        launcher_names = ['登录', '_cache_登录', '_cache_exe', 'exe.exe']

        def _check(hwnd, _lp):
            if hwnd == main_hwnd:
                return True
            if not user32.IsWindowVisible(hwnd):
                return True
            if self._is_captcha_window(hwnd):
                return True  # 验证码窗口不隐藏
            # 检查是否属于登录器进程
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                pname = psutil.Process(pid.value).name()
                if any(k in pname for k in launcher_names):
                    user32.ShowWindow(hwnd, SW_HIDE)
            except Exception:
                pass
            return True

        try:
            user32.EnumWindows(WNDENUMPROC(_check), 0)
        except Exception:
            pass

    def _is_captcha_window(self, hwnd) -> bool:
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        title_lower = title.value.lower()
        if title_lower and any(kw in title_lower for kw in CAPTCHA_KEYWORDS):
            return True

        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        cls_lower = cls.value.lower()
        if 'tcaptcha' in cls_lower or 'captcha' in cls_lower:
            return True

        try:
            for child in self._get_children(hwnd):
                text = (child.get('text') or '').strip().lower()
                if not text:
                    continue
                if any(kw in text for kw in CAPTCHA_KEYWORDS):
                    return True
                if any(hint in text for hint in CAPTCHA_TEXT_HINTS):
                    return True
        except Exception:
            pass

        return False

    def _find_captcha_window(self, exclude_hwnd=None):
        """扫描是否有验证码窗口弹出（排除登录器主窗口）"""
        result = [None]

        def check_window(hwnd, lparam):
            if exclude_hwnd and hwnd == exclude_hwnd:
                return True
            if self._is_captcha_window(hwnd):
                result[0] = hwnd
                return False
            return True

        user32.EnumWindows(WNDENUMPROC(check_window), 0)
        return result[0]

    def _find_launcher_window(self, timeout=15):
        for _ in range(timeout):
            result = [None]

            def find_main(hwnd, lparam):
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    pname = psutil.Process(pid.value).name()
                    if '登录' in pname or '_cache_登录' in pname:
                        title = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(hwnd, title, 256)
                        if title.value and '上号' in title.value:
                            result[0] = hwnd
                except Exception:
                    pass
                return True

            user32.EnumWindows(WNDENUMPROC(find_main), 0)
            if result[0]:
                return result[0]
            time.sleep(1)
        return None

    def _get_children(self, parent_hwnd):
        children = []

        def enum_all(parent):
            child = user32.GetWindow(parent, 5)
            while child:
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(child, cls, 256)
                txt = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(child, txt, 256)
                r = ctypes.wintypes.RECT()
                user32.GetWindowRect(child, ctypes.byref(r))
                children.append({
                    'hwnd': child,
                    'class': cls.value,
                    'text': txt.value,
                    'rect': (r.left, r.top, r.right, r.bottom),
                })
                enum_all(child)
                child = user32.GetWindow(child, 2)

        enum_all(parent_hwnd)
        return children

    @staticmethod
    def _read_setsoft_result(path: str) -> str:
        """读取 setsoft.ini 中的结果字段"""
        try:
            if not os.path.exists(path):
                return ''
            with open(path, 'r', encoding='gbk', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('结果'):
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        except Exception:
            pass
        return ''

    @staticmethod
    def _write_setsoft_result(path: str, value: str):
        """清空 setsoft.ini 中的结果字段"""
        try:
            if not os.path.exists(path):
                return
            lines = []
            with open(path, 'r', encoding='gbk', errors='ignore') as f:
                lines = f.readlines()
            with open(path, 'w', encoding='gbk', errors='ignore') as f:
                for line in lines:
                    if line.strip().startswith('结果'):
                        f.write(f'结果 = {value}\n')
                    else:
                        f.write(line)
        except Exception:
            pass

    def _read_launcher_result(self, hwnd) -> str:
        """从登录器窗口的 Static/Label 控件读取结果文本"""
        try:
            children = self._get_children(hwnd)
            for c in children:
                if c['class'] in ('Static', 'Label', 'RichEdit20W', 'RichEdit20A'):
                    text = _get_text(c['hwnd'])
                    if text and len(text) > 1:
                        # 过滤掉固定标签文本
                        skip = ['账号', '密码', '大区', '路径', '登录', '上号', '游戏']
                        if not any(text.strip() == kw for kw in skip):
                            # 只返回包含结果关键词的文本
                            result_hints = ['封', '冻结', '限制', '失败', '错误', '成功',
                                            '过期', '异常', '处罚', '违规', '禁止']
                            if any(kw in text for kw in result_hints):
                                return text.strip()
        except Exception:
            pass
        return ''

    def _contains_date(self, text: str) -> bool:
        """检测文本中是否包含日期

        只要包含日期格式，就认为是封号相关弹窗
        支持的日期格式：
        - 2026年3月1日
        - 2026-3-26
        - 2026/03/01
        - 2026.3.1
        - 至2026年
        - 解封时间：2026
        等等
        """
        import re

        if not text:
            return False

        # 日期正则表达式模式
        date_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',  # 2026年3月1日
            r'\d{4}-\d{1,2}-\d{1,2}',      # 2026-3-26
            r'\d{4}/\d{1,2}/\d{1,2}',      # 2026/03/01
            r'\d{4}\.\d{1,2}\.\d{1,2}',    # 2026.3.1
            r'至\d{4}年',                   # 至2026年
            r'到期.*?\d{4}',                # 到期时间：2026
            r'解封.*?\d{4}',                # 解封时间：2026
            r'处罚.*?\d{4}',                # 处罚时间：2026
            r'封停至.*?\d{4}',              # 封停至2026
        ]

        for pattern in date_patterns:
            if re.search(pattern, text):
                return True

        return False

    def _read_ban_dialog(self, exclude_hwnd=None, **_kwargs) -> str:
        """扫描封号弹窗，纯 Win32 实现（不依赖 UIA）。
        
        检测标题为 '查询结果' / '信息:' / '信息' / '信息：' 的弹窗，
        读取子控件文本判断是否包含封号关键词。
        """
        from logger import get_logger
        _log = get_logger('BanDetect')

        ban_keywords = ['封号', '处罚', '冻结', '解封', '封停', '违规',
                        '处罚时间', '解封时间', '已被封停']

        def _read_dialog_text(hwnd) -> str:
            """用 EnumChildWindows 读取弹窗内所有子控件文本"""
            texts = []
            WNDENUMPROC_LOCAL = ctypes.WINFUNCTYPE(
                ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

            def _enum_child(child, _lp):
                text = _get_text(child)
                if text and text.strip():
                    texts.append(text.strip())
                return True

            try:
                _cb = WNDENUMPROC_LOCAL(_enum_child)
                user32.EnumChildWindows(hwnd, _cb, 0)
            except Exception as e:
                _log.debug("EnumChildWindows 异常: %s", e)
            return '\n'.join(texts)

        # === 策略1: FindWindowW 精确查找已知标题 ===
        # 扩展弹窗标题列表，覆盖更多可能的变体
        search_titles = [
            '查询结果', '信息:', '信息：', '信息',
            '提示', '提示:', '提示：',
            '警告', '警告:', '警告：',
            '系统消息', '系统提示',
            '账号状态', '账号信息',
            '处罚通知', '封号通知'
        ]
        for title_keyword in search_titles:
            try:
                found = FindWindowW(None, title_keyword)
                if not found or found == (exclude_hwnd or 0):
                    continue
                child_text = _read_dialog_text(found)
                full = f"{title_keyword}\n{child_text}" if child_text else title_keyword

                # 记录所有找到的窗口（用于调试）
                _log.info("FindWindowW 找到窗口 '%s'，内容: %s", title_keyword, full[:500])

                # 双重检测：关键词检测 OR 日期检测
                has_ban_keyword = any(kw in full for kw in ban_keywords)
                has_date = self._contains_date(full)

                if has_ban_keyword or has_date:
                    detection_reason = []
                    if has_ban_keyword:
                        detection_reason.append("包含封号关键词")
                    if has_date:
                        detection_reason.append("包含日期")

                    _log.info("FindWindowW 检测到封号 (title='%s', 原因: %s): %s",
                              title_keyword, " + ".join(detection_reason), full[:300])
                    # 多次尝试销毁封号弹窗（使用多种方法）
                    for attempt in range(3):
                        try:
                            # 方法1: DestroyWindow
                            if user32.IsWindow(found):
                                user32.DestroyWindow(found)
                                _log.info("已销毁封号弹窗 (DestroyWindow, 尝试%d)", attempt + 1)
                        except Exception as e:
                            _log.warning("DestroyWindow 失败 (尝试%d): %s", attempt + 1, e)

                        try:
                            # 方法2: ShowWindow(SW_HIDE)
                            if user32.IsWindow(found):
                                user32.ShowWindow(found, SW_HIDE)
                                _log.info("已隐藏封号弹窗 (ShowWindow, 尝试%d)", attempt + 1)
                        except Exception:
                            pass

                        try:
                            # 方法3: PostMessage(WM_CLOSE)
                            if user32.IsWindow(found):
                                user32.PostMessageW(found, 0x0010, 0, 0)  # WM_CLOSE
                                _log.info("已发送关闭消息 (WM_CLOSE, 尝试%d)", attempt + 1)
                        except Exception:
                            pass

                        if attempt < 2:
                            time.sleep(0.2)

                    # 启动持续隐藏线程
                    threading.Thread(
                        target=self._continuous_hide_ban_dialog,
                        args=(found,),
                        daemon=True
                    ).start()
                    return full
                # 标题为 '查询结果' 且未检测到封号关键词或日期时，也记录内容
                if title_keyword == '查询结果':
                    _log.info("标题为'查询结果'但未检测到封号特征，内容: %s", full[:200])
            except Exception as e:
                _log.debug("FindWindowW('%s') 异常: %s", title_keyword, e)

        # === 策略2: EnumWindows 扫描登录器进程的所有弹窗 ===
        found_result = [None]

        def _scan(hwnd, _lp):
            if exclude_hwnd and hwnd == exclude_hwnd:
                return True
            title = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, title, 512)
            title_str = title.value

            # 判断是否属于登录器进程
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            is_launcher_proc = False
            try:
                pname = psutil.Process(pid.value).name()
                if any(k in pname for k in ['登录', '_cache_登录', '_cache_exe', 'exe.exe']):
                    is_launcher_proc = True
            except Exception:
                pass

            # 标题含封号关键词 或 属于登录器进程且有标题
            title_hit = title_str and any(
                kw in title_str for kw in ['查询结果', '信息', '封号', '处罚', '封停'])
            if not title_hit and not (is_launcher_proc and title_str):
                return True

            child_text = _read_dialog_text(hwnd)
            full = f"{title_str}\n{child_text}" if child_text else title_str

            # 记录所有可疑窗口（用于调试）
            _log.info("EnumWindows 找到可疑窗口 (title='%s', launcher_proc=%s): %s",
                     title_str, is_launcher_proc, full[:500])

            # 双重检测：关键词检测 OR 日期检测
            has_ban_keyword = any(kw in full for kw in ban_keywords)
            has_date = self._contains_date(full)

            if has_ban_keyword or has_date:
                detection_reason = []
                if has_ban_keyword:
                    detection_reason.append("包含封号关键词")
                if has_date:
                    detection_reason.append("包含日期")

                _log.info("EnumWindows 检测到封号 (title='%s', 原因: %s): %s",
                          title_str, " + ".join(detection_reason), full[:300])
                # 多次尝试销毁封号弹窗（使用多种方法）
                for attempt in range(3):
                    try:
                        # 方法1: DestroyWindow
                        if user32.IsWindow(hwnd):
                            user32.DestroyWindow(hwnd)
                            _log.info("已销毁封号弹窗 (DestroyWindow, 尝试%d)", attempt + 1)
                    except Exception as e:
                        _log.warning("DestroyWindow 失败 (尝试%d): %s", attempt + 1, e)

                    try:
                        # 方法2: ShowWindow(SW_HIDE)
                        if user32.IsWindow(hwnd):
                            user32.ShowWindow(hwnd, SW_HIDE)
                            _log.info("已隐藏封号弹窗 (ShowWindow, 尝试%d)", attempt + 1)
                    except Exception:
                        pass

                    try:
                        # 方法3: PostMessage(WM_CLOSE)
                        if user32.IsWindow(hwnd):
                            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                            _log.info("已发送关闭消息 (WM_CLOSE, 尝试%d)", attempt + 1)
                    except Exception:
                        pass

                    if attempt < 2:
                        time.sleep(0.2)

                # 启动持续隐藏线程
                threading.Thread(
                    target=self._continuous_hide_ban_dialog,
                    args=(hwnd,),
                    daemon=True
                ).start()
                found_result[0] = full
                return False  # 停止枚举
            return True

        try:
            user32.EnumWindows(WNDENUMPROC(_scan), 0)
        except Exception as e:
            _log.debug("EnumWindows 异常: %s", e)

        return found_result[0] or ''

    def _continuous_hide_ban_dialog(self, hwnd):
        """持续隐藏/销毁封号弹窗（后台线程，持续10秒）

        封号弹窗可能被重新显示，需要持续监控并销毁。
        """
        from logger import get_logger
        _log = get_logger('BanHide')

        _log.info("启动持续隐藏封号弹窗线程")

        for i in range(20):  # 持续10秒（每次0.5秒）
            try:
                # 检查窗口是否仍然存在
                if not user32.IsWindow(hwnd):
                    _log.info("封号弹窗已被销毁，停止监控")
                    break

                # 如果窗口可见，使用多种方法尝试销毁
                if user32.IsWindowVisible(hwnd):
                    _log.info("检测到封号弹窗重新显示，尝试销毁（第%d次）", i + 1)

                    # 方法1: DestroyWindow
                    try:
                        user32.DestroyWindow(hwnd)
                        _log.debug("DestroyWindow 成功")
                    except Exception:
                        pass

                    # 方法2: ShowWindow(SW_HIDE)
                    try:
                        user32.ShowWindow(hwnd, SW_HIDE)
                        _log.debug("ShowWindow 成功")
                    except Exception:
                        pass

                    # 方法3: PostMessage(WM_CLOSE)
                    try:
                        user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                        _log.debug("PostMessage(WM_CLOSE) 成功")
                    except Exception:
                        pass
            except Exception as e:
                _log.debug("持续隐藏异常: %s", e)

            time.sleep(0.5)

        _log.info("持续隐藏封号弹窗线程结束")
