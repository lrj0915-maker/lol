"""游戏内聊天服务 - 通过模拟键盘在游戏内发送消息"""
import time
import threading

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 禁用安全模式
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("警告: pyautogui未安装，游戏内聊天功能不可用")


class InGameChatService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._enabled = False
        self._sent_this_game = False
        self._current_game_id = None  # 用于追踪当前游戏
        self._noob_message = None
        self._noob_info = None  # 存储牛马详细信息
        self._team_analyzer = None  # 引用team_analyzer用于查询对手
    
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
    
    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-gameflow/v1/gameflow-phase', self._on_phase_change)
    
    def _on_phase_change(self, uri, data):
        """游戏阶段变化"""
        print(f"[InGameChat] 游戏阶段变化: {data}, enabled={self._enabled}, sent={self._sent_this_game}")
        
        # InProgress = 游戏进行中
        if data == 'InProgress':
            if self._enabled and not self._sent_this_game:
                print("[InGameChat] 检测到游戏进行中，触发自动嘲讽...")
                threading.Thread(target=self._auto_send_taunt, daemon=True).start()
        elif data == 'None' or data == 'Lobby' or data == 'EndOfGame':
            # 游戏结束，重置状态
            print("[InGameChat] 重置状态")
            self._sent_this_game = False
            self._current_game_id = None
    
    def _auto_send_taunt(self):
        """自动发送嘲讽（进入游戏后）"""
        try:
            print("[InGameChat] 检测到进入游戏，等待游戏加载完成...")
            
            # 轮询检测游戏是否真正开始（最多等待120秒）
            game_started = False
            for i in range(60):  # 最多等120秒
                game_time = self._get_game_time()
                if game_time is not None and game_time > 5:
                    print(f"[InGameChat] 游戏已开始，当前时间: {game_time}秒")
                    game_started = True
                    break
                print(f"[InGameChat] 等待游戏开始... ({i*2}秒)")
                time.sleep(2)
            
            if not game_started:
                print("[InGameChat] 等待超时，尝试发送")
            
            # 再次确认还在游戏中
            phase = self.api.get_gameflow_phase()
            if phase != 'InProgress':
                print(f"[InGameChat] 游戏已结束或退出，取消发送 (phase={phase})")
                return
            
            # 获取牛马信息
            if not self._noob_info:
                print("[InGameChat] 无牛马信息，尝试获取...")
                self._noob_info = self._fetch_enemy_noob()
            
            if not self._noob_info:
                print("[InGameChat] 无法获取对手信息，取消发送")
                return
            
            # 生成嘲讽（多行）
            lines = generate_smart_taunt(self._noob_info)
            if not lines:
                print("[InGameChat] 无法生成嘲讽")
                return
            
            print(f"[InGameChat] 生成嘲讽: {len(lines)} 行")
            
            # 逐行发送
            for i, line in enumerate(lines):
                full_message = f"/all {line}"
                
                # 第一条消息前多等2秒，确保聊天框准备好
                if i == 0:
                    time.sleep(2)
                
                success = self._send_with_ahk(full_message)
                if not success:
                    print(f"[InGameChat] 发送失败: {line}")
                time.sleep(0.3)
            
            self._sent_this_game = True
            print("[InGameChat] 自动嘲讽发送完成!")
                
        except Exception as e:
            print(f"[InGameChat] 自动发送错误: {e}")
            import traceback
            traceback.print_exc()
    
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
        except:
            return None
    
    def _send_with_ahk(self, message):
        """使用 AHK 发送消息"""
        try:
            import subprocess
            import os
            
            # AHK 路径
            ahk_exe = r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe"
            script_dir = os.path.dirname(os.path.dirname(__file__))
            ahk_script = os.path.join(script_dir, 'scripts', 'send_chat.ahk')
            
            if not os.path.exists(ahk_exe):
                print(f"[InGameChat] AHK不存在: {ahk_exe}")
                return False
            
            if not os.path.exists(ahk_script):
                print(f"[InGameChat] 脚本不存在: {ahk_script}")
                return False
            
            print(f"[InGameChat] 执行AHK: {message}")
            result = subprocess.run([ahk_exe, ahk_script, message], 
                                   capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"[InGameChat] AHK执行失败: {e}")
            return False
    
    def _analyze_and_send(self):
        """进入游戏后分析对手并发送嘲讽"""
        try:
            print("[InGameChat] ========== 开始分析和发送流程 ==========")
            print(f"[InGameChat] enabled={self._enabled}, sent={self._sent_this_game}")
            
            # 获取当前游戏ID，防止重复发送
            game_data = self.api.get('/lol-gameflow/v1/session')
            if game_data:
                game_id = game_data.get('gameData', {}).get('gameId')
                print(f"[InGameChat] 当前游戏ID: {game_id}, 上次游戏ID: {self._current_game_id}")
                if game_id and game_id == self._current_game_id:
                    print("[InGameChat] 同一局游戏，不重复发送")
                    return
                self._current_game_id = game_id
            
            # 如果没有预设的牛马信息，尝试从游戏中获取对手并分析
            print(f"[InGameChat] 当前牛马信息: {self._noob_info}")
            if not self._noob_info:
                print("[InGameChat] 进入游戏，开始查询对手信息...")
                self._noob_info = self._fetch_enemy_noob()
                print(f"[InGameChat] 查询结果: {self._noob_info}")
            
            if self._noob_info:
                # 生成针对性嘲讽
                self._noob_message = generate_smart_taunt(self._noob_info)
                print(f"[InGameChat] 生成嘲讽消息: {self._noob_message}")
            else:
                print("[InGameChat] 无牛马信息，无法生成嘲讽")
                return
            
            # 等待游戏加载
            print("[InGameChat] 等待30秒让游戏加载...")
            time.sleep(30)
            
            # 再次检查状态
            print(f"[InGameChat] 30秒后检查: enabled={self._enabled}, sent={self._sent_this_game}, msg={self._noob_message}")
            
            # 发送消息（只发一次）
            if self._enabled and not self._sent_this_game and self._noob_message:
                print("[InGameChat] 条件满足，开始发送嘲讽...")
                success = self.send_all_chat(self._noob_message)
                self._sent_this_game = True
                print(f"[InGameChat] 嘲讽发送结果: {'成功' if success else '失败'}")
            else:
                reasons = []
                if not self._enabled:
                    reasons.append("功能未启用")
                if self._sent_this_game:
                    reasons.append("本局已发送")
                if not self._noob_message:
                    reasons.append("无消息")
                print(f"[InGameChat] 条件不满足，未发送。原因: {', '.join(reasons)}")
            
            print("[InGameChat] ========== 流程结束 ==========")
                
        except Exception as e:
            print(f"[InGameChat] 分析发送流程错误: {e}")
            import traceback
            traceback.print_exc()
    
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
                print("无法确定对方队伍")
                return None
            
            print(f"找到对方队伍: {len(enemy_team)} 人")
            
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
                print(f"找到目标: {worst_player['name']} 评分{worst_score}")
                return worst_player
            
            print("未找到对方玩家")
            return None
            
        except Exception as e:
            print(f"获取对手信息错误: {e}")
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
            
            # 计算统计
            wins = 0
            total_kills = 0
            total_deaths = 0
            total_assists = 0
            streak = 0
            streak_type = None
            
            for i, game in enumerate(games):
                participants = game.get('participants', [])
                if not participants:
                    continue
                
                p = participants[0]
                stats = p.get('stats', {})
                
                win = stats.get('win', False)
                kills = stats.get('kills', 0)
                deaths = stats.get('deaths', 0)
                assists = stats.get('assists', 0)
                
                if win:
                    wins += 1
                
                total_kills += kills
                total_deaths += deaths
                total_assists += assists
                
                if i == 0:
                    streak_type = 'win' if win else 'lose'
                    streak = 1
                elif (win and streak_type == 'win') or (not win and streak_type == 'lose'):
                    streak += 1
            
            game_count = len(games)
            win_rate = (wins / game_count * 100) if game_count > 0 else 50
            kda = (total_kills + total_assists) / max(1, total_deaths)
            avg_deaths = total_deaths / game_count if game_count > 0 else 0
            
            # 计算评分
            win_score = min(100, max(0, win_rate))
            kda_score = min(100, kda * 20)
            if streak_type == 'win':
                streak_score = min(100, 50 + streak * 10)
            elif streak_type == 'lose':
                streak_score = max(0, 50 - streak * 10)
            else:
                streak_score = 50
            
            score = win_score * 0.4 + kda_score * 0.3 + streak_score * 0.2 + 50 * 0.1
            
            return {
                'name': name,
                'win_rate': round(win_rate, 1),
                'kda': round(kda, 2),
                'avg_deaths': round(avg_deaths, 1),
                'streak': streak if streak >= 2 else 0,
                'streak_type': streak_type if streak >= 2 else None,
                'score': round(score, 1)
            }
            
        except Exception as e:
            print(f"分析对手错误: {e}")
            return None
    
    def send_all_chat(self, message):
        """发送全体消息"""
        if not HAS_PYAUTOGUI:
            print("[InGameChat] pyautogui未安装，无法发送游戏内消息")
            return False
        
        try:
            print(f"[InGameChat] 开始发送消息: {message}")
            
            # 先激活LOL游戏窗口
            self._activate_lol_window()
            time.sleep(1)  # 等待窗口激活
            
            # 点击屏幕中央确保游戏获得焦点
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.3)
            
            # 按Enter打开聊天
            print("[InGameChat] 按Enter打开聊天框")
            pyautogui.press('enter')
            time.sleep(0.5)
            
            # 输入/all
            print("[InGameChat] 输入/all")
            pyautogui.typewrite('/all ', interval=0.05)
            time.sleep(0.3)
            
            # 输入中文消息 - 使用剪贴板
            print(f"[InGameChat] 输入消息: {message}")
            self._type_chinese(message)
            
            time.sleep(0.5)
            
            # 按Enter发送
            print("[InGameChat] 按Enter发送")
            pyautogui.press('enter')
            
            print(f"[InGameChat] 游戏内消息已发送!")
            return True
            
        except Exception as e:
            print(f"[InGameChat] 发送游戏内消息失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _activate_lol_window(self):
        """激活LOL游戏窗口"""
        try:
            import ctypes
            
            user32 = ctypes.windll.user32
            
            # LOL游戏窗口名称
            window_names = [
                "League of Legends (TM) Client",
                "League of Legends",
                "英雄联盟"
            ]
            
            hwnd = None
            for name in window_names:
                hwnd = user32.FindWindowW(None, name)
                if hwnd:
                    print(f"[InGameChat] 找到窗口: {name}")
                    break
            
            if hwnd:
                # 激活窗口
                user32.SetForegroundWindow(hwnd)
                print("[InGameChat] 已激活LOL窗口")
            else:
                print("[InGameChat] 未找到LOL窗口，尝试直接发送")
                
        except Exception as e:
            print(f"[InGameChat] 激活窗口失败: {e}")
    
    def _type_chinese(self, text):
        """输入中文 - 使用剪贴板"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # 复制到剪贴板
            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # 打开剪贴板
            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            
            # 准备数据
            text_bytes = (text + '\0').encode('utf-16-le')
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
            p_mem = kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, text_bytes, len(text_bytes))
            kernel32.GlobalUnlock(h_mem)
            
            # 设置剪贴板
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            user32.CloseClipboard()
            
            print("[InGameChat] 已复制到剪贴板")
            time.sleep(0.2)
            
            # 粘贴 - 使用 pyautogui
            pyautogui.hotkey('ctrl', 'v')
            print("[InGameChat] 已粘贴")
            time.sleep(0.2)
            
        except Exception as e:
            print(f"[InGameChat] 输入中文失败: {e}")
            import traceback
            traceback.print_exc()


def generate_smart_taunt(noob_info):
    """根据牛马数据特征生成针对性嘲讽 - 返回多行列表"""
    if not noob_info:
        return None
    
    name = noob_info.get('name', '???')
    win_rate = int(noob_info.get('win_rate', 50))
    kda = noob_info.get('kda', 2.0)
    avg_deaths = noob_info.get('avg_deaths', 5)
    streak = noob_info.get('streak', 0)
    streak_type = noob_info.get('streak_type')
    
    # 生成症状和诊断
    symptom = ""
    diagnosis = ""
    
    if streak >= 5 and streak_type == 'lose':
        symptom = f"连败{streak}场"
        diagnosis = "建议卸载保护队友"
    elif win_rate < 40:
        symptom = f"胜率{win_rate}%"
        diagnosis = "演员工会金牌会员"
    elif win_rate < 45:
        symptom = f"胜率{win_rate}%"
        diagnosis = "专业演员已上线"
    elif kda < 1.5:
        symptom = f"KDA{kda}"
        diagnosis = "人形提款机感谢充值"
    elif kda < 2.0:
        symptom = f"KDA{kda}"
        diagnosis = "送头比送外卖还勤"
    elif avg_deaths > 7:
        symptom = f"场均送{int(avg_deaths)}个"
        diagnosis = "移动经验包已上线"
    elif streak >= 3 and streak_type == 'lose':
        symptom = f"连败{streak}场"
        diagnosis = "心态已炸一打就崩"
    else:
        symptom = f"胜率{win_rate}% KDA{kda}"
        diagnosis = "对面最菜集火就完事"
    
    # 3行简洁版
    lines = [
        "====== 🎯 牛马诊断 🎯 ======",
        f"患者: {name} | 症状: {symptom}",
        f"诊断: {diagnosis} ========"
    ]
    
    return lines


def format_noob_taunt(noob_info):
    """格式化牛马嘲讽消息（兼容旧接口）"""
    return generate_smart_taunt(noob_info)
