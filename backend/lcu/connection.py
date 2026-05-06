"""LCU client connection and resilient request layer."""
import base64
import re
import threading
import time

import psutil
import requests
import urllib3

from logger import get_logger

log = get_logger('LCU')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
PROCESS_NAME = 'LeagueClientUx.exe'
PORT_PATTERN = re.compile(r'--app-port=(\d+)')
TOKEN_PATTERN = re.compile(r'--remoting-auth-token=([\w-]+)')


class LCUConnection:
    def __init__(self):
        self.port = None
        self.token = None
        self.protocol = 'https'
        self._session = None

        self._state_lock = threading.RLock()
        self._alive_cache_value = False
        self._alive_cache_until = 0.0
        self._alive_cache_ttl = 1.2

    @property
    def is_connected(self):
        return self.port is not None and self.token is not None

    @property
    def base_url(self):
        if not self.is_connected:
            return None
        return f'{self.protocol}://127.0.0.1:{self.port}'

    @property
    def auth_header(self):
        if not self.token:
            return None
        encoded = base64.b64encode(f'riot:{self.token}'.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}

    @property
    def session(self):
        with self._state_lock:
            if self._session is None:
                self._session = requests.Session()
                self._session.verify = False
                if self.auth_header:
                    self._session.headers.update(self.auth_header)
            return self._session

    def _mark_alive(self, alive: bool, ttl: float | None = None):
        effective_ttl = self._alive_cache_ttl if ttl is None else max(0.0, float(ttl))
        self._alive_cache_value = bool(alive)
        self._alive_cache_until = time.time() + effective_ttl

    def connect(self, max_attempts=3, interval=1.0):
        """Try to connect to LCU by scanning LeagueClientUx process args.

        Args:
            max_attempts: How many times to scan process list before giving up.
            interval: Seconds to wait between scans.
        """
        with self._state_lock:
            for attempt in range(max_attempts):
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if proc.info['name'] != PROCESS_NAME:
                            continue

                        cmdline = proc.info['cmdline'] or []
                        port = None
                        token = None

                        for arg in cmdline:
                            if not port:
                                port_match = PORT_PATTERN.search(arg)
                                if port_match:
                                    port = port_match.group(1)
                            if not token:
                                token_match = TOKEN_PATTERN.search(arg)
                                if token_match:
                                    token = token_match.group(1)
                            if port and token:
                                break

                        if port and token:
                            self.port = port
                            self.token = token
                            if self._session:
                                self._session.close()
                            self._session = None
                            self._mark_alive(True, ttl=0.4)
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if attempt < max_attempts - 1:
                    time.sleep(interval)

            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect and clear in-memory auth/session state."""
        with self._state_lock:
            self.port = None
            self.token = None
            if self._session:
                self._session.close()
                self._session = None
            self._mark_alive(False, ttl=0.2)

    def check_alive(self, timeout=1.5, force_probe=False):
        """Check whether current LCU credentials/session are alive."""
        if not self.is_connected:
            return False

        now = time.time()
        if not force_probe and now < self._alive_cache_until:
            return self._alive_cache_value

        try:
            resp = self.session.get(f'{self.base_url}/lol-gameflow/v1/gameflow-phase', timeout=timeout)
            alive = bool(resp.ok)
            self._mark_alive(alive)
            return alive
        except Exception:
            self._mark_alive(False, ttl=0.2)
            return False

    def ensure_connected(self, force_probe=False):
        """Ensure at least one usable connection/auth pair exists."""
        if not self.is_connected:
            return self.connect()

        if not force_probe:
            return True

        if self.check_alive(force_probe=True):
            return True

        self.disconnect()
        return self.connect()

    def _request_once(self, method, url, data=None):
        try:
            if method == 'GET':
                return self.session.get(url, timeout=3)
            if method == 'POST':
                return self.session.post(url, json=data, timeout=3)
            if method == 'PATCH':
                return self.session.patch(url, json=data, timeout=3)
            if method == 'DELETE':
                return self.session.delete(url, timeout=3)
            if method == 'PUT':
                return self.session.put(url, json=data, timeout=3)
        except requests.Timeout:
            log.debug("请求超时: %s %s", method, url)
            return None
        except requests.ConnectionError as e:
            log.debug("连接错误: %s %s -> %s", method, url, e)
            return None
        except Exception as e:
            log.debug("请求异常: %s %s -> %s", method, url, e)
            return None
        return None

    def _request_with_reconnect(self, method, endpoint, data=None):
        if not self.ensure_connected(force_probe=False):
            log.debug("未连接到 LCU，跳过请求: %s %s", method, endpoint)
            return None

        url = f'{self.base_url}{endpoint}'
        resp = self._request_once(method, url, data=data)

        if resp is not None and resp.status_code not in (401, 403):
            self._mark_alive(True)
            return resp

        if resp is not None and resp.status_code in (401, 403):
            log.debug("认证失败 (%d): %s %s，尝试重连", resp.status_code, method, endpoint)

        self.disconnect()
        if not self.ensure_connected(force_probe=True):
            log.debug("重连失败: %s %s", method, endpoint)
            return None

        retry_url = f'{self.base_url}{endpoint}'
        retry_resp = self._request_once(method, retry_url, data=data)
        if retry_resp is not None and retry_resp.status_code not in (401, 403):
            self._mark_alive(True)
            return retry_resp

        log.debug("重试后仍失败: %s %s -> status=%s", method, endpoint,
                   retry_resp.status_code if retry_resp else 'None')
        self._mark_alive(False, ttl=0.3)
        return retry_resp

    def get(self, endpoint):
        """GET request returning parsed json or None."""
        resp = self._request_with_reconnect('GET', endpoint)
        if not resp or not resp.ok:
            return None
        try:
            return resp.json()
        except Exception:
            return None

    def _parse_mutation_response(self, resp):
        """Parse response for POST/PATCH/PUT (returns None/False/True/json)."""
        if not resp:
            return None
        if not resp.ok:
            return False
        if not resp.text:
            return True
        try:
            return resp.json()
        except Exception:
            return True

    def post(self, endpoint, data=None):
        """POST request returning bool/json/None."""
        resp = self._request_with_reconnect('POST', endpoint, data=data)
        return self._parse_mutation_response(resp)

    def patch(self, endpoint, data=None):
        """PATCH request returning bool/json/None."""
        resp = self._request_with_reconnect('PATCH', endpoint, data=data)
        return self._parse_mutation_response(resp)

    def delete(self, endpoint):
        """DELETE request returning bool/None."""
        resp = self._request_with_reconnect('DELETE', endpoint)
        if not resp:
            return None
        return bool(resp.ok)

    def put(self, endpoint, data=None):
        """PUT request returning bool/json/None."""
        resp = self._request_with_reconnect('PUT', endpoint, data=data)
        return self._parse_mutation_response(resp)
