<template>
  <div class="player-card" :class="{ 'is-me': player.is_me }">
    <!-- 头部 -->
    <div class="card-header">
      <div class="champion-avatar">
        <img v-if="championIcon" :src="championIcon" :alt="player.champion_name" />
        <span v-else class="avatar-placeholder">{{ player.champion_name?.charAt(0) || '?' }}</span>
      </div>
      <div class="player-info">
        <div class="player-name">
          {{ player.summoner_name || player.champion_name }}
          <span class="me-badge" v-if="player.is_me">★</span>
        </div>
        <div class="champion-name">{{ player.champion_name }}</div>
      </div>
      <div class="score-badge" :class="scoreClass">
        <span class="score-value">{{ player.game_score || '-' }}</span>
        <span class="score-label">评分</span>
      </div>
    </div>
    
    <!-- KDA -->
    <div class="kda-section">
      <div class="kda-main">
        <span class="kills">{{ player.kills }}</span>/<span class="deaths">{{ player.deaths }}</span>/<span class="assists">{{ player.assists }}</span>
      </div>
      <div class="kda-ratio" :class="kdaClass">{{ formatKDA(player.kills, player.deaths, player.assists) }} KDA</div>
    </div>
    
    <!-- 参与率 -->
    <div class="participation-row">
      <div class="part-item"><span class="part-value">{{ participationPercent }}%</span><span class="part-label">参团</span></div>
      <div class="part-item"><span class="part-value">{{ deathSharePercent }}%</span><span class="part-label">死亡占比</span></div>
      <div class="part-item"><span class="part-value">{{ killParticipation }}%</span><span class="part-label">击杀参与</span></div>
    </div>
    
    <!-- 徽章 -->
    <div class="badges-row" v-if="player.penta_kills || player.quadra_kills || player.triple_kills || player.first_blood">
      <span class="badge penta" v-if="player.penta_kills">🔥五杀</span>
      <span class="badge quadra" v-else-if="player.quadra_kills">🔥四杀</span>
      <span class="badge triple" v-else-if="player.triple_kills">⚡三杀</span>
      <span class="badge first-blood" v-if="player.first_blood">⚔️一血</span>
    </div>
    
    <!-- 数据条 -->
    <div class="stats-section">
      <div class="stat-row">
        <span class="stat-label">伤害</span>
        <div class="stat-bar"><div class="stat-fill damage" :style="{ width: damagePercent + '%' }"></div></div>
        <span class="stat-value">{{ formatNumber(player.total_damage) }}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">承伤</span>
        <div class="stat-bar"><div class="stat-fill tank" :style="{ width: tankPercent + '%' }"></div></div>
        <span class="stat-value">{{ formatNumber(player.damage_taken) }}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">经济</span>
        <div class="stat-bar"><div class="stat-fill gold" :style="{ width: goldPercent + '%' }"></div></div>
        <span class="stat-value">{{ formatNumber(player.gold_earned) }}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">视野</span>
        <div class="stat-bar"><div class="stat-fill vision" :style="{ width: visionPercent + '%' }"></div></div>
        <span class="stat-value">{{ player.vision_score }}分</span>
      </div>
    </div>
    
    <!-- 额外信息 -->
    <div class="extra-info">
      <span>补刀 {{ totalCS }} ({{ csPerMin }}/m)</span>
      <span>控制 {{ player.cc_time || 0 }}s</span>
    </div>
    
    <!-- 近期爱玩 -->
    <div class="mastery-section">
      <span class="mastery-label">近期爱玩</span>
      <div class="mastery-icons">
        <template v-if="player.top_champions && player.top_champions.length">
          <img 
            v-for="(champ, idx) in player.top_champions.slice(0, 5)" 
            :key="idx"
            :src="getChampionIcon(champ.champion_id)"
            :title="champ.champion_name + ' - ' + champ.games + '场'"
            class="mastery-icon"
          />
        </template>
        <template v-else>
          <!-- 没有数据时显示当前英雄 -->
          <img 
            v-if="championIcon"
            :src="championIcon"
            :title="player.champion_name"
            class="mastery-icon"
          />
          <span v-else class="no-mastery">暂无数据</span>
        </template>
      </div>
    </div>
    
    <!-- 装备 -->
    <div class="items-row">
      <img v-if="getSpellIcon(player.spell1)" class="spell-icon" :src="getSpellIcon(player.spell1)" />
      <img v-if="getSpellIcon(player.spell2)" class="spell-icon" :src="getSpellIcon(player.spell2)" />
      <div class="items">
        <template v-for="(item, idx) in player.items" :key="idx">
          <img v-if="item && getItemIcon(item)" class="item-icon" :src="getItemIcon(item)" />
          <div v-else class="item-icon empty"></div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatKDA, formatNumber } from '@/utils/format'
