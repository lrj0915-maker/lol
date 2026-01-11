"""聊天发送服务 - 发送战绩信息到游戏聊天"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import config


class ChatSenderService:
    def __init__(self, api):
        self.api = api
    
    def send_to_chat(self, message):
        """发送消息到当前聊天"""
        try:
            # 获取当前对话
            conversations = self.api.get('/lol-chat/v1/conversations')
            if not conversations:
                print("无法获取对话列表")
                return False
            
            print(f"═══════════★找到 {len(conversations)} 个对话")
            for conv in conversations:
                print(f"  - 类型: {conv.get('type')}, ID: {conv.get('id')}")
            
            # 查找可用的聊天室（按优先级）
            target_conv = None
            priority_types = ['championSelect', 'lobby', 'postGame', 'customGame', 'practiceLobby']
            
            # 先找优先类型
            for ptype in priority_types:
                for conv in conversations:
                    if conv.get('type') == ptype:
                        target_conv = conv
                        print(f"选择聊天室: {ptype}")
                        break
                if target_conv:
                    break
            
            # 如果没找到，直接用第一个 chat 类型
            if not target_conv:
                for conv in conversations:
                    if conv.get('type') == 'chat':
                        target_conv = conv
                        print(f"选择chat聊天室: {conv.get('id')}")
                        break
            
            if not target_conv:
                print("未找到合适的聊天室")
                return False
            
            conv_id = target_conv.get('id')
            
            # 发送消息
            result = self.api.post(f'/lol-chat/v1/conversations/{conv_id}/messages', {
                'body': message,
                'type': 'chat'
            })
            
            print(f"发送结果: {result}")
            return result is not None and result is not False
            
        except Exception as e:
            print(f"发送聊天消息错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def format_team_analysis(self, analysis, options=None):
        """格式化队伍分析为聊天消息"""
        if not analysis:
            return None, None
        
        options = options or {}
        send_my_team = options.get('send_my_team', True)
        send_enemy = options.get('send_enemy', True)
        
        msg_my_team = None
        msg_enemy = None
        
        # 我方队伍消息
        if send_my_team and analysis.get('my_team'):
            my_team = analysis['my_team']
            
            # 找超神和牛马
            my_god = None
            my_noob = None
            for p in my_team:
                if p['rank'] == 'S' and not my_god:
                    my_god = p
                if p['rank'] == 'D' and not my_noob:
                    my_noob = p
            # 如果没有S级，取第一名；没有D级，取最后一名
            if not my_god and my_team:
                my_god = my_team[0]
            if not my_noob and my_team:
                my_noob = my_team[-1]
            
            lines = []
            lines.append("★═══════════════════════════════════════════★")
            lines.append("║  ★ ★ ★  我 方 战 力 天 梯  ★ ★ ★  ║")
            lines.append("★═══════════════════════════════════════════★")
            
            rank_labels = {'S': '神', 'A': '强', 'B': '中', 'C': '弱', 'D': '马'}
            for p in my_team:
                label = rank_labels.get(p['rank'], '中')
                name = p.get('name', '未知')[:12].ljust(12)
                wr = str(int(p['win_rate'])) + '%'
                kda = f"KDA {p['kda']}"
                streak = ''
                if p.get('streak', 0) >= 2:
                    streak = f"连胜{p['streak']}" if p.get('streak_type') == 'win' else f"连败{p['streak']}"
                lines.append(f"║ 【{label}】{name} ║ {wr.ljust(4)} ║ {kda.ljust(8)} ║ {streak.ljust(5)} ║")
            
            lines.append("★═══════════════════════════════════════════★")
            god_name = my_god['name'] if my_god else '无'
            noob_name = my_noob['name'] if my_noob else '无'
            lines.append(f"║  🔥本局超神: {god_name}   💀本局牛马: {noob_name}  ║")
            lines.append("★═══════════════════════════════════════════★")
            
            msg_my_team = '\n'.join(lines)
        
        # 对方关注消息
        if send_enemy:
            enemy = analysis.get('enemy_highlights', {})
            if enemy.get('god') or enemy.get('noob'):
                lines = []
                lines.append("★═══════════════════════════════════════════★")
                lines.append("║  ⚔️ ⚔️ ⚔️  敌 方 重 点 目 标  ⚔️ ⚔️ ⚔️  ║")
                lines.append("★═══════════════════════════════════════════★")
                
                if enemy.get('god'):
                    g = enemy['god']
                    name = g['name'][:14].ljust(14)
                    lines.append(f"║  🔥【超神】{name} ║ {int(g['win_rate'])}% ║ KDA {g['kda']}  ║")
                
                if enemy.get('noob'):
                    n = enemy['noob']
                    name = n['name'][:14].ljust(14)
                    lines.append(f"║  💀【牛马】{name} ║ {int(n['win_rate'])}% ║ KDA {n['kda']}  ║")
                
                lines.append("★═══════════════════════════════════════════★")
                lines.append("║     集火牛马！小心超神！稳住我们能赢！    ║")
                lines.append("★═══════════════════════════════════════════★")
                
                msg_enemy = '\n'.join(lines)
        
        return msg_my_team, msg_enemy
    
    def _get_rank_icon(self, rank):
        """获取档位图标"""
        icons = {
            'S': '🔥',
            'A': '⭐',
            'B': '😐',
            'C': '😰',
            'D': '💀'
        }
        return icons.get(rank, '')
    
    def _get_streak_text(self, player):
        """获取连胜/连败文本"""
        if player.get('streak', 0) >= 2:
            if player.get('streak_type') == 'win':
                return f" 连胜{player['streak']}"
            else:
                return f" 连败{player['streak']}"
        return ""
