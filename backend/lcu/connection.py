"""LCU 客户端连接管理"""
import os
import re
import base64
import psutil
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LCUConnection:
    def __init__(self):
        self.port = None
        self.token = None
        self.protocol = 'https'
        self._session = None

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
        if self._session is None:
            self._session = requests.Session()
            self._session.verify = False
            if self.auth_header:
                self._session.headers.update(self.auth_header)
        return self._session

    def connect(self):
        """尝试连接到 LCU 客户端"""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] == 'LeagueClientUx.exe':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    port_match = re.search(r'--app-port=(\d+)', cmdline)
                    token_match = re.search(r'--remoting-auth-token=([\w-]+)', cmdline)
                    
                    if port_match and token_match:
                        self.port = port_match.group(1)
                        self.token = token_match.group(1)
                        self._session = None
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        self.port = None
        self.token = None
        self._session = None
        return False

    def disconnect(self):
        """断开连接"""
        self.port = None
        self.token = None
        if self._session:
            self._session.close()
            self._session = None

    def get(self, endpoint):
        """GET 请求"""
        if not self.is_connected:
            return None
        try:
            resp = self.session.get(f'{self.base_url}{endpoint}')
            return resp.json() if resp.ok else None
        except Exception:
            return None

    def post(self, endpoint, data=None):
        """POST 请求"""
        if not self.is_connected:
            return None
        try:
            resp = self.session.post(f'{self.base_url}{endpoint}', json=data)
            return resp.json() if resp.ok and resp.text else resp.ok
        except Exception:
            return None

    def patch(self, endpoint, data=None):
        """PATCH 请求"""
        if not self.is_connected:
            return None
        try:
            resp = self.session.patch(f'{self.base_url}{endpoint}', json=data)
            return resp.json() if resp.ok and resp.text else resp.ok
        except Exception:
            return None
