"""前后端通信桥接"""
import copy
import json
import os
import re
import shutil
import ssl
import subprocess
import threading
import time
import random
import urllib.parse
import urllib.request

try:
    import jwt as pyjwt
    HAS_PYJWT = True
except ImportError:
    pyjwt = None
    HAS_PYJWT = False

from logger import get_logger
from paths import get_app_root, get_resource_root
from lcu import LCUConnection, LCUAPI, LCUEvents
from services import AutoAcceptService, AutoSelectService, MatchHistoryService, TeamAnalyzerService, ChatSenderService, InGameChatService, generate_smart_taunt, RunesDataService, AugmentsDataService
from services.jungle_monitor import jungle_monitor
from services.login_service import LoginService, SERVER_LIST, detect_game_path
from services.account_manager import AccountManager
from storage import Database, MatchRecord
from config import config

log = get_logger('Bridge')


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
        app_root = get_app_root()
        resource_root = get_resource_root()
        self.runes_data_service = RunesDataService(app_root, resource_root)
        self.runes_data_service.start_scheduler()
        self.augments_data_service = AugmentsDataService(app_root, resource_root)
        self.augments_data_service.start_scheduler()
        self._rune_manager = None

        # 登录服务
        # jicheng 目录在 lol-assistant 的上级目录
        jicheng_dir = os.path.join(os.path.dirname(app_root), 'jicheng')
        # 如果上级目录没有，尝试 app_root 下（兼容打包后的情况）
        if not os.path.isdir(jicheng_dir):
            jicheng_dir = os.path.join(app_root, 'jicheng')
        self.login_service = LoginService(jicheng_dir)
        self.login_service.set_success_callback(self._on_login_success)
        self.login_service.set_ban_callback(self._on_ban_detected)
        data_dir = os.path.join(app_root, 'data')
        self.account_manager = AccountManager(data_dir)
        
        self._window = None
        self._game_end_data = None
        self._connection_guard_started = False
        self._connection_guard_thread = None
        self._connection_guard_stop = threading.Event()
        self._connection_lock = threading.RLock()
        self._login_lock = threading.RLock()  # 保护登录相关标志
        self._keep_connected = False
        self._current_login_account_id = None  # 当前登录的账号 ID
        self._ban_saved = False  # 封号信息是否已保存（避免重复写入）
        self._service_bind_key = None
        self._connection_fail_count = 0
        self._next_reconnect_at = 0.0
        self._pending_post_login = False  # 登录成功后待执行的自动操作标志
        self._snapshot_timer = None
        self._snapshot_lock = threading.RLock()
        self._last_snapshot_signature = None
        self._snapshot_cache = None
        self._snapshot_cache_at = 0.0
        self._snapshot_cache_ttl = 0.8

    def set_window(self, window):
        """设置 PyWebView 窗口引用"""
        self._window = window

    def _stop_runtime_services(self):
        """停止运行期服务，供重连重绑与主动断开复用"""
        if self.auto_accept:
            try:
                self.auto_accept.stop()
            except Exception:
                pass
        if self.auto_select:
            try:
                self.auto_select.stop()
            except Exception:
                pass
        if self.match_history:
            try:
                self.match_history.stop()
            except Exception:
                pass
        if self.team_analyzer:
            try:
                self.team_analyzer.stop()
            except Exception:
                pass
        if self.ingame_chat:
            try:
                self.ingame_chat.stop()
            except Exception:
                pass
        if self.events:
            try:
                self.events.stop()
            except Exception:
                pass

        self.auto_accept = None
        self.auto_select = None
        self.match_history = None
        self.team_analyzer = None
        self.chat_sender = None
        self.ingame_chat = None
        self.events = None
        self.api = None
        self._rune_manager = None

    def _snapshot_signature(self, snapshot: dict):
        if not isinstance(snapshot, dict):
            return None
        mode_hint = snapshot.get('mode_hint') or {}
        current_champion = snapshot.get('current_champion') or {}
        auto_accept = snapshot.get('auto_accept') or {}
        auto_select = snapshot.get('auto_select') or {}
        runes_status = snapshot.get('runes_status') or {}
        augments_status = snapshot.get('augments_status') or {}
        return (
            bool(snapshot.get('connected')),
            snapshot.get('game_phase'),
            snapshot.get('recommended_route'),
            snapshot.get('game_mode_type'),
            current_champion.get('champion_id'),
            bool(auto_accept.get('enabled')),
            bool(auto_select.get('enabled')),
            bool(auto_select.get('oneshot')),
            bool(runes_status.get('is_updating')),
            bool(runes_status.get('is_stale')),
            bool(augments_status.get('is_updating')),
            bool(augments_status.get('is_stale')),
            mode_hint.get('queue_id'),
            mode_hint.get('queue_type'),
        )

    @staticmethod
    def _detect_mode_hint(session: dict) -> dict:
        """从 gameflow session 中提取游戏模式提示（共用逻辑）"""
        game_data = session.get('gameData') or {}
        queue_id = (
            game_data.get('queue', {}).get('id')
            or game_data.get('queueId')
            or session.get('queueId')
        )
        queue_type = (
            game_data.get('queue', {}).get('type')
            or game_data.get('queueType')
            or session.get('queueType')
            or ''
        )
        game_mode = (game_data.get('gameMode') or session.get('gameMode') or '').upper()
        game_type = (game_data.get('gameType') or session.get('gameType') or '').upper()

        try:
            queue_id_int = int(queue_id) if queue_id is not None else None
        except Exception:
            queue_id_int = None

        route = '/runes'
        mode = 'CLASSIC'
        arena_queue_ids = {1700, 1701, 1710, 1711, 1720}
        aram_queue_ids = {450}
        aram_mayhem_queue_ids = {1900, 1901}
        queue_type_upper = str(queue_type).upper()

        if (
            queue_id_int in arena_queue_ids
            or 'ARENA' in queue_type_upper
            or 'CHERRY' in game_mode
            or 'ARENA' in game_mode
            or 'CHERRY' in game_type
            or 'ARENA' in game_type
        ):
            route = '/augments'
            mode = 'ARENA'
        elif (
            queue_id_int in aram_mayhem_queue_ids
        ):
            route = '/augments'
            mode = 'ARAM_MAYHEM'
        elif (
            queue_id_int in aram_queue_ids
            or 'ARAM' in queue_type_upper
            or 'ARAM' in game_mode
            or 'ARAM' in game_type
        ):
            route = '/augments'
            mode = 'ARAM'

        return {
            'success': True,
            'route': route,
            'mode': mode,
            'queue_id': queue_id_int,
            'queue_type': queue_type,
            'game_mode': game_mode,
            'game_type': game_type,
        }

    def _push_runtime_snapshot(self, force: bool = False):
        if not self._window:
            return
        try:
            snapshot = self.get_runtime_snapshot()
            signature = self._snapshot_signature(snapshot)
            if not force and signature is not None and signature == self._last_snapshot_signature:
                return
            self._last_snapshot_signature = signature
            self._window.evaluate_js(f'window.onRuntimeSnapshot && window.onRuntimeSnapshot({json.dumps(snapshot)})')
        except Exception:
            pass

    def _schedule_runtime_snapshot_push(self, delay: float = 0.18, force: bool = False):
        if not self._window:
            return
        with self._snapshot_lock:
            if self._snapshot_timer:
                try:
                    self._snapshot_timer.cancel()
                except Exception:
                    pass
                self._snapshot_timer = None

            def _run():
                try:
                    self._push_runtime_snapshot(force=force)
                finally:
                    with self._snapshot_lock:
                        self._snapshot_timer = None

            timer = threading.Timer(max(0.0, float(delay)), _run)
            timer.daemon = True
            self._snapshot_timer = timer
            timer.start()

    def _on_runtime_state_event(self, uri, data):
        self._snapshot_cache = None  # 失效缓存，确保下次推送拿最新数据
        self._schedule_runtime_snapshot_push(delay=0.1)

        # 检测游戏阶段变化，触发设置恢复
        if '/gameflow-phase' in uri:
            try:
                phase = data if isinstance(data, str) else ''
                if phase == 'ChampSelect':
                    # 选人阶段，尝试恢复设置
                    self._maybe_restore_settings_on_login()
            except Exception as e:
                log.debug("检测阶段变化失败: %s", e)

    def init_services(self, force: bool = False):
        """初始化服务"""
        if self.conn.is_connected:
            bind_key = (self.conn.port, self.conn.token)
            services_ready = bool(
                self.events
                and getattr(self.events, '_running', False)
                and self.auto_accept
                and self.auto_select
                and self.match_history
                and self.team_analyzer
                and self.ingame_chat
            )

            if not force and self._service_bind_key == bind_key and services_ready:
                return

            self._stop_runtime_services()
            self.api = LCUAPI(self.conn)
            self.events = LCUEvents(self.conn)
            
            self.auto_accept = AutoAcceptService(self.api, self.events)
            self.auto_select = AutoSelectService(self.api, self.events)
            self.match_history = MatchHistoryService(self.api, self.events)
            self.team_analyzer = TeamAnalyzerService(self.api, self.events)
            self.chat_sender = ChatSenderService(self.api)
            self.ingame_chat = InGameChatService(self.api, self.events, jungle_monitor)
            
            self.match_history.set_game_end_callback(self._on_game_end)
            self.team_analyzer.set_callback(self._on_team_analysis)
            
            # 从配置加载 ingame_chat 状态
            self.ingame_chat.enabled = config.get('ingame_chat.enabled', False)
            log.debug("ingame_chat.enabled = %s", self.ingame_chat.enabled)
            
            self.auto_accept.start()
            self.auto_select.start()
            self.match_history.start()
            self.team_analyzer.start()
            self.ingame_chat.start()
            self.events.start()
            self.events.subscribe('/lol-gameflow/v1/gameflow-phase', self._on_runtime_state_event)
            self.events.subscribe('/lol-champ-select/v1/session', self._on_runtime_state_event)
            self.events.subscribe('/lol-matchmaking/v1/ready-check', self._on_runtime_state_event)
            self.events.subscribe('/lol-gameflow/v1/session', self._on_runtime_state_event)
            self._service_bind_key = bind_key
            self._schedule_runtime_snapshot_push(delay=0.02, force=True)

    def _start_connection_guard(self):
        if self._connection_guard_started:
            return
        self._connection_guard_stop.clear()
        self._connection_guard_started = True
        self._connection_guard_thread = threading.Thread(target=self._connection_guard_loop, daemon=True)
        self._connection_guard_thread.start()

    def _connection_guard_loop(self):
        """后台守护：客户端重启后自动重连并重绑服务"""
        while not self._connection_guard_stop.is_set():
            try:
                if not self._keep_connected:
                    self._connection_fail_count = 0
                    self._next_reconnect_at = 0.0
                    time.sleep(1)
                    continue

                now = time.time()
                if now < self._next_reconnect_at:
                    time.sleep(min(1.0, self._next_reconnect_at - now))
                    continue

                with self._connection_lock:
                    alive = self.conn.check_alive()
                    if alive:
                        self._connection_fail_count = 0
                        self._next_reconnect_at = 0.0
                    else:
                        reconnected = self.conn.connect()
                        if reconnected:
                            self.init_services(force=True)
                            self._connection_fail_count = 0
                            self._next_reconnect_at = 0.0
                            self._schedule_runtime_snapshot_push(delay=0.02, force=True)
                            if self.login_service.get_status().get('phase') == 'connecting_client':
                                self.login_service._update('success', '登录成功，客户端已连接', 100, phase='connected')
                            # 如果有待执行的登录后自动操作
                            should_post_login = False
                            account_id = None
                            with self._login_lock:
                                if self._pending_post_login:
                                    self._pending_post_login = False
                                    should_post_login = True
                                    account_id = self._current_login_account_id
                            if should_post_login:
                                if account_id:
                                    self.account_manager.touch_login(account_id)
                                self._save_summoner_name_async()
                                self._do_auto_friend_and_disenchant()
                            # 换号/重连后自动应用已保存的锁定配置
                            self._maybe_restore_settings_on_login()
                        else:
                            self._service_bind_key = None
                            self._connection_fail_count += 1
                            exp = min(self._connection_fail_count, 6)
                            base_delay = min(30.0, 1.2 * (2 ** (exp - 1)))
                            self._next_reconnect_at = time.time() + base_delay + random.uniform(0.0, 0.8)
            except Exception as e:
                log.error("连接守护异常: %s", e)
            time.sleep(1)

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
        
        # 自动发送到聊天
        if config.get('chat.auto_send', False) and data:
            log.info("自动发送分析结果到聊天...")
            self._auto_send_analysis(data)
    
    def _auto_send_analysis(self, analysis):
        """自动发送分析结果"""
        if not self.chat_sender:
            return
        
        options = {
            'send_my_team': config.get('chat.send_my_team', True),
            'send_enemy': config.get('chat.send_enemy', True)
        }
        
        msg_my_team, msg_enemy = self.chat_sender.format_team_analysis(analysis, options)
        
        if msg_my_team:
            log.debug("自动发送我方消息")
            self.chat_sender.send_to_chat(msg_my_team)
        
        if msg_enemy:
            log.debug("自动发送对方消息")
            self.chat_sender.send_to_chat(msg_enemy)

    # ========== 连接相关 ==========

    def _on_ban_detected(self, ban_info: str):
        """封号检测回调：解析封号信息、保存到账号、推送到前端

        注意：不在此处终止进程，由 LoginService._do_login() 负责终止
        """
        import json as _json
        log.info("检测到封号，处理封号信息")

        # 步骤1: 解析封号信息
        parsed = self._parse_ban_info(ban_info)
        status_data = {
            'status': 'banned',
            'message': '账号封号',
            'progress': 0,
            'ban_info': ban_info,
            'ban_start': parsed.get('ban_start', ''),
            'ban_end': parsed.get('ban_end', ''),
            'ban_days': parsed.get('ban_days', ''),
            'ban_type': parsed.get('ban_type', ''),
        }

        # 步骤2: 保存到账号记录
        account_id = self._current_login_account_id
        if account_id and not self._ban_saved:
            self._ban_saved = True
            try:
                self.account_manager.update_account(
                    account_id,
                    ban_info=parsed.get('reason') or ban_info,
                    ban_time=int(time.time()),
                    ban_start=parsed.get('ban_start', ''),
                    ban_end=parsed.get('ban_end', ''),
                    ban_days=parsed.get('ban_days', ''),
                    ban_type=parsed.get('ban_type', ''),
                )
            except Exception as e:
                log.error("保存封号信息失败: %s", e)
        # 推送到前端
        if self._window:
            try:
                self._window.evaluate_js(
                    f'window.onBanDetected && window.onBanDetected({_json.dumps(status_data, ensure_ascii=False)})'
                )
            except Exception as e:
                log.debug("推送封号信息到前端失败: %s", e)

    def _on_login_success(self):
        """登录服务回调：标记待执行自动操作，然后触发连接"""
        with self._login_lock:
            self._pending_post_login = True
        self.login_service._update('success', '登录成功，正在连接客户端...', 100, phase='connecting_client')
        result = self.connect()
        if result.get('success'):
            self.login_service._update('success', '登录成功，客户端已连接', 100, phase='connected')
        else:
            self.login_service._update('success', '登录成功，等待客户端连接，请稍后...', 100, phase='connecting_client')

    def connect(self) -> dict:
        """连接到 LCU 客户端"""
        with self._connection_lock:
            self._keep_connected = True
            success = self.conn.connect()
            if success:
                self.init_services(force=True)
                self._connection_fail_count = 0
                self._next_reconnect_at = 0.0
                self._schedule_runtime_snapshot_push(delay=0.01, force=True)
                # 如果是登录流程触发的连接，执行登录后自动操作
                should_post_login = False
                account_id = None
                with self._login_lock:
                    if self._pending_post_login:
                        self._pending_post_login = False
                        should_post_login = True
                        account_id = self._current_login_account_id
                if should_post_login:
                    if account_id:
                        self.account_manager.touch_login(account_id)
                    self._save_summoner_name_async()
                    self._maybe_restore_settings_on_login()
                # 每次连接成功都执行：清好友+加白名单+分解碎片
                self._do_auto_friend_and_disenchant()
            else:
                self._service_bind_key = None
        self._start_connection_guard()
        return {'success': success}

    def _save_summoner_name_async(self):
        """异步获取召唤师名并保存到当前登录账号"""
        def _do():
            try:
                account_id = self._current_login_account_id
                if not account_id or not self.api:
                    return
                # 等待 LCU 就绪
                time.sleep(3)
                full_name = self._fetch_full_summoner_name()
                if full_name:
                    self.account_manager.update_account(account_id, summoner_name=full_name)
                    log.info("已保存召唤师名: %s", full_name)
            except Exception as e:
                log.error("获取召唤师名失败: %s", e)
        threading.Thread(target=_do, daemon=True).start()

    def _push_post_login_tool_state(self, tool: str, state: str, result: dict = None):
        """推送登录后自动工具状态到前端"""
        if not self._window:
            return
        try:
            payload = {'tool': tool, 'state': state}
            if result is not None:
                payload['result'] = result
            self._window.evaluate_js(
                f'window.onPostLoginTools && window.onPostLoginTools({json.dumps(payload, ensure_ascii=False)})'
            )
        except Exception as e:
            log.debug("推送工具状态失败: %s", e)

    def _do_auto_friend_and_disenchant(self):
        """每次连接成功后异步执行：清好友 → 加白名单好友 → 分解碎片"""
        def _do():
            try:
                if not self.conn.is_connected or not self._keep_connected:
                    return
                # 等待客户端就绪
                self._push_post_login_tool_state('deleteFriends', 'loading')
                self._push_post_login_tool_state('addFriends', 'loading')
                self._push_post_login_tool_state('disenchant', 'loading')
                for _ in range(60):
                    if not self._keep_connected:
                        log.info("连接已断开，取消登录后自动操作")
                        self._push_post_login_tool_state('deleteFriends', 'idle')
                        self._push_post_login_tool_state('addFriends', 'idle')
                        self._push_post_login_tool_state('disenchant', 'idle')
                        return
                    time.sleep(2)
                    try:
                        chat_me = self.conn.get('/lol-chat/v1/me')
                        if chat_me and isinstance(chat_me, dict):
                            avail = chat_me.get('availability', '')
                            if avail and avail != 'offline':
                                break
                    except Exception:
                        pass
                else:
                    log.warning("等待客户端就绪超时，跳过登录后自动操作")
                    self._push_post_login_tool_state('deleteFriends', 'fail')
                    self._push_post_login_tool_state('addFriends', 'fail')
                    self._push_post_login_tool_state('disenchant', 'fail')
                    return
                if not self._keep_connected:
                    self._push_post_login_tool_state('deleteFriends', 'idle')
                    self._push_post_login_tool_state('addFriends', 'idle')
                    self._push_post_login_tool_state('disenchant', 'idle')
                    return
                time.sleep(1)
                # 1. 清好友
                try:
                    r = self.delete_all_friends()
                    log.info("自动清好友: %s", r.get('message', ''))
                    self._push_post_login_tool_state('deleteFriends', 'success' if r.get('success') else 'fail', r)
                except Exception as e:
                    log.error("自动清好友异常: %s", e)
                    self._push_post_login_tool_state('deleteFriends', 'fail')
                time.sleep(0.5)
                # 2. 加好友
                friends = config.get('auto_friends', [])
                added = 0
                failed = 0
                if friends:
                    for friend in friends:
                        name = friend.get('name', '')
                        tag = friend.get('tag', '')
                        if name and tag:
                            if self._add_friend_by_riot_id(name, tag):
                                added += 1
                            else:
                                failed += 1
                            time.sleep(0.8)
                self._push_post_login_tool_state('addFriends', 'success', {'added': added, 'failed': failed, 'total': added + failed})
                # 3. 分解碎片
                time.sleep(1)
                try:
                    r = self._do_disenchant_all()
                    if r.get('count', 0) > 0:
                        log.info("自动分解: %d 碎片 → %d 精粹", r['count'], r['total_value'])
                    self._push_post_login_tool_state('disenchant', 'success' if r.get('success') else 'fail', r)
                except Exception as e:
                    log.error("自动分解异常: %s", e)
                    self._push_post_login_tool_state('disenchant', 'fail')
            except Exception as e:
                log.error("登录后自动操作异常: %s", e)
                self._push_post_login_tool_state('deleteFriends', 'fail')
                self._push_post_login_tool_state('addFriends', 'fail')
                self._push_post_login_tool_state('disenchant', 'fail')
        threading.Thread(target=_do, daemon=True).start()

    def _fetch_full_summoner_name(self) -> str:
        """从多个 LCU 端点尝试获取完整的 gameName#gameTag"""
        if not self.api:
            return ''

        name = ''
        tag = ''

        # 端点1: /lol-chat/v1/me（国服通常有 gameName + gameTag）
        try:
            chat_me = self.conn.get('/lol-chat/v1/me')
            if chat_me and isinstance(chat_me, dict):
                log.debug("chat/me 返回: gameName=%s, gameTag=%s", chat_me.get('gameName'), chat_me.get('gameTag'))
                name = chat_me.get('gameName') or ''
                tag = chat_me.get('gameTag') or ''
                if name and tag:
                    return f"{name}#{tag}"
        except Exception as e:
            log.debug("chat/me 请求失败: %s", e)

        # 端点2: /lol-summoner/v1/current-summoner
        puuid = ''
        try:
            summoner = self.api.get_current_summoner()
            if summoner and isinstance(summoner, dict):
                log.debug("summoner 返回: gameName=%s, gameTag=%s, displayName=%s",
                          summoner.get('gameName'), summoner.get('gameTag'), summoner.get('displayName'))
                if not name:
                    name = summoner.get('gameName') or summoner.get('displayName') or ''
                if not tag:
                    tag = summoner.get('gameTag') or ''
                puuid = summoner.get('puuid') or ''
                if name and tag:
                    return f"{name}#{tag}"
        except Exception as e:
            log.debug("summoner 请求失败: %s", e)

        # 端点3: 通过 puuid 查询 /lol-summoner/v2/summoners/puuid/{puuid}
        if puuid:
            try:
                v2 = self.conn.get(f'/lol-summoner/v2/summoners/puuid/{puuid}')
                if v2 and isinstance(v2, dict):
                    log.debug("summoner/v2 返回: gameName=%s, gameTag=%s", v2.get('gameName'), v2.get('gameTag'))
                    if not name:
                        name = v2.get('gameName') or ''
                    if not tag:
                        tag = v2.get('gameTag') or ''
                    if name and tag:
                        return f"{name}#{tag}"
            except Exception as e:
                log.debug("summoner/v2 请求失败: %s", e)

        # 端点4: /riotclient/auth/userinfo（Riot 账号信息）
        try:
            userinfo = self.conn.get('/riotclient/auth/userinfo')
            if userinfo and isinstance(userinfo, dict):
                acct = userinfo.get('acct') or {}
                log.debug("userinfo 返回: game_name=%s, tag_line=%s", acct.get('game_name'), acct.get('tag_line'))
                if not name:
                    name = acct.get('game_name') or ''
                if not tag:
                    tag = acct.get('tag_line') or ''
                if name and tag:
                    return f"{name}#{tag}"
        except Exception as e:
            log.debug("userinfo 请求失败: %s", e)

        # 端点5: /lol-league-session/v1/league-session-token (JWT 解码)
        if name and not tag and HAS_PYJWT:
            try:
                token_data = self.conn.get('/lol-league-session/v1/league-session-token')
                if token_data and isinstance(token_data, str):
                    payload = pyjwt.decode(token_data, options={"verify_signature": False})
                    tag = payload.get('dat', {}).get('tag') or ''
                    log.debug("league-session-token tag=%s", tag)
            except Exception:
                pass

        log.info("最终获取到: name=%s, tag=%s", name, tag)
        if name and tag:
            return f"{name}#{tag}"
        return name

    def fetch_summoner_name(self, account_id: str) -> dict:
        """手动获取当前已连接客户端的召唤师名并保存到指定账号"""
        if not self.api or not self.conn.is_connected:
            return {'success': False, 'message': '未连接到客户端'}
        # 校验：只能获取当前登录账号的名字
        if self._current_login_account_id and account_id != self._current_login_account_id:
            return {'success': False, 'message': '当前客户端登录的不是该账号，请先登录该账号'}
        try:
            full_name = self._fetch_full_summoner_name()
            if not full_name:
                return {'success': False, 'message': '无法获取召唤师信息'}
            self.account_manager.update_account(account_id, summoner_name=full_name)
            log.info("手动获取召唤师名: %s -> %s", account_id, full_name)
            return {'success': True, 'summoner_name': full_name}
        except Exception as e:
            log.error("手动获取召唤师名失败: %s", e)
            return {'success': False, 'message': str(e)}

    # ========== 自动加好友 ==========

    def _add_friend_by_riot_id(self, name: str, tag: str) -> bool:
        """通过 Riot ID 添加好友（国服使用 v2 端点 + puuid）"""
        try:
            # 先通过 alias/lookup 查找 puuid
            encoded_name = urllib.parse.quote(name)
            encoded_tag = urllib.parse.quote(tag)
            lookup = self.conn.get(
                f'/lol-summoner/v1/alias/lookup?gameName={encoded_name}&tagLine={encoded_tag}'
            )
            if lookup and isinstance(lookup, dict) and lookup.get('puuid'):
                puuid = lookup['puuid']
                # 使用 v2 端点添加好友
                result = self.conn.post('/lol-chat/v2/friend-requests', {'puuid': puuid})
                log.info("加好友: %s#%s (puuid=%s) -> %s", name, tag, puuid[:12], result)
                return result is not False and result is not None
            else:
                log.warning("查找玩家失败: %s#%s -> %s", name, tag, lookup)
                return False
        except Exception as e:
            log.warning("加好友异常: %s#%s -> %s", name, tag, e)
            return False

    def get_auto_friends(self) -> list:
        """获取自动加好友列表"""
        return config.get('auto_friends', [])

    def add_auto_friend(self, name: str, tag: str) -> dict:
        """添加自动好友"""
        friends = config.get('auto_friends', [])
        # 去重
        for f in friends:
            if f.get('name') == name and f.get('tag') == tag:
                return {'success': False, 'message': '已存在'}
        friends.append({'name': name, 'tag': tag})
        config.set('auto_friends', friends)
        return {'success': True}

    def remove_auto_friend(self, name: str, tag: str) -> dict:
        """删除自动好友"""
        friends = config.get('auto_friends', [])
        before = len(friends)
        friends = [f for f in friends if not (f.get('name') == name and f.get('tag') == tag)]
        if len(friends) == before:
            return {'success': False, 'message': '不存在'}
        config.set('auto_friends', friends)
        return {'success': True}

    def trigger_add_friends(self) -> dict:
        """手动触发添加好友列表"""
        if not self.conn.is_connected:
            return {'success': False, 'message': '未连接到客户端'}
        friends = config.get('auto_friends', [])
        if not friends:
            return {'success': False, 'message': '好友列表为空'}
        total = 0
        added = 0
        failed = 0
        for friend in friends:
            name = friend.get('name', '')
            tag = friend.get('tag', '')
            if not name or not tag:
                continue
            total += 1
            if self._add_friend_by_riot_id(name, tag):
                added += 1
            else:
                failed += 1
            time.sleep(0.5)
        return {
            'success': True,
            'total': total,
            'added': added,
            'failed': failed,
            'message': f'已尝试 {total} 个，成功 {added} 个'
        }

    def delete_all_friends(self) -> dict:
        """删除当前账号的所有好友（排除自动加好友列表中的人），循环直到清空"""
        if not self.conn.is_connected:
            return {'success': False, 'message': '未连接到客户端'}
        try:
            # 构建白名单（自动加好友列表）
            keep_set = set()
            for af in config.get('auto_friends', []):
                name = (af.get('name') or '').strip()
                tag = (af.get('tag') or '').strip()
                if name and tag:
                    keep_set.add(f"{name}#{tag}".lower())

            total_deleted = 0
            total_skipped = 0
            total_failed = 0

            # 循环删除，最多 50 轮防止死循环
            for round_num in range(50):
                friends = self.conn.get('/lol-chat/v1/friends')
                if not friends or not isinstance(friends, list):
                    break

                # 过滤掉白名单
                to_delete = []
                for f in friends:
                    game_name = (f.get('gameName') or f.get('name') or '').strip()
                    game_tag = (f.get('gameTag') or '').strip()
                    if game_name and game_tag:
                        key = f"{game_name}#{game_tag}".lower()
                        if key in keep_set:
                            if round_num == 0:
                                total_skipped += 1
                            continue
                    to_delete.append(f)

                if not to_delete:
                    break

                round_deleted = 0
                for f in to_delete:
                    fid = f.get('id') or f.get('puuid') or ''
                    if not fid:
                        continue
                    try:
                        self.conn.delete(f'/lol-chat/v1/friends/{fid}')
                        total_deleted += 1
                        round_deleted += 1
                    except Exception:
                        total_failed += 1
                    time.sleep(0.1)

                # 如果本轮一个都没删掉，说明 API 有问题，提前退出
                if round_deleted == 0:
                    log.warning("本轮未删除任何好友，提前退出循环")
                    break

                time.sleep(0.5)

            log.info("删除好友完成: 删除 %d, 保留 %d, 失败 %d", total_deleted, total_skipped, total_failed)
            return {'success': True, 'deleted': total_deleted, 'skipped': total_skipped, 'failed': total_failed,
                    'message': f'已删除 {total_deleted} 个好友，保留 {total_skipped} 个'}
        except Exception as e:
            log.error("删除好友异常: %s", e)
            return {'success': False, 'message': str(e)}

    # ========== 自动分解精粹 ==========

    def _do_disenchant_all(self) -> dict:
        """执行分解所有英雄碎片"""
        loot = self.conn.get('/lol-loot/v1/player-loot')
        if not loot or not isinstance(loot, list):
            return {'success': False, 'message': '无法获取战利品', 'count': 0, 'total_value': 0}

        count = 0
        total_value = 0
        details = []
        failed_items = []

        for item in loot:
            if item.get('type') != 'CHAMPION_RENTAL':
                continue
            loot_name = item.get('lootName', '')
            loot_count = item.get('count', 0)
            disenchant_value = item.get('disenchantValue', 0)
            if loot_count <= 0 or not loot_name:
                continue

            # LCU 分解配方格式: CHAMPION_RENTAL_disenchant
            recipe = 'CHAMPION_RENTAL_disenchant'
            item_count_before = count
            consecutive_failures = 0
            
            for i in range(loot_count):
                try:
                    r = self.conn.post(f'/lol-loot/v1/recipes/{recipe}/craft', [loot_name])
                    log.debug("分解 %s (%d/%d): 结果=%s", loot_name, i+1, loot_count, r)
                    if r is not None and r is not False:
                        count += 1
                        total_value += disenchant_value
                        consecutive_failures = 0  # 重置连续失败计数
                    else:
                        consecutive_failures += 1
                        log.warning("分解 %s (%d/%d) 失败", loot_name, i+1, loot_count)
                        # 连续失败3次才跳过该物品
                        if consecutive_failures >= 3:
                            log.warning("分解 %s 连续失败3次，跳过剩余", loot_name)
                            failed_items.append(item.get('localizedName', loot_name))
                            break
                        time.sleep(0.3)  # 失败后等待更久
                except Exception as e:
                    consecutive_failures += 1
                    log.warning("分解 %s (%d/%d) 异常: %s", loot_name, i+1, loot_count, e)
                    # 连续异常3次才跳过该物品
                    if consecutive_failures >= 3:
                        log.warning("分解 %s 连续异常3次，跳过剩余", loot_name)
                        failed_items.append(item.get('localizedName', loot_name))
                        break
                    time.sleep(0.3)  # 异常后等待更久
                
                time.sleep(0.15)

            crafted = count - item_count_before
            if crafted > 0:
                details.append({
                    'name': item.get('localizedName', loot_name),
                    'count': crafted,
                    'value': disenchant_value,
                })

        message = f'已分解 {count} 个碎片，获得 {total_value} 精粹'
        if failed_items:
            message += f'（部分失败: {", ".join(failed_items[:3])}{"..." if len(failed_items) > 3 else ""}）'

        return {
            'success': True,
            'count': count,
            'total_value': total_value,
            'details': details,
            'message': message,
        }

    def disenchant_all_shards(self) -> dict:
        """手动分解所有英雄碎片"""
        if not self.conn.is_connected:
            return {'success': False, 'message': '未连接到客户端', 'count': 0, 'total_value': 0}
        return self._do_disenchant_all()

    def get_loot_shards(self) -> dict:
        """获取当前英雄碎片列表（预览用）"""
        if not self.conn.is_connected:
            return {'success': False, 'shards': [], 'total_value': 0}
        loot = self.conn.get('/lol-loot/v1/player-loot')
        if not loot or not isinstance(loot, list):
            return {'success': False, 'shards': [], 'total_value': 0}

        shards = []
        total_value = 0
        for item in loot:
            if item.get('type') != 'CHAMPION_RENTAL':
                continue
            cnt = item.get('count', 0)
            val = item.get('disenchantValue', 0)
            if cnt <= 0:
                continue
            shards.append({
                'name': item.get('localizedName', item.get('lootName', '')),
                'count': cnt,
                'value': val,
                'total': cnt * val,
            })
            total_value += cnt * val
        return {'success': True, 'shards': shards, 'total_value': total_value}

    def get_auto_disenchant(self) -> dict:
        """获取自动分解开关状态"""
        return {'enabled': config.get('auto_disenchant', False)}

    def set_auto_disenchant(self, enabled: bool) -> dict:
        """设置自动分解开关"""
        config.set('auto_disenchant', bool(enabled))
        return {'success': True}

    def disconnect(self) -> dict:
        """断开连接"""
        with self._connection_lock:
            self._keep_connected = False
            self._stop_runtime_services()
            self.conn.disconnect()
            self._service_bind_key = None
            self._connection_fail_count = 0
            self._next_reconnect_at = 0.0
            # 取消待执行的 snapshot 推送
            with self._snapshot_lock:
                if self._snapshot_timer:
                    try:
                        self._snapshot_timer.cancel()
                    except Exception:
                        pass
                    self._snapshot_timer = None
            self._snapshot_cache = None
            self._schedule_runtime_snapshot_push(delay=0.01, force=True)
        return {'success': True}

    def get_connection_status(self) -> dict:
        """获取连接状态（纯查询，不触发重连或服务重建）"""
        connected = bool(self.conn.is_connected and self.conn.check_alive())
        return {'connected': connected}

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
        if self.auto_select:
            return {
                'enabled': self.auto_select.enabled,
                'oneshot': self.auto_select.oneshot,
            }
        return {
            'enabled': bool(config.get('auto_select.enabled', False)),
            'oneshot': bool(config.get('auto_select.oneshot', True)),
        }

    def set_auto_select(self, enabled: bool) -> dict:
        """设置自动选人"""
        config.set('auto_select.enabled', enabled)
        if self.auto_select:
            self.auto_select.enabled = enabled
        return {'success': True}

    def set_auto_select_oneshot(self, oneshot: bool) -> dict:
        """设置自动选人是否单次触发"""
        config.set('auto_select.oneshot', bool(oneshot))
        if self.auto_select:
            self.auto_select.oneshot = bool(oneshot)
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

    @staticmethod
    def _extract_ranked_queue(stats: dict, queue_type: str) -> dict:
        if not isinstance(stats, dict):
            return {}

        queue_map = stats.get('queueMap') or {}
        entry = queue_map.get(queue_type)
        if isinstance(entry, dict):
            return entry

        for candidate in stats.get('queues', []) or []:
            if candidate.get('queueType') == queue_type:
                return candidate

        for candidate in stats.get('rankedQueues', []) or []:
            if candidate.get('queueType') == queue_type:
                return candidate

        return {}

    @staticmethod
    def _normalize_ranked_entry(entry: dict) -> dict:
        if not entry:
            return {
                'tier': '',
                'division': '',
                'lp': 0,
                'wins': 0,
                'losses': 0,
                'is_placement': True,
                'last_updated_at': int(time.time()),
            }

        wins = int(entry.get('wins') or entry.get('leaguePointsWins') or 0)
        losses = int(entry.get('losses') or entry.get('leaguePointsLosses') or 0)
        return {
            'tier': entry.get('tier') or entry.get('highestTier') or '',
            'division': entry.get('division') or entry.get('rank') or '',
            'lp': int(entry.get('leaguePoints') or entry.get('lp') or 0),
            'wins': wins,
            'losses': losses,
            'is_placement': (wins + losses) < 10,
            'last_updated_at': int(time.time()),
        }

    def _build_live_profile_cache(self) -> dict:
        summoner = self.get_current_summoner() or {}
        if not summoner:
            return self.db.get_summoner_profile_cache() or {}

        profile = {
            'display_name': self._fetch_full_summoner_name() or summoner.get('displayName') or '',
            'game_name': summoner.get('gameName') or summoner.get('displayName') or '',
            'tag_line': summoner.get('gameTag') or '',
            'icon_id': summoner.get('profileIconId') or summoner.get('icon') or 0,
            'puuid': summoner.get('puuid') or '',
            'summoner_id': summoner.get('summonerId') or 0,
            'last_updated_at': int(time.time()),
            'is_online': True,
        }
        self.db.set_summoner_profile_cache(profile)

        puuid = profile.get('puuid')
        if self.api and puuid:
            try:
                ranked_stats = self.api.get_ranked_stats(puuid) or {}
                solo = self._normalize_ranked_entry(self._extract_ranked_queue(ranked_stats, 'RANKED_SOLO_5x5'))
                flex = self._normalize_ranked_entry(self._extract_ranked_queue(ranked_stats, 'RANKED_FLEX_SR'))
                self.db.set_ranked_profile_cache('RANKED_SOLO_5x5', solo)
                self.db.set_ranked_profile_cache('RANKED_FLEX_SR', flex)
            except Exception as exc:
                log.debug("刷新段位缓存失败: %s", exc)

        return profile

    def get_battle_profile_summary(self) -> dict:
        summary = self.db.get_battle_profile_summary()
        if self.api:
            try:
                profile = self._build_live_profile_cache()
                summary = self.db.get_battle_profile_summary()
                summary['profile'] = profile
                summary['profile']['is_online'] = True
            except Exception as exc:
                log.debug("获取实时战绩中心概要失败，回退缓存: %s", exc)
        else:
            summary.setdefault('profile', {})
            summary['profile']['is_online'] = False
        return summary

    def refresh_battle_profile_summary(self) -> dict:
        if not self.api:
            cached = self.db.get_battle_profile_summary()
            cached.setdefault('profile', {})
            cached['profile']['is_online'] = False
            return {
                'success': False,
                'message': '当前离线，仅展示缓存数据',
                'data': cached,
            }

        try:
            self._build_live_profile_cache()
            return {
                'success': True,
                'data': self.db.get_battle_profile_summary(),
            }
        except Exception as exc:
            log.error("刷新战绩中心概要失败: %s", exc)
            return {
                'success': False,
                'message': str(exc),
                'data': self.db.get_battle_profile_summary(),
            }

    def get_battle_history_page(self, page: int = 1, page_size: int = 20, filters: dict = None) -> dict:
        return self.db.get_battle_history_page(page=page, page_size=page_size, filters=filters or {})

    def get_battle_match_detail(self, game_id: int) -> dict:
        return self.db.get_battle_match_detail(game_id) or {}

    # ========== 游戏状态 ==========
    
    def get_gameflow_phase(self) -> dict:
        """获取当前游戏阶段"""
        if self.api:
            phase = self.api.get_gameflow_phase()
            return {'phase': phase or 'None'}
        return {'phase': 'None'}

    def get_game_mode_route_hint(self) -> dict:
        """返回当前对局建议跳转页面（符文/强化）"""
        if not self.api:
            return {'success': False, 'route': '/match', 'mode': 'UNKNOWN'}

        try:
            session = self.api.get('/lol-gameflow/v1/session') or {}
            return self._detect_mode_hint(session)
        except Exception as exc:
            return {
                'success': False,
                'route': '/match',
                'mode': 'UNKNOWN',
                'error': str(exc),
            }

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
        log.info("发送分析到聊天")
        
        if not self.api:
            return {'success': False, 'error': '未连接'}
        
        # 获取当前游戏阶段
        phase = self.api.get_gameflow_phase() or 'None'
        log.debug("当前阶段: %s", phase)
        
        # 游戏中 → 使用 AHK 发送嘲讽
        if phase == 'InProgress':
            log.debug("游戏中，使用AHK发送嘲讽")
            return self.send_ingame_taunt()
        
        # 选人阶段 → 用 LCU API 发送
        if not self.chat_sender or not self.team_analyzer:
            log.warning("服务未初始化")
            return {'success': False, 'error': '服务未初始化'}
        
        analysis = self.team_analyzer.get_analysis_result()
        if not analysis:
            log.debug("暂无分析数据")
            return {'success': False, 'error': '暂无分析数据'}
        
        log.debug("分析数据: 我方%d人", len(analysis.get('my_team', [])))
        
        options = {
            'send_my_team': config.get('chat.send_my_team', True),
            'send_enemy': config.get('chat.send_enemy', True)
        }
        
        msg_my_team, msg_enemy = self.chat_sender.format_team_analysis(analysis, options)
        
        success = True
        
        # 发送我方队伍消息
        if msg_my_team:
            log.debug("发送我方消息")
            if not self.chat_sender.send_to_chat(msg_my_team):
                success = False
        
        # 发送对方关注消息
        if msg_enemy:
            log.debug("发送对方消息")
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
        """游戏内嘲讽 - 委托给 ingame_chat 服务"""
        if not self.ingame_chat:
            return {'success': False, 'error': '服务未初始化'}
        
        # 如果没有牛马信息，先获取
        if not self.ingame_chat._noob_info:
            log.debug("无牛马信息，尝试获取...")
            self.ingame_chat._noob_info = self.ingame_chat._fetch_enemy_noob()
        
        if not self.ingame_chat._noob_info:
            return {'success': False, 'error': '无法获取对手信息'}
        
        # 生成嘲讽消息（多行）
        from services import generate_smart_taunt
        lines = generate_smart_taunt(self.ingame_chat._noob_info)
        log.debug("生成嘲讽: %s", lines)
        
        if not lines:
            return {'success': False, 'error': '无法生成嘲讽'}
        
        # 使用 ingame_chat 的统一 AHK 发送方法逐行发送
        try:
            for line in lines:
                full_message = f"/all {line}"
                log.debug("发送: %s", full_message)
                self.ingame_chat._send_with_ahk(full_message)
                time.sleep(0.3)
            
            return {'success': True}
                
        except Exception as e:
            log.error("发送失败: %s", e)
            return {'success': False, 'error': str(e)}


    # ========== 野怪监控 ==========
    
    def get_jungle_monitor_status(self) -> dict:
        """获取野怪监控状态"""
        return {
            'running': jungle_monitor.is_running(),
            'auto_start': jungle_monitor.auto_start,
            'config': jungle_monitor.get_config()
        }
    
    def set_jungle_monitor_config(self, config_data: dict) -> dict:
        """设置野怪监控配置"""
        jungle_monitor.set_config(config_data)
        return {'success': True}
    
    def start_jungle_monitor(self) -> dict:
        """启动野怪监控"""
        # 加载配置
        saved_config = config.get('jungle_monitor', {})
        if saved_config:
            jungle_monitor.set_config(saved_config)
        
        success = jungle_monitor.start()
        return {'success': success}
    
    def stop_jungle_monitor(self) -> dict:
        """停止野怪监控"""
        jungle_monitor.stop()
        return {'success': True}

    def set_jungle_monitor_auto_start(self, enabled: bool) -> dict:
        """设置野怪监控自动启停"""
        jungle_monitor.auto_start = enabled
        return {'success': True, 'auto_start': enabled}
    
    def get_jungle_monitor_logs(self) -> list:
        """获取野怪监控日志"""
        return jungle_monitor.get_logs()
    
    def clear_jungle_monitor_logs(self) -> dict:
        """清空野怪监控日志"""
        jungle_monitor.clear_logs()
        return {'success': True}
    
    def get_cached_jungle_message(self) -> dict:
        """获取缓存的野怪消息"""
        message = jungle_monitor.get_cached_message()
        return {'message': message}
    
    def send_cached_jungle_message(self) -> dict:
        """发送缓存的野怪消息"""
        return jungle_monitor.send_cached_message()
    
    def test_jungle_ocr(self) -> dict:
        """测试野怪OCR识别"""
        return jungle_monitor.test_ocr()

    # ========== 设置锁定 ==========

    def get_settings_lock_config(self) -> dict:
        """获取设置锁定配置"""
        return {
            'enabled': config.get('settings_lock.enabled', False),
            'auto_restore': config.get('settings_lock.auto_restore', True),
            'game_path': config.get('settings_lock.game_path', ''),
            'last_save_at': config.get('settings_lock.last_save_at', ''),
        }

    def set_settings_lock_config(self, enabled: bool = None, auto_restore: bool = None, game_path: str = None) -> dict:
        """设置设置锁定配置"""
        if enabled is not None:
            config.set('settings_lock.enabled', bool(enabled))
        if auto_restore is not None:
            config.set('settings_lock.auto_restore', bool(auto_restore))
        if game_path is not None:
            config.set('settings_lock.game_path', game_path)
        return {'success': True}

    def _get_settings_template_path(self) -> str:
        """获取设置模板目录路径"""
        game_path = config.get('settings_lock.game_path', '')
        if not game_path:
            # 默认使用检测到的游戏路径
            from services.login_service import detect_game_path
            game_path = detect_game_path() or ''
            if game_path:
                config.set('settings_lock.game_path', game_path)
        if game_path:
            return os.path.join(game_path, '.settings_template')
        return ''

    def save_current_settings(self) -> dict:
        """保存当前游戏的设置到模板目录"""
        try:
            game_path = config.get('settings_lock.game_path', '')
            if not game_path:
                from services.login_service import detect_game_path
                game_path = detect_game_path()
                if not game_path:
                    return {'success': False, 'message': '无法检测游戏路径'}
                config.set('settings_lock.game_path', game_path)

            # 游戏设置目录
            game_config_dir = os.path.join(game_path, 'Game', 'Config')
            if not os.path.exists(game_config_dir):
                return {'success': False, 'message': '游戏配置目录不存在'}

            # 模板目录
            template_dir = os.path.join(game_path, '.settings_template')
            os.makedirs(template_dir, exist_ok=True)

            # 要复制的文件
            files_to_copy = ['PersistedSettings.json', 'input.ini']
            # game.cfg 在 DATA/CFG
            game_data_cfg = os.path.join(game_path, 'Game', 'DATA', 'CFG')
            if os.path.exists(os.path.join(game_data_cfg, 'game.cfg')):
                files_to_copy.append(('game.cfg', game_data_cfg))

            copied = []
            for f in files_to_copy:
                if isinstance(f, tuple):
                    src = os.path.join(f[1], f[0])
                    dst = os.path.join(template_dir, f[0])
                else:
                    src = os.path.join(game_config_dir, f)
                    dst = os.path.join(template_dir, f)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    copied.append(f[0] if isinstance(f, tuple) else f)
                    log.debug("已保存设置文件: %s", f)

            # 记录保存时间
            from datetime import datetime
            save_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            config.set('settings_lock.last_save_at', save_time)

            return {
                'success': True,
                'message': f'已保存 {len(copied)} 个设置文件',
                'files': copied,
                'saved_at': save_time,
            }
        except Exception as e:
            log.error("保存设置失败: %s", e)
            return {'success': False, 'message': str(e)}

    def restore_settings(self) -> dict:
        """从模板目录恢复设置到游戏目录"""
        try:
            game_path = config.get('settings_lock.game_path', '')
            if not game_path:
                from services.login_service import detect_game_path
                game_path = detect_game_path()
                if not game_path:
                    return {'success': False, 'message': '无法检测游戏路径'}
                config.set('settings_lock.game_path', game_path)

            # 模板目录
            template_dir = os.path.join(game_path, '.settings_template')
            if not os.path.exists(template_dir):
                return {'success': False, 'message': '设置模板不存在，请先保存当前设置'}

            # 游戏配置目录
            game_config_dir = os.path.join(game_path, 'Game', 'Config')
            game_data_cfg = os.path.join(game_path, 'Game', 'DATA', 'CFG')
            os.makedirs(game_config_dir, exist_ok=True)
            os.makedirs(game_data_cfg, exist_ok=True)

            restored = []

            file_mappings = [
                ('PersistedSettings.json', os.path.join(game_config_dir, 'PersistedSettings.json')),
                ('input.ini', os.path.join(game_config_dir, 'input.ini')),
                ('game.cfg', os.path.join(game_data_cfg, 'game.cfg')),
            ]

            for filename, dst in file_mappings:
                src = os.path.join(template_dir, filename)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    restored.append(filename)
                    log.debug("已恢复设置文件: %s", filename)

            if not restored:
                return {'success': False, 'message': '未找到可应用的已保存配置文件'}

            return {
                'success': True,
                'message': f'已应用 {len(restored)} 个设置文件',
                'files': restored,
            }
        except Exception as e:
            log.error("恢复设置失败: %s", e)
            return {'success': False, 'message': str(e)}

    def get_settings_template_info(self) -> dict:
        """获取设置模板文件信息"""
        try:
            game_path = config.get('settings_lock.game_path', '')
            if not game_path:
                from services.login_service import detect_game_path
                game_path = detect_game_path()

            if not game_path:
                return {'success': False, 'message': '无法检测游戏路径', 'files': []}

            template_dir = os.path.join(game_path, '.settings_template')
            if not os.path.exists(template_dir):
                return {'success': False, 'message': '设置模板不存在', 'files': []}

            files = []
            for f in os.listdir(template_dir):
                fp = os.path.join(template_dir, f)
                if os.path.isfile(fp):
                    size = os.path.getsize(fp)
                    files.append({'name': f, 'size': size})

            return {
                'success': True,
                'files': files,
                'template_dir': template_dir,
            }
        except Exception as e:
            log.error("获取设置模板信息失败: %s", e)
            return {'success': False, 'message': str(e), 'files': []}

    def _maybe_restore_settings_on_login(self) -> None:
        """登录成功后自动恢复设置（内部调用）"""
        if not config.get('settings_lock.enabled', False):
            return
        if not config.get('settings_lock.auto_restore', True):
            return

        try:
            result = self.restore_settings()
            if result.get('success'):
                log.info("自动恢复设置成功: %s", result.get('files'))
            else:
                log.warning("自动恢复设置失败: %s", result.get('message'))
        except Exception as e:
            log.error("自动恢复设置异常: %s", e)

    def start_region_select(self) -> dict:
        """启动全屏区域选择 - 使用独立进程（异步，不阻塞 bridge 线程）"""
        log.debug("start_region_select 被调用")

        try:
            # 使用独立脚本进行区域选择
            script_path = os.path.join(get_app_root(), 'select_region.pyw')

            if not os.path.exists(script_path):
                log.warning("脚本不存在: %s", script_path)
                return {'success': False, 'error': '区域选择脚本不存在'}

            def _run_select():
                try:
                    # 先最小化窗口
                    if self._window:
                        log.debug("最小化窗口...")
                        self._window.minimize()
                        time.sleep(0.3)

                    # 运行独立脚本
                    log.debug("运行区域选择脚本...")
                    subprocess.run(
                        ['pythonw', script_path],
                        capture_output=False,
                        timeout=60
                    )
                except subprocess.TimeoutExpired:
                    log.warning("区域选择超时")
                except Exception as e:
                    log.error("区域选择异常: %s", e, exc_info=True)
                finally:
                    # 恢复窗口
                    if self._window:
                        try:
                            self._window.restore()
                        except Exception:
                            pass
                    # 从配置文件读取结果并更新
                    try:
                        config_path = os.path.join(get_app_root(), 'data', 'config.json')
                        if os.path.exists(config_path):
                            with open(config_path, 'r', encoding='utf-8') as f:
                                cfg = json.load(f)
                                region = cfg.get('jungle_monitor', {}).get('region')
                                if region:
                                    jungle_monitor.set_config({'region': region})
                                    log.info("区域选择完成: %s", region)
                    except Exception as e:
                        log.error("读取区域选择结果失败: %s", e)

            threading.Thread(target=_run_select, daemon=True).start()
            return {'success': True, 'message': '区域选择已启动'}

        except Exception as e:
            log.error("启动区域选择异常: %s", e, exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_cache_template_info(self) -> dict:
        """获取缓存模板文件信息"""
        from pathlib import Path

        try:
            app_root = get_app_root()
            cache_template = Path(app_root) / 'cache_template'

            if not cache_template.exists():
                return {
                    'success': False,
                    'message': '缓存模板不存在',
                    'files': []
                }

            files = []

            # config.ini
            config_src = cache_template / 'config.ini'
            if config_src.exists():
                size = config_src.stat().st_size
                files.append({
                    'name': 'config.ini',
                    'type': 'config',
                    'size': size,
                    'valid': size > 0 and size < 10 * 1024 * 1024
                })

            # saves/*.bson
            saves_src = cache_template / 'saves'
            if saves_src.exists():
                for bson_file in saves_src.glob('*.bson'):
                    size = bson_file.stat().st_size
                    files.append({
                        'name': f'saves/{bson_file.name}',
                        'type': 'save',
                        'size': size,
                        'valid': size > 0 and size < 100 * 1024 * 1024
                    })

            # shards/**
            shards_src = cache_template / 'shards'
            if shards_src.exists():
                for shard_file in shards_src.rglob('*'):
                    if not shard_file.is_file():
                        continue
                    size = shard_file.stat().st_size
                    try:
                        relative = shard_file.relative_to(shards_src)
                        name = f'shards/{relative.as_posix()}'
                    except Exception:
                        name = f'shards/{shard_file.name}'
                    files.append({
                        'name': name,
                        'type': 'shard',
                        'size': size,
                        'valid': size > 0 and size < 500 * 1024 * 1024
                    })
            valid_count = sum(1 for f in files if f['valid'])

            return {
                'success': True,
                'files': files,
                'total_size': total_size,
                'total_count': len(files),
                'valid_count': valid_count
            }

        except Exception as e:
            log.error(f'获取模板信息失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'files': []
            }

    def check_target_safety(self, target_path: str) -> dict:
        """检查目标路径的安全性"""
        from pathlib import Path
        import shutil
        import psutil

        try:
            target = Path(target_path)

            if not target.exists():
                return {
                    'success': False,
                    'message': '目标路径不存在'
                }

            # 检查磁盘空间
            disk_usage = shutil.disk_usage(target)
            free_space_mb = disk_usage.free // (1024 * 1024)

            if free_space_mb < 100:  # 少于100MB
                return {
                    'success': False,
                    'message': f'磁盘空间不足（剩余 {free_space_mb} MB）',
                    'free_space_mb': free_space_mb
                }

            # 检查写入权限
            test_file = target / '.cache_test_write'
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, IOError):
                return {
                    'success': False,
                    'message': '目标路径无写入权限'
                }

            # 检查是否有相关进程占用
            occupied_processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        exe = proc.info.get('exe')
                        if exe and target_path.lower() in exe.lower():
                            occupied_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception as e:
                log.warning(f'进程检查失败: {e}')

            return {
                'success': True,
                'free_space_mb': free_space_mb,
                'writable': True,
                'occupied_processes': occupied_processes,
                'warning': '检测到相关进程运行' if occupied_processes else None
            }

        except Exception as e:
            log.error(f'安全检查失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'检查失败: {str(e)}'
            }

    def get_recommended_paths(self) -> dict:
        """获取推荐的目标路径"""
        from pathlib import Path
        import json

        try:
            app_root = get_app_root()
            config_file = Path(app_root) / 'data' / 'cache_config.json'

            recommendations = []

            # 1. 上次使用的路径
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_path = config.get('last_path')
                    if last_path and Path(last_path).exists():
                        recommendations.append({
                            'path': last_path,
                            'label': '上次使用',
                            'priority': 1
                        })

            # 2. 历史记录中的路径
            history_file = Path(app_root) / 'data' / 'cache_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for item in history.get('paths', [])[:5]:
                        if item['path'] not in [r['path'] for r in recommendations]:
                            if Path(item['path']).exists():
                                recommendations.append({
                                    'path': item['path'],
                                    'label': f"使用 {item['count']} 次",
                                    'priority': 2
                                })

            # 3. 常见的防封目录模式
            common_patterns = [
                'ZM-BOT*',
                'league of legends',
                '*防封*'
            ]

            # 搜索常见路径
            search_roots = [
                Path('C:/Users') / Path.home().name,
                Path('D:/'),
                Path('E:/')
            ]

            for root in search_roots:
                if not root.exists():
                    continue
                try:
                    for pattern in common_patterns:
                        for match in root.glob(f'**/{pattern}'):
                            if match.is_dir() and str(match) not in [r['path'] for r in recommendations]:
                                recommendations.append({
                                    'path': str(match),
                                    'label': '自动发现',
                                    'priority': 3
                                })
                                if len(recommendations) >= 10:
                                    break
                        if len(recommendations) >= 10:
                            break
                except Exception as e:
                    log.warning(f'搜索路径失败: {e}')

            # 按优先级排序
            recommendations.sort(key=lambda x: x['priority'])

            return {
                'success': True,
                'recommendations': recommendations[:10]
            }

        except Exception as e:
            log.error(f'获取推荐路径失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'recommendations': []
            }

    def quick_restore_latest_backup(self) -> dict:
        """快速恢复到最近的备份"""
        from pathlib import Path
        import zipfile

        try:
            # 从配置读取上次操作的路径
            app_root = get_app_root()
            config_file = Path(app_root) / 'data' / 'cache_config.json'

            if not config_file.exists():
                return {'success': False, 'message': '未找到操作记录'}

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                last_path = config.get('last_path')

            if not last_path:
                return {'success': False, 'message': '未找到上次操作路径'}

            target_path = Path(last_path)

            # 查找最新的备份
            backups = sorted(target_path.glob('.cache_backup_*.zip'), reverse=True)

            if not backups:
                return {'success': False, 'message': '未找到可用的备份'}

            latest_backup = backups[0]

            # 解析备份时间
            from datetime import datetime
            timestamp_str = latest_backup.stem.replace('.cache_backup_', '')
            try:
                backup_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                backup_time_str = backup_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                backup_time_str = '未知时间'

            # 恢复备份
            log.info(f'正在恢复备份: {latest_backup.name}')

            # 先清空目标位置
            config_dst = target_path / 'config.ini'
            hc_dst = target_path / 'hc.dat'
            saves_dst = target_path / 'saves'

            if config_dst.exists():
                config_dst.unlink()
            if hc_dst.exists():
                hc_dst.unlink()
            if saves_dst.exists():
                for f in saves_dst.glob('*.bson'):
                    f.unlink()

            # 解压备份
            with zipfile.ZipFile(latest_backup, 'r') as zf:
                zf.extractall(target_path)

            log.info(f'已恢复备份: {latest_backup.name}')

            return {
                'success': True,
                'message': f'已恢复到 {backup_time_str} 的备份',
                'backup_name': latest_backup.name,
                'backup_time': backup_time_str
            }

        except Exception as e:
            log.error(f'快速恢复失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'恢复失败: {str(e)}'
            }

    def get_operation_statistics(self) -> dict:
        """获取操作统计信息"""
        from pathlib import Path

        try:
            app_root = get_app_root()
            metrics_file = Path(app_root) / 'data' / 'cache_metrics.json'

            if not metrics_file.exists():
                return {
                    'success': True,
                    'statistics': {
                        'total_operations': 0,
                        'successful_operations': 0,
                        'failed_operations': 0,
                        'success_rate': 0.0,
                        'avg_time_per_operation': 0.0,
                        'avg_files_per_operation': 0.0,
                        'total_time': 0.0,
                        'total_files': 0
                    }
                }

            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)

            return {
                'success': True,
                'statistics': metrics
            }

        except Exception as e:
            log.error(f'获取统计信息失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'statistics': {}
            }

    def cleanup_all_temp_files(self, target_path: str) -> dict:
        """清理所有临时文件"""
        from pathlib import Path

        try:
            target = Path(target_path)

            if not target.exists():
                return {'success': False, 'message': '目标路径不存在'}

            temp_patterns = [
                '*.tmp',
                '*.bak',
                '*.temp',
                '.cache_temp_*',
                '~*',
                '*.swp',
                '*.swo',
                '.DS_Store',
                'Thumbs.db'
            ]

            cleaned_files = []
            total_size = 0

            for pattern in temp_patterns:
                for temp_file in target.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleaned_files.append({
                                'name': temp_file.name,
                                'size': size
                            })
                            total_size += size
                    except Exception as e:
                        log.warning(f'清理文件失败: {temp_file}, {e}')

            log.info(f'已清理 {len(cleaned_files)} 个临时文件，释放 {total_size // 1024} KB')

            return {
                'success': True,
                'cleaned_count': len(cleaned_files),
                'total_size_kb': total_size // 1024,
                'files': cleaned_files[:10]  # 只返回前10个
            }

        except Exception as e:
            log.error(f'清理临时文件失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'清理失败: {str(e)}'
            }

    def replace_cache_files(self) -> dict:
        """缓存文件置换功能 - 完整增强版（带操作锁、重试、日志持久化）"""
        import tkinter as tk
        from tkinter import filedialog, messagebox
        import shutil
        import hashlib
        import zipfile
        import threading
        from pathlib import Path
        from datetime import datetime
        import time

        # 操作锁（防止并发）
        if not hasattr(self, '_cache_replace_lock'):
            self._cache_replace_lock = threading.Lock()

        if not self._cache_replace_lock.acquire(blocking=False):
            return {
                'success': False,
                'message': '另一个缓存置换操作正在进行中，请稍后再试'
            }

        logs = []
        backup_zip = None
        operation_start_time = time.time()

        try:
            def validate_config_ini(config_path):
                """验证 config.ini 文件格式"""
                try:
                    import configparser

                    if not config_path.exists():
                        return True, []  # 不存在不算错误

                    issues = []

                    # 尝试解析
                    config = configparser.ConfigParser()
                    try:
                        config.read(config_path, encoding='utf-8')
                    except UnicodeDecodeError:
                        try:
                            config.read(config_path, encoding='gbk')
                        except Exception as e:
                            issues.append(f'编码错误: {str(e)}')
                            return False, issues
                    except Exception as e:
                        issues.append(f'解析失败: {str(e)}')
                        return False, issues

                    # 检查是否为空
                    if not config.sections():
                        issues.append('配置文件为空')
                        return False, issues

                    # 检查关键配置项（根据实际需求调整）
                    # 这里只做基本检查

                    return True, []

                except Exception as e:
                    return False, [f'验证异常: {str(e)}']

            def deep_file_integrity_check(file_path, file_type='unknown'):
                """深度文件完整性检查"""
                try:
                    if not file_path.exists():
                        return True, []  # 不存在不算错误

                    issues = []
                    size = file_path.stat().st_size

                    # 1. 大小检查
                    if size == 0:
                        issues.append('文件为空')
                        return False, issues

                    # 2. 可读性检查
                    try:
                        with open(file_path, 'rb') as f:
                            header = f.read(min(1024, size))
                            if not header:
                                issues.append('文件无法读取')
                                return False, issues
                    except Exception as e:
                        issues.append(f'读取失败: {str(e)}')
                        return False, issues

                    # 3. 文件类型特定检查
                    if file_type == 'config':
                        # config.ini 特定检查
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(1024)
                                if not content.strip():
                                    issues.append('配置文件内容为空')
                                    return False, issues
                                # 检查是否包含基本的 ini 格式标记
                                if '[' not in content and '=' not in content:
                                    issues.append('不是有效的 INI 格式')
                                    return False, issues
                        except Exception as e:
                            issues.append(f'格式检查失败: {str(e)}')
                            return False, issues

                    elif file_type == 'bson':
                        # BSON 文件特定检查
                        try:
                            # 检查文件头（BSON 通常以特定字节开始）
                            with open(file_path, 'rb') as f:
                                header = f.read(4)
                                if len(header) < 4:
                                    issues.append('BSON 文件头不完整')
                                    return False, issues
                        except Exception as e:
                            issues.append(f'BSON 检查失败: {str(e)}')
                            return False, issues

                    # 4. 文件完整性（尝试完整读取）
                    try:
                        with open(file_path, 'rb') as f:
                            while True:
                                chunk = f.read(8192)
                                if not chunk:
                                    break
                    except Exception as e:
                        issues.append(f'文件可能损坏: {str(e)}')
                        return False, issues

                    return True, []

                except Exception as e:
                    return False, [f'检查异常: {str(e)}']

            def auto_repair_file(file_path, file_type='unknown'):
                """自动修复损坏的文件"""
                try:
                    if not file_path.exists():
                        return False, '文件不存在'

                    # 1. 尝试修复编码问题
                    if file_type == 'config':
                        try:
                            # 读取并重新编码
                            content = None
                            for encoding in ['utf-8', 'gbk', 'latin-1']:
                                try:
                                    with open(file_path, 'r', encoding=encoding) as f:
                                        content = f.read()
                                    break
                                except:
                                    continue

                            if content:
                                # 重新写入为 UTF-8
                                backup = file_path.with_suffix('.bak')
                                shutil.copy2(file_path, backup)

                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)

                                log.info(f'已修复文件编码: {file_path}')
                                return True, '已修复编码问题'
                        except Exception as e:
                            log.warning(f'修复编码失败: {e}')

                    # 2. 尝试修复文件尾部损坏
                    try:
                        size = file_path.stat().st_size
                        if size > 0:
                            with open(file_path, 'rb') as f:
                                data = f.read()

                            # 移除尾部的空字节
                            data = data.rstrip(b'\x00')

                            if len(data) < size:
                                backup = file_path.with_suffix('.bak')
                                shutil.copy2(file_path, backup)

                                with open(file_path, 'wb') as f:
                                    f.write(data)

                                log.info(f'已修复文件尾部: {file_path}')
                                return True, '已修复文件尾部'
                    except Exception as e:
                        log.warning(f'修复文件尾部失败: {e}')

                    return False, '无法自动修复'

                except Exception as e:
                    return False, f'修复异常: {str(e)}'

            def create_audit_log(operation_type, details):
                """创建操作审计日志"""
                try:
                    app_root = get_app_root()
                    audit_file = Path(app_root) / 'data' / 'cache_audit.jsonl'
                    audit_file.parent.mkdir(parents=True, exist_ok=True)

                    audit_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'operation': operation_type,
                        'details': details,
                        'user': os.environ.get('USERNAME', 'unknown')
                    }

                    # 追加写入（JSONL 格式）
                    with open(audit_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')

                    log.info(f'审计日志已记录: {operation_type}')

                except Exception as e:
                    log.warning(f'记录审计日志失败: {e}')

            def record_performance_metrics(operation_time, success, file_count):
                """记录性能指标"""
                try:
                    app_root = get_app_root()
                    metrics_file = Path(app_root) / 'data' / 'cache_metrics.json'
                    metrics_file.parent.mkdir(parents=True, exist_ok=True)

                    # 读取现有指标
                    metrics = {
                        'total_operations': 0,
                        'successful_operations': 0,
                        'failed_operations': 0,
                        'total_time': 0.0,
                        'total_files': 0,
                        'avg_time_per_operation': 0.0,
                        'avg_files_per_operation': 0.0,
                        'success_rate': 0.0,
                        'last_updated': None
                    }

                    if metrics_file.exists():
                        with open(metrics_file, 'r', encoding='utf-8') as f:
                            metrics = json.load(f)

                    # 更新指标
                    metrics['total_operations'] += 1
                    if success:
                        metrics['successful_operations'] += 1
                    else:
                        metrics['failed_operations'] += 1

                    metrics['total_time'] += operation_time
                    metrics['total_files'] += file_count

                    # 计算平均值
                    if metrics['total_operations'] > 0:
                        metrics['avg_time_per_operation'] = metrics['total_time'] / metrics['total_operations']
                        metrics['avg_files_per_operation'] = metrics['total_files'] / metrics['total_operations']
                        metrics['success_rate'] = (metrics['successful_operations'] / metrics['total_operations']) * 100

                    metrics['last_updated'] = datetime.now().isoformat()

                    # 写入
                    with open(metrics_file, 'w', encoding='utf-8') as f:
                        json.dump(metrics, f, ensure_ascii=False, indent=2)

                    log.info(f'性能指标已更新: 耗时 {operation_time:.2f}s, 成功率 {metrics["success_rate"]:.1f}%')

                except Exception as e:
                    log.warning(f'记录性能指标失败: {e}')

            def save_operation_log(operation_data):
                """持久化操作日志到数据库"""
                try:
                    app_root = get_app_root()
                    log_file = Path(app_root) / 'data' / 'cache_operations.json'
                    log_file.parent.mkdir(parents=True, exist_ok=True)

                    # 读取现有日志
                    operations = []
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8') as f:
                            operations = json.load(f)

                    # 添加新日志
                    operations.append(operation_data)

                    # 只保留最近100条
                    operations = operations[-100:]

                    # 写入
                    with open(log_file, 'w', encoding='utf-8') as f:
                        json.dump(operations, f, ensure_ascii=False, indent=2)

                    log.info(f'操作日志已保存')
                except Exception as e:
                    log.warning(f'保存操作日志失败: {e}')

            def retry_operation(func, max_retries=3, delay=1):
                """重试机制"""
                for attempt in range(max_retries):
                    try:
                        return func()
                    except (IOError, OSError) as e:
                        if attempt < max_retries - 1:
                            log.warning(f'操作失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}')
                            time.sleep(delay)
                            delay *= 2  # 指数退避
                        else:
                            raise

            def find_target_directory(selected_path):
                """智能识别目标目录 - 只按 console.exe 匹配"""
                from pathlib import Path

                selected = Path(selected_path)

                # 情况1：用户选择的目录本身包含 console.exe
                if (selected / 'console.exe').exists():
                    log.info(f'直接使用选择的目录（包含 console.exe）: {selected}')
                    return selected, 'direct'

                # 情况2：用户选择的目录下存在 league of legends 子目录，且包含 console.exe
                lol_patterns = [
                    'league of legends',
                    'League of Legends',
                    'LEAGUE OF LEGENDS',
                    'LeagueOfLegends',
                    'league_of_legends'
                ]

                for pattern in lol_patterns:
                    lol_dir = selected / pattern
                    if lol_dir.exists() and lol_dir.is_dir():
                        if (lol_dir / 'console.exe').exists():
                            log.info(f'找到 league of legends 子目录（包含 console.exe）: {lol_dir}')
                            return lol_dir, 'subdirectory'

                # 情况3：未找到匹配
                log.warning(f'未找到 console.exe，无法执行置换')
                return None, 'not_found'

            def validate_template_files(cache_template):
                """验证缓存模板文件完整性"""
                issues = []
                config_src = cache_template / 'config.ini'
                saves_src = cache_template / 'saves'
                shards_src = cache_template / 'shards'

                if config_src.exists():
                    size = config_src.stat().st_size
                    if size == 0:
                        issues.append('config.ini 为空文件')
                    elif size > 10 * 1024 * 1024:
                        issues.append('config.ini 文件过大')
                    else:
                        try:
                            with open(config_src, 'r', encoding='utf-8', errors='ignore') as f:
                                if not f.read(1024).strip():
                                    issues.append('config.ini 内容为空')
                        except Exception as e:
                            issues.append(f'config.ini 读取失败: {str(e)}')

                if saves_src.exists():
                    bson_files = [f for f in saves_src.glob('*.bson') if f.stat().st_size > 0]
                    if not bson_files:
                        issues.append('saves 目录中没有有效的 .bson 文件')

                if shards_src.exists():
                    shard_files = [f for f in shards_src.rglob('*') if f.is_file() and f.stat().st_size > 0]
                    if not shard_files:
                        issues.append('shards 目录中没有有效文件')

                return issues

            def check_file_locks(config_dst, saves_dst, shards_dst, hc_dst):
                """检查文件是否被占用"""
                locked_files = []

                for file_path, name in [(config_dst, 'config.ini'), (hc_dst, 'hc.dat')]:
                    if file_path.exists():
                        try:
                            with open(file_path, 'a'):
                                pass
                        except (PermissionError, IOError):
                            locked_files.append(name)

                if saves_dst.exists():
                    for bson_file in saves_dst.glob('*.bson'):
                        try:
                            with open(bson_file, 'a'):
                                pass
                        except (PermissionError, IOError):
                            locked_files.append(f'saves/{bson_file.name}')

                if shards_dst.exists():
                    for shard_file in shards_dst.rglob('*'):
                        if not shard_file.is_file():
                            continue
                        try:
                            with open(shard_file, 'ab'):
                                pass
                        except (PermissionError, IOError):
                            try:
                                relative_path = shard_file.relative_to(shards_dst)
                                locked_files.append(f'shards/{relative_path.as_posix()}')
                            except Exception:
                                locked_files.append(f'shards/{shard_file.name}')

                return locked_files

            def calculate_md5(file_path):
                """计算文件MD5"""
                md5 = hashlib.md5()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5.update(chunk)
                return md5.hexdigest()

            def check_incremental_update(cache_template, target_path):
                """检查是否需要增量更新"""
                changes = {'add': [], 'update': [], 'delete': [], 'unchanged': []}

                config_src = cache_template / 'config.ini'
                config_dst = target_path / 'config.ini'

                if config_src.exists():
                    if not config_dst.exists():
                        changes['add'].append('config.ini')
                    elif calculate_md5(config_src) != calculate_md5(config_dst):
                        changes['update'].append('config.ini')
                    else:
                        changes['unchanged'].append('config.ini')

                saves_src = cache_template / 'saves'
                saves_dst = target_path / 'saves'

                if saves_src.exists():
                    src_bsons = {f.name: f for f in saves_src.glob('*.bson')}
                    dst_bsons = {f.name: f for f in saves_dst.glob('*.bson')} if saves_dst.exists() else {}

                    for name, src_file in src_bsons.items():
                        if name not in dst_bsons:
                            changes['add'].append(f'saves/{name}')
                        elif calculate_md5(src_file) != calculate_md5(dst_bsons[name]):
                            changes['update'].append(f'saves/{name}')
                        else:
                            changes['unchanged'].append(f'saves/{name}')

                shards_src = cache_template / 'shards'
                shards_dst = target_path / 'shards'

                if shards_src.exists():
                    src_shards = {
                        file.relative_to(shards_src).as_posix(): file
                        for file in shards_src.rglob('*') if file.is_file()
                    }
                    dst_shards = {
                        file.relative_to(shards_dst).as_posix(): file
                        for file in shards_dst.rglob('*') if file.is_file()
                    } if shards_dst.exists() else {}

                    for relative_name, src_file in src_shards.items():
                        if relative_name not in dst_shards:
                            changes['add'].append(f'shards/{relative_name}')
                        elif calculate_md5(src_file) != calculate_md5(dst_shards[relative_name]):
                            changes['update'].append(f'shards/{relative_name}')
                        else:
                            changes['unchanged'].append(f'shards/{relative_name}')

                return changes

            def backup_files_compressed(target_path, config_dst, saves_dst, shards_dst, hc_dst):
                """备份原有文件（压缩版）"""
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_zip = target_path / f'.cache_backup_{timestamp}.zip'

                backed_up = []

                try:
                    with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                        if config_dst.exists():
                            zf.write(config_dst, 'config.ini')
                            backed_up.append('config.ini')

                        if saves_dst.exists():
                            for bson_file in saves_dst.glob('*.bson'):
                                zf.write(bson_file, f'saves/{bson_file.name}')
                                backed_up.append(f'saves/{bson_file.name}')

                        if shards_dst.exists():
                            for shard_file in shards_dst.rglob('*'):
                                if not shard_file.is_file():
                                    continue
                                try:
                                    relative = shard_file.relative_to(shards_dst)
                                    zf.write(shard_file, f'shards/{relative.as_posix()}')
                                    backed_up.append(f'shards/{relative.as_posix()}')
                                except Exception as e:
                                    log.warning(f'备份 shards 文件失败 {shard_file}: {e}')

                    return backup_zip, backed_up
                except Exception as e:
                    log.error(f'压缩备份失败: {e}', exc_info=True)
                    if backup_zip.exists():
                        backup_zip.unlink()
                    raise

            def restore_from_backup_compressed(backup_zip, target_path):
                """从压缩备份恢复"""
                try:
                    with zipfile.ZipFile(backup_zip, 'r') as zf:
                        zf.extractall(target_path)
                    log.info('已从压缩备份恢复文件')
                    return True
                except Exception as e:
                    log.error(f'恢复失败: {e}', exc_info=True)
                    return False

            def init_cache_template():
                """自动初始化缓存模板目录"""
                app_root = get_app_root()
                cache_template = Path(app_root) / 'cache_template'

                if not cache_template.exists():
                    cache_template.mkdir(parents=True, exist_ok=True)
                    (cache_template / 'saves').mkdir(exist_ok=True)
                    (cache_template / 'shards').mkdir(exist_ok=True)
                    (cache_template / 'config.ini').touch()
                    log.info('已自动创建缓存模板目录')
                    return True
                else:
                    # 如果目录存在但没有 shards 目录，创建它
                    shards_dir = cache_template / 'shards'
                    if not shards_dir.exists():
                        shards_dir.mkdir(exist_ok=True)
                        log.info('已创建 shards 子目录')
                return False

            def load_last_path():
                """加载上次选择的路径"""
                try:
                    app_root = get_app_root()
                    config_file = Path(app_root) / 'data' / 'cache_config.json'
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            return config.get('last_path')
                except Exception as e:
                    log.warning(f'加载上次路径失败: {e}')
                return None

            def save_last_path(path):
                """保存本次选择的路径"""
                try:
                    app_root = get_app_root()
                    config_dir = Path(app_root) / 'data'
                    config_dir.mkdir(parents=True, exist_ok=True)
                    config_file = config_dir / 'cache_config.json'

                    config = {}
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)

                    config['last_path'] = str(path)
                    config['last_update'] = datetime.now().isoformat()

                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)

                    log.info(f'已保存路径记忆: {path}')
                except Exception as e:
                    log.warning(f'保存路径失败: {e}')

            if True:
                # 0. 自动初始化缓存模板
                template_created = init_cache_template()
                if template_created:
                    logs.append({'type': 'info', 'message': '已自动创建缓存模板目录'})

                # 1. 定位缓存模板目录
                app_root = get_app_root()
                cache_template = Path(app_root) / 'cache_template'

                if not cache_template.exists():
                    return {
                        'success': False,
                        'message': '缓存模板不存在，请联系技术支持',
                        'logs': logs
                    }

                # 2. 预检查模板文件
                logs.append({'type': 'info', 'message': '正在检查模板文件...'})
                template_issues = validate_template_files(cache_template)

                if template_issues:
                    return {
                        'success': False,
                        'message': f'模板文件存在问题：{"; ".join(template_issues)}',
                        'logs': logs
                    }

                logs.append({'type': 'info', 'message': '模板文件检查通过'})

                # 3. 弹出文件夹选择对话框
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)

                last_path = load_last_path()
                initial_dir = last_path if last_path and Path(last_path).exists() else None

                target_dir = filedialog.askdirectory(
                    title="选择防封位置（目标文件夹）",
                    initialdir=initial_dir,
                    mustexist=True
                )

                if not target_dir:
                    root.destroy()
                    return {'success': False, 'message': '未选择文件夹', 'cancelled': True}

                # 智能识别目标目录
                target_path, find_type = find_target_directory(target_dir)

                # 如果未匹配到 console.exe，直接报错
                if find_type == 'not_found':
                    root.destroy()
                    return {
                        'success': False,
                        'message': '未在选定目录或其 league of legends 子目录中找到 console.exe，无法执行置换',
                        'logs': logs
                    }

                # 记录识别结果
                if find_type == 'direct':
                    logs.append({'type': 'info', 'message': '已识别：直接使用选择的目录'})
                elif find_type == 'subdirectory':
                    logs.append({'type': 'info', 'message': '已识别：找到子目录'})
                else:
                    logs.append({'type': 'info', 'message': '使用选择的路径'})

                save_last_path(target_path)

                # 4. 定位目标文件
                config_dst = target_path / 'config.ini'
                saves_dst = target_path / 'saves'
                shards_dst = target_path / 'shards'
                hc_dst = target_path / 'hc.dat'

                # 5. 磁盘空间预检查
                logs.append({'type': 'info', 'message': '正在检查磁盘空间...'})
                try:
                    import shutil as shutil_disk
                    disk_usage = shutil_disk.disk_usage(target_path)
                    free_space_mb = disk_usage.free // (1024 * 1024)

                    # 估算需要的空间（模板大小 + 备份大小 + 安全余量）
                    template_size = 0
                    if (cache_template / 'config.ini').exists():
                        template_size += (cache_template / 'config.ini').stat().st_size
                    if (cache_template / 'saves').exists():
                        for f in (cache_template / 'saves').glob('*.bson'):
                            template_size += f.stat().st_size
                    if (cache_template / 'shards').exists():
                        for f in (cache_template / 'shards').rglob('*'):
                            if f.is_file():
                                template_size += f.stat().st_size

                    # 估算备份大小（假设压缩率50%）
                    backup_size = 0
                    if config_dst.exists():
                        backup_size += config_dst.stat().st_size
                    if saves_dst.exists():
                        for f in saves_dst.glob('*.bson'):
                            backup_size += f.stat().st_size
                    if shards_dst.exists():
                        for f in shards_dst.rglob('*'):
                            if f.is_file():
                                backup_size += f.stat().st_size

                    estimated_backup_size = backup_size // 2  # 压缩后大小
                    required_space_mb = (template_size + estimated_backup_size + 50 * 1024 * 1024) // (1024 * 1024)  # 额外50MB安全余量

                    if free_space_mb < required_space_mb:
                        root.destroy()
                        return {
                            'success': False,
                            'message': f'磁盘空间不足：需要 {required_space_mb} MB，剩余 {free_space_mb} MB',
                            'logs': logs
                        }

                    logs.append({'type': 'info', 'message': f'磁盘空间充足：剩余 {free_space_mb} MB'})

                except Exception as e:
                    log.warning(f'磁盘空间检查失败: {e}')
                    logs.append({'type': 'info', 'message': '磁盘空间检查跳过'})

                # 6. 进程占用检测
                logs.append({'type': 'info', 'message': '正在检查进程占用...'})
                try:
                    import psutil

                    occupied_processes = []
                    target_path_str = str(target_path).lower()

                    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                        try:
                            proc_info = proc.info

                            # 检查进程可执行文件路径
                            exe = proc_info.get('exe')
                            if exe and target_path_str in exe.lower():
                                occupied_processes.append({
                                    'pid': proc_info['pid'],
                                    'name': proc_info['name']
                                })
                                continue

                            # 检查命令行参数
                            cmdline = proc_info.get('cmdline')
                            if cmdline:
                                cmdline_str = ' '.join(cmdline).lower()
                                if target_path_str in cmdline_str:
                                    occupied_processes.append({
                                        'pid': proc_info['pid'],
                                        'name': proc_info['name']
                                    })

                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass

                    if occupied_processes:
                        process_names = ', '.join(set(p['name'] for p in occupied_processes))
                        logs.append({'type': 'info', 'message': f'检测到相关进程：{process_names}'})

                        # 询问用户是否继续
                        warning_msg = f"检测到以下进程可能正在使用目标文件：\n\n"
                        for p in occupied_processes[:5]:  # 最多显示5个
                            warning_msg += f"• {p['name']} (PID: {p['pid']})\n"
                        if len(occupied_processes) > 5:
                            warning_msg += f"... 还有 {len(occupied_processes) - 5} 个进程\n"
                        warning_msg += f"\n建议关闭这些进程后再继续。\n是否仍要继续？"

                        if not messagebox.askyesno("进程占用警告", warning_msg, parent=root, icon='warning'):
                            root.destroy()
                            return {'success': False, 'message': '用户取消操作（进程占用）', 'cancelled': True}
                    else:
                        logs.append({'type': 'info', 'message': '未检测到进程占用'})

                except ImportError:
                    log.warning('psutil 未安装，跳过进程检测')
                    logs.append({'type': 'info', 'message': '进程检测跳过（psutil未安装）'})
                except Exception as e:
                    log.warning(f'进程检测失败: {e}')
                    logs.append({'type': 'info', 'message': '进程检测跳过'})

                # 7. 检查文件占用
                logs.append({'type': 'info', 'message': '正在检查文件占用...'})
                locked_files = check_file_locks(config_dst, saves_dst, shards_dst, hc_dst)

                if locked_files:
                    root.destroy()
                    return {
                        'success': False,
                        'message': f'以下文件被占用：{", ".join(locked_files)}，请关闭相关程序后重试',
                        'logs': logs
                    }

                logs.append({'type': 'info', 'message': '文件占用检查通过'})

                # 6. 增量更新检查
                logs.append({'type': 'info', 'message': '正在分析文件变化...'})
                changes = check_incremental_update(cache_template, target_path)

                total_changes = len(changes['add']) + len(changes['update']) + len(changes['delete'])

                if total_changes == 0:
                    root.destroy()
                    return {
                        'success': True,
                        'message': '所有文件已是最新，无需更新',
                        'logs': logs,
                        'stats': {
                            'total_files': len(changes['unchanged']),
                            'copied_files': 0,
                            'deleted_files': 0,
                            'verified_files': 0,
                            'total_size_kb': 0
                        }
                    }

                logs.append({'type': 'info', 'message': f'检测到 {total_changes} 个文件需要更新'})
                if changes['add']:
                    logs.append({'type': 'info', 'message': f'新增: {len(changes["add"])} 个'})
                if changes['update']:
                    logs.append({'type': 'info', 'message': f'更新: {len(changes["update"])} 个'})
                if changes['delete']:
                    logs.append({'type': 'info', 'message': f'删除: {len(changes["delete"])} 个'})

                # 7. 显示详细确认对话框
                confirm_msg = f"即将执行缓存置换操作：\n\n"
                confirm_msg += f"【目标位置】\n{target_path}\n\n"
                confirm_msg += f"【识别方式】\n"
                if find_type == 'direct':
                    confirm_msg += "✓ 直接使用选择的目录\n\n"
                elif find_type == 'subdirectory':
                    confirm_msg += "✓ 自动找到子目录\n\n"
                elif find_type == 'recursive':
                    confirm_msg += "✓ 智能搜索找到目标\n\n"
                else:
                    confirm_msg += "✓ 使用选择的路径\n\n"

                confirm_msg += f"【操作内容】\n"
                if changes['add']:
                    confirm_msg += f"新增文件：{len(changes['add'])} 个\n"
                if changes['update']:
                    confirm_msg += f"更新文件：{len(changes['update'])} 个\n"
                if changes['delete']:
                    confirm_msg += f"删除文件：{len(changes['delete'])} 个\n"
                if changes['unchanged']:
                    confirm_msg += f"无变化：{len(changes['unchanged'])} 个\n"

                confirm_msg += f"\n【安全保障】\n"
                confirm_msg += "✓ 自动创建压缩备份\n"
                confirm_msg += "✓ MD5 完整性校验\n"
                confirm_msg += "✓ 失败自动恢复\n\n"
                confirm_msg += "是否继续？"

                confirmed = messagebox.askyesno("确认操作", confirm_msg, parent=root)
                root.destroy()

                if not confirmed:
                    return {'success': False, 'message': '用户取消操作', 'cancelled': True}

                logs.append({'type': 'info', 'message': '定制缓存封装中...'})

                # 8. 压缩备份原有文件（带取消检查）
                logs.append({'type': 'info', 'message': '正在创建压缩备份...'})

                # 操作取消标志
                cancel_flag = {'cancelled': False}

                def check_cancellation():
                    """检查操作是否被取消"""
                    return cancel_flag['cancelled']

                try:
                    backup_zip, backed_up = backup_files_compressed(target_path, config_dst, saves_dst, shards_dst, hc_dst)

                    if check_cancellation():
                        if backup_zip and backup_zip.exists():
                            backup_zip.unlink()
                        return {'success': False, 'message': '操作已取消', 'cancelled': True}

                    if backed_up:
                        backup_size = backup_zip.stat().st_size // 1024
                        logs.append({'type': 'info', 'message': f'已备份 {len(backed_up)} 个文件（压缩后 {backup_size} KB）'})
                    else:
                        logs.append({'type': 'info', 'message': '无需备份（目标位置无文件）'})
                except Exception as e:
                    return {
                        'success': False,
                        'message': f'备份失败: {str(e)}',
                        'logs': logs
                    }

                # 9. 执行增量更新（带进度回调和取消检查）
                logs.append({'type': 'info', 'message': '正在执行文件置换...'})

                config_src = cache_template / 'config.ini'
                saves_src = cache_template / 'saves'
                shards_src = cache_template / 'shards'

                copied_count = 0
                deleted_count = 0
                verified_count = 0
                total_operations = len(changes['add']) + len(changes['update'])
                current_operation = 0

                try:
                    # 新增和更新文件
                    if not saves_dst.exists():
                        saves_dst.mkdir(parents=True, exist_ok=True)

                    for file_rel in changes['add'] + changes['update']:
                        if check_cancellation():
                            raise Exception('操作已取消')

                        if file_rel == 'config.ini':
                            retry_operation(lambda: shutil.copy2(config_src, config_dst))
                            if calculate_md5(config_src) == calculate_md5(config_dst):
                                verified_count += 1
                            copied_count += 1
                        elif file_rel.startswith('saves/'):
                            bson_name = file_rel.replace('saves/', '')
                            src_file = saves_src / bson_name
                            dst_file = saves_dst / bson_name
                            retry_operation(lambda: shutil.copy2(src_file, dst_file))
                            if calculate_md5(src_file) == calculate_md5(dst_file):
                                verified_count += 1
                            copied_count += 1
                        elif file_rel.startswith('shards/'):
                            shard_rel = file_rel.replace('shards/', '')
                            src_file = shards_src / shard_rel
                            dst_file = shards_dst / shard_rel
                            # 确保目标子目录存在
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            retry_operation(lambda: shutil.copy2(src_file, dst_file))
                            if calculate_md5(src_file) == calculate_md5(dst_file):
                                verified_count += 1
                            copied_count += 1

                        current_operation += 1

                    logs.append({'type': 'info', 'message': f'文件校验完成：{verified_count}/{copied_count} 通过'})

                    if verified_count != copied_count:
                        raise Exception(f'文件校验失败：仅 {verified_count}/{copied_count} 通过')

                except Exception as e:
                    if 'cancel' in str(e).lower():
                        # 操作取消，恢复备份
                        if backup_zip:
                            logs.append({'type': 'info', 'message': '操作已取消，正在恢复备份...'})
                            if restore_from_backup_compressed(backup_zip, target_path):
                                logs.append({'type': 'info', 'message': '已恢复到操作前状态'})
                        return {
                            'success': False,
                            'message': '操作已取消',
                            'logs': logs,
                            'cancelled': True
                        }
                    else:
                        # 其他错误，恢复备份
                        if backup_zip:
                            logs.append({'type': 'info', 'message': '检测到错误，正在恢复备份...'})
                            if restore_from_backup_compressed(backup_zip, target_path):
                                logs.append({'type': 'info', 'message': '已恢复到操作前状态'})

                        log.error(f'增量更新失败: {e}', exc_info=True)
                        return {
                            'success': False,
                            'message': f'文件写入失败: {str(e)}',
                            'logs': logs
                        }

                # 10. 清理临时文件和旧备份
                logs.append({'type': 'info', 'message': '正在清理临时文件...'})
                try:
                    # 清理旧备份（保留最近3个）
                    backups = sorted(target_path.glob('.cache_backup_*.zip'))
                    if len(backups) > 3:
                        for old_backup in backups[:-3]:
                            old_backup.unlink()
                            log.info(f'已清理旧备份: {old_backup.name}')

                    # 清理临时文件
                    temp_patterns = [
                        '*.tmp',
                        '*.bak',
                        '.cache_temp_*',
                        '~*'
                    ]

                    cleaned_count = 0
                    for pattern in temp_patterns:
                        for temp_file in target_path.glob(pattern):
                            try:
                                if temp_file.is_file():
                                    temp_file.unlink()
                                    cleaned_count += 1
                            except Exception as e:
                                log.warning(f'清理临时文件失败: {temp_file}, {e}')

                    if cleaned_count > 0:
                        logs.append({'type': 'info', 'message': f'已清理 {cleaned_count} 个临时文件'})

                except Exception as e:
                    log.warning(f'清理临时文件失败: {e}')

                logs.append({'type': 'info', 'message': f'成功置换 {copied_count} 个文件'})

                return {
                    'success': True,
                    'logs': logs,
                    'stats': {
                        'total_files': total_changes,
                        'copied_files': copied_count,
                        'verified_files': verified_count,
                        'total_size_kb': 0,
                        'backup_path': str(backup_zip.name) if backup_zip else None,
                        'incremental': True,
                        'unchanged_files': len(changes['unchanged'])
                    }
                }

        except Exception as e:
            log.error(f'缓存置换失败: {e}', exc_info=True)
            error_msg = str(e)
            if 'permission' in error_msg.lower():
                error_msg = '权限不足，请以管理员身份运行'
            elif 'access' in error_msg.lower():
                error_msg = '文件被占用，请关闭相关程序后重试'

            return {
                'success': False,
                'message': f'操作失败: {error_msg}',
                'logs': logs
            }
        import tkinter as tk
        from tkinter import filedialog, messagebox
        import shutil
        import hashlib
        from pathlib import Path
        from datetime import datetime

        logs = []
        backup_dir = None

        def calculate_md5(file_path):
            """计算文件MD5"""
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()

        def backup_files(target_path, config_dst, saves_dst, hc_dst):
            """备份原有文件"""
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = target_path / f'.cache_backup_{timestamp}'
            backup_path.mkdir(parents=True, exist_ok=True)

            backed_up = []

            try:
                if config_dst.exists():
                    shutil.copy2(config_dst, backup_path / 'config.ini')
                    backed_up.append('config.ini')

                if hc_dst.exists():
                    shutil.copy2(hc_dst, backup_path / 'hc.dat')
                    backed_up.append('hc.dat')

                if saves_dst.exists():
                    backup_saves = backup_path / 'saves'
                    backup_saves.mkdir(exist_ok=True)
                    for bson_file in saves_dst.glob('*.bson'):
                        shutil.copy2(bson_file, backup_saves / bson_file.name)
                        backed_up.append(f'saves/{bson_file.name}')

                return backup_path, backed_up
            except Exception as e:
                log.error(f'备份失败: {e}', exc_info=True)
                if backup_path.exists():
                    shutil.rmtree(backup_path, ignore_errors=True)
                raise

        def restore_from_backup(backup_path, target_path):
            """从备份恢复"""
            try:
                config_backup = backup_path / 'config.ini'
                hc_backup = backup_path / 'hc.dat'
                saves_backup = backup_path / 'saves'

                if config_backup.exists():
                    shutil.copy2(config_backup, target_path / 'config.ini')

                if hc_backup.exists():
                    shutil.copy2(hc_backup, target_path / 'hc.dat')

                if saves_backup.exists():
                    saves_dst = target_path / 'saves'
                    saves_dst.mkdir(exist_ok=True)
                    for bson_file in saves_backup.glob('*.bson'):
                        shutil.copy2(bson_file, saves_dst / bson_file.name)

                log.info('已从备份恢复文件')
                return True
            except Exception as e:
                log.error(f'恢复失败: {e}', exc_info=True)
                return False

        def init_cache_template():
            """自动初始化缓存模板目录"""
            app_root = get_app_root()
            cache_template = Path(app_root) / 'cache_template'

            if not cache_template.exists():
                cache_template.mkdir(parents=True, exist_ok=True)
                (cache_template / 'saves').mkdir(exist_ok=True)

                # 创建示例文件（空文件）
                (cache_template / 'config.ini').touch()
                (cache_template / 'hc.dat').touch()

                log.info('已自动创建缓存模板目录')
                return True
            return False

        def load_last_path():
            """加载上次选择的路径"""
            try:
                app_root = get_app_root()
                config_file = Path(app_root) / 'data' / 'cache_config.json'
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        return config.get('last_path')
            except Exception as e:
                log.warning(f'加载上次路径失败: {e}')
            return None

        def save_last_path(path):
            """保存本次选择的路径"""
            try:
                app_root = get_app_root()
                config_dir = Path(app_root) / 'data'
                config_dir.mkdir(parents=True, exist_ok=True)
                config_file = config_dir / 'cache_config.json'

                config = {}
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                config['last_path'] = str(path)
                config['last_update'] = datetime.now().isoformat()

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                log.info(f'已保存路径记忆: {path}')
            except Exception as e:
                log.warning(f'保存路径失败: {e}')

        try:
            # 0. 自动初始化缓存模板
            template_created = init_cache_template()
            if template_created:
                logs.append({'type': 'info', 'message': '已自动创建缓存模板目录'})

            # 1. 弹出文件夹选择对话框（带路径记忆）
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            last_path = load_last_path()
            initial_dir = last_path if last_path and Path(last_path).exists() else None

            target_dir = filedialog.askdirectory(
                title="选择防封位置（目标文件夹）",
                initialdir=initial_dir,
                mustexist=True
            )

            if not target_dir:
                root.destroy()
                return {'success': False, 'message': '未选择文件夹', 'cancelled': True}

            target_path = Path(target_dir)

            # 保存路径记忆
            save_last_path(target_path)

            # 2. 定位缓存模板目录
            app_root = get_app_root()
            cache_template = Path(app_root) / 'cache_template'

            if not cache_template.exists():
                root.destroy()
                return {
                    'success': False,
                    'message': '缓存模板不存在，请联系技术支持',
                    'logs': logs
                }

            # 3. 定位源文件和目标文件
            config_src = cache_template / 'config.ini'
            saves_src = cache_template / 'saves'
            hc_src = cache_template / 'hc.dat'

            config_dst = target_path / 'config.ini'
            saves_dst = target_path / 'saves'
            hc_dst = target_path / 'hc.dat'

            # 统计源文件信息
            total_files = 0
            total_size = 0
            bson_files = []

            if config_src.exists() and config_src.stat().st_size > 0:
                total_files += 1
                total_size += config_src.stat().st_size

            if hc_src.exists() and hc_src.stat().st_size > 0:
                total_files += 1
                total_size += hc_src.stat().st_size

            if saves_src.exists():
                bson_files = [f for f in saves_src.glob('*.bson') if f.stat().st_size > 0]
                total_files += len(bson_files)
                total_size += sum(f.stat().st_size for f in bson_files)

            if total_files == 0:
                root.destroy()
                return {
                    'success': False,
                    'message': '缓存模板为空，请先配置模板文件',
                    'logs': logs
                }

            # 4. 显示确认对话框
            confirm_msg = f"即将执行缓存置换操作：\n\n"
            confirm_msg += f"目标位置：{target_path}\n"
            confirm_msg += f"文件数量：{total_files} 个\n"
            confirm_msg += f"总大小：{total_size // 1024} KB\n\n"
            confirm_msg += "原有文件将被自动备份。\n是否继续？"

            confirmed = messagebox.askyesno("确认操作", confirm_msg, parent=root)
            root.destroy()

            if not confirmed:
                return {'success': False, 'message': '用户取消操作', 'cancelled': True}

            logs.append({'type': 'info', 'message': '定制缓存封装中...'})
            logs.append({'type': 'info', 'message': f'检测到 {total_files} 个文件，总大小 {total_size // 1024} KB'})

            # 5. 备份原有文件
            logs.append({'type': 'info', 'message': '正在备份原有文件...'})
            try:
                backup_dir, backed_up = backup_files(target_path, config_dst, saves_dst, hc_dst)
                if backed_up:
                    logs.append({'type': 'info', 'message': f'已备份 {len(backed_up)} 个文件'})
                else:
                    logs.append({'type': 'info', 'message': '无需备份（目标位置无文件）'})
            except Exception as e:
                return {
                    'success': False,
                    'message': f'备份失败: {str(e)}',
                    'logs': logs
                }

            logs.append({'type': 'info', 'message': '正在清理目标环境...'})

            # 6. 清空目标位置
            deleted_count = 0

            try:
                if config_dst.exists():
                    config_dst.unlink()
                    deleted_count += 1

                if hc_dst.exists():
                    hc_dst.unlink()
                    deleted_count += 1

                if saves_dst.exists():
                    for bson_file in saves_dst.glob('*.bson'):
                        bson_file.unlink()
                        deleted_count += 1
                else:
                    saves_dst.mkdir(parents=True, exist_ok=True)

                if deleted_count > 0:
                    logs.append({'type': 'info', 'message': f'已清理 {deleted_count} 个旧文件'})

            except PermissionError:
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到权限错误，正在恢复备份...'})
                    restore_from_backup(backup_dir, target_path)
                return {
                    'success': False,
                    'message': '文件被占用，请关闭相关程序后重试',
                    'logs': logs
                }
            except Exception as e:
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到错误，正在恢复备份...'})
                    restore_from_backup(backup_dir, target_path)
                return {
                    'success': False,
                    'message': f'清理失败: {str(e)}',
                    'logs': logs
                }

            logs.append({'type': 'info', 'message': '正在写入新缓存...'})

            # 7. 复制文件并校验
            copied_count = 0
            verified_count = 0

            try:
                if config_src.exists() and config_src.stat().st_size > 0:
                    shutil.copy2(config_src, config_dst)
                    if calculate_md5(config_src) == calculate_md5(config_dst):
                        verified_count += 1
                    copied_count += 1

                if hc_src.exists() and hc_src.stat().st_size > 0:
                    shutil.copy2(hc_src, hc_dst)
                    if calculate_md5(hc_src) == calculate_md5(hc_dst):
                        verified_count += 1
                    copied_count += 1

                if saves_src.exists() and bson_files:
                    for bson_file in bson_files:
                        dst_file = saves_dst / bson_file.name
                        shutil.copy2(bson_file, dst_file)
                        if calculate_md5(bson_file) == calculate_md5(dst_file):
                            verified_count += 1
                        copied_count += 1

                    logs.append({'type': 'info', 'message': f'已写入 {len(bson_files)} 个存档文件'})

                logs.append({'type': 'info', 'message': f'文件校验完成：{verified_count}/{copied_count} 通过'})

                if verified_count != copied_count:
                    raise Exception(f'文件校验失败：仅 {verified_count}/{copied_count} 通过')

            except Exception as e:
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到错误，正在恢复备份...'})
                    if restore_from_backup(backup_dir, target_path):
                        logs.append({'type': 'info', 'message': '已恢复到操作前状态'})

                log.error(f'复制文件失败: {e}', exc_info=True)
                return {
                    'success': False,
                    'message': f'文件写入失败: {str(e)}',
                    'logs': logs
                }

            # 8. 清理旧备份（保留最近3个）
            try:
                backups = sorted(target_path.glob('.cache_backup_*'))
                if len(backups) > 3:
                    for old_backup in backups[:-3]:
                        shutil.rmtree(old_backup, ignore_errors=True)
                        log.info(f'已清理旧备份: {old_backup.name}')
            except Exception as e:
                log.warning(f'清理旧备份失败: {e}')

            logs.append({'type': 'info', 'message': f'成功写入 {copied_count} 个文件'})

            return {
                'success': True,
                'logs': logs,
                'stats': {
                    'total_files': total_files,
                    'copied_files': copied_count,
                    'deleted_files': deleted_count,
                    'verified_files': verified_count,
                    'total_size_kb': total_size // 1024,
                    'backup_path': str(backup_dir.name) if backup_dir else None
                }
            }

        except Exception as e:
            log.error(f'缓存置换失败: {e}', exc_info=True)
            error_msg = str(e)
            if 'permission' in error_msg.lower():
                error_msg = '权限不足，请以管理员身份运行'
            elif 'access' in error_msg.lower():
                error_msg = '文件被占用，请关闭相关程序后重试'

            return {
                'success': False,
                'message': f'操作失败: {error_msg}',
                'logs': logs
            }

    def rollback_cache(self, backup_name: str) -> dict:
        """回滚到指定备份"""
        import shutil
        from pathlib import Path

        try:
            # 从配置读取上次操作的路径
            app_root = get_app_root()
            config_file = Path(app_root) / 'data' / 'cache_config.json'

            if not config_file.exists():
                return {'success': False, 'message': '未找到操作记录'}

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                last_path = config.get('last_path')

            if not last_path:
                return {'success': False, 'message': '未找到上次操作路径'}

            target_path = Path(last_path)
            backup_path = target_path / backup_name

            if not backup_path.exists():
                return {'success': False, 'message': f'备份不存在: {backup_name}'}

            # 恢复备份
            config_backup = backup_path / 'config.ini'
            hc_backup = backup_path / 'hc.dat'
            saves_backup = backup_path / 'saves'

            restored_count = 0

            if config_backup.exists():
                shutil.copy2(config_backup, target_path / 'config.ini')
                restored_count += 1

            if hc_backup.exists():
                shutil.copy2(hc_backup, target_path / 'hc.dat')
                restored_count += 1

            if saves_backup.exists():
                saves_dst = target_path / 'saves'
                saves_dst.mkdir(exist_ok=True)
                # 先清空
                for f in saves_dst.glob('*.bson'):
                    f.unlink()
                # 再恢复
                for bson_file in saves_backup.glob('*.bson'):
                    shutil.copy2(bson_file, saves_dst / bson_file.name)
                    restored_count += 1

            log.info(f'已回滚到备份: {backup_name}，恢复 {restored_count} 个文件')

            return {
                'success': True,
                'message': f'已回滚到 {backup_name}',
                'restored_count': restored_count
            }

        except Exception as e:
            log.error(f'回滚失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'回滚失败: {str(e)}'
            }

    def list_cache_backups(self) -> dict:
        """列出所有可用的备份"""
        from pathlib import Path
        from datetime import datetime

        try:
            app_root = get_app_root()
            config_file = Path(app_root) / 'data' / 'cache_config.json'

            if not config_file.exists():
                return {'success': True, 'backups': []}

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                last_path = config.get('last_path')

            if not last_path:
                return {'success': True, 'backups': []}

            target_path = Path(last_path)
            backups = []

            for backup_dir in sorted(target_path.glob('.cache_backup_*'), reverse=True):
                try:
                    # 解析时间戳
                    timestamp_str = backup_dir.name.replace('.cache_backup_', '')
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                    # 统计文件数量
                    file_count = 0
                    if (backup_dir / 'config.ini').exists():
                        file_count += 1
                    if (backup_dir / 'hc.dat').exists():
                        file_count += 1
                    saves_backup = backup_dir / 'saves'
                    if saves_backup.exists():
                        file_count += len(list(saves_backup.glob('*.bson')))

                    backups.append({
                        'name': backup_dir.name,
                        'timestamp': timestamp.isoformat(),
                        'display_time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'file_count': file_count
                    })
                except Exception as e:
                    log.warning(f'解析备份失败: {backup_dir.name}, {e}')

            return {
                'success': True,
                'backups': backups
            }

        except Exception as e:
            log.error(f'列出备份失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'列出备份失败: {str(e)}',
                'backups': []
            }

    def export_cache_logs(self, logs: list) -> dict:
        """导出操作日志到文件"""
        from pathlib import Path
        from datetime import datetime
        import tkinter as tk
        from tkinter import filedialog

        try:
            # 弹出保存对话框
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'cache_logs_{timestamp}.txt'

            file_path = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )

            root.destroy()

            if not file_path:
                return {'success': False, 'message': '用户取消', 'cancelled': True}

            # 写入日志
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"缓存置换操作日志\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'=' * 60}\n\n")

                for idx, log_entry in enumerate(logs, 1):
                    log_type = log_entry.get('type', 'info').upper()
                    message = log_entry.get('message', '')
                    f.write(f"[{idx}] [{log_type}] {message}\n")

                f.write(f"\n{'=' * 60}\n")
                f.write(f"共 {len(logs)} 条日志\n")

            log.info(f'日志已导出到: {file_path}')

            return {
                'success': True,
                'message': f'日志已保存到: {Path(file_path).name}',
                'file_path': file_path
            }

        except Exception as e:
            log.error(f'导出日志失败: {e}', exc_info=True)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }
        import tkinter as tk
        from tkinter import filedialog, messagebox
        import shutil
        import hashlib
        from pathlib import Path
        from datetime import datetime

        logs = []
        backup_dir = None

        def calculate_md5(file_path):
            """计算文件MD5"""
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()

        def backup_files(target_path, config_dst, saves_dst, hc_dst):
            """备份原有文件"""
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = target_path / f'.cache_backup_{timestamp}'
            backup_path.mkdir(parents=True, exist_ok=True)

            backed_up = []

            try:
                if config_dst.exists():
                    shutil.copy2(config_dst, backup_path / 'config.ini')
                    backed_up.append('config.ini')

                if hc_dst.exists():
                    shutil.copy2(hc_dst, backup_path / 'hc.dat')
                    backed_up.append('hc.dat')

                if saves_dst.exists():
                    backup_saves = backup_path / 'saves'
                    backup_saves.mkdir(exist_ok=True)
                    for bson_file in saves_dst.glob('*.bson'):
                        shutil.copy2(bson_file, backup_saves / bson_file.name)
                        backed_up.append(f'saves/{bson_file.name}')

                return backup_path, backed_up
            except Exception as e:
                log.error(f'备份失败: {e}', exc_info=True)
                # 清理不完整的备份
                if backup_path.exists():
                    shutil.rmtree(backup_path, ignore_errors=True)
                raise

        def restore_from_backup(backup_path, target_path):
            """从备份恢复"""
            try:
                config_backup = backup_path / 'config.ini'
                hc_backup = backup_path / 'hc.dat'
                saves_backup = backup_path / 'saves'

                if config_backup.exists():
                    shutil.copy2(config_backup, target_path / 'config.ini')

                if hc_backup.exists():
                    shutil.copy2(hc_backup, target_path / 'hc.dat')

                if saves_backup.exists():
                    saves_dst = target_path / 'saves'
                    saves_dst.mkdir(exist_ok=True)
                    for bson_file in saves_backup.glob('*.bson'):
                        shutil.copy2(bson_file, saves_dst / bson_file.name)

                log.info('已从备份恢复文件')
                return True
            except Exception as e:
                log.error(f'恢复失败: {e}', exc_info=True)
                return False

        try:
            # 1. 弹出文件夹选择对话框
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            target_dir = filedialog.askdirectory(
                title="选择防封位置（目标文件夹）",
                mustexist=True
            )

            if not target_dir:
                root.destroy()
                return {'success': False, 'message': '未选择文件夹', 'cancelled': True}

            target_path = Path(target_dir)

            # 2. 定位缓存模板目录
            app_root = get_app_root()
            cache_template = Path(app_root) / 'cache_template'

            if not cache_template.exists():
                root.destroy()
                return {
                    'success': False,
                    'message': '缓存模板不存在，请联系技术支持',
                    'logs': logs
                }

            # 3. 定位源文件和目标文件
            config_src = cache_template / 'config.ini'
            saves_src = cache_template / 'saves'
            hc_src = cache_template / 'hc.dat'

            config_dst = target_path / 'config.ini'
            saves_dst = target_path / 'saves'
            hc_dst = target_path / 'hc.dat'

            # 统计源文件信息
            total_files = 0
            total_size = 0
            bson_files = []

            if config_src.exists():
                total_files += 1
                total_size += config_src.stat().st_size

            if hc_src.exists():
                total_files += 1
                total_size += hc_src.stat().st_size

            if saves_src.exists():
                bson_files = list(saves_src.glob('*.bson'))
                total_files += len(bson_files)
                total_size += sum(f.stat().st_size for f in bson_files)

            # 4. 显示确认对话框
            confirm_msg = f"即将执行缓存置换操作：\n\n"
            confirm_msg += f"目标位置：{target_path}\n"
            confirm_msg += f"文件数量：{total_files} 个\n"
            confirm_msg += f"总大小：{total_size // 1024} KB\n\n"
            confirm_msg += "原有文件将被自动备份。\n是否继续？"

            confirmed = messagebox.askyesno("确认操作", confirm_msg, parent=root)
            root.destroy()

            if not confirmed:
                return {'success': False, 'message': '用户取消操作', 'cancelled': True}

            logs.append({'type': 'info', 'message': '定制缓存封装中...'})
            logs.append({'type': 'info', 'message': f'检测到 {total_files} 个文件，总大小 {total_size // 1024} KB'})

            # 5. 备份原有文件
            logs.append({'type': 'info', 'message': '正在备份原有文件...'})
            try:
                backup_dir, backed_up = backup_files(target_path, config_dst, saves_dst, hc_dst)
                if backed_up:
                    logs.append({'type': 'info', 'message': f'已备份 {len(backed_up)} 个文件'})
                else:
                    logs.append({'type': 'info', 'message': '无需备份（目标位置无文件）'})
            except Exception as e:
                return {
                    'success': False,
                    'message': f'备份失败: {str(e)}',
                    'logs': logs
                }

            logs.append({'type': 'info', 'message': '正在清理目标环境...'})

            # 6. 清空目标位置
            deleted_count = 0

            try:
                if config_dst.exists():
                    config_dst.unlink()
                    deleted_count += 1

                if hc_dst.exists():
                    hc_dst.unlink()
                    deleted_count += 1

                if saves_dst.exists():
                    for bson_file in saves_dst.glob('*.bson'):
                        bson_file.unlink()
                        deleted_count += 1
                else:
                    saves_dst.mkdir(parents=True, exist_ok=True)

                if deleted_count > 0:
                    logs.append({'type': 'info', 'message': f'已清理 {deleted_count} 个旧文件'})

            except PermissionError:
                # 恢复备份
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到权限错误，正在恢复备份...'})
                    restore_from_backup(backup_dir, target_path)
                return {
                    'success': False,
                    'message': '文件被占用，请关闭相关程序后重试',
                    'logs': logs
                }
            except Exception as e:
                # 恢复备份
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到错误，正在恢复备份...'})
                    restore_from_backup(backup_dir, target_path)
                return {
                    'success': False,
                    'message': f'清理失败: {str(e)}',
                    'logs': logs
                }

            logs.append({'type': 'info', 'message': '正在写入新缓存...'})

            # 7. 复制文件并校验
            copied_count = 0
            verified_count = 0

            try:
                if config_src.exists():
                    shutil.copy2(config_src, config_dst)
                    # 校验
                    if calculate_md5(config_src) == calculate_md5(config_dst):
                        verified_count += 1
                    copied_count += 1

                if hc_src.exists():
                    shutil.copy2(hc_src, hc_dst)
                    if calculate_md5(hc_src) == calculate_md5(hc_dst):
                        verified_count += 1
                    copied_count += 1

                if saves_src.exists():
                    for bson_file in bson_files:
                        dst_file = saves_dst / bson_file.name
                        shutil.copy2(bson_file, dst_file)
                        if calculate_md5(bson_file) == calculate_md5(dst_file):
                            verified_count += 1
                        copied_count += 1

                    logs.append({'type': 'info', 'message': f'已写入 {len(bson_files)} 个存档文件'})

                logs.append({'type': 'info', 'message': f'文件校验完成：{verified_count}/{copied_count} 通过'})

                if verified_count != copied_count:
                    raise Exception(f'文件校验失败：仅 {verified_count}/{copied_count} 通过')

            except Exception as e:
                # 恢复备份
                if backup_dir:
                    logs.append({'type': 'info', 'message': '检测到错误，正在恢复备份...'})
                    if restore_from_backup(backup_dir, target_path):
                        logs.append({'type': 'info', 'message': '已恢复到操作前状态'})

                log.error(f'复制文件失败: {e}', exc_info=True)
                return {
                    'success': False,
                    'message': f'文件写入失败: {str(e)}',
                    'logs': logs
                }

            # 8. 清理备份（可选保留）
            # 保留最近3个备份
            try:
                backups = sorted(target_path.glob('.cache_backup_*'))
                if len(backups) > 3:
                    for old_backup in backups[:-3]:
                        shutil.rmtree(old_backup, ignore_errors=True)
                        log.info(f'已清理旧备份: {old_backup.name}')
            except Exception as e:
                log.warning(f'清理旧备份失败: {e}')

            logs.append({'type': 'info', 'message': f'成功写入 {copied_count} 个文件'})

            return {
                'success': True,
                'logs': logs,
                'stats': {
                    'total_files': total_files,
                    'copied_files': copied_count,
                    'deleted_files': deleted_count,
                    'verified_files': verified_count,
                    'total_size_kb': total_size // 1024,
                    'backup_path': str(backup_dir.name) if backup_dir else None
                }
            }

        except Exception as e:
            log.error(f'缓存置换失败: {e}', exc_info=True)
            error_msg = str(e)
            if 'permission' in error_msg.lower():
                error_msg = '权限不足，请以管理员身份运行'
            elif 'access' in error_msg.lower():
                error_msg = '文件被占用，请关闭相关程序后重试'

            return {
                'success': False,
                'message': f'操作失败: {error_msg}',
                'logs': logs
            }

    # ========== 实时对局数据 ==========

    def get_live_game_data(self) -> dict:
        """获取实时对局数据（通过 Live Client Data API）"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                raw = json.loads(resp.read().decode())
        except Exception as e:
            return {'success': False, 'error': str(e)}

        # 解析 activePlayer
        active = raw.get('activePlayer') or {}
        active_name = active.get('riotIdGameName') or active.get('summonerName') or ''

        # 解析所有玩家
        all_players = raw.get('allPlayers') or []
        order_team = []
        chaos_team = []
        my_team_tag = None

        for p in all_players:
            name = p.get('riotIdGameName') or p.get('summonerName') or ''
            entry = {
                'name': name,
                'champion': p.get('championName', ''),
                'level': p.get('level', 0),
                'kills': p.get('scores', {}).get('kills', 0),
                'deaths': p.get('scores', {}).get('deaths', 0),
                'assists': p.get('scores', {}).get('assists', 0),
                'cs': p.get('scores', {}).get('creepScore', 0),
                'is_me': name == active_name,
            }
            team = p.get('team', '')
            if entry['is_me']:
                my_team_tag = team
            if team == 'ORDER':
                order_team.append(entry)
            else:
                chaos_team.append(entry)

        if my_team_tag == 'ORDER':
            my_team, enemy_team = order_team, chaos_team
        else:
            my_team, enemy_team = chaos_team, order_team

        # 团队汇总
        my_kills = sum(p['kills'] for p in my_team)
        enemy_kills = sum(p['kills'] for p in enemy_team)

        # 筛选重要事件
        events_raw = (raw.get('events') or {}).get('Events') or []
        important_events = []
        important_types = {'DragonKill', 'BaronKill', 'HeraldKill', 'TurretKilled', 'InhibKilled'}
        for ev in events_raw:
            etype = ev.get('EventName', '')
            if etype in important_types:
                killer = ev.get('KillerName', '')
                # 判断是我方还是对方
                is_ally = any(p['name'] == killer or p['champion'] == killer for p in my_team)
                side = 'ally' if is_ally else 'enemy'
                label = {
                    'DragonKill': f"击杀 {ev.get('DragonType', '龙')}龙",
                    'BaronKill': '击杀 男爵纳什尔',
                    'HeraldKill': '击杀 峡谷先锋',
                    'TurretKilled': '摧毁 防御塔',
                    'InhibKilled': '摧毁 水晶',
                }.get(etype, etype)
                important_events.append({
                    'time': ev.get('EventTime', 0),
                    'side': side,
                    'label': label,
                })
            elif etype == 'Multikill' and ev.get('KillStreak', 0) >= 3:
                killer = ev.get('KillerName', '')
                is_ally = any(p['name'] == killer or p['champion'] == killer for p in my_team)
                streak = ev.get('KillStreak', 3)
                streak_names = {3: '三杀', 4: '四杀', 5: '五杀'}
                label = f"{killer} {streak_names.get(streak, f'{streak}连杀')}"
                important_events.append({
                    'time': ev.get('EventTime', 0),
                    'side': 'ally' if is_ally else 'enemy',
                    'label': label,
                })

        important_events.sort(key=lambda e: e['time'], reverse=True)

        game_data = raw.get('gameData') or {}
        game_time = game_data.get('gameTime', 0)

        return {
            'success': True,
            'game_time': game_time,
            'my_team': my_team,
            'enemy_team': enemy_team,
            'my_kills': my_kills,
            'enemy_kills': enemy_kills,
            'events': important_events[:20],
        }

    # ========== 当前选择英雄 ==========
    
    def get_current_champion(self) -> dict:
        """获取当前选人阶段选择的英雄ID"""
        if not self.api:
            return {'champion_id': None}
        
        try:
            # 获取选人阶段数据
            session = self.api.get_champ_select_session()
            if not session:
                return {'champion_id': None}
            
            my_summoner_id = session.get('localPlayerCellId', -1)
            my_team = session.get('myTeam', [])
            
            for player in my_team:
                if player.get('cellId') == my_summoner_id:
                    # 优先使用已确认的英雄，其次是预选英雄
                    champion_id = player.get('championId') or player.get('championPickIntent')
                    if champion_id and champion_id > 0:
                        return {'champion_id': champion_id}
            
            return {'champion_id': None}
        except Exception as e:
            log.warning("获取当前英雄失败: %s", e)
            return {'champion_id': None}

    # ========== 强化推荐 ==========
    
    def get_augments_data(self) -> dict:
        """获取强化推荐数据"""
        return self.augments_data_service.get_data()

    def get_augments_data_status(self) -> dict:
        """获取强化数据状态"""
        return self.augments_data_service.get_status()

    def refresh_augments_data(self) -> dict:
        """触发强化数据刷新"""
        return self.augments_data_service.trigger_update(reason='manual')
    
    # ========== 符文推荐 ==========
    
    def get_runes_data(self) -> dict:
        """获取符文推荐数据（带服务端缓存）"""
        return self.runes_data_service.get_data()

    def get_runes_data_status(self) -> dict:
        """获取符文数据状态"""
        return self.runes_data_service.get_status()

    def get_runes_entry(self, champion_id: int, position: str = 'MID') -> dict:
        """按英雄 + 分路获取符文，减少前端全量拉取。"""
        return self.runes_data_service.get_entry(champion_id=champion_id, position=position)

    def refresh_runes_data(self) -> dict:
        """触发符文数据刷新"""
        return self.runes_data_service.trigger_update(reason='manual')

    def refresh_runes_single(self, champion_id: int, champion_key: str, position: str = 'MID', region: str = 'CN') -> dict:
        """仅刷新当前英雄+位置的符文数据（增量）"""
        return self.runes_data_service.refresh_single_entry(
            champion_id=champion_id,
            champion_key=champion_key,
            position=position,
            region=region,
        )

    def refresh_runes_selected(self, targets: list[dict], region: str = 'CN', positions: list[str] | None = None) -> dict:
        """批量刷新已选英雄符文数据（增量）"""
        return self.runes_data_service.refresh_selected_entries(
            targets=targets,
            region=region,
            positions=positions,
        )

    def get_champion_overview(self, champion_key: str, position: str = 'MID', region: str = 'CN') -> dict:
        """获取当前英雄概览指标（Win/Pick/Ban/Tier等）"""
        return self.runes_data_service.fetch_champion_overview(
            champion_key=champion_key,
            position=position,
            region=region,
        )

    def get_runtime_snapshot(self) -> dict:
        """高频轮询快照：合并连接、阶段、模式、英雄与自动功能状态。"""
        now = time.time()
        if self._snapshot_cache is not None and (now - self._snapshot_cache_at) < self._snapshot_cache_ttl:
            return self._snapshot_cache

        connected = bool(self.conn.is_connected and self.conn.check_alive())

        # 合并 phase / mode_hint / current_champion 为一次 LCU 请求
        phase_str = 'None'
        mode_hint = {'success': False, 'route': '/runes', 'mode': 'CLASSIC'}
        current_champion = {'champion_id': None}

        if connected and self.api:
            try:
                session = self.api.get('/lol-gameflow/v1/session') or {}
                phase_str = session.get('phase') or 'None'

                # --- mode_hint 从 session 提取（复用共享逻辑）---
                mode_hint = self._detect_mode_hint(session)

                # --- current_champion 从 champ-select session 提取（仅选人阶段）---
                if phase_str == 'ChampSelect':
                    try:
                        cs = self.api.get_champ_select_session()
                        if cs:
                            my_cell = cs.get('localPlayerCellId', -1)
                            for player in cs.get('myTeam', []):
                                if player.get('cellId') == my_cell:
                                    cid = player.get('championId') or player.get('championPickIntent')
                                    if cid and cid > 0:
                                        current_champion = {'champion_id': cid}
                                    break
                    except Exception:
                        pass
            except Exception:
                # session 请求失败时降级为简单 phase 查询
                raw_phase = self.api.get('/lol-gameflow/v1/gameflow-phase')
                if raw_phase:
                    phase_str = raw_phase

        auto_accept = self.get_auto_accept_status()
        auto_select = self.get_auto_select_status()
        summoner = self.get_current_summoner()
        runes_status = self.runes_data_service.get_brief_status()
        augments_status = self.augments_data_service.get_status()

        compact_augments_status = {
            'exists': bool(augments_status.get('exists')),
            'is_updating': bool(augments_status.get('is_updating')),
            'is_stale': bool(augments_status.get('is_stale')),
            'days_old': augments_status.get('days_old'),
            'last_update': augments_status.get('last_update'),
            'last_update_error': augments_status.get('last_update_error'),
        }

        result = {
            'connected': connected,
            'game_phase': phase_str,
            'mode_hint': mode_hint,
            'recommended_route': mode_hint.get('route') if isinstance(mode_hint, dict) else '/runes',
            'game_mode_type': mode_hint.get('mode') if isinstance(mode_hint, dict) else 'CLASSIC',
            'auto_accept': copy.deepcopy(auto_accept),
            'auto_select': copy.deepcopy(auto_select),
            'current_champion': copy.deepcopy(current_champion),
            'summoner': copy.deepcopy(summoner),
            'runes_status': runes_status,
            'augments_status': compact_augments_status,
            'timestamp': int(time.time()),
        }
        self._snapshot_cache = result
        self._snapshot_cache_at = now
        return result
    
    def apply_rune_config(self, rune_config: dict, champion_name: str = '', position: str = '') -> dict:
        """
        应用符文配置到客户端
        """
        try:
            if not self.conn.is_connected:
                return {
                    'success': False,
                    'message': '未连接到游戏客户端，请确保客户端已启动'
                }
            
            # 复用或创建符文管理器
            if self._rune_manager is None:
                from services.rune_manager import RuneManager
                self._rune_manager = RuneManager(self.conn)
            
            rune_mgr = self._rune_manager
            
            # 验证符文配置
            is_valid, error = rune_mgr.validate_rune_config(rune_config)
            if not is_valid:
                return {
                    'success': False,
                    'message': f'符文配置无效: {error}',
                    'code': 'RUNE_CONFIG_INVALID'
                }
            
            # 应用符文
            result = rune_mgr.apply_rune_config(rune_config, champion_name, position)
            if 'code' not in result:
                result['code'] = 'OK' if result.get('success', False) else 'RUNE_APPLY_FAILED'
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'应用符文时出错: {str(e)}'
            }

    # ========== 登录相关 ==========

    def get_server_list(self) -> list:
        """获取大区列表"""
        return [{'index': i, 'name': name} for i, name in enumerate(SERVER_LIST)]

    def detect_game_path(self) -> dict:
        """自动检测游戏路径"""
        path = detect_game_path()
        return {'success': bool(path), 'path': path}

    def get_login_status(self) -> dict:
        """获取登录状态，如果检测到封号则保存到账号（只保存一次）"""
        status = self.login_service.get_status()
        account_id = self._current_login_account_id
        status_name = status.get('status')
        if account_id and status_name in {'success', 'failed', 'banned', 'password_leaked'}:
            signature = f"{status_name}:{status.get('phase', '')}:{status.get('message', '')}"
            if getattr(self, '_last_login_status_signature', None) != signature:
                self._last_login_status_signature = signature
                try:
                    self.account_manager.mark_login_result(account_id, status_name, status.get('message', ''))
                except Exception as exc:
                    log.debug("保存最近登录结果失败: %s", exc)
        # 检测到封号，解析并返回结构化字段
        if status.get('status') == 'banned' and status.get('ban_info'):
            raw = status['ban_info']
            parsed = self._parse_ban_info(raw)
            log.info("封号解析结果: raw=%s, parsed=%s", raw[:200], parsed)
            # 每次都把解析后的字段合并到 status 里给前端
            status['ban_start'] = parsed.get('ban_start', '')
            status['ban_end'] = parsed.get('ban_end', '')
            status['ban_days'] = parsed.get('ban_days', '')
            status['ban_type'] = parsed.get('ban_type', '')
            status['ban_reason'] = parsed.get('reason', '')
            # 保存到账号记录（用标志位避免每次轮询都写磁盘）
            account_id = self._current_login_account_id
            if account_id and not self._ban_saved:
                self._ban_saved = True
                self.account_manager.update_account(
                    account_id,
                    ban_info=parsed.get('reason') or raw,
                    ban_time=int(time.time()),
                    ban_start=parsed.get('ban_start', ''),
                    ban_end=parsed.get('ban_end', ''),
                    ban_days=parsed.get('ban_days', ''),
                    ban_type=parsed.get('ban_type', ''),
                )
        return status

    @staticmethod
    def _parse_ban_info(text: str) -> dict:
        """从封号弹窗文本解析结构化字段。

        支持多种格式：
        1. 详细格式（标题"查询结果"）：封号类型/封号原因/处罚时间/解封时间/处罚天数
        2. 简短格式（标题"信息:"）：这个账号已被封停至:2026-3-26 1:10:22
        3. 通用日期格式：自动提取文本中的日期作为解封时间
        """
        result = {}
        if not text:
            return result

        # 简短格式：匹配 "已被封停至:日期"
        m = re.search(r'已被封停至[：:]?\s*(.+)', text)
        if m and '封号类型' not in text:
            result['ban_type'] = '封停'
            result['ban_end'] = m.group(1).strip()
            result['reason'] = text.strip()
            return result

        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 封号类型:封号
            if '封号类型' in line:
                result['ban_type'] = line.split(':', 1)[-1].split('：', 1)[-1].strip()
            # 封号原因：检测到第三方软件加载，修改游戏客户端
            elif '封号原因' in line or '原因' in line:
                result['reason'] = line.split(':', 1)[-1].split('：', 1)[-1].strip()
            # 处罚时间：2026年2月25日9时8分28秒
            elif '处罚时间' in line:
                result['ban_start'] = line.split(':', 1)[-1].split('：', 1)[-1].strip()
            # 解封时间：2026年3月27日9时8分28秒
            elif '解封时间' in line:
                result['ban_end'] = line.split(':', 1)[-1].split('：', 1)[-1].strip()
            # 处罚天数:30
            elif '处罚天数' in line:
                result['ban_days'] = line.split(':', 1)[-1].split('：', 1)[-1].strip()

        # 如果没有解析到解封时间，尝试从文本中提取日期
        if 'ban_end' not in result:
            # 尝试匹配多种日期格式
            date_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日(?:\d{1,2}时\d{1,2}分\d{1,2}秒)?)',  # 2026年3月1日9时8分28秒
                r'(\d{4}-\d{1,2}-\d{1,2}(?: \d{1,2}:\d{1,2}:\d{1,2})?)',  # 2026-3-26 1:10:22
                r'(\d{4}/\d{1,2}/\d{1,2}(?: \d{1,2}:\d{1,2}:\d{1,2})?)',  # 2026/03/01 09:08:28
                r'(\d{4}\.\d{1,2}\.\d{1,2}(?: \d{1,2}:\d{1,2}:\d{1,2})?)',  # 2026.3.1 9:8:28
            ]
            for pattern in date_patterns:
                m = re.search(pattern, text)
                if m:
                    result['ban_end'] = m.group(1)
                    break

        # 如果没有封号类型，设置默认值
        if 'ban_type' not in result and 'ban_end' in result:
            result['ban_type'] = '封号'

        return result

    def force_close_game(self) -> dict:
        """一键关闭：断开连接 + 重置登录状态 + 杀掉所有 LOL 相关进程"""
        try:
            # 断开 LCU 连接
            self.disconnect()
            # 重置登录状态
            self.login_service._update('idle', '', 0)
            self.login_service._ban_info = ''
            # 杀掉所有 LOL / Riot / 登录器进程
            self.login_service._kill_launcher_processes()
            log.info("一键关闭：已断开连接并终止所有游戏进程")
            return {'success': True, 'message': '已关闭游戏'}
        except Exception as e:
            log.error("一键关闭失败: %s", e)
            return {'success': False, 'message': str(e)}

    def start_login(self, qq: str = '', password: str = '', server_index: int = 0,
                    game_path: str = '', account_id: str = '') -> dict:
        """启动登录"""
        self._ban_saved = False  # 重置封号保存标志
        self._last_login_status_signature = None
        self._current_login_account_id = None
        # 如果传了 account_id，从账号管理器读取
        if account_id:
            acct = self.account_manager.get_account(account_id)
            if not acct:
                return {'success': False, 'message': '账号不存在'}
            qq = acct['qq']
            password = acct['password']
            server_index = acct.get('server_index', 0)
            game_path = game_path or acct.get('game_path', '')
            self._current_login_account_id = account_id
        else:
            # 通过 QQ 号查找对应的 account_id
            for a in self.account_manager.list_accounts():
                if a.get('qq') == qq:
                    self._current_login_account_id = a.get('id')
                    break
            if not self._current_login_account_id:
                log.warning("start_login 未找到 account_id，qq=%s，封号信息可能无法落库", qq)

        if not game_path:
            game_path = detect_game_path()
        if not game_path:
            return {'success': False, 'message': '未检测到游戏路径，请手动指定'}

        if self._current_login_account_id:
            try:
                self.account_manager.mark_login_result(self._current_login_account_id, 'logging_in', '登录流程已启动')
            except Exception:
                pass
        return self.login_service.start_login(qq, password, server_index, game_path)

    # ========== 账号管理 ==========

    def get_accounts(self) -> list:
        """获取已保存账号列表"""
        return self.account_manager.list_accounts()

    def add_account(self, qq: str, password: str, nickname: str = '',
                    server_index: int = 0, game_path: str = '') -> dict:
        """添加账号"""
        return self.account_manager.add_account(qq, password, nickname, server_index, game_path)

    def update_account(self, account_id: str, qq: str = '', password: str = '',
                       nickname: str = '', server_index: int = -1, game_path: str = None) -> dict:
        """更新账号"""
        kwargs = {}
        if qq:
            kwargs['qq'] = qq
        if password:
            kwargs['password'] = password
        if nickname:
            kwargs['nickname'] = nickname
        if server_index >= 0:
            kwargs['server_index'] = server_index
        if game_path is not None:
            kwargs['game_path'] = game_path
        return self.account_manager.update_account(account_id, **kwargs)

    def delete_account(self, account_id: str) -> dict:
        """删除账号"""
        return self.account_manager.delete_account(account_id)

    def set_default_account(self, account_id: str) -> dict:
        """设置默认账号"""
        return self.account_manager.set_default_account(account_id)

    def focus_login_captcha(self) -> dict:
        """尝试将当前验证码窗口置前"""
        return self.login_service.focus_captcha_window()
