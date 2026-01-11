"""配置管理"""
import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

DEFAULT_CONFIG = {
    'auto_accept': {
        'enabled': False,
        'delay_min': 1,
        'delay_max': 3
    },
    'auto_select': {
        'enabled': False,
        'ban': [],
        'pick': []
    }
}


class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self._ensure_dir()
        self._load()

    def _ensure_dir(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

    def _load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = DEFAULT_CONFIG.copy()

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()


config = Config()
