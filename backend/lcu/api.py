"""LCU API 封装"""


class LCUAPI:
    def __init__(self, connection):
        self.conn = connection

    def get(self, endpoint):
        """通用GET请求"""
        return self.conn.get(endpoint)

    def post(self, endpoint, data=None):
        """通用POST请求"""
        return self.conn.post(endpoint, data)

    # ========== 玩家信息 ==========
    
    def get_current_summoner(self):
        """获取当前登录的召唤师信息"""
        return self.conn.get('/lol-summoner/v1/current-summoner')

    def get_summoner_by_name(self, name):
        """根据名字获取召唤师信息"""
        return self.conn.get(f'/lol-summoner/v1/summoners?name={name}')

    # ========== 游戏状态 ==========
    
    def get_gameflow_phase(self):
        """获取当前游戏阶段"""
        return self.conn.get('/lol-gameflow/v1/gameflow-phase')

    def get_lobby(self):
        """获取当前房间信息"""
        return self.conn.get('/lol-lobby/v2/lobby')

    def get_champ_select_session(self):
        """获取选人阶段信息"""
        return self.conn.get('/lol-champ-select/v1/session')

    # ========== 自动准备 ==========
    
    def accept_match(self):
        """接受对局"""
        return self.conn.post('/lol-matchmaking/v1/ready-check/accept')

    def decline_match(self):
        """拒绝对局"""
        return self.conn.post('/lol-matchmaking/v1/ready-check/decline')

    # ========== 选人 ==========
    
    def get_pickable_champions(self):
        """获取可选英雄列表"""
        return self.conn.get('/lol-champ-select/v1/pickable-champion-ids')

    def get_bannable_champions(self):
        """获取可禁用英雄列表"""
        return self.conn.get('/lol-champ-select/v1/bannable-champion-ids')

    def hover_champion(self, action_id, champion_id):
        """预选英雄"""
        return self.conn.patch(
            f'/lol-champ-select/v1/session/actions/{action_id}',
            {'championId': champion_id}
        )

    def lock_champion(self, action_id, champion_id):
        """锁定英雄"""
        self.hover_champion(action_id, champion_id)
        return self.conn.post(
            f'/lol-champ-select/v1/session/actions/{action_id}/complete'
        )

    # ========== 战绩 ==========
    
    def get_match_history(self, puuid, beg_index=0, end_index=20):
        """获取对局历史"""
        return self.conn.get(
            f'/lol-match-history/v1/products/lol/{puuid}/matches'
            f'?begIndex={beg_index}&endIndex={end_index}'
        )

    def get_match_details(self, game_id):
        """获取对局详情"""
        return self.conn.get(f'/lol-match-history/v1/games/{game_id}')

    def get_end_of_game_stats(self):
        """获取游戏结束统计"""
        return self.conn.get('/lol-end-of-game/v1/eog-stats-block')

    # ========== 英雄数据 ==========
    
    def get_all_champions(self):
        """获取所有英雄信息"""
        return self.conn.get('/lol-game-data/assets/v1/champion-summary.json')

    def get_champion_by_id(self, champion_id):
        """获取指定英雄信息"""
        return self.conn.get(f'/lol-game-data/assets/v1/champions/{champion_id}.json')

    # ========== 段位 ==========
    
    def get_ranked_stats(self, puuid):
        """获取段位信息"""
        return self.conn.get(f'/lol-ranked/v1/ranked-stats/{puuid}')
