"""账号管理服务 - 多账号保存与读取"""
import json
import os
import base64
import time
import uuid
import tempfile
import threading


class AccountManager:
    """管理多个 QQ 登录账号"""

    # 旧区服顺序 index → 新区服顺序 index 的映射（仅 8-13 受影响）
    _SERVER_INDEX_MIGRATION = {8: 9, 9: 10, 10: 11, 11: 8, 12: 13, 13: 12}

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._file = os.path.join(data_dir, 'accounts.json')
        self._migrated_flag = os.path.join(data_dir, '.server_index_migrated')
        self._lock = threading.RLock()
        os.makedirs(data_dir, exist_ok=True)
        self._migrate_server_index()

    def _migrate_server_index(self):
        """一次性迁移：修正旧版区服顺序 index（8-13 错位）"""
        if os.path.exists(self._migrated_flag):
            return
        accounts = self._load()
        if not accounts:
            # 标记已迁移，避免重复检查
            with open(self._migrated_flag, 'w') as f:
                f.write('1')
            return
        changed = False
        for a in accounts:
            old_idx = a.get('server_index', 0)
            if old_idx in self._SERVER_INDEX_MIGRATION:
                a['server_index'] = self._SERVER_INDEX_MIGRATION[old_idx]
                changed = True
        if changed:
            self._save(accounts)
        with open(self._migrated_flag, 'w') as f:
            f.write('1')

    def _load(self) -> list:
        if not os.path.exists(self._file):
            return []
        try:
            with open(self._file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, accounts: list):
        """原子写：先写临时文件再 replace，防止写入中断导致数据丢失"""
        temp_fd, temp_path = tempfile.mkstemp(
            prefix='accounts-', suffix='.tmp', dir=self._data_dir
        )
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self._file)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    @staticmethod
    def _encode_pw(pw: str) -> str:
        return base64.b64encode(pw.encode('utf-8')).decode('ascii')

    @staticmethod
    def _decode_pw(encoded: str) -> str:
        try:
            return base64.b64decode(encoded.encode('ascii')).decode('utf-8')
        except Exception:
            return ''

    def list_accounts(self) -> list:
        """返回账号列表（含明文密码），按最后登录时间降序"""
        with self._lock:
            accounts = self._load()
            result = []
            for a in accounts:
                item = dict(a)
                item['password'] = self._decode_pw(item.get('password', ''))
                result.append(item)
            # 默认账号优先，其次按最近登录时间排序
            result.sort(
                key=lambda x: (
                    1 if x.get('is_default') else 0,
                    x.get('last_login', 0),
                    x.get('created_at', 0),
                ),
                reverse=True,
            )
            return result

    def get_account(self, account_id: str) -> dict | None:
        """获取单个账号（含明文密码，仅内部使用）"""
        with self._lock:
            for a in self._load():
                if a.get('id') == account_id:
                    item = dict(a)
                    item['password'] = self._decode_pw(item.get('password', ''))
                    return item
            return None

    def add_account(self, qq: str, password: str, nickname: str = '',
                    server_index: int = 0, game_path: str = '') -> dict:
        with self._lock:
            accounts = self._load()
            # 检查重复
            for a in accounts:
                if a.get('qq') == qq:
                    return {'success': False, 'message': f'账号 {qq} 已存在'}
            account = {
                'id': uuid.uuid4().hex[:8],
                'qq': qq,
                'password': self._encode_pw(password),
                'nickname': nickname or qq,
                'server_index': server_index,
                'game_path': game_path,
                'created_at': int(time.time()),
                'last_login': 0,
                'last_login_status': 'idle',
                'last_login_message': '',
                'is_default': False,
            }
            accounts.append(account)
            self._save(accounts)
            return {'success': True, 'id': account['id']}

    def update_account(self, account_id: str, **kwargs) -> dict:
        with self._lock:
            accounts = self._load()
            for a in accounts:
                if a.get('id') == account_id:
                    if 'qq' in kwargs:
                        a['qq'] = kwargs['qq']
                    if 'password' in kwargs and kwargs['password']:
                        a['password'] = self._encode_pw(kwargs['password'])
                    if 'nickname' in kwargs:
                        a['nickname'] = kwargs['nickname']
                    if 'server_index' in kwargs:
                        a['server_index'] = kwargs['server_index']
                    if 'game_path' in kwargs:
                        a['game_path'] = kwargs['game_path']
                    if 'summoner_name' in kwargs:
                        a['summoner_name'] = kwargs['summoner_name']
                    if 'ban_info' in kwargs:
                        a['ban_info'] = kwargs['ban_info']
                    if 'ban_time' in kwargs:
                        a['ban_time'] = kwargs['ban_time']
                    if 'ban_start' in kwargs:
                        a['ban_start'] = kwargs['ban_start']
                    if 'ban_end' in kwargs:
                        a['ban_end'] = kwargs['ban_end']
                    if 'ban_days' in kwargs:
                        a['ban_days'] = kwargs['ban_days']
                    if 'ban_type' in kwargs:
                        a['ban_type'] = kwargs['ban_type']
                    if 'last_login_status' in kwargs:
                        a['last_login_status'] = kwargs['last_login_status']
                    if 'last_login_message' in kwargs:
                        a['last_login_message'] = kwargs['last_login_message']
                    if 'is_default' in kwargs:
                        a['is_default'] = bool(kwargs['is_default'])
                    self._save(accounts)
                    return {'success': True}
            return {'success': False, 'message': '账号不存在'}

    def delete_account(self, account_id: str) -> dict:
        with self._lock:
            accounts = self._load()
            before = len(accounts)
            accounts = [a for a in accounts if a.get('id') != account_id]
            if len(accounts) == before:
                return {'success': False, 'message': '账号不存在'}
            self._save(accounts)
            return {'success': True}

    def touch_login(self, account_id: str):
        """更新最后登录时间"""
        with self._lock:
            accounts = self._load()
            for a in accounts:
                if a.get('id') == account_id:
                    a['last_login'] = int(time.time())
                    self._save(accounts)
                    return

    def mark_login_result(self, account_id: str, status: str, message: str = '') -> dict:
        with self._lock:
            accounts = self._load()
            for a in accounts:
                if a.get('id') == account_id:
                    a['last_login_status'] = status
                    a['last_login_message'] = message
                    if status == 'success':
                        a['last_login'] = int(time.time())
                    self._save(accounts)
                    return {'success': True}
            return {'success': False, 'message': '账号不存在'}

    def set_default_account(self, account_id: str) -> dict:
        with self._lock:
            accounts = self._load()
            found = False
            for a in accounts:
                is_target = a.get('id') == account_id
                a['is_default'] = is_target
                if is_target:
                    found = True
            if not found:
                return {'success': False, 'message': '账号不存在'}
            self._save(accounts)
            return {'success': True}
