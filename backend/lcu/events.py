"""LCU WebSocket 事件监听"""
import json
import threading
import ssl
import websocket


class LCUEvents:
    def __init__(self, connection):
        self.conn = connection
        self._ws = None
        self._thread = None
        self._running = False
        self._callbacks = {}

    def subscribe(self, event_uri, callback):
        """订阅事件"""
        if event_uri not in self._callbacks:
            self._callbacks[event_uri] = []
        self._callbacks[event_uri].append(callback)

    def unsubscribe(self, event_uri, callback=None):
        """取消订阅"""
        if event_uri in self._callbacks:
            if callback:
                self._callbacks[event_uri].remove(callback)
            else:
                del self._callbacks[event_uri]

    def start(self):
        """启动事件监听"""
        if self._running or not self.conn.is_connected:
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """停止事件监听"""
        self._running = False
        if self._ws:
            self._ws.close()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        """WebSocket 运行循环"""
        ws_url = f'wss://127.0.0.1:{self.conn.port}'
        
        self._ws = websocket.WebSocketApp(
            ws_url,
            header=[f'Authorization: {self.conn.auth_header["Authorization"]}'],
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self._ws.run_forever(
            sslopt={'cert_reqs': ssl.CERT_NONE},
            skip_utf8_validation=True
        )

    def _on_open(self, ws):
        """连接建立"""
        # 订阅所有事件
        ws.send(json.dumps([5, 'OnJsonApiEvent']))

    def _on_message(self, ws, message):
        """收到消息"""
        try:
            data = json.loads(message)
            if isinstance(data, list) and len(data) >= 3:
                event_type, event_name, payload = data[0], data[1], data[2]
                if event_type == 8 and isinstance(payload, dict):
                    uri = payload.get('uri', '')
                    event_data = payload.get('data')
                    self._dispatch(uri, event_data)
        except Exception:
            pass

    def _on_error(self, ws, error):
        """连接错误"""
        pass

    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        self._running = False

    def _dispatch(self, uri, data):
        """分发事件"""
        for pattern, callbacks in self._callbacks.items():
            if uri.startswith(pattern) or pattern == '*':
                for callback in callbacks:
                    try:
                        callback(uri, data)
                    except Exception:
                        pass
