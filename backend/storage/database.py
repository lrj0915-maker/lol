"""SQLite 数据库操作"""
import os
import sqlite3
import time
import json
import threading
from typing import List, Optional, Any, Dict

from logger import get_logger
from paths import get_app_root
from storage.models import MatchRecord

log = get_logger('Database')

DATA_DIR = os.path.join(get_app_root(), 'data')
DB_FILE = os.path.join(DATA_DIR, 'history.db')

# 保留天数
RETENTION_DAYS = 30


class Database:
    def __init__(self):
        self._cleanup_started = False
        self._thread_local = threading.local()
        self._conn_lock = threading.RLock()
        self._ensure_dir()
        self._init_db()
        self.start_cleanup_scheduler()

    def _ensure_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA busy_timeout=5000;')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS match_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER UNIQUE,
                    game_mode TEXT,
                    game_length INTEGER,
                    is_win INTEGER,
                    champion_id INTEGER,
                    champion_name TEXT,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    game_score TEXT,
                    timestamp INTEGER,
                    data_json TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON match_history(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_mode_timestamp ON match_history(game_mode, timestamp DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_champion_timestamp ON match_history(champion_id, timestamp DESC)
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summoner_profile_cache (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    data_json TEXT,
                    updated_at INTEGER
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ranked_profile_cache (
                    queue_type TEXT PRIMARY KEY,
                    data_json TEXT,
                    updated_at INTEGER
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS teammate_cache (
                    cache_key TEXT PRIMARY KEY,
                    data_json TEXT,
                    updated_at INTEGER
                )
            ''')
            conn.commit()

    def _get_conn(self):
        conn = getattr(self._thread_local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(DB_FILE, timeout=5.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA busy_timeout=5000;')
            self._thread_local.conn = conn
        return conn

    def start_cleanup_scheduler(self):
        if self._cleanup_started:
            return
        self._cleanup_started = True

        def loop():
            while True:
                try:
                    self.cleanup_old_records()
                except Exception as e:
                    log.error("清理过期记录异常: %s", e)
                time.sleep(6 * 60 * 60)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def save_match(self, record: MatchRecord) -> bool:
        """保存对局记录"""
        try:
            conn = self._get_conn()
            with self._conn_lock:
                conn.execute('''
                    INSERT OR REPLACE INTO match_history 
                    (game_id, game_mode, game_length, is_win, champion_id, champion_name,
                     kills, deaths, assists, game_score, timestamp, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.game_id,
                    record.game_mode,
                    record.game_length,
                    1 if record.is_win else 0,
                    record.champion_id,
                    record.champion_name,
                    record.kills,
                    record.deaths,
                    record.assists,
                    record.game_score,
                    record.timestamp,
                    record.data_json
                ))
                conn.commit()
                return True
        except Exception as e:
            log.error("保存对局记录失败 game_id=%s: %s", getattr(record, 'game_id', '?'), e)
            return False

    def get_match_list(self, limit: int = 50, offset: int = 0, 
                       game_mode: str = None, champion_id: int = None) -> List[dict]:
        """获取对局列表"""
        query = 'SELECT * FROM match_history WHERE 1=1'
        params = []

        if game_mode:
            query += ' AND game_mode = ?'
            params.append(game_mode)
        
        if champion_id:
            query += ' AND champion_id = ?'
            params.append(champion_id)

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        conn = self._get_conn()
        with self._conn_lock:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    'game_id': row['game_id'],
                    'game_mode': row['game_mode'],
                    'game_length': row['game_length'],
                    'is_win': bool(row['is_win']),
                    'champion_id': row['champion_id'],
                    'champion_name': row['champion_name'],
                    'kills': row['kills'],
                    'deaths': row['deaths'],
                    'assists': row['assists'],
                    'game_score': row['game_score'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]

    def get_match_detail(self, game_id: int) -> Optional[dict]:
        """获取对局详情"""
        conn = self._get_conn()
        with self._conn_lock:
            cursor = conn.execute(
                'SELECT data_json FROM match_history WHERE game_id = ?',
                (game_id,)
            )
            row = cursor.fetchone()
            
            if row and row['data_json']:
                return json.loads(row['data_json'])
            return None

    def cleanup_old_records(self):
        """清理过期记录"""
        cutoff = int(time.time()) - (RETENTION_DAYS * 24 * 60 * 60)
        
        conn = self._get_conn()
        with self._conn_lock:
            conn.execute(
                'DELETE FROM match_history WHERE timestamp < ?',
                (cutoff,)
            )
            conn.commit()

    def get_stats(self) -> dict:
        """获取统计信息"""
        conn = self._get_conn()
        with self._conn_lock:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as wins
                FROM match_history
            ''')
            row = cursor.fetchone()
            
            total = row[0] or 0
            wins = row[1] or 0
            
            return {
                'total_games': total,
                'wins': wins,
                'losses': total - wins,
                'win_rate': round(wins / total * 100, 1) if total > 0 else 0
            }

    def set_summoner_profile_cache(self, profile: dict):
        conn = self._get_conn()
        with self._conn_lock:
            conn.execute(
                '''
                INSERT INTO summoner_profile_cache (id, data_json, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                ''',
                (json.dumps(profile or {}, ensure_ascii=False), int(time.time()))
            )
            conn.commit()

    def get_summoner_profile_cache(self) -> dict:
        conn = self._get_conn()
        with self._conn_lock:
            row = conn.execute(
                'SELECT data_json, updated_at FROM summoner_profile_cache WHERE id = 1'
            ).fetchone()
            if not row:
                return {}
            data = json.loads(row['data_json']) if row['data_json'] else {}
            data['last_updated_at'] = data.get('last_updated_at') or row['updated_at'] or 0
            return data

    def set_ranked_profile_cache(self, queue_type: str, payload: dict):
        conn = self._get_conn()
        with self._conn_lock:
            conn.execute(
                '''
                INSERT INTO ranked_profile_cache (queue_type, data_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(queue_type) DO UPDATE SET
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                ''',
                (queue_type, json.dumps(payload or {}, ensure_ascii=False), int(time.time()))
            )
            conn.commit()

    def get_ranked_profile_cache(self, queue_type: str) -> dict:
        conn = self._get_conn()
        with self._conn_lock:
            row = conn.execute(
                'SELECT data_json, updated_at FROM ranked_profile_cache WHERE queue_type = ?',
                (queue_type,)
            ).fetchone()
            if not row:
                return {}
            data = json.loads(row['data_json']) if row['data_json'] else {}
            data['last_updated_at'] = data.get('last_updated_at') or row['updated_at'] or 0
            return data

    def set_teammate_cache(self, payload: list):
        conn = self._get_conn()
        with self._conn_lock:
            conn.execute(
                '''
                INSERT INTO teammate_cache (cache_key, data_json, updated_at)
                VALUES ('recent_teammates', ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                ''',
                (json.dumps(payload or [], ensure_ascii=False), int(time.time()))
            )
            conn.commit()

    def get_teammate_cache(self) -> list:
        conn = self._get_conn()
        with self._conn_lock:
            row = conn.execute(
                'SELECT data_json FROM teammate_cache WHERE cache_key = ?',
                ('recent_teammates',)
            ).fetchone()
            if not row or not row['data_json']:
                return []
            return json.loads(row['data_json'])

    def _get_match_rows(self, limit: Optional[int] = None) -> List[sqlite3.Row]:
        query = 'SELECT * FROM match_history ORDER BY timestamp DESC'
        params = []
        if isinstance(limit, int) and limit > 0:
            query += ' LIMIT ?'
            params.append(limit)
        conn = self._get_conn()
        with self._conn_lock:
            return conn.execute(query, params).fetchall()

    @staticmethod
    def _safe_detail(row: sqlite3.Row) -> dict:
        try:
            return json.loads(row['data_json']) if row['data_json'] else {}
        except Exception:
            return {}

    @staticmethod
    def _get_my_player(detail: dict) -> dict:
        my_team = detail.get('my_team', []) or []
        for player in my_team:
            if player.get('is_me'):
                return player
        return my_team[0] if my_team else {}

    @staticmethod
    def _calculate_kda(kills: int, deaths: int, assists: int) -> float:
        return round((kills + assists) / max(1, deaths), 2)

    @staticmethod
    def _calc_share(value: int, total: int) -> float:
        if not total:
            return 0.0
        return round(value / total * 100, 2)

    @staticmethod
    def _calc_cs(player: dict) -> int:
        return int(player.get('minions_killed', 0) or 0) + int(player.get('neutral_minions_killed', 0) or 0)

    @staticmethod
    def _normalize_ranked_payload(payload: dict) -> dict:
        if not payload:
            return {
                'tier': '',
                'division': '',
                'lp': 0,
                'wins': 0,
                'losses': 0,
                'is_placement': True,
                'last_updated_at': 0,
            }
        return {
            'tier': payload.get('tier', ''),
            'division': payload.get('division', ''),
            'lp': int(payload.get('lp') or 0),
            'wins': int(payload.get('wins') or 0),
            'losses': int(payload.get('losses') or 0),
            'is_placement': bool(payload.get('is_placement', False)),
            'last_updated_at': payload.get('last_updated_at', 0),
        }

    def _build_hero_usage(self, limit: int = 20) -> list:
        rows = self._get_match_rows(limit=limit)
        champions: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            champ_id = int(row['champion_id'] or 0)
            if champ_id not in champions:
                champions[champ_id] = {
                    'champion_id': champ_id,
                    'champion_name': row['champion_name'] or '',
                    'games': 0,
                    'wins': 0,
                    'kda_total': 0.0,
                }
            detail = self._safe_detail(row)
            my_player = self._get_my_player(detail)
            champions[champ_id]['games'] += 1
            champions[champ_id]['wins'] += 1 if row['is_win'] else 0
            champions[champ_id]['kda_total'] += self._calculate_kda(
                int(my_player.get('kills', 0) or 0),
                int(my_player.get('deaths', 0) or 0),
                int(my_player.get('assists', 0) or 0),
            )
        result = []
        for item in champions.values():
            games = max(1, item['games'])
            result.append({
                'champion_id': item['champion_id'],
                'champion_name': item['champion_name'],
                'games': item['games'],
                'wins': item['wins'],
                'win_rate': round(item['wins'] / games * 100, 2),
                'avg_kda': round(item['kda_total'] / games, 2),
            })
        result.sort(key=lambda item: (-item['games'], -item['win_rate'], item['champion_name']))
        return result[:8]

    def _build_recent_teammates(self, limit: int = 50) -> list:
        rows = self._get_match_rows(limit=limit)
        teammates: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            detail = self._safe_detail(row)
            for teammate in detail.get('my_team', []) or []:
                if teammate.get('is_me'):
                    continue
                name = (teammate.get('summoner_name') or teammate.get('name') or '').strip()
                if not name:
                    continue
                tag = (teammate.get('tag_line') or '').strip()
                identity = f'{name}#{tag}' if tag else name
                if identity not in teammates:
                    teammates[identity] = {
                        'name': name,
                        'tag': tag,
                        'identity': identity,
                        'display_name': identity,
                        'games': 0,
                        'wins': 0,
                        'losses': 0,
                        'last_played_at': 0,
                    }
                teammates[identity]['games'] += 1
                if row['is_win']:
                    teammates[identity]['wins'] += 1
                else:
                    teammates[identity]['losses'] += 1
                teammates[identity]['last_played_at'] = max(teammates[identity]['last_played_at'], int(row['timestamp'] or 0))
        result = list(teammates.values())
        result.sort(key=lambda item: (-item['games'], -item['last_played_at'], item['identity']))
        return result[:12]

    def get_battle_profile_summary(self) -> dict:
        rows = self._get_match_rows()
        total_games = len(rows)
        wins = 0
        total_kda = 0.0
        total_kp = 0.0
        total_damage_share = 0.0
        total_tank_share = 0.0
        total_gold_share = 0.0
        total_cs_per_min = 0.0
        for row in rows:
            detail = self._safe_detail(row)
            my_team = detail.get('my_team', []) or []
            my_player = self._get_my_player(detail)
            if row['is_win']:
                wins += 1
            team_kills = sum(int(player.get('kills', 0) or 0) for player in my_team)
            team_damage = sum(int(player.get('total_damage', 0) or 0) for player in my_team)
            team_tank = sum(int(player.get('damage_taken', 0) or 0) for player in my_team)
            team_gold = sum(int(player.get('gold_earned', 0) or 0) for player in my_team)
            cs = self._calc_cs(my_player)
            duration_minutes = max(1.0, float(row['game_length'] or 0) / 60.0)
            total_kda += self._calculate_kda(
                int(my_player.get('kills', 0) or 0),
                int(my_player.get('deaths', 0) or 0),
                int(my_player.get('assists', 0) or 0),
            )
            total_kp += self._calc_share(int(my_player.get('kills', 0) or 0) + int(my_player.get('assists', 0) or 0), team_kills)
            total_damage_share += self._calc_share(int(my_player.get('total_damage', 0) or 0), team_damage)
            total_tank_share += self._calc_share(int(my_player.get('damage_taken', 0) or 0), team_tank)
            total_gold_share += self._calc_share(int(my_player.get('gold_earned', 0) or 0), team_gold)
            total_cs_per_min += round(cs / duration_minutes, 2)

        divisor = max(1, total_games)
        summary = {
            'total_games': total_games,
            'wins': wins,
            'losses': total_games - wins,
            'win_rate': round(wins / divisor * 100, 2),
            'avg_kda': round(total_kda / divisor, 2),
            'avg_kill_participation': round(total_kp / divisor, 2),
            'avg_damage_share': round(total_damage_share / divisor, 2),
            'avg_tank_share': round(total_tank_share / divisor, 2),
            'avg_gold_share': round(total_gold_share / divisor, 2),
            'avg_cs_per_min': round(total_cs_per_min / divisor, 2),
        }
        hero_usage = self._build_hero_usage(limit=20)
        recent_teammates = self._build_recent_teammates(limit=50)
        if recent_teammates:
            self.set_teammate_cache(recent_teammates)
        else:
            recent_teammates = self.get_teammate_cache()
        return {
            'profile': self.get_summoner_profile_cache() or {},
            'ranked_solo': self._normalize_ranked_payload(self.get_ranked_profile_cache('RANKED_SOLO_5x5')),
            'ranked_flex': self._normalize_ranked_payload(self.get_ranked_profile_cache('RANKED_FLEX_SR')),
            'summary': summary,
            'hero_usage': hero_usage,
            'recent_teammates': recent_teammates,
        }

    def _build_brief_players(self, players: list) -> list:
        result = []
        for player in players or []:
            name = (player.get('summoner_name') or player.get('name') or player.get('champion_name') or '').strip()
            tag = (player.get('tag_line') or '').strip()
            identity = f'{name}#{tag}' if tag else name
            result.append({
                'name': name,
                'tag': tag,
                'identity': identity,
                'display_name': identity,
                'champion_id': player.get('champion_id') or 0,
                'champion_name': player.get('champion_name') or '',
                'is_me': bool(player.get('is_me')),
                'game_score': player.get('game_score') or '',
            })
        return result

    def _build_history_item(self, row: sqlite3.Row, detail: dict) -> dict:
        my_team = detail.get('my_team', []) or []
        enemy_team = detail.get('enemy_team', []) or []
        my_player = self._get_my_player(detail)
        my_kills = int(my_player.get('kills', 0) or 0)
        my_deaths = int(my_player.get('deaths', 0) or 0)
        my_assists = int(my_player.get('assists', 0) or 0)
        team_kills = sum(int(player.get('kills', 0) or 0) for player in my_team)
        team_damage = sum(int(player.get('total_damage', 0) or 0) for player in my_team)
        team_tank = sum(int(player.get('damage_taken', 0) or 0) for player in my_team)
        team_gold = sum(int(player.get('gold_earned', 0) or 0) for player in my_team)
        cs = self._calc_cs(my_player)
        duration = int(row['game_length'] or detail.get('game_length') or 0)
        duration_minutes = max(1.0, duration / 60.0)
        return {
            'game_id': row['game_id'],
            'game_mode': row['game_mode'],
            'queue_label': row['game_mode'],
            'timestamp': int(row['timestamp'] or 0),
            'duration': duration,
            'is_win': bool(row['is_win']),
            'champion_id': row['champion_id'],
            'champion_name': row['champion_name'],
            'level': int(my_player.get('level', 0) or 0),
            'kills': my_kills,
            'deaths': my_deaths,
            'assists': my_assists,
            'kda': self._calculate_kda(my_kills, my_deaths, my_assists),
            'game_score': row['game_score'] or my_player.get('game_score') or '',
            'spell1': my_player.get('spell1', 0),
            'spell2': my_player.get('spell2', 0),
            'perks': my_player.get('perks') or my_player.get('runes') or [],
            'items': my_player.get('items', []) or [],
            'kill_participation': self._calc_share(my_kills + my_assists, team_kills),
            'damage_share': self._calc_share(int(my_player.get('total_damage', 0) or 0), team_damage),
            'tank_share': self._calc_share(int(my_player.get('damage_taken', 0) or 0), team_tank),
            'gold_share': self._calc_share(int(my_player.get('gold_earned', 0) or 0), team_gold),
            'cs': cs,
            'cs_per_min': round(cs / duration_minutes, 2),
            'ally_brief': self._build_brief_players(my_team),
            'enemy_brief': self._build_brief_players(enemy_team),
        }

    def get_battle_history_page(self, page: int = 1, page_size: int = 20, filters: Optional[dict] = None) -> dict:
        filters = filters or {}
        rows = self._get_match_rows()
        now_ts = int(time.time())
        items = []
        for row in rows:
            detail = self._safe_detail(row)
            item = self._build_history_item(row, detail)
            if filters.get('game_mode') and item['game_mode'] != filters.get('game_mode'):
                continue
            champion_id = filters.get('champion_id')
            if champion_id:
                try:
                    if int(item['champion_id']) != int(champion_id):
                        continue
                except Exception:
                    continue
            result = filters.get('result')
            if result == 'win' and not item['is_win']:
                continue
            if result == 'lose' and item['is_win']:
                continue
            teammate = (filters.get('teammate') or '').strip()
            if teammate:
                ally_keys = {
                    player.get('identity', '') or player.get('display_name', '') or player.get('name', '')
                    for player in item['ally_brief']
                    if not player.get('is_me')
                }
                if teammate not in ally_keys:
                    continue
            time_range = filters.get('time_range')
            if time_range:
                days = {'7d': 7, '15d': 15, '30d': 30}.get(time_range)
                if days and item['timestamp'] < now_ts - days * 24 * 60 * 60:
                    continue
            items.append(item)

        page = max(1, int(page or 1))
        page_size = int(page_size or 20)
        if page_size not in (10, 20, 50):
            page_size = 20
        total = len(items)
        total_pages = max(1, (total + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
        start = (page - 1) * page_size
        end = start + page_size
        normalized_filters = {
            'game_mode': filters.get('game_mode') or '',
            'champion_id': filters.get('champion_id') or None,
            'result': filters.get('result') or '',
            'time_range': filters.get('time_range') or '',
            'teammate': filters.get('teammate') or '',
        }
        return {
            'items': items[start:end],
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'filters_applied': normalized_filters,
        }

    def get_battle_match_detail(self, game_id: int) -> Optional[dict]:
        detail = self.get_match_detail(game_id)
        if not detail:
            return None

        my_team = detail.get('my_team', []) or []
        enemy_team = detail.get('enemy_team', []) or []
        my_player = self._get_my_player(detail)
        my_position = my_player.get('position') or ''
        opponent = next((player for player in enemy_team if player.get('position') == my_position), None) if my_position else None
        if opponent is None and enemy_team:
            opponent = enemy_team[0]

        def _sorted(players, field):
            return sorted(players or [], key=lambda player: player.get(field, 0), reverse=True)

        team_kills = sum(int(player.get('kills', 0) or 0) for player in my_team)
        team_damage = sum(int(player.get('total_damage', 0) or 0) for player in my_team)
        team_tank = sum(int(player.get('damage_taken', 0) or 0) for player in my_team)
        team_gold = sum(int(player.get('gold_earned', 0) or 0) for player in my_team)
        cs = self._calc_cs(my_player)
        duration = int(detail.get('game_length') or 0)

        detail['overview_metrics'] = {
            'kda': self._calculate_kda(int(my_player.get('kills', 0) or 0), int(my_player.get('deaths', 0) or 0), int(my_player.get('assists', 0) or 0)),
            'kill_participation': self._calc_share(int(my_player.get('kills', 0) or 0) + int(my_player.get('assists', 0) or 0), team_kills),
            'damage_share': self._calc_share(int(my_player.get('total_damage', 0) or 0), team_damage),
            'tank_share': self._calc_share(int(my_player.get('damage_taken', 0) or 0), team_tank),
            'gold_share': self._calc_share(int(my_player.get('gold_earned', 0) or 0), team_gold),
            'cs': cs,
            'cs_per_min': round(cs / max(1.0, duration / 60.0), 2),
        }
        detail['damage_breakdown'] = {'my_team': _sorted(my_team, 'total_damage'), 'enemy_team': _sorted(enemy_team, 'total_damage')}
        detail['economy_breakdown'] = {'my_team': _sorted(my_team, 'gold_earned'), 'enemy_team': _sorted(enemy_team, 'gold_earned')}
        detail['vision_breakdown'] = {'my_team': _sorted(my_team, 'vision_score'), 'enemy_team': _sorted(enemy_team, 'vision_score')}
        detail['objective_breakdown'] = {'my_team': _sorted(my_team, 'turrets_killed'), 'enemy_team': _sorted(enemy_team, 'turrets_killed')}
        detail['laning_compare'] = {'my_player': my_player, 'opponent': opponent or {}}
        detail['teamfight_breakdown'] = {'my_team': _sorted(my_team, 'assists'), 'enemy_team': _sorted(enemy_team, 'assists')}
        return detail
