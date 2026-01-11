"""战绩分析服务"""


class MatchHistoryService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._on_game_end_callback = None

    def set_game_end_callback(self, callback):
        """设置游戏结束回调"""
        self._on_game_end_callback = callback

    def start(self):
        """启动服务"""
        self.events.subscribe('/lol-end-of-game/v1/eog-stats-block', self._on_game_end)

    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-end-of-game/v1/eog-stats-block', self._on_game_end)

    def _on_game_end(self, uri, data):
        """游戏结束事件"""
        if data and self._on_game_end_callback:
            processed = self.process_match_data(data)
            self._on_game_end_callback(processed)

    def get_current_match_stats(self):
        """获取当前对局统计"""
        data = self.api.get_end_of_game_stats()
        if data:
            return self.process_match_data(data)
        return None

    def process_match_data(self, data):
        """处理对局数据"""
        if not data:
            return None

        game_id = data.get('gameId')
        game_length = data.get('gameLength', 0)
        
        # 游戏模式 - 尝试多种字段
        game_mode = data.get('gameMode') or ''
        game_type = data.get('gameType') or ''
        queue_type = data.get('queueType') or ''
        
        # 转换为友好名称
        if 'RANKED' in queue_type.upper() or 'RANKED' in game_type.upper():
            game_mode = '排位赛'
        elif 'ARAM' in game_mode.upper():
            game_mode = '大乱斗'
        elif 'URF' in game_mode.upper():
            game_mode = '无限火力'
        elif game_mode == 'CLASSIC':
            game_mode = '匹配赛'
        
        # 获取本地玩家
        local_player = data.get('localPlayer', {})
        local_puuid = local_player.get('puuid')

        # 处理队伍数据
        teams = data.get('teams', [])
        my_team = []
        enemy_team = []
        my_team_win = False

        for team in teams:
            is_winner = team.get('isWinningTeam', False)
            players = team.get('players', [])
            
            for player in players:
                player_data = self._process_player(player)
                
                if player.get('puuid') == local_puuid:
                    player_data['is_me'] = True
                    my_team_win = is_winner
                    my_team.append(player_data)
                elif any(p.get('puuid') == local_puuid for p in players):
                    player_data['is_me'] = False
                    my_team.append(player_data)
                else:
                    player_data['is_me'] = False
                    enemy_team.append(player_data)

        # 重新整理队伍
        all_players = []
        for team in teams:
            players = team.get('players', [])
            for player in players:
                player_data = self._process_player(player)
                player_data['is_me'] = player.get('puuid') == local_puuid
                player_data['is_my_team'] = any(
                    p.get('puuid') == local_puuid for p in players
                )
                if player_data['is_my_team']:
                    player_data['is_winner'] = my_team_win
                else:
                    player_data['is_winner'] = not my_team_win
                all_players.append(player_data)

        my_team = [p for p in all_players if p['is_my_team']]
        enemy_team = [p for p in all_players if not p['is_my_team']]

        return {
            'game_id': game_id,
            'game_mode': game_mode,
            'game_length': game_length,
            'is_win': my_team_win,
            'my_team': my_team,
            'enemy_team': enemy_team,
            'radar_data': self._calculate_radar_data(my_team)
        }

    def _process_player(self, player):
        """处理单个玩家数据"""
        stats = player.get('stats', {})
        
        # 尝试多种字段名获取召唤师名字
        summoner_name = (
            player.get('summonerName') or 
            player.get('riotIdGameName') or 
            player.get('gameName') or
            player.get('displayName') or
            ''
        )
        
        # 尝试多种字段名获取英雄名
        champion_name = (
            player.get('championName') or
            player.get('skinName') or
            ''
        )
        
        return {
            'summoner_name': summoner_name,
            'champion_id': player.get('championId', 0),
            'champion_name': champion_name,
            'position': player.get('selectedPosition') or player.get('detectedTeamPosition') or '',
            'level': stats.get('LEVEL', 0),
            
            # KDA
            'kills': stats.get('CHAMPIONS_KILLED', 0),
            'deaths': stats.get('NUM_DEATHS', 0),
            'assists': stats.get('ASSISTS', 0),
            
            # 伤害
            'total_damage': stats.get('TOTAL_DAMAGE_DEALT_TO_CHAMPIONS', 0),
            'physical_damage': stats.get('PHYSICAL_DAMAGE_DEALT_TO_CHAMPIONS', 0),
            'magic_damage': stats.get('MAGIC_DAMAGE_DEALT_TO_CHAMPIONS', 0),
            'true_damage': stats.get('TRUE_DAMAGE_DEALT_TO_CHAMPIONS', 0),
            'damage_taken': stats.get('TOTAL_DAMAGE_TAKEN', 0),
            'damage_to_buildings': stats.get('TOTAL_DAMAGE_DEALT_TO_BUILDINGS', 0),
            'damage_to_objectives': stats.get('TOTAL_DAMAGE_DEALT_TO_OBJECTIVES', 0),
            'largest_critical_strike': stats.get('LARGEST_CRITICAL_STRIKE', 0),
            'damage_self_mitigated': stats.get('TOTAL_DAMAGE_SELF_MITIGATED', 0),
            
            # 经济
            'gold_earned': stats.get('GOLD_EARNED', 0),
            'gold_spent': stats.get('GOLD_SPENT', 0),
            'minions_killed': stats.get('MINIONS_KILLED', 0),
            'neutral_minions_killed': stats.get('NEUTRAL_MINIONS_KILLED', 0),
            'items_purchased': stats.get('ITEMS_PURCHASED', 0),
            
            # 视野
            'vision_score': stats.get('VISION_SCORE', 0),
            'wards_placed': stats.get('WARD_PLACED', 0),
            'wards_killed': stats.get('WARD_KILLED', 0),
            'control_wards': stats.get('VISION_WARDS_BOUGHT_IN_GAME', 0),
            
            # 击杀相关
            'first_blood': stats.get('FIRST_BLOOD_KILL', False),
            'double_kills': stats.get('DOUBLE_KILLS', 0),
            'triple_kills': stats.get('TRIPLE_KILLS', 0),
            'quadra_kills': stats.get('QUADRA_KILLS', 0),
            'penta_kills': stats.get('PENTA_KILLS', 0),
            'largest_killing_spree': stats.get('LARGEST_KILLING_SPREE', 0),
            'killing_sprees': stats.get('KILLING_SPREES', 0),
            
            # 目标
            'turrets_killed': stats.get('TURRETS_KILLED', 0),
            'dragons_killed': stats.get('DRAGON_KILLS', 0),
            'barons_killed': stats.get('BARON_KILLS', 0),
            
            # 控制
            'cc_time': stats.get('TIME_CCING_OTHERS', 0),
            
            # 治疗
            'heal': stats.get('TOTAL_HEAL', 0),
            'heal_on_teammates': stats.get('TOTAL_HEAL_ON_TEAMMATES', 0),
            
            # 生存
            'longest_time_living': stats.get('LONGEST_TIME_SPENT_LIVING', 0),
            'time_spent_dead': stats.get('TOTAL_TIME_SPENT_DEAD', 0),
            
            # 技能使用
            'spell1_casts': stats.get('SPELL1_CASTS', 0),
            'spell2_casts': stats.get('SPELL2_CASTS', 0),
            
            # 装备
            'items': [
                stats.get('ITEM0', 0),
                stats.get('ITEM1', 0),
                stats.get('ITEM2', 0),
                stats.get('ITEM3', 0),
                stats.get('ITEM4', 0),
                stats.get('ITEM5', 0),
            ],
            
            # 召唤师技能
            'spell1': player.get('spell1Id', 0),
            'spell2': player.get('spell2Id', 0),
            
            # 评分 - 尝试多种字段
            'game_score': stats.get('GAME_SCORE') or stats.get('SCORE') or '',
        }

    def _calculate_radar_data(self, team):
        """计算六芒星数据"""
        if not team:
            return []

        # 计算队伍总和用于归一化
        totals = {
            'damage': sum(p['total_damage'] for p in team),
            'deaths': sum(p['deaths'] for p in team),
            'gold': sum(p['gold_earned'] for p in team),
            'vision': sum(p['vision_score'] for p in team),
            'objectives': sum(
                p['turrets_killed'] + p.get('dragons_killed', 0) + p.get('barons_killed', 0)
                for p in team
            ),
            'kills_assists': sum(p['kills'] + p['assists'] for p in team),
        }

        radar_data = []
        for player in team:
            # 计算各维度得分 (0-100)
            damage_score = (player['total_damage'] / totals['damage'] * 100) if totals['damage'] > 0 else 0
            
            # 生存：死亡越少越好
            avg_deaths = totals['deaths'] / len(team) if team else 1
            survival_score = max(0, 100 - (player['deaths'] / avg_deaths * 50)) if avg_deaths > 0 else 100
            
            gold_score = (player['gold_earned'] / totals['gold'] * 100) if totals['gold'] > 0 else 0
            vision_score = (player['vision_score'] / totals['vision'] * 100) if totals['vision'] > 0 else 0
            
            objective_score = 0
            if totals['objectives'] > 0:
                player_obj = player['turrets_killed'] + player.get('dragons_killed', 0) + player.get('barons_killed', 0)
                objective_score = (player_obj / totals['objectives'] * 100)
            
            teamfight_score = 0
            if totals['kills_assists'] > 0:
                teamfight_score = ((player['kills'] + player['assists']) / totals['kills_assists'] * 100)

            radar_data.append({
                'summoner_name': player['summoner_name'],
                'is_me': player.get('is_me', False),
                'dimensions': {
                    'output': round(damage_score, 1),      # 输出
                    'survival': round(survival_score, 1),  # 生存
                    'development': round(gold_score, 1),   # 发育
                    'teamfight': round(teamfight_score, 1),# 团战
                    'vision': round(vision_score, 1),      # 视野
                    'objective': round(objective_score, 1) # 目标
                }
            })

        return radar_data
