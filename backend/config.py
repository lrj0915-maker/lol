"""Configuration manager with deep-merge, migration and atomic write."""

import atexit
import copy
import json
import os
import tempfile
import threading
from threading import RLock

from logger import get_logger
from paths import get_app_root

log = get_logger("Config")

CONFIG_DIR = os.path.join(get_app_root(), "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CONFIG_VERSION = 2

DEFAULT_CONFIG = {
    "meta": {
        "config_version": CONFIG_VERSION,
    },
    "auto_accept": {
        "enabled": False,
        "delay_min": 1,
        "delay_max": 3,
    },
    "auto_select": {
        "enabled": False,
        "oneshot": True,
        "ban": [],
        "pick": [],
    },
    "chat": {
        "auto_send": False,
        "send_my_team": True,
        "send_enemy": True,
        "hotkey": "F1",
    },
    "ingame_chat": {
        "enabled": False,
    },
    "auto_friends": [
        {"name": "friend_a", "tag": "51953"},
        {"name": "friend_b", "tag": "52962"},
        {"name": "friend_c", "tag": "58389"},
    ],
    "auto_disenchant": False,
    "jungle_monitor": {
        "region": {
            "x": 50,
            "y": 50,
            "width": 400,
            "height": 80,
        },
        "interval": 500,
        "duplicate_interval": 5,
        "notify_mode": "both",
    },
    "settings_lock": {
        "enabled": False,
        "auto_restore": True,
        "game_path": "",
        "last_save_at": "",
    },
}


def _is_dict(value):
    return isinstance(value, dict)


def _deep_merge(base, override):
    if not _is_dict(base):
        return copy.deepcopy(override)

    result = copy.deepcopy(base)
    if not _is_dict(override):
        return result

    for key, value in override.items():
        if key in result and _is_dict(result[key]) and _is_dict(value):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Config:
    def __init__(self):
        self._lock = RLock()
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._dirty = False
        self._save_timer = None
        self._ensure_dir()
        self._load()

    def _ensure_dir(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)

    def _migrate(self, payload):
        if not _is_dict(payload):
            return copy.deepcopy(DEFAULT_CONFIG)

        migrated = _deep_merge(DEFAULT_CONFIG, payload)
        meta = migrated.setdefault("meta", {})
        version = int(meta.get("config_version") or 1)

        if version < 2:
            auto_select = migrated.setdefault("auto_select", {})
            auto_select["enabled"] = bool(auto_select.get("enabled", False))
            auto_select["oneshot"] = bool(auto_select.get("oneshot", True))
            auto_select["ban"] = list(auto_select.get("ban") or [])
            auto_select["pick"] = list(auto_select.get("pick") or [])
            meta["config_version"] = 2

        return _deep_merge(DEFAULT_CONFIG, migrated)

    def _load(self):
        with self._lock:
            if not os.path.exists(CONFIG_FILE):
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self._dirty = True
                self.save()
                return

            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self._config = self._migrate(payload)
                self._dirty = True
                self.save()
            except Exception as error:
                log.error("Failed to load config, fallback to defaults: %s", error)
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self._dirty = True
                self.save()

    def _flush_to_disk(self):
        with self._lock:
            if not self._dirty:
                return

            temp_fd, temp_path = tempfile.mkstemp(
                prefix="config-",
                suffix=".tmp",
                dir=CONFIG_DIR,
            )
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
                    json.dump(self._config, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())

                os.replace(temp_path, CONFIG_FILE)
                self._dirty = False
                self._save_timer = None
            except Exception as error:
                log.error("Failed to write config: %s", error)
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def save(self):
        self._flush_to_disk()

    def _schedule_save(self, delay_seconds: float = 0.2):
        with self._lock:
            if self._save_timer:
                try:
                    self._save_timer.cancel()
                except Exception:
                    pass
                self._save_timer = None

            timer = threading.Timer(max(0.0, float(delay_seconds)), self._flush_to_disk)
            timer.daemon = True
            self._save_timer = timer
            timer.start()

    def get(self, key, default=None):
        with self._lock:
            keys = key.split(".")
            value = self._config
            for current in keys:
                if isinstance(value, dict) and current in value:
                    value = value[current]
                else:
                    return default
            return copy.deepcopy(value)

    def set(self, key, value):
        with self._lock:
            keys = key.split(".")
            config = self._config
            for current in keys[:-1]:
                if current not in config or not isinstance(config[current], dict):
                    config[current] = {}
                config = config[current]
            config[keys[-1]] = copy.deepcopy(value)
            self._dirty = True
            self._schedule_save(0.2)


config = Config()
atexit.register(config.save)