import { getChampionIcon, getItemIcon, getSpellIcon } from '@/utils/ddragon'

const props = defineProps({ player: Object, teamTotals: Object, isActive: Boolean, gameLength: Number })

const championIcon = computed(() => getChampionIcon(props.player?.champion_id))
const scoreClass = computed(() => {
  const s = props.player?.game_score || 0
  if (s >= 80) return 'score-s'
  if (s >= 60) return 'score-a'
  if (s >= 40) return 'score-b'
  return 'score-c'
})
const kdaClass = computed(() => {
  const kda = (props.player.kills + props.player.assists) / Math.max(1, props.player.deaths)
  if (kda >= 5) return 'kda-excellent'
  if (kda >= 3) return 'kda-good'
  return 'kda-normal'
})

const damagePercent = computed(() => props.teamTotals?.damage ? Math.round(props.player.total_damage / props.teamTotals.damage * 100) : 0)
const tankPercent = computed(() => props.teamTotals?.tank ? Math.round(props.player.damage_taken / props.teamTotals.tank * 100) : 0)
const goldPercent = computed(() => props.teamTotals?.gold ? Math.round(props.player.gold_earned / props.teamTotals.gold * 100) : 0)
const visionPercent = computed(() => props.teamTotals?.vision ? Math.round(props.player.vision_score / props.teamTotals.vision * 100) : 0)
const totalCS = computed(() => (props.player.minions_killed || 0) + (props.player.neutral_minions_killed || 0) || props.player.cs || 0)
const csPerMin = computed(() => props.gameLength ? (totalCS.value / (props.gameLength / 60)).toFixed(1) : 0)
const participationPercent = computed(() => props.teamTotals?.kills ? Math.round((props.player.kills + props.player.assists) / props.teamTotals.kills * 100) : 0)
const deathSharePercent = computed(() => props.teamTotals?.deaths ? Math.round(props.player.deaths / props.teamTotals.deaths * 100) : 0)
const killParticipation = computed(() => participationPercent.value)
</script>

<style scoped>
.player-card {
  background: linear-gradient(145deg, rgba(33, 38, 45, 0.95), rgba(22, 27, 34, 0.98));
  border-radius: 10px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: relative;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-style: preserve-3d;
  perspective: 1000px;
}

/* 顶部发光线 */
.player-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 2px;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--transition-normal);
  border-radius: 0 0 2px 2px;
}
.player-card:hover::before { opacity: 0.8; }
.player-card.is-me::before { opacity: 0.6; background: var(--gradient-gold); }

.player-card:hover {
  border-color: rgba(78, 204, 163, 0.3);
  box-shadow:
    var(--shadow-lg),
    0 0 30px rgba(78, 204, 163, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transform: translateY(-4px) scale(1.02) rotateX(2deg);
}

.player-card.is-me {
  border-top: 3px solid var(--radar-me);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.1);
}

.player-card.is-me:hover {
  box-shadow:
    var(--shadow-lg),
    0 0 35px rgba(255, 215, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.champion-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.player-card:hover .champion-avatar {
  border-color: var(--accent-secondary);
  box-shadow: 0 0 15px rgba(78, 204, 163, 0.4);
  transform: scale(1.1) rotate(5deg);
}

.champion-avatar img { width: 100%; height: 100%; object-fit: cover; }

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  font-weight: 600;
  font-size: 16px;
}

.player-info { flex: 1; }

.player-name {
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.me-badge { color: var(--radar-me); font-size: 12px; }

.champion-name { font-size: 11px; color: var(--text-muted); }

.score-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--bg-secondary);
  transition: box-shadow var(--transition-normal);
}

/* 高分发光效果 */
.score-s { box-shadow: 0 0 12px rgba(255, 107, 53, 0.25); }
.score-a { box-shadow: 0 0 10px rgba(255, 215, 0, 0.2); }

.score-value { font-size: 18px; font-weight: 700; }
.score-label { font-size: 9px; color: var(--text-muted); }

