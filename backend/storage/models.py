"""数据模型"""
from dataclasses import dataclass
import json


@dataclass
class MatchRecord:
    game_id: int
    game_mode: str
    game_length: int
    is_win: bool
    champion_id: int
    champion_name: str
    kills: int
    deaths: int
    assists: int
    game_score: str
    timestamp: int
    data_json: str  # 完整数据 JSON

    def to_dict(self):
        return {
            'game_id': self.game_id,
            'game_mode': self.game_mode,
            'game_length': self.game_length,
            'is_win': self.is_win,
            'champion_id': self.champion_id,
            'champion_name': self.champion_name,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'game_score': self.game_score,
            'timestamp': self.timestamp,
            'full_data': json.loads(self.data_json) if self.data_json else None
        }

    @classmethod
    def from_match_data(cls, data: dict, timestamp: int):
        """从战绩数据创建记录"""
        my_player = None
        for player in data.get('my_team', []):
            if player.get('is_me'):
                my_player = player
                break

        if not my_player:
            return None

        return cls(
            game_id=data.get('game_id', 0),
            game_mode=data.get('game_mode', ''),
            game_length=data.get('game_length', 0),
            is_win=data.get('is_win', False),
            champion_id=my_player.get('champion_id', 0),
            champion_name=my_player.get('champion_name', ''),
            kills=my_player.get('kills', 0),
            deaths=my_player.get('deaths', 0),
            assists=my_player.get('assists', 0),
            game_score=str(my_player.get('game_score', '')),
            timestamp=timestamp,
            data_json=json.dumps(data, ensure_ascii=False)
        )
