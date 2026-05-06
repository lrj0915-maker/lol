"""LCU WebSocket 事件监听"""
import json
import ssl
import threading
import time
import queue

import websocket

from logger import get_logger

_log = get_logger('LCUEvents')


class LCUEvents:
    def __init__(self, connection, reconnect_interval=2.0):
        self.conn = connection
        self._ws = None
        self._thread = None
        self._running = False
        self._callbacks = {}
        self._cb_lock = threading.RLock()  # 保护 _callbacks 的读写
        self._reconnect_interval = reconnect_interval
        self._reconnect_max = 30.0
        self._reconnect_consecutive_fails = 0
        self._event_queue = queue.Queue(maxsize=1200)
        self._worker_thread = None
        self._last_event_ts = {}
        self._coalesce_window = 0.12
        # 关键事件不做合并，避免丢失选人阶段的快速状态变更
        self._no_coalesce_prefixes = (
            '/lol-gameflow/v1/',
            '/lol-champ-select/',
            '/lol-matchmaking/v1/ready-check',
        )

    def subscribe(self, event_uri, callback):
        """订阅事件"""
        with self._cb_lock:
            if event_uri not in self._callbacks:
                self._callbacks[event_uri] = []
            if callback not in self._callbacks[event_uri]:
                self._callbacks[event_uri].append(callback)

    def unsubscribe(self, event_uri, callback=None):
        """取消订阅"""
        with self._cb_lock:
            if event_uri not in self._callbacks:
                return

            if callback is None:
                del self._callbacks[event_uri]
                return

            try:
                self._callbacks[event_uri].remove(callback)
            except ValueError:
                pass

            if not self._callbacks[event_uri]:
                del self._callbacks[event_uri]

    def start(self):
        """启动事件监听"""
        if self._running:
            return False

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """停止事件监听"""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
            self._worker_thread = None

    def _enqueue_event(self, uri, data):
        now = time.time()
        # 关键事件跳过合并窗口，确保不丢失快速连续的状态变更
        skip_coalesce = any(uri.startswith(prefix) for prefix in self._no_coalesce_prefixes)
        if not skip_coalesce:
            last = self._last_event_ts.get(uri, 0.0)
            if now - last < self._coalesce_window:
                return
        self._last_event_ts[uri] = now
        try:
            self._event_queue.put_nowait((uri, data))
        except queue.Full:
            try:
                self._event_queue.get_nowait()
            except Exception:
                pass
            try:
                self._event_queue.put_nowait((uri, data))
            except Exception:
                pass

    def _worker_loop(self):
        while self._running:
            try:
                uri, data = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._dispatch(uri, data)
            except Exception as e:
                _log.error("事件分发异常 uri=%s: %s", uri, e)

    def _run_loop(self):
        """维持 websocket 连接，断线自动重连（指数退避）"""
        while self._running:
            if not self.conn.ensure_connected():
                self._reconnect_consecutive_fails += 1
                delay = min(
                    self._reconnect_max,
                    self._reconnect_interval * (2 ** min(self._reconnect_consecutive_fails - 1, 5)),
                )
                time.sleep(delay)
                continue

            ws_url = f'wss://127.0.0.1:{self.conn.port}'
            auth = self.conn.auth_header or {}
            auth_header = auth.get('Authorization')
            if not auth_header:
                self._reconnect_consecutive_fails += 1
                delay = min(
                    self._reconnect_max,
                    self._reconnect_interval * (2 ** min(self._reconnect_consecutive_fails - 1, 5)),
                )
                time.sleep(delay)
                continue

            self._ws = websocket.WebSocketApp(
                ws_url,
                header=[f'Authorization: {auth_header}'],
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            try:
                self._ws.run_forever(
                    sslopt={'cert_reqs': ssl.CERT_NONE},
                    skip_utf8_validation=True,
                    ping_interval=20,
                    ping_timeout=10,
                )
            except Exception:
                pass
            finally:
                self._ws = None

            if self._running:
                self._reconnect_consecutive_fails += 1
                delay = min(
                    self._reconnect_max,
                    self._reconnect_interval * (2 ** min(self._reconnect_consecutive_fails - 1, 5)),
                )
                time.sleep(delay)

    def _on_open(self, ws):
        """连接建立"""
        self._reconnect_consecutive_fails = 0
        try:
            ws.send(json.dumps([5, 'OnJsonApiEvent']))
        except Exception:
            pass

    def _on_message(self, ws, message):
        """收到消息"""
        try:
            data = json.loads(message)
            if not (isinstance(data, list) and len(data) >= 3):
                return

            event_type, payload = data[0], data[2]
            if event_type != 8 or not isinstance(payload, dict):
                return

            uri = payload.get('uri', '')
            event_data = payload.get('data')
            self._enqueue_event(uri, event_data)
        except Exception:
            pass

    def _on_error(self, ws, error):
        """连接错误（不主动 disconnect，由 _run_loop 处理重连）"""
        _log.debug("WebSocket 错误: %s", error)

    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭（不主动 disconnect，由 _run_loop 处理重连）"""
        _log.debug("WebSocket 关闭: code=%s, msg=%s", close_status_code, close_msg)

    def _dispatch(self, uri, data):
        """分发事件"""
        with self._cb_lock:
            snapshot = [(pattern, list(callbacks)) for pattern, callbacks in self._callbacks.items()]

        for pattern, callbacks in snapshot:
            if not (uri.startswith(pattern) or pattern == '*'):
                continue

            for callback in callbacks:
                try:
                    callback(uri, data)
                except Exception as e:
                    _log.error("事件回调异常 uri=%s callback=%s: %s",
                               uri, getattr(callback, '__name__', callback), e)