.score-s .score-value { color: #ff6b35; }
.score-a .score-value { color: #ffd700; }
.score-b .score-value { color: var(--text-secondary); }
.score-c .score-value { color: var(--color-info); }

.kda-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.kda-main { font-size: 16px; font-weight: 600; }
.kills { color: var(--color-win); }
.deaths { color: var(--color-lose); }
.assists { color: var(--text-secondary); }

.kda-ratio {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-secondary);
}

.kda-excellent { color: #ff6b35; background: rgba(255, 107, 53, 0.15); }
.kda-good { color: var(--color-win); background: rgba(78, 204, 163, 0.15); }

.participation-row {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}

.part-item { display: flex; flex-direction: column; align-items: center; }
.part-value { font-size: 13px; font-weight: 600; }
.part-label { font-size: 9px; color: var(--text-muted); }

.badges-row {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.badge {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: default;
  position: relative;
  overflow: hidden;
}

.badge:hover {
  transform: translateY(-2px) scale(1.1);
}

.badge.penta {
  background: linear-gradient(135deg, #ff6b35, #e94560);
  color: white;
  animation: pentaBounce 0.6s ease-in-out infinite alternate, pentaGlow 1.5s ease-in-out infinite;
  box-shadow: 0 0 15px rgba(255, 107, 53, 0.6);
}

@keyframes pentaBounce {
  0% { transform: translateY(0) scale(1); }
  100% { transform: translateY(-3px) scale(1.05); }
}

@keyframes pentaGlow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(255, 107, 53, 0.6), 0 0 25px rgba(255, 107, 53, 0.4);
  }
  50% {
    box-shadow: 0 0 25px rgba(255, 107, 53, 0.9), 0 0 40px rgba(255, 107, 53, 0.6);
  }
}

.badge.quadra {
  background: rgba(255, 107, 53, 0.2);
  color: #ff6b35;
  animation: badgeShimmer 2s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(255, 107, 53, 0.3);
}

@keyframes badgeShimmer {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}

.badge.triple {
  background: rgba(255, 215, 0, 0.15);
  color: #ffd700;
  animation: badgeShimmer 2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.badge.first-blood {
  background: rgba(233, 69, 96, 0.15);
  color: var(--color-lose);
  animation: badgeShimmer 2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(233, 69, 96, 0.3);
}

.stats-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label { font-size: 11px; color: var(--text-muted); width: 32px; }

.stat-bar {
  flex: 1;
  height: 8px;
  background: rgba(13, 17, 23, 0.8);
  border-radius: 4px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 4px;
  position: relative;
  transition: width 0.6s var(--ease-smooth);
  animation: statPulse 2s ease-in-out infinite;
}

/* 脉冲呼吸动画 */
@keyframes statPulse {
  0%, 100% {
    opacity: 0.95;
    filter: brightness(1);
  }
  50% {
    opacity: 1;
    filter: brightness(1.15);
  }
}

/* 数据条微光动画 */
.stat-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: barShimmer 3s ease-in-out infinite;
}
@keyframes barShimmer {
  0% { left: -100%; }
  50% { left: 100%; }
  100% { left: 100%; }
}
.stat-fill.damage {
  background: linear-gradient(90deg, #e94560, #ff6b35);
  box-shadow: 0 0 8px rgba(233, 69, 96, 0.3);
}
.stat-fill.tank {
  background: linear-gradient(90deg, #58a6ff, #22d3ee);
  box-shadow: 0 0 8px rgba(88, 166, 255, 0.3);
}
.stat-fill.gold {
  background: linear-gradient(90deg, #ffd700, #f39c12);
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}
.stat-fill.vision {
  background: linear-gradient(90deg, #a855f7, #ec4899);
  box-shadow: 0 0 8px rgba(168, 85, 247, 0.3);
}

.stat-value { font-size: 11px; color: var(--text-secondary); width: 50px; text-align: right; font-family: 'Consolas', monospace; }

.extra-info {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 10px;
  padding: 6px 0;
  border-top: 1px solid var(--border-color);
}

.mastery-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding: 6px 0;
  border-top: 1px solid var(--border-color);
}

.mastery-label {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
}

.mastery-icons {
  display: flex;
  gap: 4px;
}

.mastery-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  transition: transform var(--transition-normal), border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.mastery-icon:hover {
  transform: scale(1.2);
  border-color: var(--accent-secondary);
  box-shadow: 0 0 8px rgba(78, 204, 163, 0.3);
}

.no-mastery {
  font-size: 10px;
  color: var(--text-muted);
}

.items-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
}

.spell-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  position: relative;
}

.spell-icon:hover {
  transform: scale(1.25) translateY(-3px) rotate(5deg);
  border-color: var(--accent-secondary);
  box-shadow:
    0 0 15px rgba(78, 204, 163, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.4);
  z-index: 10;
}

.items {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  position: relative;
}

.item-icon:hover:not(.empty) {
  transform: scale(1.3) translateY(-5px) rotate(-3deg);
  border-color: var(--accent-secondary);
  box-shadow:
    0 0 20px rgba(78, 204, 163, 0.5),
    0 6px 16px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  z-index: 10;
}

.item-icon:hover:not(.empty)::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 5px;
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.3), rgba(88, 166, 255, 0.3));
  z-index: -1;
  animation: itemGlow 1s ease-in-out infinite;
}

@keyframes itemGlow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.item-icon.empty {
  opacity: 0.3;
  cursor: default;
}
</style>
