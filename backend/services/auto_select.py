"""自动选人服务"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import config


class AutoSelectService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._enabled = config.get('auto_select.enabled', False)
        self._ban_list = config.get('auto_select.ban', [])
        self._pick_list = config.get('auto_select.pick', [])

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        config.set('auto_select.enabled', value)

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

                if action_type == 'ban':
                    self._handle_ban(action_id)
                elif action_type == 'pick':
                    self._handle_pick(action_id)

    def _handle_ban(self, action_id):
        """处理 Ban 阶段"""
        if not self._ban_list:
            return

        bannable = self.api.get_bannable_champions() or []
        
        for champion_id in self._ban_list:
            if champion_id in bannable:
                self.api.lock_champion(action_id, champion_id)
                return

    def _handle_pick(self, action_id):
        """处理 Pick 阶段"""
        if not self._pick_list:
            return

        pickable = self.api.get_pickable_champions() or []
        
        for champion_id in self._pick_list:
            if champion_id in pickable:
                self.api.lock_champion(action_id, champion_id)
                return
