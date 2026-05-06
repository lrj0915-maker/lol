import json
import os
import re
import threading
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logger import get_logger

_log = get_logger('RunesDataService')


class RunesDataService:
    VALID_POSITIONS = {'TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT'}
    POSITION_ORDER = ('TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT')
    DEFAULT_REGION = 'CN'
    REGION_ALIASES = {
        'CN': 'GLOBAL',
        'ZH': 'GLOBAL',
    }
    SUPPORTED_REGIONS = {
        'GLOBAL',
        'KR',
        'JP',
        'NA',
        'EUW',
        'EUNE',
        'BR',
        'LAN',
        'LAS',
        'OCE',
        'TR',
        'RU',
        'TW',
        'VN',
        'PH',
        'SG',
        'TH',
        'ME',
    }
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    def __init__(self, app_root: str, resource_root: str = '', stale_days: int = 7, check_interval_seconds: int = 600):
        self.app_root = app_root
        self.resource_root = resource_root or app_root
        self.runes_path = os.path.join(app_root, 'data', 'runes.json')
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
        self._inflight_refresh_keys: dict[str, float] = {}

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
                _log.error("符文数据定时检查异常: %s", e)
            time.sleep(self.check_interval_seconds)

    def _load_file(self, force_reload: bool = False):
        with self._lock:
            if not os.path.exists(self.runes_path):
                self._cached_data = None
                self._cached_mtime = None
                return None, None

            file_mtime = os.path.getmtime(self.runes_path)
            if (
                not force_reload
                and self._cached_data is not None
                and self._cached_mtime is not None
                and abs(file_mtime - self._cached_mtime) < 1e-6
            ):
                return self._cached_data, file_mtime

            with open(self.runes_path, 'r', encoding='utf-8') as handle:
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
            'file_path': self.runes_path,
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
                return {
                    'error': '符文数据文件不存在',
                    'message': '请运行 scripts/fetch_runes.py 获取数据',
                }

            payload = dict(data)
            payload['_meta'] = self._build_meta(file_mtime)
            return payload
        except json.JSONDecodeError as exc:
            return {
                'error': '符文数据文件格式错误',
                'message': f'JSON 解析失败: {exc}',
            }
        except Exception as exc:
            return {
                'error': '加载符文数据失败',
                'message': str(exc),
            }

    def get_entry(self, champion_id: int, position: str = 'MID', force_reload: bool = False):
        """Return one champion + position payload to avoid full-file transfer."""
        try:
            normalized_position = self._normalize_position(position)
            data, file_mtime = self._load_file(force_reload=force_reload)
            if not data or file_mtime is None:
                return {
                    'success': False,
                    'error': 'RUNE_DATA_NOT_FOUND',
                    'message': 'runes.json not found',
                }

            champion_bucket = (data.get('data') or {}).get(str(int(champion_id)))
            if not champion_bucket:
                return {
                    'success': False,
                    'error': 'CHAMPION_NOT_FOUND',
                    'champion_id': int(champion_id),
                    'position': normalized_position,
                    'meta': self._build_meta(file_mtime),
                }

            positions = champion_bucket.get('positions') or {}
            position_data = positions.get(normalized_position)
            if not position_data:
                return {
                    'success': False,
                    'error': 'POSITION_NOT_FOUND',
                    'champion_id': int(champion_id),
                    'champion_key': champion_bucket.get('key', ''),
                    'position': normalized_position,
                    'available_positions': list(positions.keys()),
                    'meta': self._build_meta(file_mtime),
                }

            return {
                'success': True,
                'champion_id': int(champion_id),
                'champion_key': champion_bucket.get('key', ''),
                'position': normalized_position,
                'position_data': position_data,
                'available_positions': list(positions.keys()),
                'version': data.get('version'),
                'updateTime': data.get('updateTime'),
                'meta': data.get('meta') or {},
                'normalized_schema': 'v2',
                '_meta': self._build_meta(file_mtime),
            }
        except Exception as exc:
            return {
                'success': False,
                'error': 'RUNE_ENTRY_EXCEPTION',
                'message': str(exc),
            }

    def get_brief_status(self):
        """Compact status for high-frequency polling."""
        status = self.get_status()
        return {
            'exists': bool(status.get('exists')),
            'is_updating': bool(status.get('is_updating')),
            'is_stale': bool(status.get('is_stale')),
            'days_old': status.get('days_old'),
            'last_update': status.get('last_update'),
            'last_update_error': status.get('last_update_error'),
        }

    def get_status(self):
        if not os.path.exists(self.runes_path):
            return {
                'exists': False,
                'is_updating': self._updating,
                'last_update_error': self._last_update_error,
            }

        file_mtime = os.path.getmtime(self.runes_path)
        meta = self._build_meta(file_mtime)
        return {
            'exists': True,
            **meta,
        }

    def trigger_update(self, reason: str = 'manual'):
        with self._lock:
            if self._updating:
                return {'success': False, 'message': '更新任务正在执行中。'}

            self._updating = True
            self._last_update_error = None
            self._last_update_started_at = time.time()

        thread = threading.Thread(target=self._run_bulk_update, args=(reason,), daemon=True)
        thread.start()
        return {'success': True, 'message': '符文数据更新已开始。'}

    def _load_champion_list(self) -> list[dict]:
        """加载英雄列表：优先从已有 runes.json，否则从 frontend champions.js 解析。"""
        champions = []
        # 策略1: 从已有 runes.json 加载
        if os.path.exists(self.runes_path):
            try:
                with open(self.runes_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                for cid, cdata in (payload.get('data') or {}).items():
                    key = (cdata or {}).get('key')
                    if key:
                        champions.append({'id': int(cid), 'key': str(key)})
            except Exception as e:
                _log.debug("从 runes.json 加载英雄列表失败: %s", e)

        # 策略2: 从 frontend/src/data/champions.js 解析
        if not champions:
            champions_js = os.path.join(self.resource_root, 'frontend', 'src', 'data', 'champions.js')
            if os.path.exists(champions_js):
                try:
                    source = open(champions_js, 'r', encoding='utf-8', errors='ignore').read()
                    pattern = re.compile(r"\{\s*id:\s*(\d+)\s*,\s*key:\s*'([^']+)'", re.MULTILINE)
                    seen_ids = set()
                    for m in pattern.finditer(source):
                        cid = int(m.group(1))
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            champions.append({'id': cid, 'key': m.group(2).lower()})
                except Exception as e:
                    _log.debug("从 champions.js 加载英雄列表失败: %s", e)

        # 去重并按 id 排序
        unique = {}
        for c in champions:
            unique[c['id']] = c
        return [unique[k] for k in sorted(unique.keys())]

    @staticmethod
    def _create_retry_session(retries: int = 3, backoff: float = 0.5) -> requests.Session:
        """创建带重试的 requests Session。"""
        session = requests.Session()
        retry = Retry(
            total=retries, read=retries, connect=retries,
            backoff_factor=backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=['GET'],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _run_bulk_update(self, reason: str):
        """全量拉取符文数据（内嵌执行，不依赖外部脚本）。"""
        try:
            champions = self._load_champion_list()
            if not champions:
                self._last_update_error = f'[{reason}] 未找到英雄列表'
                return

            region = self._normalize_region(self.DEFAULT_REGION)
            positions = list(self.POSITION_ORDER)
            workers = 12 if reason == 'manual' else 6
            min_interval = 0.06 if reason == 'manual' else 0.2
            timeout_seconds = 10 if reason == 'manual' else 15
            max_attempts = 2 if reason == 'manual' else 3

            # 全局限速器
            _rate_lock = threading.Lock()
            _last_request_at = [0.0]

            def _wait_turn():
                with _rate_lock:
                    now = time.time()
                    wait = min_interval - (now - _last_request_at[0])
                    if wait > 0:
                        time.sleep(wait)
                    _last_request_at[0] = time.time()

            # 线程局部 session
            _local = threading.local()

            def _get_session() -> requests.Session:
                s = getattr(_local, 'session', None)
                if s is None:
                    s = self._create_retry_session(retries=3)
                    _local.session = s
                return s

            # 结果容器
            result_data = {
                str(c['id']): {'key': c['key'], 'positions': {}}
                for c in champions
            }
            stats = {'success': 0, 'no_data': 0, 'failed': 0, 'total': len(champions) * len(positions)}
            stats_lock = threading.Lock()
            data_lock = threading.Lock()

            def _fetch_task(champion: dict, position: str):
                _wait_turn()
                session = _get_session()
                url = self._build_ranked_url(champion['key'], position, region)
                payload = None
                for attempt in range(1, max_attempts + 1):
                    _wait_turn()
                    try:
                        resp = session.get(url, headers=self.REQUEST_HEADERS, timeout=timeout_seconds)
                        if resp.status_code == 200:
                            payload = resp.json()
                            break
                        if resp.status_code == 404:
                            break
                        if resp.status_code == 429:
                            time.sleep(min(6.0, 0.8 * attempt))
                    except requests.RequestException:
                        time.sleep(min(5.0, 0.5 * attempt))

                parsed = self._parse_position_data(payload) if payload else None
                if parsed and parsed.get('rune_pages'):
                    with data_lock:
                        result_data[str(champion['id'])]['positions'][position] = parsed
                    with stats_lock:
                        stats['success'] += 1
                elif payload is None:
                    with stats_lock:
                        stats['failed'] += 1
                else:
                    with stats_lock:
                        stats['no_data'] += 1

            # 并发执行
            _log.info("开始全量拉取符文数据: 英雄=%d 分路=%d 并发=%d",
                      len(champions), len(positions), workers)
            futures = []
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for champion in champions:
                    for position in positions:
                        futures.append(executor.submit(_fetch_task, champion, position))
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        _log.debug("拉取任务异常: %s", e)

            # 写入文件
            from datetime import datetime, timezone
            utc_now = datetime.now(timezone.utc)
            local_now = datetime.now().astimezone()
            output_payload = {
                'version': utc_now.strftime('%Y.%m.%d'),
                'updateTime': local_now.strftime('%Y-%m-%d %H:%M:%S'),
                'meta': {
                    'generated_at_utc': utc_now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'region': self._requested_region(self.DEFAULT_REGION),
                    'source_region': region,
                    'positions': positions,
                    'workers': workers,
                    'stats': stats,
                },
                'data': result_data,
            }
            self._atomic_write_json(self.runes_path, output_payload)
            self._load_file(force_reload=True)
            self._last_update_error = None

            rate = (stats['success'] / stats['total'] * 100) if stats['total'] else 0
            _log.info("符文数据更新完成: success=%d no_data=%d failed=%d total=%d rate=%.1f%%",
                      stats['success'], stats['no_data'], stats['failed'], stats['total'], rate)
        except Exception as exc:
            _log.error("符文数据更新异常: %s", exc, exc_info=True)
            self._last_update_error = f'[{reason}] {exc}'
        finally:
            with self._lock:
                self._updating = False
                self._last_update_finished_at = time.time()

    def _atomic_write_json(self, target_path: str, payload: dict):
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix='runes-', suffix='.tmp', dir=target_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _normalize_position(self, position: str):
        normalized = (position or '').upper().strip()
        return normalized if normalized in self.VALID_POSITIONS else 'MID'

    def _normalize_region(self, region: str | None):
        requested = (region or self.DEFAULT_REGION).upper().strip() or self.DEFAULT_REGION
        normalized = self.REGION_ALIASES.get(requested, requested)
        if normalized not in self.SUPPORTED_REGIONS:
            return 'GLOBAL'
        return normalized

    def _requested_region(self, region: str | None):
        return (region or self.DEFAULT_REGION).upper().strip() or self.DEFAULT_REGION

    def _normalize_positions(self, positions: list[str] | tuple[str, ...] | None):
        if not positions:
            return list(self.POSITION_ORDER)

        normalized_positions: list[str] = []
        for raw_position in positions:
            normalized = self._normalize_position(raw_position)
            if normalized not in normalized_positions:
                normalized_positions.append(normalized)
        return normalized_positions or list(self.POSITION_ORDER)

    def _create_empty_payload(self, region: str):
        return {
            'version': time.strftime('%Y.%m.%d', time.localtime()),
            'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'meta': {
                'region': region,
                'positions': list(self.POSITION_ORDER),
            },
            'data': {},
        }

    def _upsert_position_payload(
        self,
        existing_data: dict,
        champion_id: int,
        champion_key: str,
        position: str,
        position_data: dict,
        region: str,
        source_region: str | None = None,
    ):
        existing_data.setdefault('data', {})
        champion_bucket = existing_data['data'].setdefault(str(champion_id), {'key': champion_key, 'positions': {}})
        champion_bucket['key'] = champion_key
        champion_bucket.setdefault('positions', {})
        champion_bucket['positions'][position] = position_data

        existing_data['updateTime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        existing_data.setdefault('meta', {})
        existing_data['meta']['region'] = region
        existing_data['meta']['source_region'] = source_region or region
        existing_data['meta'].setdefault('positions', list(self.POSITION_ORDER))

    def _build_ranked_url(self, champion_key: str, position: str, region: str):
        return f'https://lol-api-champion.op.gg/api/{region}/champions/ranked/{champion_key}/{position}'

    def _normalize_champion_key(self, champion_key: str) -> str:
        value = (champion_key or '').strip().lower()
        aliases = {
            'wukong': 'monkeyking',
            'fiddle': 'fiddlesticks',
            'belveth': 'belveth',
            'velkoz': 'velkoz',
            'tahmkench': 'tahmkench',
            'drmundo': 'drmundo',
            'kaisa': 'kaisa',
            'khazix': 'khazix',
            'chogath': 'chogath',
            'kogmaw': 'kogmaw',
            'ksante': 'ksante',
            'leblanc': 'leblanc',
            'lee sin': 'leesin',
            'jarvan iv': 'jarvaniv',
            'jarvaniv': 'jarvaniv',
            'xin zhao': 'xinzhao',
            'master yi': 'masteryi',
        }
        compact = value.replace("'", '').replace(' ', '')
        return aliases.get(value, aliases.get(compact, compact))

    def _fetch_ranked_payload(
        self,
        champion_key: str,
        position: str,
        region: str,
        timeout_seconds: int = 10,
        attempts: int = 2,
    ):
        champion_key = (champion_key or '').strip().lower()
        champion_key = self._normalize_champion_key(champion_key)
        if not champion_key:
            return None

        position = self._normalize_position(position)
        region = self._normalize_region(region)
        url = self._build_ranked_url(champion_key=champion_key, position=position, region=region)

        for attempt in range(1, max(1, attempts) + 1):
            try:
                response = requests.get(
                    url,
                    headers=self.REQUEST_HEADERS,
                    timeout=max(3, int(timeout_seconds)),
                )
                if response.status_code == 200:
                    return response.json()
                if response.status_code == 404:
                    return None
                if response.status_code == 429:
                    time.sleep(min(2.0, 0.4 * attempt))
                    continue
            except Exception:
                time.sleep(min(2.0, 0.3 * attempt))

        return None

    def _first_list(self, data: dict, *keys: str):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []

    def _normalize_rune_pages(self, data: dict):
        pages = self._first_list(data, 'rune_pages', 'perk_pages')
        flat_runes = self._first_list(data, 'runes')
        normalized = []

        for page in pages:
            if not isinstance(page, dict):
                continue
            builds = page.get('builds') if isinstance(page.get('builds'), list) else []
            normalized.append({
                **page,
                'id': page.get('id'),
                'primary_page_id': page.get('primary_page_id'),
                'secondary_page_id': page.get('secondary_page_id'),
                'play': page.get('play', 0),
                'win': page.get('win', 0),
                'pick_rate': page.get('pick_rate', 0),
                'builds': builds,
            })

        if normalized:
            return normalized

        for rune in flat_runes:
            if not isinstance(rune, dict):
                continue
            normalized.append({
                **rune,
                'id': rune.get('id'),
                'primary_page_id': rune.get('primary_page_id'),
                'secondary_page_id': rune.get('secondary_page_id'),
                'play': rune.get('play', 0),
                'win': rune.get('win', 0),
                'pick_rate': rune.get('pick_rate', 0),
                'builds': [rune],
            })
        return normalized

    def _normalize_item_group(self, data: dict, *keys: str):
        groups = self._first_list(data, *keys)
        normalized = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            normalized.append({
                'ids': group.get('ids', []),
                'play': group.get('play', 0),
                'win': group.get('win', 0),
                'pick_rate': group.get('pick_rate', 0),
            })
        return normalized

    def _parse_position_data(self, api_payload: dict | None):
        if not api_payload or 'data' not in api_payload:
            return None

        data = api_payload.get('data') or {}
        api_meta = api_payload.get('meta') or data.get('meta') or {}
        rune_pages = self._normalize_rune_pages(data)
        flat_runes = self._first_list(data, 'runes')
        core_items = self._normalize_item_group(data, 'core_items', 'items', 'build_items')
        boots = self._normalize_item_group(data, 'boots', 'boot_items')
        starter_items = self._normalize_item_group(data, 'starter_items', 'start_items')
        last_items = self._normalize_item_group(data, 'last_items', 'final_items')
        return {
            'schema_version': 'opgg-ranked-v2',
            'source': 'opgg-ranked-api',
            'source_version': api_meta.get('version'),
            'source_cached_at': api_meta.get('cached_at'),
            'rune_pages': rune_pages,
            'summoner_spells': self._first_list(data, 'summoner_spells'),
            'core_items': core_items,
            'items': core_items,
            'boots': boots,
            'starter_items': starter_items,
            'last_items': last_items,
            'skills': self._first_list(data, 'skills'),
            'counters': self._first_list(data, 'counters'),
            'game_lengths': self._first_list(data, 'game_lengths'),
            'trends': data.get('trends', {}),
        }

    def fetch_champion_overview(self, champion_key: str, position: str = 'MID', region: str = DEFAULT_REGION):
        champion_key = self._normalize_champion_key(champion_key)
        if not champion_key:
            return {'success': False, 'message': '缺少 champion_key'}

        normalized_position = self._normalize_position(position)
        requested_region = self._requested_region(region)
        normalized_region = self._normalize_region(region)

        payload = self._fetch_ranked_payload(
            champion_key=champion_key,
            position=normalized_position,
            region=normalized_region,
            timeout_seconds=10,
            attempts=2,
        )

        if not payload:
            return {'success': False, 'message': '未获取到 OP.GG ranked 数据'}

        data = payload.get('data') or {}
        summary = data.get('summary') or {}
        positions = summary.get('positions') or []
        selected_position = next(
            (item for item in positions if (item.get('name') or '').upper() == normalized_position),
            None,
        )

        return {
            'success': True,
            'region': requested_region,
            'source_region': normalized_region,
            'position': normalized_position,
            'version': (payload.get('meta') or {}).get('version'),
            'cached_at': (payload.get('meta') or {}).get('cached_at'),
            'average_stats': summary.get('average_stats') or {},
            'position_stats': (selected_position or {}).get('stats') or {},
            'counters': (selected_position or {}).get('counters') or data.get('counters') or [],
        }

    def refresh_single_entry(self, champion_id: int, champion_key: str, position: str = 'MID', region: str = DEFAULT_REGION):
        with self._lock:
            if self._updating:
                return {'success': False, 'message': '全量更新正在执行，请稍后重试'}

        champion_key = self._normalize_champion_key(champion_key)
        if not champion_key:
            return {'success': False, 'message': '缺少 champion_key'}

        try:
            champion_id = int(champion_id)
        except Exception:
            return {'success': False, 'message': 'champion_id 非法'}

        normalized_position = self._normalize_position(position)
        requested_region = self._requested_region(region)
        normalized_region = self._normalize_region(region)
        inflight_key = f'{champion_id}:{champion_key}:{normalized_position}:{normalized_region}'

        with self._lock:
            last_at = self._inflight_refresh_keys.get(inflight_key)
            now = time.time()
            if last_at and (now - last_at) < 1.5:
                return {'success': False, 'message': '相同刷新请求过于频繁，请稍后重试'}
            self._inflight_refresh_keys[inflight_key] = now
            # 清理超过 10 秒的旧条目
            expired = [k for k, ts in self._inflight_refresh_keys.items() if now - ts > 10]
            for k in expired:
                del self._inflight_refresh_keys[k]

        payload = self._fetch_ranked_payload(
            champion_key=champion_key,
            position=normalized_position,
            region=normalized_region,
            timeout_seconds=10,
            attempts=2,
        )
        if not payload:
            return {'success': False, 'message': '未从 OP.GG 获取到当前英雄位置数据'}

        parsed_position = self._parse_position_data(payload)
        if not parsed_position:
            return {'success': False, 'message': 'OP.GG 返回数据格式异常'}

        with self._lock:
            existing_data, _ = self._load_file(force_reload=True)
            if not existing_data or not isinstance(existing_data, dict):
                existing_data = self._create_empty_payload(normalized_region)

            self._upsert_position_payload(
                existing_data=existing_data,
                champion_id=champion_id,
                champion_key=champion_key,
                position=normalized_position,
                position_data=parsed_position,
                region=requested_region,
                source_region=normalized_region,
            )

            existing_data['meta']['last_single_refresh'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            existing_data['meta']['last_single_refresh_target'] = {
                'champion_id': champion_id,
                'champion_key': champion_key,
                'position': normalized_position,
            }

            self._atomic_write_json(self.runes_path, existing_data)

            self._cached_data = existing_data
            self._cached_mtime = os.path.getmtime(self.runes_path)
            self._last_update_error = None

        return {
            'success': True,
            'message': f'已刷新 {champion_key.upper()} {normalized_position} 数据',
            'champion_id': champion_id,
            'position': normalized_position,
            'region': requested_region,
            'source_region': normalized_region,
        }

    def refresh_selected_entries(
        self,
        targets: list[dict[str, Any]] | None,
        region: str = DEFAULT_REGION,
        positions: list[str] | tuple[str, ...] | None = None,
    ):
        with self._lock:
            if self._updating:
                return {'success': False, 'message': '全量更新正在执行，请稍后重试'}

        if not targets or not isinstance(targets, list):
            return {'success': False, 'message': '缺少要刷新的英雄列表'}

        requested_region = self._requested_region(region)
        normalized_region = self._normalize_region(region)
        fallback_positions = self._normalize_positions(positions)

        normalized_targets = []
        for raw_target in targets:
            if not isinstance(raw_target, dict):
                continue
            try:
                champion_id_val = int(raw_target.get('champion_id'))
            except Exception:
                continue
            champion_key_val = str(raw_target.get('champion_key') or '').strip().lower()
            target_positions = raw_target.get('positions')
            if isinstance(target_positions, str):
                target_positions = [target_positions]
            if not champion_key_val:
                continue
            normalized_targets.append({
                'champion_id': champion_id_val,
                'champion_key': champion_key_val,
                'positions': self._normalize_positions(target_positions or fallback_positions),
            })

        if not normalized_targets:
            return {'success': False, 'message': '未找到有效的英雄刷新参数'}

        with self._lock:
            now = time.time()
            # 清理超过 10 秒的旧条目
            expired = [k for k, ts in self._inflight_refresh_keys.items() if now - ts > 10]
            for k in expired:
                del self._inflight_refresh_keys[k]
            deduped = []
            for item in normalized_targets:
                for current_position in item.get('positions') or []:
                    key = f"{item['champion_id']}:{item['champion_key']}:{current_position}:{normalized_region}"
                    last_at = self._inflight_refresh_keys.get(key)
                    if last_at and (now - last_at) < 1.5:
                        continue
                    self._inflight_refresh_keys[key] = now
                    deduped.append({
                        'champion_id': item['champion_id'],
                        'champion_key': item['champion_key'],
                        'positions': [current_position],
                    })

        if not deduped:
            return {'success': False, 'message': '刷新请求过于频繁，请稍后重试'}

        merged_targets: dict[int, dict[str, Any]] = {}
        for raw_target in deduped:
            if not isinstance(raw_target, dict):
                continue

            champion_key = str(raw_target.get('champion_key') or '').strip().lower()
            if not champion_key:
                continue

            try:
                champion_id = int(raw_target.get('champion_id'))
            except Exception:
                continue

            target_positions = raw_target.get('positions')
            if isinstance(target_positions, str):
                target_positions = [target_positions]
            normalized_positions = self._normalize_positions(target_positions or fallback_positions)

            bucket = merged_targets.setdefault(
                champion_id,
                {'champion_key': champion_key, 'positions': []},
            )
            bucket['champion_key'] = champion_key
            for current_position in normalized_positions:
                if current_position not in bucket['positions']:
                    bucket['positions'].append(current_position)

        if not merged_targets:
            return {'success': False, 'message': '未找到有效的英雄刷新参数'}

        success_payloads: list[dict[str, Any]] = []
        failed_entries: list[dict[str, Any]] = []

        for champion_id, bucket in merged_targets.items():
            champion_key = bucket.get('champion_key')
            for current_position in bucket.get('positions') or []:
                payload = self._fetch_ranked_payload(
                    champion_key=champion_key,
                    position=current_position,
                    region=normalized_region,
                    timeout_seconds=10,
                    attempts=2,
                )
                if not payload:
                    failed_entries.append({
                        'champion_id': champion_id,
                        'champion_key': champion_key,
                        'position': current_position,
                        'reason': '未获取到 OP.GG 数据',
                    })
                    continue

                parsed_position = self._parse_position_data(payload)
                if not parsed_position:
                    failed_entries.append({
                        'champion_id': champion_id,
                        'champion_key': champion_key,
                        'position': current_position,
                        'reason': '返回数据格式异常',
                    })
                    continue

                success_payloads.append({
                    'champion_id': champion_id,
                    'champion_key': champion_key,
                    'position': current_position,
                    'position_data': parsed_position,
                })

        if not success_payloads:
            return {
                'success': False,
                'message': '未成功刷新任何英雄符文数据',
                'summary': {
                    'success': 0,
                    'failed': len(failed_entries),
                    'total': len(failed_entries),
                },
                'failed': failed_entries[:30],
            }

        with self._lock:
            existing_data, _ = self._load_file(force_reload=True)
            if not existing_data or not isinstance(existing_data, dict):
                existing_data = self._create_empty_payload(requested_region)

            for item in success_payloads:
                self._upsert_position_payload(
                    existing_data=existing_data,
                    champion_id=item['champion_id'],
                    champion_key=item['champion_key'],
                    position=item['position'],
                    position_data=item['position_data'],
                    region=requested_region,
                    source_region=normalized_region,
                )

            existing_data.setdefault('meta', {})
            existing_data['meta']['last_selected_refresh'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            existing_data['meta']['last_selected_refresh_targets'] = [
                {
                    'champion_id': item['champion_id'],
                    'champion_key': item['champion_key'],
                    'position': item['position'],
                }
                for item in success_payloads[:100]
            ]

            self._atomic_write_json(self.runes_path, existing_data)

            self._cached_data = existing_data
            self._cached_mtime = os.path.getmtime(self.runes_path)
            self._last_update_error = None

        success_count = len(success_payloads)
        failed_count = len(failed_entries)
        total_count = success_count + failed_count

        return {
            'success': True,
            'message': f'已刷新 {success_count}/{total_count} 条英雄分路符文数据',
            'region': requested_region,
            'source_region': normalized_region,
            'summary': {
                'success': success_count,
                'failed': failed_count,
                'total': total_count,
            },
            'failed': failed_entries[:30],
        }
