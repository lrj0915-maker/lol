"""SQLite 数据库操作"""
import os
import sqlite3
import time
import json
from typing import List, Optional

from storage.models import MatchRecord

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
DB_FILE = os.path.join(DATA_DIR, 'history.db')

# 保留天数
RETENTION_DAYS = 30


class Database:
    def __init__(self):
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DB_FILE) as conn:
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
            conn.commit()

    def save_match(self, record: MatchRecord) -> bool:
        """保存对局记录"""
        try:
            with sqlite3.connect(DB_FILE) as conn:
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
        except Exception:
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

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
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
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
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
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                'DELETE FROM match_history WHERE timestamp < ?',
                (cutoff,)
            )
            conn.commit()

    def get_stats(self) -> dict:
        """获取统计信息"""
        with sqlite3.connect(DB_FILE) as conn:
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
