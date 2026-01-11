"""队伍分析服务 - 选人阶段查询队友/对手战绩"""
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import config


class TeamAnalyzerService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._analysis_result = None
        self._analyzing = False
        self._sent_this_session = False  # 本次选人是否已发送
        self._current_session_id = None  # 当前选人会话ID
        self._callback = None
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def set_callback(self, callback):
        """设置分析完成回调"""
        self._callback = callback
    
    def start(self):
        """启动服务，订阅选人阶段事件"""
        self.events.subscribe('/lol-champ-select/v1/session', self._on_champ_select)
        self.events.subscribe('/lol-gameflow/v1/gameflow-phase', self._on_phase_change)
    
    def stop(self):
        """停止服务"""
        self.events.unsubscribe('/lol-champ-select/v1/session', self._on_champ_select)
        self.events.unsubscribe('/lol-gameflow/v1/gameflow-phase', self._on_phase_change)
    
    def _on_phase_change(self, uri, data):
        """游戏阶段变化时重置状态"""
        if data in ['None', 'Lobby', 'EndOfGame', 'Matchmaking']:
            # 离开选人阶段，重置状态
            print(f"[TeamAnalyzer] 阶段变化: {data}，重置发送状态")
            self._sent_this_session = False
            self._current_session_id = None
            self._analyzing = False
    
    def _on_champ_select(self, uri, data):
        """进入选人阶段时触发分析"""
        if not data:
            return
        
        # 获取会话ID，用于判断是否同一局选人
        session_id = data.get('gameId') or data.get('counter')
        
        # 如果是同一局选人且已发送，不再重复
        if session_id and session_id == self._current_session_id and self._sent_this_session:
            return
        
        # 新的选人会话
        if session_id != self._current_session_id:
            self._current_session_id = session_id
            self._sent_this_session = False
        
        if not self._analyzing:
            self._analyzing = True
            threading.Thread(target=self._analyze_teams, daemon=True).start()
    
    def _analyze_teams(self):
        """分析双方队伍"""
        try:
            # 获取当前召唤师
            current_summoner = self.api.get_current_summoner()
            my_summoner_id = current_summoner.get('summonerId') if current_summoner else None
            my_puuid = current_summoner.get('puuid') if current_summoner else None
            
            print(f"当前召唤师: {current_summoner.get('displayName') if current_summoner else 'None'}")
            
            # 尝试获取选人会话
            session = self.api.get('/lol-champ-select/v1/session')
            
            my_team_results = []
            their_team_results = []
            
            if session and session.get('myTeam'):
                # 在选人阶段
                print("在选人阶段，分析队伍...")
                my_team = session.get('myTeam', [])
                their_team = session.get('theirTeam', [])
                
                for player in my_team:
                    summoner_id = player.get('summonerId')
                    champion_id = player.get('championId') or player.get('championPickIntent')
                    if summoner_id and summoner_id > 0:
                        result = self._analyze_player(summoner_id, summoner_id == my_summoner_id, champion_id)
                        if result:
                            my_team_results.append(result)
                
                for player in their_team:
                    summoner_id = player.get('summonerId')
                    champion_id = player.get('championId') or player.get('championPickIntent')
                    if summoner_id and summoner_id > 0:
                        result = self._analyze_player(summoner_id, False, champion_id)
                        if result:
                            their_team_results.append(result)
            else:
                # 不在选人阶段，尝试从游戏中或最近对局获取队友
                print("不在选人阶段，尝试获取当前游戏或最近对局队友...")
                
                # 先尝试获取当前游戏中的队友
                game_data = self.api.get('/lol-gameflow/v1/session')
                found_from_game = False
                
                if game_data and game_data.get('gameData'):
                    print("从当前游戏获取队友...")
                    gd = game_data['gameData']
                    
                    # 尝试不同的字段名
                    team_one = gd.get('teamOne') or gd.get('playerChampionSelections', {}).get('teamOne', [])
                    team_two = gd.get('teamTwo') or gd.get('playerChampionSelections', {}).get('teamTwo', [])
                    
                    # 如果没有teamOne/teamTwo，尝试从queue获取
                    if not team_one and gd.get('queue'):
                        print(f"gameData结构: {list(gd.keys())}")
                    
                    # 找到自己在哪个队伍
                    my_team = None
                    enemy_team = None
                    
                    if team_one:
                        for player in team_one:
                            sid = player.get('summonerId') or player.get('summonerInternalName')
                            if sid == my_summoner_id or player.get('puuid') == my_puuid:
                                my_team = team_one
                                enemy_team = team_two
                                break
                    
                    if not my_team and team_two:
                        for player in team_two:
                            sid = player.get('summonerId') or player.get('summonerInternalName')
                            if sid == my_summoner_id or player.get('puuid') == my_puuid:
                                my_team = team_two
                                enemy_team = team_one
                                break
                    
                    if my_team:
                        found_from_game = True
                        print(f"找到我方队伍: {len(my_team)} 人")
                        for player in my_team:
                            summoner_id = player.get('summonerId')
                            if summoner_id and summoner_id > 0:
                                is_me = summoner_id == my_summoner_id
                                result = self._analyze_player(summoner_id, is_me)
                                if result:
                                    my_team_results.append(result)
                        
                        if enemy_team:
                            print(f"找到对方队伍: {len(enemy_team)} 人")
                            for player in enemy_team:
                                summoner_id = player.get('summonerId')
                                if summoner_id and summoner_id > 0:
                                    result = self._analyze_player(summoner_id, False)
                                    if result:
                                        their_team_results.append(result)
                
                # 从最近一场对局获取（无论是否从游戏中获取到）
                if not found_from_game and my_puuid:
                    print("从最近对局获取队友...")
                    matches = self.api.get(f'/lol-match-history/v1/products/lol/{my_puuid}/matches?begIndex=0&endIndex=1')
                    if matches:
                        games = matches.get('games', {})
                        if isinstance(games, dict):
                            games = games.get('games', [])
                        
                        if games:
                            last_game = games[0]
                            participant_identities = last_game.get('participantIdentities', [])
                            participants = last_game.get('participants', [])
                            
                            print(f"最近对局: {len(participant_identities)} 个玩家")
                            
                            # 找到自己的队伍ID
                            my_team_id = None
                            for i, pi in enumerate(participant_identities):
                                player_info = pi.get('player', {})
                                if player_info.get('puuid') == my_puuid or player_info.get('summonerId') == my_summoner_id:
                                    pid = pi.get('participantId')
                                    for p in participants:
                                        if p.get('participantId') == pid:
                                            my_team_id = p.get('teamId')
                                            print(f"我的队伍ID: {my_team_id}")
                                            break
                                    break
                            
                            # 分析所有玩家
                            if my_team_id:
                                for pi in participant_identities:
                                    player_info = pi.get('player', {})
                                    summoner_id = player_info.get('summonerId')
                                    puuid = player_info.get('puuid')
                                    
                                    if not summoner_id:
                                        continue
                                    
                                    # 找到对应的participant获取teamId
                                    pid = pi.get('participantId')
                                    team_id = None
                                    for p in participants:
                                        if p.get('participantId') == pid:
                                            team_id = p.get('teamId')
                                            break
                                    
                                    is_me = puuid == my_puuid or summoner_id == my_summoner_id
                                    result = self._analyze_player(summoner_id, is_me)
                                    
                                    if result:
                                        if team_id == my_team_id:
                                            my_team_results.append(result)
                                        else:
                                            their_team_results.append(result)
                
                # 如果还是没数据，至少分析自己
                if not my_team_results and my_summoner_id:
                    print("只分析当前召唤师...")
                    result = self._analyze_player(my_summoner_id, True)
                    if result:
                        my_team_results.append(result)
            
            # 排序：按评分降序
            my_team_results.sort(key=lambda x: x['score'], reverse=True)
            their_team_results.sort(key=lambda x: x['score'], reverse=True)
            
            # 找出对方超神和牛马
            # 超神：评分最高且>=70
            enemy_god = their_team_results[0] if their_team_results and their_team_results[0]['score'] >= 70 else None
            # 牛马：直接取评分最低的那个
            enemy_noob = their_team_results[-1] if their_team_results else None
            
            self._analysis_result = {
                'my_team': my_team_results,
                'enemy_highlights': {
                    'god': enemy_god,
                    'noob': enemy_noob
                },
                'my_team_avg': sum(p['score'] for p in my_team_results) / len(my_team_results) if my_team_results else 0,
                'enemy_avg': sum(p['score'] for p in their_team_results) / len(their_team_results) if their_team_results else 0
            }
            
            print(f"分析完成: 我方{len(my_team_results)}人, 对方{len(their_team_results)}人")
            
            if self._callback:
                self._callback(self._analysis_result)
                self._sent_this_session = True  # 标记已发送
                
        except Exception as e:
            print(f"队伍分析错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._analyzing = False
    
    def _analyze_player(self, summoner_id, is_me=False, champion_id=None):
        """分析单个玩家"""
        try:
            # 获取召唤师信息
            summoner = self.api.get(f'/lol-summoner/v1/summoners/{summoner_id}')
            if not summoner:
                print(f"无法获取召唤师信息: {summoner_id}")
                return None
            
            puuid = summoner.get('puuid')
            name = summoner.get('displayName') or summoner.get('gameName') or '未知'
            
            print(f"分析玩家: {name} (puuid: {puuid}, champion: {champion_id})")
            
            # 获取最近20场战绩
            matches = self.api.get(f'/lol-match-history/v1/products/lol/{puuid}/matches?begIndex=0&endIndex=20')
            if not matches:
                print(f"无法获取战绩: {name}")
                return self._default_result(name, is_me, champion_id)
            
            games = matches.get('games', {})
            if isinstance(games, dict):
                games = games.get('games', [])
            
            if not games:
                print(f"无战绩数据: {name}")
                return self._default_result(name, is_me, champion_id)
            
            print(f"获取到 {len(games)} 场战绩")
            
            # 计算统计数据
            wins = 0
            total_kills = 0
            total_deaths = 0
            total_assists = 0
            streak = 0
            streak_type = None  # 'win' or 'lose'
            
            for i, game in enumerate(games):
                participants = game.get('participants', [])
                if not participants:
                    continue
                
                p = participants[0]
                stats = p.get('stats', {})
                
                win = stats.get('win', False)
                kills = stats.get('kills', 0)
                deaths = stats.get('deaths', 0)
                assists = stats.get('assists', 0)
                
                if win:
                    wins += 1
                
                total_kills += kills
                total_deaths += deaths
                total_assists += assists
                
                # 计算连胜/连败（只看最近的连续）
                if i == 0:
                    streak_type = 'win' if win else 'lose'
                    streak = 1
                elif (win and streak_type == 'win') or (not win and streak_type == 'lose'):
                    streak += 1
                else:
                    pass  # 连续中断
            
            game_count = len(games)
            win_rate = (wins / game_count * 100) if game_count > 0 else 50
            kda = (total_kills + total_assists) / max(1, total_deaths)
            avg_deaths = total_deaths / game_count if game_count > 0 else 0
            
            # 计算综合评分
            score = self._calculate_score(win_rate, kda, streak, streak_type)
            rank = self._get_rank(score)
            
            result = {
                'name': name,
                'is_me': is_me,
                'champion_id': champion_id,
                'win_rate': round(win_rate, 1),
                'kda': round(kda, 2),
                'avg_deaths': round(avg_deaths, 1),
                'streak': streak if streak >= 2 else 0,
                'streak_type': streak_type if streak >= 2 else None,
                'score': round(score, 1),
                'rank': rank,
                'games': game_count
            }
            print(f"分析结果: {result}")
            return result
            
        except Exception as e:
            print(f"分析玩家错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _default_result(self, name, is_me, champion_id=None):
        """无数据时的默认结果"""
        return {
            'name': name,
            'is_me': is_me,
            'champion_id': champion_id,
            'is_me': is_me,
            'win_rate': 50,
            'kda': 2.0,
            'streak': 0,
            'streak_type': None,
            'score': 50,
            'rank': 'B',
            'games': 0
        }
    
    def _calculate_score(self, win_rate, kda, streak, streak_type):
        """计算综合评分"""
        # 胜率分 (40%) - 直接映射
        win_score = min(100, max(0, win_rate))
        
        # KDA分 (30%) - KDA * 20, 上限100
        kda_score = min(100, kda * 20)
        
        # 连胜连败分 (20%)
        if streak_type == 'win':
            streak_score = min(100, 50 + streak * 10)
        elif streak_type == 'lose':
            streak_score = max(0, 50 - streak * 10)
        else:
            streak_score = 50
        
        # 综合
        total = win_score * 0.4 + kda_score * 0.3 + streak_score * 0.2 + 50 * 0.1
        return total
    
    def _get_rank(self, score):
        """根据评分获取档位"""
        if score >= 85:
            return 'S'
        elif score >= 70:
            return 'A'
        elif score >= 50:
            return 'B'
        elif score >= 35:
            return 'C'
        else:
            return 'D'
    
    def get_analysis_result(self):
        """获取分析结果"""
        return self._analysis_result
    
    def clear_result(self):
        """清除结果（离开选人阶段时）"""
        self._analysis_result = None
    
    def manual_analyze(self):
        """手动触发分析（用于测试或非选人阶段）"""
        if not self._analyzing:
            self._analyzing = True
            threading.Thread(target=self._analyze_teams, daemon=True).start()
            return True
        return False
