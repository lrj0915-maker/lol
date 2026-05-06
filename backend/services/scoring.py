"""玩家评分共享模块 — team_analyzer 和 ingame_chat 共用"""


def calculate_player_score(win_rate: float, kda: float, streak: int, streak_type: str | None) -> float:
    """计算综合评分（0-100）"""
    # 胜率分 (40%)
    win_score = min(100, max(0, win_rate))
    # KDA分 (30%)
    kda_score = min(100, kda * 20)
    # 连胜连败分 (20%)
    if streak_type == 'win':
        streak_score = min(100, 50 + streak * 10)
    elif streak_type == 'lose':
        streak_score = max(0, 50 - streak * 10)
    else:
        streak_score = 50
    return win_score * 0.4 + kda_score * 0.3 + streak_score * 0.2 + 50 * 0.1


def get_rank(score: float) -> str:
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


def compute_match_stats(games: list, puuid: str) -> dict:
    """从战绩列表计算统计数据，返回 wins/kills/deaths/assists/streak/streak_type/game_count"""
    wins = 0
    total_kills = 0
    total_deaths = 0
    total_assists = 0
    streak = 0
    streak_type = None
    streak_broken = False  # 连续是否已中断

    for i, game in enumerate(games):
        participants = game.get('participants', [])
        participant_identities = game.get('participantIdentities', [])

        # 找到该玩家的 participantId
        my_pid = None
        if participant_identities:
            for identity in participant_identities:
                if identity.get('player', {}).get('puuid') == puuid:
                    my_pid = identity.get('participantId')
                    break

        # 找到对应的 participant 数据
        p = None
        if my_pid is not None:
            for participant in participants:
                if participant.get('participantId') == my_pid:
                    p = participant
                    break
        elif participants:
            # 兼容：没有 identities 时取第一个
            p = participants[0]

        if p is None:
            continue

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

        # 连胜连败：只从第一场开始连续计算，中断即停止
        if not streak_broken:
            if streak_type is None:
                # 第一场
                streak_type = 'win' if win else 'lose'
                streak = 1
            elif streak_type == 'win' and win:
                streak += 1
            elif streak_type == 'lose' and not win:
                streak += 1
            else:
                streak_broken = True  # 连续中断，后续不再累加

    game_count = len(games)
    return {
        'wins': wins,
        'total_kills': total_kills,
        'total_deaths': total_deaths,
        'total_assists': total_assists,
        'streak': streak,
        'streak_type': streak_type,
        'game_count': game_count,
    }
