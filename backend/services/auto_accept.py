"""自动准备服务"""
import random
import threading
import time

from config import config

# Constants
READY_CHECK_STATE_IN_PROGRESS = 'InProgress'
PLAYER_RESPONSE_NONE = 'None'


class AutoAcceptService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._enabled = config.get('auto_accept.enabled', True)  # 默认开启
        self._delay_min = config.get('auto_accept.delay_min', 1)
        self._delay_max = config.get('auto_accept.delay_max', 3)
        self._pending_accept = False
        self._pending_lock = threading.RLock()
        self._last_ready_check_id = None

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        config.set('auto_accept.enabled', value)

    def start(self):
        """启动服务，订阅事件"""
        self.events.subscribe('/lol-matchmaking/v1/ready-check', self._on_ready_check)

    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-matchmaking/v1/ready-check', self._on_ready_check)

    def _on_ready_check(self, uri, data):
        """处理准备检查事件"""
        if not self._enabled or not data:
            return

        state = data.get('state')
        player_response = data.get('playerResponse')

        # 检测到准备检查且玩家未响应
        if state == READY_CHECK_STATE_IN_PROGRESS and player_response == PLAYER_RESPONSE_NONE:
            ready_check_id = data.get('id') or data.get('timer') or data.get('state')
            with self._pending_lock:
                if ready_check_id and ready_check_id == self._last_ready_check_id:
                    return
                if self._pending_accept:
                    return
                self._last_ready_check_id = ready_check_id
                self._pending_accept = True
            threading.Thread(target=self._delayed_accept, daemon=True).start()

    def _delayed_accept(self):
        """延迟接受"""
        delay = random.uniform(self._delay_min, self._delay_max)
        time.sleep(delay)
        
        if self._enabled:
            self.api.accept_match()

        with self._pending_lock:
            self._pending_accept = False
