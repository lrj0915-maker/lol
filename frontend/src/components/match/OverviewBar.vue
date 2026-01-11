<template>
  <div class="overview-bar" :class="{ win: match.is_win, lose: !match.is_win }">
    <div class="result-section">
      <div class="result-badge">
        <span class="result-icon">{{ match.is_win ? '🏆' : '❌' }}</span>
        <span class="result-text">{{ match.is_win ? '胜利' : '失败' }}</span>
      </div>
      <div class="game-info">
        <span class="game-mode">{{ gameModeText }}</span>
        <span class="game-time">{{ formatGameLength(match.game_length) }}</span>
      </div>
    </div>
    
    <div class="score-section">
      <div class="team-score our">
        <span class="score-value">{{ ourKills }}</span>
        <span class="score-label">击杀</span>
      </div>
      <div class="vs-divider">
        <span class="vs-text">VS</span>
      </div>
      <div class="team-score enemy">
        <span class="score-value">{{ enemyKills }}</span>
        <span class="score-label">击杀</span>
      </div>
    </div>
    
    <div class="stats-section">
      <div class="stat-item">
        <span class="stat-icon">⚔️</span>
        <div class="stat-content">
          <span class="stat-value">{{ myPlayer?.kills }}/{{ myPlayer?.deaths }}/{{ myPlayer?.assists }}</span>
          <span class="stat-label">我的KDA</span>
        </div>
      </div>
      <div class="stat-item">
        <span class="stat-icon">💰</span>
        <div class="stat-content">
          <span class="stat-value">{{ formatNumber(myPlayer?.gold_earned || 0) }}</span>
          <span class="stat-label">经济</span>
        </div>
      </div>
      <div class="stat-item">
        <span class="stat-icon">💥</span>
        <div class="stat-content">
          <span class="stat-value">{{ formatNumber(myPlayer?.total_damage || 0) }}</span>
          <span class="stat-label">伤害</span>
        </div>
      </div>
      <div class="stat-item highlight">
        <span class="stat-icon">⭐</span>
        <div class="stat-content">
          <span class="stat-value score" :style="{ color: getScoreColor(myPlayer?.game_score) }">
            {{ myPlayer?.game_score || '-' }}
          </span>
          <span class="stat-label">评分</span>
        </div>
      </div>
    </div>
    
    <div class="timestamp-section">
      <span class="timestamp">{{ formatTimestamp(match.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatGameLength, formatTimestamp, formatNumber, getScoreColor, gameModeNames } from '@/utils/format'

const props = defineProps({
  match: Object
})

const gameModeText = computed(() => {
  return gameModeNames[props.match?.game_mode] || props.match?.game_mode || '未知模式'
})

const myPlayer = computed(() => {
  return props.match?.my_team?.find(p => p.is_me)
})

const ourKills = computed(() => {
  return props.match?.my_team?.reduce((sum, p) => sum + (p.kills || 0), 0) || 0
})

const enemyKills = computed(() => {
  return props.match?.enemy_team?.reduce((sum, p) => sum + (p.kills || 0), 0) || 0
})
</script>

<style scoped>
.overview-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
}

.overview-bar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.overview-bar.win::before {
  background: var(--gradient-win);
  box-shadow: 0 0 20px var(--color-win);
}

.overview-bar.lose::before {
  background: var(--gradient-lose);
  box-shadow: 0 0 20px var(--color-lose);
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  min-width: 100px;
}

.result-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.result-icon {
  font-size: var(--font-size-xl);
}

.result-text {
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.overview-bar.win .result-text { color: var(--color-win); }
.overview-bar.lose .result-text { color: var(--color-lose); }

.game-info {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.score-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 0 var(--spacing-lg);
  border-left: 1px solid var(--border-color);
  border-right: 1px solid var(--border-color);
}

.team-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.team-score .score-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.team-score.our .score-value { color: var(--color-win); }
.team-score.enemy .score-value { color: var(--color-lose); }

.team-score .score-label {
  font-size: 10px;
  color: var(--text-muted);
}

.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
}

.vs-text {
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--text-disabled);
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius-sm);
}

.stats-section {
  display: flex;
  gap: var(--spacing-lg);
  flex: 1;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.stat-icon {
  font-size: var(--font-size-md);
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.score {
  font-size: var(--font-size-lg);
}

.stat-label {
  font-size: 10px;
  color: var(--text-muted);
}

.stat-item.highlight {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.timestamp-section {
  margin-left: auto;
}

.timestamp {
  font-size: var(--font-size-xs);
  color: var(--text-disabled);
}
</style>
