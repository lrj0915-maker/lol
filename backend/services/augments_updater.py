import json
import os
import re
import tempfile
import threading
import time
from typing import Any

import requests

from logger import get_logger

_log = get_logger('AugmentsDataService')

_AUGMENT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

_RARITY_TO_TIER = {
    1: 'silver',
    4: 'gold',
    8: 'prismatic',
    16: 'prismatic',
}


class AugmentsDataService:
    def __init__(self, app_root: str, resource_root: str = '', stale_days: int = 3, check_interval_seconds: int = 900):
        self.app_root = app_root
        self.resource_root = resource_root or app_root
        self.augments_path = os.path.join(app_root, 'data', 'augments.json')
        self.stale_days = stale_days
        self.check_interval_seconds = check_interval_seconds

        self._lock = threading.RLock()
        self._cached_data: dict[str, Any] | None = None
        self._cached_mtime: float | None = None
        self._updating = False
        self._last_update_error: str | None = None
        self._last_update_started_at: float | None = None
        self._last_update_finished_at: float | None = None
        self._scheduler_started = False

    def start_scheduler(self):
        if self._scheduler_started:
            return
        self._scheduler_started = True
        thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        thread.start()

    def _scheduler_loop(self):
        while True:
            try:
                status = self.get_status()
                if status.get('exists') and status.get('is_stale') and not status.get('is_updating'):
                    self.trigger_update(reason='auto-stale')
            except Exception as e:
                _log.error("强化数据定时检查异常: %s", e)
            time.sleep(self.check_interval_seconds)

    def _load_file(self, force_reload: bool = False):
        with self._lock:
            if not os.path.exists(self.augments_path):
                self._cached_data = None
                self._cached_mtime = None
                return None, None

            file_mtime = os.path.getmtime(self.augments_path)
            if (
                not force_reload
                and self._cached_data is not None
                and self._cached_mtime is not None
                and abs(file_mtime - self._cached_mtime) < 1e-6
            ):
                return self._cached_data, file_mtime

            with open(self.augments_path, 'r', encoding='utf-8') as handle:
                parsed = json.load(handle)

            self._cached_data = parsed
            self._cached_mtime = file_mtime
            return parsed, file_mtime

    def _build_meta(self, file_mtime: float):
        now = time.time()
        age_days = (now - file_mtime) / 86400
        return {
            'last_update': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime)),
            'days_old': round(age_days, 1),
            'is_stale': age_days > self.stale_days,
            'file_path': self.augments_path,
            'file_mtime': file_mtime,
            'is_updating': self._updating,
            'last_update_error': self._last_update_error,
            'last_update_started_at': self._last_update_started_at,
            'last_update_finished_at': self._last_update_finished_at,
        }

    def get_data(self, force_reload: bool = False):
        try:
            data, file_mtime = self._load_file(force_reload=force_reload)
            if not data or file_mtime is None:
                return {'error': '强化数据文件不存在'}

            payload = dict(data)
            payload['_meta'] = self._build_meta(file_mtime)
            return payload
        except Exception as exc:
            return {'error': str(exc)}

    def get_status(self):
        if not os.path.exists(self.augments_path):
            return {
                'exists': False,
                'is_updating': self._updating,
                'last_update_error': self._last_update_error,
                'file_path': self.augments_path,
            }

        file_mtime = os.path.getmtime(self.augments_path)
        meta = self._build_meta(file_mtime)
        meta['exists'] = True
        return meta

    def trigger_update(self, reason: str = 'manual'):
        with self._lock:
            if self._updating:
                return {'success': False, 'message': '强化更新任务已在执行中'}
            self._updating = True
            self._last_update_error = None
            self._last_update_started_at = time.time()

        thread = threading.Thread(target=self._run_bulk_fetch, args=(reason,), daemon=True)
        thread.start()
        return {'success': True, 'message': f'已触发强化更新任务（{reason}）'}

    def _load_champion_list(self) -> list[dict]:
        """从 frontend/src/data/champions.js 加载英雄列表。"""
        champions_js = os.path.join(self.resource_root, 'frontend', 'src', 'data', 'champions.js')
        if not os.path.exists(champions_js):
            _log.warning("英雄列表文件不存在: %s", champions_js)
            return []
        source = open(champions_js, 'r', encoding='utf-8', errors='ignore').read()
        pattern = re.compile(r"\{\s*id:\s*(\d+)\s*,\s*key:\s*'([^']+)'", re.MULTILINE)
        champions = []
        seen_ids = set()
        for m in pattern.finditer(source):
            cid = int(m.group(1))
            if cid not in seen_ids:
                seen_ids.add(cid)
                champions.append({'id': cid, 'key': m.group(2)})
        return champions

    @staticmethod
    def _load_augment_mapping(timeout_seconds: int = 15) -> tuple[dict, dict]:
        """从 CDragon 加载强化 id->name 和 id->tier 映射。"""
        url = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/cherry-augments.json'
        resp = requests.get(url, headers=_AUGMENT_HEADERS, timeout=timeout_seconds)
        resp.raise_for_status()
        id_to_name = {}
        id_to_tier = {}
        for aug in resp.json():
            aid = aug.get('id')
            name = aug.get('nameTRA') or aug.get('name')
            if not aid or not name:
                continue
            id_to_name[int(aid)] = str(name)
            rarity = str(aug.get('rarity', '')).lower()
            if 'prismatic' in rarity:
                id_to_tier[int(aid)] = 'prismatic'
            elif 'silver' in rarity:
                id_to_tier[int(aid)] = 'silver'
            else:
                id_to_tier[int(aid)] = 'gold'
        return id_to_name, id_to_tier

    @staticmethod
    def _fetch_one_champion(champion_key: str, region: str, timeout_seconds: int = 15, retries: int = 2) -> dict | None:
        """拉取单个英雄的强化数据。"""
        url = f'https://lol-api-champion.op.gg/api/{region}/champions/arena/{champion_key.lower()}'
        for attempt in range(1, max(1, retries) + 1):
            try:
                resp = requests.get(url, headers=_AUGMENT_HEADERS, timeout=timeout_seconds)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code in (404, 422):
                    return None
                if resp.status_code == 429:
                    time.sleep(min(2.0, 0.4 * attempt))
            except Exception:
                time.sleep(min(2.0, 0.4 * attempt))
        return None

    @staticmethod
    def _parse_augments(api_payload: dict, id_to_name: dict, id_to_tier: dict) -> dict:
        """解析强化数据。"""
        result = {'silver': [], 'gold': [], 'prismatic': []}
        data = (api_payload or {}).get('data') or {}
        for group in data.get('augment_group') or []:
            rarity_value = int(group.get('rarity') or 0)
            group_tier = _RARITY_TO_TIER.get(rarity_value, 'gold')
            for aug in group.get('augments') or []:
                aid = int(aug.get('id') or 0)
                if aid <= 0:
                    continue
                tier = id_to_tier.get(aid, group_tier)
                if tier not in result:
                    tier = group_tier
                play = int(aug.get('play') or 0)
                win = int(aug.get('win') or 0)
                win_rate = (win / play * 100) if play > 0 else 0.0
                result[tier].append({
                    'id': aid,
                    'name': id_to_name.get(aid, f'Augment_{aid}'),
                    'pickRate': round(float(aug.get('pick_rate') or 0) * 100, 2),
                    'winRate': round(win_rate, 2),
                    'games': play,
                })
        for tier in ('silver', 'gold', 'prismatic'):
            result[tier].sort(key=lambda x: (x.get('winRate', 0), x.get('games', 0)), reverse=True)
        return result

    @staticmethod
    def _parse_items(api_payload: dict) -> dict:
        data = (api_payload or {}).get('data') or {}
        return {
            'core': data.get('core_items') or [],
            'boots': data.get('boots') or [],
            'starter': data.get('starter_items') or [],
        }

    @staticmethod
    def _parse_summary(api_payload: dict) -> dict:
        data = (api_payload or {}).get('data') or {}
        summary = data.get('summary') or {}
        avg = summary.get('average_stats') or {}
        play = int(avg.get('play') or 0)
        win_rate = float(avg.get('win_rate') or 0)
        if play > 0 and win_rate <= 0:
            win_rate = float(avg.get('win') or 0) / play
        return {
            'play': play,
            'win_rate': round(win_rate * 100, 2),
            'pick_rate': round(float(avg.get('pick_rate') or 0) * 100, 2),
            'ban_rate': round(float(avg.get('ban_rate') or 0) * 100, 2),
        }

    def _atomic_write_json(self, target_path: str, payload: dict):
        """原子写入 JSON 文件。"""
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix='augments-', suffix='.tmp', dir=target_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _run_bulk_fetch(self, reason: str):
        """全量拉取强化数据（内嵌执行，不依赖外部脚本）。"""
        try:
            champions = self._load_champion_list()
            if not champions:
                raise RuntimeError('未找到英雄列表')

            region = 'GLOBAL'
            sleep_interval = 0.25
            timeout_seconds = 15
            retries = 2

            id_to_name, id_to_tier = self._load_augment_mapping(timeout_seconds)
            _log.info("开始拉取强化数据: 英雄=%d mapping=%d", len(champions), len(id_to_name))

            result = {
                'version': time.strftime('%Y.%m.%d'),
                'updateTime': time.strftime('%Y-%m-%d %H:%M:%S'),
                'meta': {
                    'region': region,
                    'source': 'OP.GG arena API',
                    'source_type': 'api',
                    'mode': 'arena',
                    'is_official': True,
                    'champions': len(champions),
                },
                'data': {},
            }

            success_count = 0
            fail_count = 0
            discovered_version = ''

            for idx, champion in enumerate(champions, start=1):
                cid = str(champion['id'])
                ckey = str(champion['key'])
                payload = self._fetch_one_champion(ckey, region, timeout_seconds, retries)
                if not payload:
                    fail_count += 1
                    _log.debug("[%d/%d] %s NO_DATA", idx, len(champions), ckey)
                    time.sleep(max(0.0, sleep_interval))
                    continue

                if not discovered_version:
                    discovered_version = str((payload.get('meta') or {}).get('version') or '')

                augments = self._parse_augments(payload, id_to_name, id_to_tier)
                result['data'][cid] = {
                    'key': ckey.lower(),
                    'summary': self._parse_summary(payload),
                    'augments': augments,
                    'items': self._parse_items(payload),
                }
                success_count += 1
                time.sleep(max(0.0, sleep_interval))

            if discovered_version:
                result['version'] = discovered_version

            self._atomic_write_json(self.augments_path, result)

            with self._lock:
                self._cached_data = None
                self._cached_mtime = None
                self._last_update_error = None
                self._last_update_finished_at = time.time()

            _log.info("强化数据更新完成: success=%d failed=%d total=%d",
                      success_count, fail_count, len(champions))
        except Exception as exc:
            _log.error("强化数据更新异常: %s", exc, exc_info=True)
            with self._lock:
                self._last_update_error = f'{reason}: {exc}'
                self._last_update_finished_at = time.time()
        finally:
            with self._lock:
                self._updating = False
