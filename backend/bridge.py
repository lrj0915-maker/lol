"""前后端通信桥接"""
import json
import time
from typing import Callable

from lcu import LCUConnection, LCUAPI, LCUEvents
from services import AutoAcceptService, AutoSelectService, MatchHistoryService, TeamAnalyzerService, ChatSenderService, InGameChatService, generate_smart_taunt
from storage import Database, MatchRecord
from config import config


class Bridge:
    """PyWebView 与前端的桥接类"""
    
    def __init__(self):
        self.conn = LCUConnection()
        self.api = None
        self.events = None
        self.auto_accept = None
        self.auto_select = None
        self.match_history = None
        self.team_analyzer = None
        self.chat_sender = None
        self.ingame_chat = None
        self.db = Database()
        
        self._window = None
        self._game_end_data = None

    def set_window(self, window):
        """设置 PyWebView 窗口引用"""
        self._window = window

    def init_services(self):
        """初始化服务"""
        if self.conn.is_connected:
            self.api = LCUAPI(self.conn)
            self.events = LCUEvents(self.conn)
            
            self.auto_accept = AutoAcceptService(self.api, self.events)
            self.auto_select = AutoSelectService(self.api, self.events)
            self.match_history = MatchHistoryService(self.api, self.events)
            self.team_analyzer = TeamAnalyzerService(self.api, self.events)
            self.chat_sender = ChatSenderService(self.api)
            self.ingame_chat = InGameChatService(self.api, self.events)
            
            self.match_history.set_game_end_callback(self._on_game_end)
            self.team_analyzer.set_callback(self._on_team_analysis)
            
            # 从配置加载 ingame_chat 状态
            self.ingame_chat.enabled = config.get('ingame_chat.enabled', False)
            print(f"[Bridge] ingame_chat.enabled = {self.ingame_chat.enabled}")
            
            self.auto_accept.start()
            self.auto_select.start()
            self.match_history.start()
            self.team_analyzer.start()
            self.ingame_chat.start()
            self.events.start()

    def _on_game_end(self, data):
        """游戏结束回调"""
        self._game_end_data = data
        
        # 保存到数据库
        record = MatchRecord.from_match_data(data, int(time.time()))
        if record:
            self.db.save_match(record)
        
        # 通知前端
        if self._window:
            self._window.evaluate_js(f'window.onGameEnd({json.dumps(data)})')

    def _on_team_analysis(self, data):
        """队伍分析完成回调"""
        if self._window:
            self._window.evaluate_js(f'window.onTeamAnalysis({json.dumps(data)})')
        
        # 设置游戏内嘲讽消息
        if self.ingame_chat and data:
            enemy = data.get('enemy_highlights', {})
            noob = enemy.get('noob')
            if noob:
                # 传递完整的牛马信息，让ingame_chat生成针对性嘲讽
                self.ingame_chat.set_noob_info(noob)

    # ========== 连接相关 ==========
    
    def connect(self) -> dict:
        """连接到 LCU 客户端"""
        success = self.conn.connect()
        if success:
            self.init_services()
        return {'success': success}

    def disconnect(self) -> dict:
        """断开连接"""
        if self.events:
            self.events.stop()
        self.conn.disconnect()
        return {'success': True}

    def get_connection_status(self) -> dict:
        """获取连接状态"""
        return {'connected': self.conn.is_connected}

    # ========== 自动准备 ==========
    
    def get_auto_accept_status(self) -> dict:
        """获取自动准备状态"""
        if self.auto_accept:
            return {'enabled': self.auto_accept.enabled}
        # 未连接时从配置读取
        return {'enabled': config.get('auto_accept.enabled', True)}

    def set_auto_accept(self, enabled: bool) -> dict:
        """设置自动准备"""
        config.set('auto_accept.enabled', enabled)
        if self.auto_accept:
            self.auto_accept.enabled = enabled
        return {'success': True}

    # ========== 自动选人 ==========
    
    def get_auto_select_status(self) -> dict:
        """获取自动选人状态"""
        return {'enabled': self.auto_select.enabled if self.auto_select else False}

    def set_auto_select(self, enabled: bool) -> dict:
        """设置自动选人"""
        if self.auto_select:
            self.auto_select.enabled = enabled
        return {'success': True}

    def get_select_config(self) -> dict:
        """获取选人配置"""
        return {
            'ban': config.get('auto_select.ban', []),
            'pick': config.get('auto_select.pick', [])
        }

    def set_select_config(self, ban_list: list, pick_list: list) -> dict:
        """设置选人配置"""
        config.set('auto_select.ban', ban_list)
        config.set('auto_select.pick', pick_list)
        if self.auto_select:
            self.auto_select.update_config(ban_list, pick_list)
        return {'success': True}

    # ========== 英雄数据 ==========
    
    def get_champions(self) -> list:
        """获取所有英雄"""
        if self.api:
            data = self.api.get_all_champions()
            if data:
                return [
                    {'id': c['id'], 'name': c['name'], 'alias': c.get('alias', '')}
                    for c in data if c.get('id', 0) > 0
                ]
        return []

    # ========== 战绩相关 ==========
    
    def get_current_match_stats(self) -> dict:
        """获取当前对局统计"""
        if self._game_end_data:
            return self._game_end_data
        if self.match_history:
            return self.match_history.get_current_match_stats() or {}
        return {}

    def get_match_history_list(self, limit: int = 50, offset: int = 0,
                                game_mode: str = None, champion_id: int = None) -> list:
        """获取历史对局列表"""
        return self.db.get_match_list(limit, offset, game_mode, champion_id)

    def get_match_detail(self, game_id: int) -> dict:
        """获取对局详情"""
        return self.db.get_match_detail(game_id) or {}

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.db.get_stats()

    # ========== 游戏状态 ==========
    
    def get_gameflow_phase(self) -> dict:
        """获取当前游戏阶段"""
        if self.api:
            phase = self.api.get_gameflow_phase()
            return {'phase': phase or 'None'}
        return {'phase': 'None'}

    def get_current_summoner(self) -> dict:
        """获取当前召唤师信息"""
        if self.api:
            return self.api.get_current_summoner() or {}
        return {}

    # ========== 队伍分析 ==========
    
    def get_team_analysis(self) -> dict:
        """获取队伍分析结果"""
        if self.team_analyzer:
            return self.team_analyzer.get_analysis_result() or {}
        return {}
    
    def refresh_team_analysis(self) -> dict:
        """手动刷新队伍分析"""
        if self.team_analyzer:
            success = self.team_analyzer.manual_analyze()
            return {'success': success}
        return {'success': False}
    
    # ========== 聊天发送 ==========
    
    def get_chat_config(self) -> dict:
        """获取聊天发送配置"""
        return {
            'auto_send': config.get('chat.auto_send', False),
            'send_my_team': config.get('chat.send_my_team', True),
            'send_enemy': config.get('chat.send_enemy', True),
            'hotkey': config.get('chat.hotkey', 'F1')
        }
    
    def set_chat_config(self, auto_send: bool = None, send_my_team: bool = None, 
                        send_enemy: bool = None, hotkey: str = None) -> dict:
        """设置聊天发送配置"""
        if auto_send is not None:
            config.set('chat.auto_send', auto_send)
        if send_my_team is not None:
            config.set('chat.send_my_team', send_my_team)
        if send_enemy is not None:
            config.set('chat.send_enemy', send_enemy)
        if hotkey is not None:
            config.set('chat.hotkey', hotkey)
        return {'success': True}
    
    def send_analysis_to_chat(self) -> dict:
        """发送分析结果到聊天 - 自动判断阶段"""
        print("=== 发送分析到聊天 ===")
        
        if not self.api:
            return {'success': False, 'error': '未连接'}
        
        # 获取当前游戏阶段
        phase = self.api.get_gameflow_phase() or 'None'
        print(f"当前阶段: {phase}")
        
        # 游戏中 → 使用 AHK 发送嘲讽
        if phase == 'InProgress':
            print("游戏中，使用AHK发送嘲讽")
            return self.send_ingame_taunt()
        
        # 选人阶段 → 用 LCU API 发送
        if not self.chat_sender or not self.team_analyzer:
            print("服务未初始化")
            return {'success': False, 'error': '服务未初始化'}
        
        analysis = self.team_analyzer.get_analysis_result()
        if not analysis:
            print("暂无分析数据")
            return {'success': False, 'error': '暂无分析数据'}
        
        print(f"分析数据: 我方{len(analysis.get('my_team', []))}人")
        
        options = {
            'send_my_team': config.get('chat.send_my_team', True),
            'send_enemy': config.get('chat.send_enemy', True)
        }
        
        msg_my_team, msg_enemy = self.chat_sender.format_team_analysis(analysis, options)
        
        success = True
        
        # 发送我方队伍消息
        if msg_my_team:
            print(f"发送我方消息:\n{msg_my_team}")
            if not self.chat_sender.send_to_chat(msg_my_team):
                success = False
        
        # 发送对方关注消息
        if msg_enemy:
            print(f"发送对方消息:\n{msg_enemy}")
            if not self.chat_sender.send_to_chat(msg_enemy):
                success = False
        
        if not msg_my_team and not msg_enemy:
            return {'success': False, 'error': '无消息可发送'}
        
        return {'success': success}

    # ========== 游戏内聊天 ==========
    
    def get_ingame_chat_status(self) -> dict:
        """获取游戏内聊天状态"""
        if self.ingame_chat:
            enabled = self.ingame_chat.enabled
        else:
            # 未连接时从配置读取
            enabled = config.get('ingame_chat.enabled', False)
        return {'enabled': enabled}
    
    def set_ingame_chat(self, enabled: bool) -> dict:
        """设置游戏内聊天开关"""
        if self.ingame_chat:
            self.ingame_chat.enabled = enabled
        config.set('ingame_chat.enabled', enabled)
        return {'success': True}
    
    def send_ingame_taunt(self) -> dict:
        """游戏内嘲讽 - 使用 AutoHotKey 发送"""
        if not self.ingame_chat:
            return {'success': False, 'error': '服务未初始化'}
        
        # 如果没有牛马信息，先获取
        if not self.ingame_chat._noob_info:
            print("[Bridge] 无牛马信息，尝试获取...")
            self.ingame_chat._noob_info = self.ingame_chat._fetch_enemy_noob()
        
        if not self.ingame_chat._noob_info:
            return {'success': False, 'error': '无法获取对手信息'}
        
        # 生成嘲讽消息（多行）
        from services import generate_smart_taunt
        lines = generate_smart_taunt(self.ingame_chat._noob_info)
        print(f"[Bridge] 生成嘲讽: {lines}")
        
        if not lines:
            return {'success': False, 'error': '无法生成嘲讽'}
        
        # 使用 AHK 逐行发送
        try:
            import subprocess
            import os
            import time
            
            # AHK 路径
            ahk_exe = r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe"
            script_dir = os.path.dirname(__file__)
            ahk_script = os.path.join(script_dir, 'scripts', 'send_chat.ahk')
            
            if not os.path.exists(ahk_exe):
                print("[Bridge] 未找到 AutoHotkey")
                return {'success': False, 'error': '未安装AutoHotkey'}
            
            for line in lines:
                full_message = f"/all {line}"
                print(f"[Bridge] 发送: {full_message}")
                result = subprocess.run([ahk_exe, ahk_script, full_message], 
                                       capture_output=True, text=True, timeout=10)
                time.sleep(0.3)
            
            return {'success': True}
                
        except Exception as e:
            print(f"[Bridge] 发送失败: {e}")
            return {'success': False, 'error': str(e)}
