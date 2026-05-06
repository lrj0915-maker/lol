<template>
  <div class="tab-laning">
    <div class="laning-card" v-if="myPlayer && opponent">
      <h4>对位对比</h4>
      <div class="versus">
        <div class="player-side">
          <div class="avatar">{{ myPlayer.champion_name?.charAt(0) }}</div>
          <div class="name">{{ myPlayer.summoner_name }}</div>
          <div class="champion">{{ myPlayer.champion_name }}</div>
        </div>
        <div class="vs-badge">VS</div>
        <div class="player-side enemy">
          <div class="avatar">{{ opponent.champion_name?.charAt(0) }}</div>
          <div class="name">{{ opponent.summoner_name }}</div>
          <div class="champion">{{ opponent.champion_name }}</div>
        </div>
      </div>
      <div class="compare-list">
        <div class="compare-item">
          <span class="my-val">{{ myPlayer.kills }}/{{ myPlayer.deaths }}/{{ myPlayer.assists }}</span>
          <span class="compare-label">KDA</span>
          <span class="enemy-val">{{ opponent.kills }}/{{ opponent.deaths }}/{{ opponent.assists }}</span>
        </div>
        <div class="compare-item">
          <span class="my-val">{{ formatNumber(myPlayer.total_damage) }}</span>
          <span class="compare-label">伤害</span>
          <span class="enemy-val">{{ formatNumber(opponent.total_damage) }}</span>
        </div>
        <div class="compare-item">
          <span class="my-val">{{ formatNumber(myPlayer.gold_earned) }}</span>
          <span class="compare-label">经济</span>
          <span class="enemy-val">{{ formatNumber(opponent.gold_earned) }}</span>
        </div>
        <div class="compare-item">
          <span class="my-val">{{ getCS(myPlayer) }}</span>
          <span class="compare-label">补刀</span>
          <span class="enemy-val">{{ getCS(opponent) }}</span>
        </div>
        <div class="compare-item">
          <span class="my-val">{{ myPlayer.vision_score }}</span>
          <span class="compare-label">视野</span>
          <span class="enemy-val">{{ opponent.vision_score }}</span>
        </div>
      </div>
      <div class="result-text" :class="{ win: isWinning }">
        {{ isWinning ? '✓ 你在对位中表现更优' : '对位表现需要提升' }}
      </div>
    </div>
    <div class="no-data" v-else>暂无对位数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'
const props = defineProps({ match: Object, team: Array })
const myPlayer = computed(() => props.team?.find(p => p.is_me))
const opponent = computed(() => {
  if (!myPlayer.value || !props.match?.enemy_team) return null
  const myPos = myPlayer.value.position
  return props.match.enemy_team.find(p => p.position === myPos) || props.match.enemy_team[0]
})
const isWinning = computed(() => {
  if (!myPlayer.value || !opponent.value) return false
  const myScore = myPlayer.value.total_damage + myPlayer.value.gold_earned
  const enemyScore = opponent.value.total_damage + opponent.value.gold_earned
  return myScore > enemyScore
})
function getCS(p) { return p.minions_killed + p.neutral_minions_killed }
</script>

<style scoped>
.tab-laning {
  padding: var(--spacing-md);
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.laning-card {
  background: var(--gradient-card);
  padding: var(--spacing-xl);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.laning-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent-secondary) 0%, var(--accent-primary) 100%);
}

.laning-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at center top, rgba(78, 204, 163, 0.03) 0%, transparent 50%);
  pointer-events: none;
}

.laning-card h4 {
  text-align: center;
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
  font-size: var(--font-size-md);
  font-weight: 600;
  position: relative;
}

.laning-card h4::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: var(--gradient-primary);
  border-radius: 1px;
}

.versus {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  position: relative;
  overflow: hidden;
}

.versus::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, rgba(78, 204, 163, 0.05) 0%, transparent 100%);
  pointer-events: none;
}

.versus::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(-90deg, rgba(233, 69, 96, 0.05) 0%, transparent 100%);
  pointer-events: none;
}

.player-side {
  text-align: center;
  flex: 1;
}

.player-side.enemy .avatar {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.2) 0%, rgba(233, 69, 96, 0.1) 100%);
  border-color: var(--accent-primary);
  box-shadow: 0 0 25px rgba(233, 69, 96, 0.4);
}

.player-side.enemy .avatar::before {
  border-top-color: rgba(233, 69, 96, 0.5);
}

.player-side.enemy .name {
  color: var(--accent-primary);
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.2) 0%, rgba(78, 204, 163, 0.1) 100%);
  border: 3px solid var(--accent-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 600;
  margin: 0 auto var(--spacing-sm);
  box-shadow: 0 0 25px rgba(78, 204, 163, 0.4);
  transition: all var(--transition-normal);
  position: relative;
}

.avatar::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: rgba(78, 204, 163, 0.5);
  animation: avatarSpin 3s linear infinite;
}

@keyframes avatarSpin {
  to { transform: rotate(360deg); }
}

.avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 0 35px rgba(78, 204, 163, 0.6);
}

.name {
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--accent-secondary);
  margin-bottom: 2px;
}

.champion {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.vs-badge {
  font-size: var(--font-size-2xl);
  font-weight: 800;
  color: var(--text-muted);
  text-shadow: 0 2px 15px rgba(0, 0, 0, 0.6);
  padding: 0 var(--spacing-md);
  position: relative;
  z-index: 1;
  animation: vsPulse 2s ease-in-out infinite;
}

@keyframes vsPulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 0.8;
  }
  50% { 
    transform: scale(1.1);
    opacity: 1;
  }
}

.compare-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-primary);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.compare-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  transition: all var(--transition-normal);
  position: relative;
}

.compare-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: linear-gradient(90deg, rgba(78, 204, 163, 0.1) 0%, transparent 100%);
  transition: width var(--transition-normal);
}

.compare-item::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: linear-gradient(-90deg, rgba(233, 69, 96, 0.1) 0%, transparent 100%);
  transition: width var(--transition-normal);
}

.compare-item:hover {
  background: var(--bg-hover);
}

.compare-item:hover::before,
.compare-item:hover::after {
  width: 40%;
}

.my-val {
  flex: 1;
  text-align: right;
  color: var(--accent-secondary);
  font-weight: 600;
  font-family: 'Consolas', monospace;
}

.compare-label {
  width: 80px;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.enemy-val {
  flex: 1;
  text-align: left;
  color: var(--accent-primary);
  font-weight: 600;
  font-family: 'Consolas', monospace;
}

.result-text {
  text-align: center;
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius);
  background: rgba(110, 118, 129, 0.1);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.result-text::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%);
  animation: resultShine 3s ease-in-out infinite;
}

@keyframes resultShine {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

.result-text.win {
  background: linear-gradient(90deg, rgba(78, 204, 163, 0.2) 0%, rgba(78, 204, 163, 0.08) 100%);
  color: var(--color-win);
  border: 1px solid rgba(78, 204, 163, 0.4);
  box-shadow: var(--glow-win), inset 0 0 20px rgba(78, 204, 163, 0.1);
  font-weight: 600;
}

.no-data {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-xl);
  font-size: var(--font-size-sm);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
