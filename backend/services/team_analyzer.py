"""队伍分析服务 - 选人阶段查询队友/对手战绩"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from config import config
from logger import get_logger
from services.scoring import calculate_player_score, get_rank, compute_match_stats

log = get_logger('TeamAnalyzer')


class TeamAnalyzerService:
    def __init__(self, api, events):
        self.api = api
        self.events = events
        self._analysis_result = None
        self._analyzing = False
        self._analyzing_lock = threading.RLock()
        self._sent_this_session = False  # 本次选人是否已发送
        self._current_session_id = None  # 当前选人会话ID
        self._callback = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._player_cache = {}
        self._cache_ttl_seconds = 90
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
            log.debug("阶段变化: %s，重置发送状态", data)
            self._sent_this_session = False
            self._current_session_id = None
            with self._analyzing_lock:
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
        
        with self._analyzing_lock:
            if self._analyzing:
                return
            self._analyzing = True
        threading.Thread(target=self._analyze_teams, daemon=True).start()
    
    def _analyze_teams(self):
        """分析双方队伍"""
        try:
            self._cleanup_cache()
            # 获取当前召唤师
            current_summoner = self.api.get_current_summoner()
            my_summoner_id = current_summoner.get('summonerId') if current_summoner else None
            my_puuid = current_summoner.get('puuid') if current_summoner else None
            
            log.debug("当前召唤师: %s", current_summoner.get('displayName') if current_summoner else 'None')
            
            # 尝试获取选人会话
            session = self.api.get('/lol-champ-select/v1/session')
            
            my_team_results = []
            their_team_results = []
            
            if session and session.get('myTeam'):
                # 在选人阶段
                log.debug("在选人阶段，分析队伍...")
                my_team = session.get('myTeam', [])
                their_team = session.get('theirTeam', [])
                
                # 收集需要分析的玩家参数
                my_team_tasks = []
                for player in my_team:
                    summoner_id = player.get('summonerId')
                    champion_id = player.get('championId') or player.get('championPickIntent')
                    if summoner_id and summoner_id > 0:
                        my_team_tasks.append((summoner_id, summoner_id == my_summoner_id, champion_id))
                
                their_team_tasks = []
                for player in their_team:
                    summoner_id = player.get('summonerId')
                    champion_id = player.get('championId') or player.get('championPickIntent')
                    if summoner_id and summoner_id > 0:
                        their_team_tasks.append((summoner_id, False, champion_id))
                
                # 并发分析所有玩家
                all_tasks = my_team_tasks + their_team_tasks
                futures = {
                    self._executor.submit(self._analyze_player, sid, is_me, cid): ('my' if i < len(my_team_tasks) else 'their')
                    for i, (sid, is_me, cid) in enumerate(all_tasks)
                }
                for future in futures:
                    team_tag = futures[future]
                    try:
                        result = future.result(timeout=15)
                        if result:
                            if team_tag == 'my':
                                my_team_results.append(result)
                            else:
                                their_team_results.append(result)
                    except Exception as e:
                        log.warning("并发分析异常: %s", e)
            else:
                # 不在选人阶段，尝试从游戏中或最近对局获取队友
                log.debug("不在选人阶段，尝试获取当前游戏或最近对局队友...")
                
                # 先尝试获取当前游戏中的队友
                game_data = self.api.get('/lol-gameflow/v1/session')
                found_from_game = False
                
                if game_data and game_data.get('gameData'):
                    log.debug("从当前游戏获取队友...")
                    gd = game_data['gameData']
                    
                    # 尝试不同的字段名
                    team_one = gd.get('teamOne') or gd.get('playerChampionSelections', {}).get('teamOne', [])
                    team_two = gd.get('teamTwo') or gd.get('playerChampionSelections', {}).get('teamTwo', [])
                    
                    # 如果没有teamOne/teamTwo，尝试从queue获取
                    if not team_one and gd.get('queue'):
                        log.debug("gameData结构: %s", list(gd.keys()))
                    
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
                        log.debug("找到我方队伍: %d 人", len(my_team))
                        for player in my_team:
                            summoner_id = player.get('summonerId')
                            if summoner_id and summoner_id > 0:
                                is_me = summoner_id == my_summoner_id
                                result = self._analyze_player(summoner_id, is_me)
                                if result:
                                    my_team_results.append(result)
                        
                        if enemy_team:
                            log.debug("找到对方队伍: %d 人", len(enemy_team))
                            for player in enemy_team:
                                summoner_id = player.get('summonerId')
                                if summoner_id and summoner_id > 0:
                                    result = self._analyze_player(summoner_id, False)
                                    if result:
                                        their_team_results.append(result)
                
                # 从最近一场对局获取（无论是否从游戏中获取到）
                if not found_from_game and my_puuid:
                    log.debug("从最近对局获取队友...")
                    matches = self.api.get(f'/lol-match-history/v1/products/lol/{my_puuid}/matches?begIndex=0&endIndex=1')
                    if matches:
                        games = matches.get('games', {})
                        if isinstance(games, dict):
                            games = games.get('games', [])
                        
                        if games:
                            last_game = games[0]
                            participant_identities = last_game.get('participantIdentities', [])
                            participants = last_game.get('participants', [])
                            
                            log.debug("最近对局: %d 个玩家", len(participant_identities))
                            
                            # 找到自己的队伍ID
                            my_team_id = None
                            for i, pi in enumerate(participant_identities):
                                player_info = pi.get('player', {})
                                if player_info.get('puuid') == my_puuid or player_info.get('summonerId') == my_summoner_id:
                                    pid = pi.get('participantId')
                                    for p in participants:
                                        if p.get('participantId') == pid:
                                            my_team_id = p.get('teamId')
                                            log.debug("我的队伍ID: %s", my_team_id)
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
                    log.debug("只分析当前召唤师...")
                    result = self._analyze_player(my_summoner_id, True)
                    if result:
                        my_team_results.append(result)
            
            # 排序：按评分降序
            my_team_results.sort(key=lambda x: x['score'], reverse=True)
            their_team_results.sort(key=lambda x: x['score'], reverse=True)
            
            # 找出对方超神和牛马
            enemy_god = their_team_results[0] if their_team_results else None
            enemy_noob = their_team_results[-1] if their_team_results else None
            
            self._analysis_result = {
                'my_team': my_team_results,
                'enemy_team': their_team_results,  # 新增：对方全部队员
                'enemy_highlights': {
                    'god': enemy_god,
                    'noob': enemy_noob
                },
                'my_team_avg': sum(p['score'] for p in my_team_results) / len(my_team_results) if my_team_results else 0,
                'enemy_avg': sum(p['score'] for p in their_team_results) / len(their_team_results) if their_team_results else 0
            }
            
            log.info("分析完成: 我方%d人, 对方%d人", len(my_team_results), len(their_team_results))
            
            if self._callback:
                self._callback(self._analysis_result)
                self._sent_this_session = True  # 标记已发送
                
        except Exception as e:
            log.error("队伍分析错误: %s", e, exc_info=True)

        finally:
            with self._analyzing_lock:
                self._analyzing = False

    def _cleanup_cache(self):
        now = time.time()
        expired_keys = [
            key for key, (_, ts) in self._player_cache.items()
            if now - ts > self._cache_ttl_seconds
        ]
        for key in expired_keys:
            self._player_cache.pop(key, None)
    
    def _analyze_player(self, summoner_id, is_me=False, champion_id=None):
        """分析单个玩家"""
        try:
            cache_key = (int(summoner_id), int(champion_id or 0))
            cached = self._player_cache.get(cache_key)
            if cached and (time.time() - cached[1]) <= self._cache_ttl_seconds:
                return dict(cached[0])

            # 获取召唤师信息
            summoner = self.api.get(f'/lol-summoner/v1/summoners/{summoner_id}')
            if not summoner:
                log.warning("无法获取召唤师信息: %s", summoner_id)
                return None
            
            puuid = summoner.get('puuid')
            name = summoner.get('displayName') or summoner.get('gameName') or '未知'
            
            log.debug("分析玩家: %s (puuid: %s, champion: %s)", name, puuid, champion_id)
            
            # 获取最近20场战绩
            matches = self.api.get(f'/lol-match-history/v1/products/lol/{puuid}/matches?begIndex=0&endIndex=20')
            if not matches:
                log.warning("无法获取战绩: %s", name)
                result = self._default_result(name, is_me, champion_id)
                self._player_cache[cache_key] = (dict(result), time.time())
                return result
            
            games = matches.get('games', {})
            if isinstance(games, dict):
                games = games.get('games', [])
            
            if not games:
                log.debug("无战绩数据: %s", name)
                result = self._default_result(name, is_me, champion_id)
                self._player_cache[cache_key] = (dict(result), time.time())
                return result
            
            log.debug("获取到 %d 场战绩", len(games))
            
            # 使用共享模块计算统计数据
            ms = compute_match_stats(games, puuid)
            game_count = ms['game_count']
            win_rate = (ms['wins'] / game_count * 100) if game_count > 0 else 50
            kda = (ms['total_kills'] + ms['total_assists']) / max(1, ms['total_deaths'])
            avg_deaths = ms['total_deaths'] / game_count if game_count > 0 else 0
            streak = ms['streak']
            streak_type = ms['streak_type']
            
            # 计算综合评分
            score = calculate_player_score(win_rate, kda, streak, streak_type)
            rank = get_rank(score)
            
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
            log.debug("分析结果: %s", result)
            self._player_cache[cache_key] = (dict(result), time.time())
            return result
            
        except Exception as e:
            log.error("分析玩家错误: %s", e, exc_info=True)
            return None
    
    def _default_result(self, name, is_me, champion_id=None):
        """无数据时的默认结果"""
        return {
            'name': name,
            'is_me': is_me,
            'champion_id': champion_id,
            'win_rate': 50,
            'kda': 2.0,
            'streak': 0,
            'streak_type': None,
            'score': 50,
            'rank': 'B',
            'games': 0
        }
    
    def get_analysis_result(self):
        """获取分析结果"""
        return self._analysis_result
    
    def clear_result(self):
        """清除结果（离开选人阶段时）"""
        self._analysis_result = None
    
    def manual_analyze(self):
        """手动触发分析（用于测试或非选人阶段）"""
        with self._analyzing_lock:
            if self._analyzing:
                return False
            self._analyzing = True
        threading.Thread(target=self._analyze_teams, daemon=True).start()
        return True
