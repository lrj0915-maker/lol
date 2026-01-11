<template>
  <div class="history-view">
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">📜</span>
        历史记录
      </h2>
      <div class="filters">
        <select v-model="filterMode" class="filter-select">
          <option value="">全部模式</option>
          <option value="CLASSIC">排位/匹配</option>
          <option value="ARAM">大乱斗</option>
        </select>
      </div>
    </div>
    
    <div class="history-list" v-if="matchStore.historyList.length">
      <div 
        v-for="(match, index) in matchStore.historyList" 
        :key="match.game_id"
        class="history-item"
        :class="{ win: match.is_win, lose: !match.is_win }"
        :style="{ animationDelay: `${index * 0.05}s` }"
        @click="viewDetail(match.game_id)"
      >
        <div class="result-indicator"></div>
        
        <div class="result-badge">
          <span class="result-icon">{{ match.is_win ? '🏆' : '❌' }}</span>
        </div>
        
        <div class="match-info">
          <span class="game-mode">{{ gameModeNames[match.game_mode] || match.game_mode }}</span>
          <span class="champion">{{ match.champion_name }}</span>
        </div>
        
        <div class="kda-section">
          <span class="kda-value">
            <span class="kills">{{ match.kills }}</span>
            <span class="sep">/</span>
            <span class="deaths">{{ match.deaths }}</span>
            <span class="sep">/</span>
            <span class="assists">{{ match.assists }}</span>
          </span>
        </div>
        
        <div class="score-section">
          <span class="score" :class="getScoreClass(match.game_score)">{{ match.game_score }}</span>
        </div>
        
        <div class="game-length">
          <span class="length-icon">⏱️</span>
          <span>{{ formatGameLength(match.game_length) }}</span>
        </div>
        
        <div class="timestamp">{{ formatTimestamp(match.timestamp) }}</div>
        
        <div class="arrow-icon">→</div>
      </div>
    </div>
    
    <div class="empty-state" v-else>
      <div class="empty-icon">📜</div>
      <p class="empty-text">暂无历史记录</p>
      <p class="empty-hint">完成游戏后会自动记录</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchStore } from '@/stores/match'
import { formatGameLength, formatTimestamp, getScoreColor, gameModeNames } from '@/utils/format'

const router = useRouter()
const matchStore = useMatchStore()
const filterMode = ref('')

function getScoreClass(score) {
  if (score >= 80) return 'score-s'
  if (score >= 60) return 'score-a'
  if (score >= 40) return 'score-b'
  if (score >= 20) return 'score-c'
  return 'score-d'
}

onMounted(() => {
  matchStore.fetchHistoryList()
})

watch(filterMode, (mode) => {
  matchStore.fetchHistoryList({ gameMode: mode || undefined })
})

async function viewDetail(gameId) {
  const detail = await matchStore.fetchMatchDetail(gameId)
  if (detail) {
    matchStore.setCurrentMatch(detail)
    router.push('/match')
  }
}
</script>

<style scoped>
.history-view {
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.title-icon {
  font-size: var(--font-size-xl);
}

.filter-select {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-select:hover {
  border-color: var(--border-color-light);
}

.filter-select:focus {
  border-color: var(--accent-secondary);
  box-shadow: 0 0 0 3px rgba(78, 204, 163, 0.15);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.history-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  border-radius: var(--border-radius);
  cursor: pointer;
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-normal);
  animation: fadeIn 0.3s ease forwards;
  opacity: 0;
}

.history-item:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-color-light);
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.history-item:hover .arrow-icon {
  opacity: 1;
  transform: translateX(0);
}

.result-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.history-item.win .result-indicator {
  background: var(--gradient-win);
}

.history-item.lose .result-indicator {
  background: var(--gradient-lose);
}

.result-badge {
  font-size: var(--font-size-lg);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.match-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 100px;
}

.game-mode {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.champion {
  font-weight: 600;
  font-size: var(--font-size-sm);
}

.kda-section {
  min-width: 90px;
}

.kda-value {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.kills { color: var(--color-win); }
.deaths { color: var(--color-lose); }
.assists { color: var(--text-secondary); }
.sep { color: var(--text-disabled); margin: 0 2px; }

.score-section {
  min-width: 50px;
}

.score {
  font-size: var(--font-size-lg);
  font-weight: 700;
  padding: 4px 12px;
  border-radius: var(--border-radius-sm);
  background: var(--bg-secondary);
}

.score-s { color: #ff6b35; background: rgba(255, 107, 53, 0.15); }
.score-a { color: #ffd700; background: rgba(255, 215, 0, 0.15); }
.score-b { color: var(--text-secondary); }
.score-c { color: var(--color-info); background: rgba(88, 166, 255, 0.15); }
.score-d { color: var(--color-lose); background: rgba(233, 69, 96, 0.15); }

.game-length {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  min-width: 70px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.length-icon {
  font-size: var(--font-size-xs);
}

.timestamp {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  margin-left: auto;
}

.arrow-icon {
  color: var(--text-muted);
  font-size: var(--font-size-md);
  opacity: 0;
  transform: translateX(-10px);
  transition: all var(--transition-fast);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl) * 2;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
  opacity: 0.3;
}

.empty-text {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
