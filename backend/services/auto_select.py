"""自动选人服务"""
import time
import threading

from config import config

# Constants
ACTION_TYPE_BAN = 'ban'
ACTION_TYPE_PICK = 'pick'


class AutoSelectService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._enabled = config.get('auto_select.enabled', False)
        self._oneshot = config.get('auto_select.oneshot', True)
        self._ban_list = config.get('auto_select.ban', [])
        self._pick_list = config.get('auto_select.pick', [])
        self._action_ttl_seconds = 120
        self._processed_actions = {}
        self._action_lock = threading.RLock()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        config.set('auto_select.enabled', value)

    @property
    def oneshot(self):
        return self._oneshot

    @oneshot.setter
    def oneshot(self, value):
        self._oneshot = bool(value)
        config.set('auto_select.oneshot', self._oneshot)

    def update_config(self, ban_list, pick_list):
        """更新配置"""
        self._ban_list = ban_list
        self._pick_list = pick_list

    def start(self):
        """启动服务"""
        self.events.subscribe('/lol-champ-select/v1/session', self._on_champ_select)

    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-champ-select/v1/session', self._on_champ_select)

    def _on_champ_select(self, uri, data):
        """处理选人阶段事件"""
        if not self._enabled or not data:
            return

        self._cleanup_processed_actions()

        # 获取本地玩家信息
        local_player_cell_id = data.get('localPlayerCellId')
        if local_player_cell_id is None:
            return

        # 获取当前动作
        actions = data.get('actions', [])
        for action_group in actions:
            for action in action_group:
                if action.get('actorCellId') != local_player_cell_id:
                    continue
                if not action.get('isInProgress'):
                    continue

                action_id = action.get('id')
                action_type = action.get('type')
                completed = action.get('completed')

                if completed:
                    continue

                if self._is_action_processed(action_id):
                    continue

                if action_type == ACTION_TYPE_BAN:
                    handled = self._handle_ban(action_id)
                    if handled:
                        self._mark_action_processed(action_id)
                elif action_type == ACTION_TYPE_PICK:
                    handled = self._handle_pick(action_id, data, local_player_cell_id)
                    if handled:
                        self._mark_action_processed(action_id)

    def _cleanup_processed_actions(self):
        now = time.time()
        with self._action_lock:
            expired = [aid for aid, ts in self._processed_actions.items() if now - ts > self._action_ttl_seconds]
            for aid in expired:
                self._processed_actions.pop(aid, None)

    def _is_action_processed(self, action_id):
        if action_id is None:
            return False
        with self._action_lock:
            return action_id in self._processed_actions

    def _mark_action_processed(self, action_id):
        if action_id is None:
            return
        with self._action_lock:
            self._processed_actions[action_id] = time.time()

    def _handle_ban(self, action_id):
        """处理 Ban 阶段"""
        if not self._ban_list:
            return False

        bannable = self.api.get_bannable_champions()
        if not bannable:
            return False

        for champion_id in self._ban_list:
            if champion_id in bannable:
                self.api.lock_champion(action_id, champion_id)
                return True
        return False

    def _handle_pick(self, action_id, session_data=None, local_player_cell_id=None):
        """处理 Pick 阶段"""
        if not self._pick_list:
            return False

        if session_data and local_player_cell_id is not None:
            for player in session_data.get('myTeam', []) or []:
                if player.get('cellId') != local_player_cell_id:
                    continue
                manual_choice = player.get('championId') or player.get('championPickIntent')
                if manual_choice and int(manual_choice) > 0:
                    return False

        pickable = self.api.get_pickable_champions()
        if not pickable:
            return False

        for champion_id in self._pick_list:
            if champion_id in pickable:
                self.api.lock_champion(action_id, champion_id)
                if self._oneshot:
                    self.enabled = False
                return True
        return False
