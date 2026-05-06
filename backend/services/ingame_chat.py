"""游戏内聊天服务 - 通过模拟键盘在游戏内发送消息"""
import time
import threading

from logger import get_logger
from services.scoring import calculate_player_score, compute_match_stats

log = get_logger('InGameChat')

IN_GAME_PHASES = {'GameStart', 'InProgress', 'Reconnect'}
RESET_PHASES = {
    'None',
    'Lobby',
    'Matchmaking',
    'CheckedIntoTournament',
    'ReadyCheck',
    'ChampSelect',
    'FailedToLaunch',
    'WaitingForStats',
    'PreEndOfGame',
    'EndOfGame',
    'TerminatedInError',
}

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 禁用安全模式
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    log.warning("pyautogui未安装，游戏内聊天功能不可用")


class InGameChatService:
    def __init__(self, api, events, jungle_monitor=None):
        self.api = api
        self.events = events
        self.jungle_monitor = jungle_monitor  # 引用野怪监控服务
        self._enabled = False
        self._sent_this_game = False
        self._game_state_lock = threading.RLock()  # 保护 _sent_this_game / _current_game_id
        self._current_game_id = None  # 用于追踪当前游戏
        self._noob_message = None
        self._noob_info = None  # 存储牛马详细信息
        self._team_analyzer = None  # 引用team_analyzer用于查询对手
        self._phase_guard_thread = None
        self._phase_guard_stop = threading.Event()
        self._phase_guard_interval = 1.2
        self._last_phase = 'None'
        self._auto_send_inflight = False
        self._last_auto_send_attempt_ts = 0.0
        self._auto_send_cooldown_seconds = 12.0
    
    @property
    def enabled(self):
        return self._enabled
    
    @enabled.setter
    def enabled(self, value):
        self._enabled = value
    
    def set_team_analyzer(self, analyzer):
        """设置team_analyzer引用"""
        self._team_analyzer = analyzer
    
    def set_noob_message(self, message):
        """设置要发送的牛马消息"""
        self._noob_message = message
    
    def set_noob_info(self, noob_info):
        """设置牛马详细信息"""
        self._noob_info = noob_info
    
    def start(self):
        """启动服务，监听游戏阶段变化"""
        self.events.subscribe('/lol-gameflow/v1/gameflow-phase', self._on_phase_change)
        self._phase_guard_stop.clear()
        if not self._phase_guard_thread or not self._phase_guard_thread.is_alive():
            self._phase_guard_thread = threading.Thread(target=self._phase_guard_loop, daemon=True)
            self._phase_guard_thread.start()
        try:
            phase, game_id = self._get_phase_and_game_id()
            if phase:
                self._handle_phase_change(phase, game_id=game_id, source='bootstrap')
        except Exception as e:
            log.debug("phase bootstrap sync failed: %s", e)
    
    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-gameflow/v1/gameflow-phase', self._on_phase_change)
        self._phase_guard_stop.set()
        if self._phase_guard_thread and self._phase_guard_thread.is_alive():
            self._phase_guard_thread.join(timeout=2.0)
        self._phase_guard_thread = None

    @staticmethod
    def _normalize_phase(phase):
        if phase is None:
            return ''
        if isinstance(phase, str):
            return phase
        return str(phase)

    @staticmethod
    def _is_in_game_phase(phase):
        return phase in IN_GAME_PHASES

    def _extract_game_id(self, session):
        if not isinstance(session, dict):
            return None
        game_data = session.get('gameData')
        if not isinstance(game_data, dict):
            return None
        game_id = game_data.get('gameId')
        if not game_id:
            return None
        return str(game_id)

    def _get_phase_and_game_id(self):
        phase = ''
        game_id = None

        session = self.api.get('/lol-gameflow/v1/session')
        if isinstance(session, dict):
            phase = self._normalize_phase(session.get('phase'))
            game_id = self._extract_game_id(session)

        if not phase:
            phase = self._normalize_phase(self.api.get_gameflow_phase())
        return phase, game_id

    def _phase_guard_loop(self):
        while not self._phase_guard_stop.wait(self._phase_guard_interval):
            try:
                phase, game_id = self._get_phase_and_game_id()
                if not phase:
                    continue
                self._handle_phase_change(phase, game_id=game_id, source='poll')
            except Exception as e:
                log.debug("phase guard loop error: %s", e)

    def _sync_jungle_monitor_state(self, phase: str):
        """根据游戏阶段自动控制野怪监控启停。"""
        if not self.jungle_monitor:
            log.warning("jungle_monitor 引用为空，无法自动控制启停")
            return

        auto_start_enabled = self.jungle_monitor.auto_start
        is_running = self.jungle_monitor.is_running()
        log.info("野怪监控阶段同步: phase=%s, auto_start=%s, is_running=%s", phase, auto_start_enabled, is_running)

        if not auto_start_enabled:
            return

        if self._is_in_game_phase(phase):
            if not is_running:
                log.info("检测到进入游戏，自动启动野怪监控")
                try:
                    started = self.jungle_monitor.start()
                    log.info("野怪监控启动结果: %s", started)
                except Exception as e:
                    log.error("自动启动野怪监控失败: %s", e)
            return

        if is_running and phase in RESET_PHASES:
            log.info("检测到离开游戏阶段(%s)，自动停止野怪监控", phase)
            try:
                stopped = self.jungle_monitor.stop()
                log.info("野怪监控停止结果: %s", stopped)
            except Exception as e:
                log.error("自动停止野怪监控失败: %s", e)

    def _reset_runtime_state(self):
        with self._game_state_lock:
            self._sent_this_game = False
            self._current_game_id = None
            self._auto_send_inflight = False
            self._last_auto_send_attempt_ts = 0.0
        self._noob_info = None
        self._noob_message = None

    def _mark_current_game(self, game_id):
        if not game_id:
            return
        with self._game_state_lock:
            if self._current_game_id and self._current_game_id != game_id:
                self._sent_this_game = False
            self._current_game_id = game_id

    def _maybe_trigger_auto_taunt(self, phase, game_id=None, source='event'):
        now = time.time()
        with self._game_state_lock:
            if not self._enabled:
                return
            if self._sent_this_game or self._auto_send_inflight:
                return
            if now - self._last_auto_send_attempt_ts < self._auto_send_cooldown_seconds:
                return
            self._last_auto_send_attempt_ts = now
            self._auto_send_inflight = True

        log.info("检测到游戏内阶段(%s, source=%s)，触发自动嘲讽...", phase, source)
        threading.Thread(target=self._auto_send_taunt, args=(game_id,), daemon=True).start()

    def _handle_phase_change(self, phase, game_id=None, source='event'):
        phase = self._normalize_phase(phase)
        if not phase:
            return

        with self._game_state_lock:
            self._last_phase = phase
        self._mark_current_game(game_id)

        self._sync_jungle_monitor_state(phase)

        if phase == 'ChampSelect':
            self._noob_info = None
            self._noob_message = None

        if self._is_in_game_phase(phase):
            self._maybe_trigger_auto_taunt(phase, game_id=game_id, source=source)
            return

        if phase in RESET_PHASES:
            log.debug("重置状态: phase=%s", phase)
            self._reset_runtime_state()

    def _on_phase_change(self, uri, data):
        phase = self._normalize_phase(data)
        log.debug("游戏阶段变化: %s, enabled=%s, sent=%s", phase, self._enabled, self._sent_this_game)
        session_game_id = None
        if self._is_in_game_phase(phase):
            try:
                session = self.api.get('/lol-gameflow/v1/session')
                session_game_id = self._extract_game_id(session)
            except Exception:
                session_game_id = None
        self._handle_phase_change(phase, game_id=session_game_id, source='event')
    
    def _auto_send_taunt(self, game_id_hint=None):
        """自动发送嘲讽（进入游戏后）"""
        try:
            log.info("检测到进入游戏，等待游戏加载完成...")

            game_started = False
            for i in range(60):
                game_time = self._get_game_time()
                if game_time is not None and game_time > 5:
                    log.debug("游戏已开始，当前时间: %s秒", game_time)
                    game_started = True
                    break
                time.sleep(2)

            if not game_started:
                log.warning("等待游戏时间超时，继续尝试发送")

            phase = self._normalize_phase(self.api.get_gameflow_phase())
            if not self._is_in_game_phase(phase):
                log.debug("当前不在游戏内阶段，取消发送 (phase=%s)", phase)
                return

            session = self.api.get('/lol-gameflow/v1/session')
            session_game_id = self._extract_game_id(session)
            game_id = session_game_id or game_id_hint
            self._mark_current_game(game_id)

            if not self._noob_info:
                for _ in range(8):
                    self._noob_info = self._fetch_enemy_noob()
                    if self._noob_info:
                        break
                    phase = self._normalize_phase(self.api.get_gameflow_phase())
                    if not self._is_in_game_phase(phase):
                        log.debug("获取对手信息期间已离开游戏，取消发送")
                        return
                    time.sleep(1.5)

            if not self._noob_info:
                log.warning("无法获取对手信息，取消发送")
                return

            lines = generate_smart_taunt(self._noob_info)
            if not lines:
                log.warning("无法生成嘲讽")
                return

            log.debug("生成嘲讽: %d 行", len(lines))
            for i, line in enumerate(lines):
                full_message = f"/all {line}"
                if i == 0:
                    time.sleep(1)

                success = self._send_with_ahk(full_message)
                if not success:
                    log.warning("发送失败: %s", line)
                time.sleep(0.5)

            with self._game_state_lock:
                self._sent_this_game = True
                if game_id:
                    self._current_game_id = game_id
            log.info("自动嘲讽发送完成")

        except Exception as e:
            log.error("自动发送错误: %s", e, exc_info=True)
        finally:
            with self._game_state_lock:
                self._auto_send_inflight = False
    
    def _get_game_time(self):
        """获取当前游戏时间（通过Live Client API）"""
        try:
            import urllib.request
            import ssl
            import json
            
            # Live Client API 不验证证书
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = "https://127.0.0.1:2999/liveclientdata/gamestats"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=2, context=ctx) as response:
                data = json.loads(response.read().decode())
                return data.get('gameTime', 0)
        except Exception:
            return None
    
    def _send_with_ahk(self, message):
        """使用 AHK 发送消息（自动探测路径）"""
        try:
            import subprocess
            import os
            
            ahk_exe = self._find_ahk_exe()
            if not ahk_exe:
                log.warning("未找到 AutoHotkey，请安装 AutoHotkey v2 或将其加入 PATH")
                return False
            
            script_dir = os.path.dirname(os.path.dirname(__file__))
            ahk_script = os.path.join(script_dir, 'scripts', 'send_chat.ahk')
            
            if not os.path.exists(ahk_script):
                log.warning("脚本不存在: %s", ahk_script)
                return False
            
            log.debug("执行AHK: %s", message)
            result = subprocess.run([ahk_exe, ahk_script, message], 
                                   capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
            
        except Exception as e:
            log.error("AHK执行失败: %s", e)
            return False
    
    @staticmethod
    def _find_ahk_exe():
        """自动探测 AutoHotkey 可执行文件路径"""
        import shutil
        import os
        
        # 1. 检查 PATH 环境变量
        path_exe = shutil.which('AutoHotkey64.exe') or shutil.which('AutoHotkey32.exe') or shutil.which('AutoHotkey.exe')
        if path_exe:
            return path_exe
        
        # 2. 检查常见安装路径（v2 优先）
        candidates = [
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe',
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe',
            r'C:\Program Files\AutoHotkey\v2\AutoHotkey.exe',
            r'C:\Program Files\AutoHotkey\AutoHotkey.exe',
            r'C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe',
            r'D:\Program Files\AutoHotkey\v2\AutoHotkey.exe',
            r'D:\Program Files\AutoHotkey\AutoHotkey.exe',
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        return None
    
    def _fetch_enemy_noob(self):
        """从游戏中获取对手信息并找出牛马"""
        try:
            # 获取当前召唤师
            current_summoner = self.api.get_current_summoner()
            my_puuid = current_summoner.get('puuid') if current_summoner else None
            my_summoner_id = current_summoner.get('summonerId') if current_summoner else None
            
            # 获取游戏会话
            game_data = self.api.get('/lol-gameflow/v1/session')
            if not game_data or not game_data.get('gameData'):
                return None
            
            gd = game_data['gameData']
            team_one = gd.get('teamOne', [])
            team_two = gd.get('teamTwo', [])
            
            # 找到对方队伍
            enemy_team = None
            for player in team_one:
                if player.get('puuid') == my_puuid or player.get('summonerId') == my_summoner_id:
                    enemy_team = team_two
                    break
            
            if not enemy_team:
                for player in team_two:
                    if player.get('puuid') == my_puuid or player.get('summonerId') == my_summoner_id:
                        enemy_team = team_one
                        break
            
            if not enemy_team:
                log.warning("无法确定对方队伍")
                return None
            
            log.debug("找到对方队伍: %d 人", len(enemy_team))
            
            # 分析对方每个玩家，找出牛马
            worst_player = None
            worst_score = 100
            
            for player in enemy_team:
                summoner_id = player.get('summonerId')
                if not summoner_id or summoner_id <= 0:
                    continue
                
                player_info = self._analyze_enemy_player(summoner_id)
                if player_info and player_info['score'] < worst_score:
                    worst_score = player_info['score']
                    worst_player = player_info
            
            # 直接返回评分最低的那个作为目标
            if worst_player:
                log.info("找到目标: %s 评分%s", worst_player['name'], worst_score)
                return worst_player
            
            log.warning("未找到对方玩家")
            return None
            
        except Exception as e:
            log.error("获取对手信息错误: %s", e)
            return None
    
    def _analyze_enemy_player(self, summoner_id):
        """分析单个对手玩家"""
        try:
            summoner = self.api.get(f'/lol-summoner/v1/summoners/{summoner_id}')
            if not summoner:
                return None
            
            puuid = summoner.get('puuid')
            name = summoner.get('displayName') or summoner.get('gameName') or '未知'
            
            # 获取最近20场战绩
            matches = self.api.get(f'/lol-match-history/v1/products/lol/{puuid}/matches?begIndex=0&endIndex=20')
            if not matches:
                return None
            
            games = matches.get('games', {})
            if isinstance(games, dict):
                games = games.get('games', [])
            
            if not games:
                return None
            
            # 使用共享模块计算统计
            ms = compute_match_stats(games, puuid)
            game_count = ms['game_count']
            win_rate = (ms['wins'] / game_count * 100) if game_count > 0 else 50
            kda = (ms['total_kills'] + ms['total_assists']) / max(1, ms['total_deaths'])
            avg_deaths = ms['total_deaths'] / game_count if game_count > 0 else 0
            
            score = calculate_player_score(win_rate, kda, ms['streak'], ms['streak_type'])
            
            return {
                'name': name,
                'win_rate': round(win_rate, 1),
                'kda': round(kda, 2),
                'avg_deaths': round(avg_deaths, 1),
                'streak': ms['streak'] if ms['streak'] >= 2 else 0,
                'streak_type': ms['streak_type'] if ms['streak'] >= 2 else None,
                'score': round(score, 1)
            }
            
        except Exception as e:
            log.error("分析对手错误: %s", e)
            return None
    
    def send_all_chat(self, message):
        """发送全体消息（统一使用 AHK）"""
        if not message:
            return False
        full_message = f"/all {message}"
        return self._send_with_ahk(full_message)


def generate_smart_taunt(noob_info):
    """根据牛马数据特征生成针对性嘲讽 - 返回多行列表，随机化"""
    if not noob_info:
        return None
    
    import random
    
    name = noob_info.get('name', '???')
    win_rate = int(noob_info.get('win_rate', 50))
    kda = noob_info.get('kda', 2.0)
    avg_deaths = noob_info.get('avg_deaths', 5)
    streak = noob_info.get('streak', 0)
    streak_type = noob_info.get('streak_type')
    
    # 根据不同数据特征选择话术库
    taunts = []
    
    # 1. 连败系列（优先级最高）
    if streak >= 5 and streak_type == 'lose':
        taunts = [
            [
                f"对面{name}连败{streak}场了",
                "心态已经炸穿地心",
                "兄弟们有福了 稳赢"
            ],
            [
                f"{name}连跪{streak}把还敢来",
                "这不是送分是什么",
                "集火他就完事了"
            ],
            [
                f"对面{name}连败{streak}场",
                "建议直接挂机保护队友",
                "别演了兄弟"
            ],
            [
                f"{name}连败{streak}场心态已崩",
                "这把又要背锅了",
                "同情对面队友3秒"
            ],
            [
                f"对面{name}连败{streak}场",
                "这是来体验失败的吗",
                "建议卸载保平安"
            ]
        ]
    
    # 2. 中等连败（3-4场）
    elif streak >= 3 and streak_type == 'lose':
        taunts = [
            [
                f"{name}连败{streak}场状态不行啊",
                "这把又要输了",
                "针对他就行"
            ],
            [
                f"对面{name}最近很倒霉",
                f"连败{streak}场了",
                "可以针对一下"
            ],
            [
                f"{name}连跪{streak}把",
                "心态应该不太好",
                "集火他试试"
            ],
            [
                f"对面{name}连败{streak}场",
                "这把估计又要崩",
                "稳住能赢"
            ]
        ]
    
    # 3. 超低胜率（<40%）
    elif win_rate < 40:
        taunts = [
            [
                f"{name}胜率{win_rate}%",
                "纯纯的演员啊",
                "对面队友已经在哭了"
            ],
            [
                f"对面{name}胜率{win_rate}%",
                "这是来送分的吧",
                "感谢充值"
            ],
            [
                f"{name}胜率{win_rate}%还敢排",
                "勇气可嘉",
                "但是没用"
            ],
            [
                f"对面{name}胜率{win_rate}%",
                "演员工会金牌会员",
                "兄弟们躺好"
            ],
            [
                f"{name}胜率{win_rate}%",
                "这数据我奶奶都比他强",
                "稳了稳了"
            ]
        ]
    
    # 4. 低胜率（40-45%）
    elif win_rate < 45:
        taunts = [
            [
                f"{name}胜率{win_rate}%",
                "对面最弱的就是他",
                "集火就完事"
            ],
            [
                f"对面{name}胜率{win_rate}%",
                "专业演员已上线",
                "可以针对"
            ],
            [
                f"{name}胜率{win_rate}%",
                "这数据有点惨",
                "突破口找到了"
            ],
            [
                f"对面{name}胜率{win_rate}%",
                "菜得真实",
                "针对他就行"
            ]
        ]
    
    # 5. 超低KDA（<1.5）
    elif kda < 1.5:
        taunts = [
            [
                f"{name} KDA只有{kda}",
                "人形提款机",
                "感谢充值"
            ],
            [
                f"对面{name} KDA{kda}",
                "送人头专业户",
                "多来几次"
            ],
            [
                f"{name} KDA{kda}",
                "这是来送温暖的吗",
                "不客气"
            ],
            [
                f"对面{name} KDA{kda}",
                "移动经验包已上线",
                "兄弟们快来"
            ],
            [
                f"{name} KDA{kda}",
                "送头比送外卖还勤",
                "五星好评"
            ]
        ]
    
    # 6. 低KDA（1.5-2.0）
    elif kda < 2.0:
        taunts = [
            [
                f"{name} KDA{kda}",
                "这数据有点拉胯",
                "可以针对"
            ],
            [
                f"对面{name} KDA{kda}",
                "送得有点多啊",
                "继续保持"
            ],
            [
                f"{name} KDA{kda}",
                "对面最菜的",
                "集火他"
            ],
            [
                f"对面{name} KDA{kda}",
                "这是来体验游戏的",
                "欢迎欢迎"
            ]
        ]
    
    # 7. 高死亡率（>7次/场）
    elif avg_deaths > 7:
        taunts = [
            [
                f"{name}场均送{int(avg_deaths)}个",
                "ATM机啊这是",
                "多来几次"
            ],
            [
                f"对面{name}场均死{int(avg_deaths)}次",
                "送头冠军",
                "感谢贡献"
            ],
            [
                f"{name}场均{int(avg_deaths)}个人头",
                "移动经验包",
                "兄弟们快来"
            ],
            [
                f"对面{name}场均送{int(avg_deaths)}个",
                "这是来做慈善的吗",
                "谢谢老板"
            ],
            [
                f"{name}场均死{int(avg_deaths)}次",
                "送得太勤了",
                "注意身体"
            ]
        ]
    
    # 8. 综合菜（默认）
    else:
        taunts = [
            [
                f"对面{name}是突破口",
                f"胜率{win_rate}% KDA{kda}",
                "集火他就完事"
            ],
            [
                f"{name}数据有点惨",
                f"胜率{win_rate}% KDA{kda}",
                "可以针对一下"
            ],
            [
                f"对面{name}最菜",
                f"胜率{win_rate}% KDA{kda}",
                "兄弟们冲"
            ],
            [
                f"{name}是送分童子",
                f"胜率{win_rate}% KDA{kda}",
                "稳住能赢"
            ],
            [
                f"对面{name}",
                f"胜率{win_rate}% KDA{kda}",
                "这把有了"
            ]
        ]
    
    # 随机选择一组话术
    selected = random.choice(taunts)
    
    # 添加装饰性开头和结尾（随机）
    headers = [
        "====== 🎯 送分童子诊断 🎯 ======",
        "====== ⚠️ 对方最弱分析 ⚠️ ======",
        "====== 💀 突破口已找到 💀 ======",
        "====== 🔥 集火目标锁定 🔥 ======",
        "====== 📊 战力分析报告 📊 ======"
    ]
    
    footers = [
        "======== 集火就完事 ========",
        "======== 稳住能赢 ========",
        "======== 兄弟们冲 ========",
        "======== 感谢充值 ========",
        "======== 这把有了 ========"
    ]
    
    # 组合最终消息
    lines = [random.choice(headers)] + selected + [random.choice(footers)]
    
    return lines


def format_noob_taunt(noob_info):
    """格式化牛马嘲讽消息（兼容旧接口）"""
    return generate_smart_taunt(noob_info)
