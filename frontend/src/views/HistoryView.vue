<template>
  <div class="history-view">
    <div class="page-header">
      <h2>历史记录</h2>
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
        v-for="match in matchStore.historyList" 
        :key="match.game_id"
        class="history-item"
        :class="{ win: match.is_win, lose: !match.is_win }"
        @click="viewDetail(match.game_id)"
      >
        <div class="result-badge">{{ match.is_win ? '🏆' : '❌' }}</div>
        <div class="match-info">
          <span class="game-mode">{{ gameModeNames[match.game_mode] || match.game_mode }}</span>
          <span class="champion">{{ match.champion_name }}</span>
        </div>
        <div class="kda">{{ match.kills }}/{{ match.deaths }}/{{ match.assists }}</div>
        <div class="score" :style="{ color: getScoreColor(match.game_score) }">{{ match.game_score }}</div>
        <div class="game-length">{{ formatGameLength(match.game_length) }}</div>
        <div class="timestamp">{{ formatTimestamp(match.timestamp) }}</div>
      </div>
    </div>
    
    <div class="empty-state" v-else>
      <p>暂无历史记录</p>
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
.history-view { padding: var(--spacing-md); height: 100%; overflow-y: auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-lg); }
.page-header h2 { font-size: var(--font-size-lg); }
.filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); padding: var(--spacing-sm) var(--spacing-md); border-radius: var(--border-radius); }
.history-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.history-item { display: flex; align-items: center; gap: var(--spacing-md); padding: var(--spacing-md); background: var(--bg-card); border-radius: var(--border-radius); cursor: pointer; border-left: 3px solid var(--border-color); }
.history-item:hover { background: var(--bg-hover); }
.history-item.win { border-left-color: var(--color-win); }
.history-item.lose { border-left-color: var(--color-lose); }
.result-badge { font-size: 20px; }
.match-info { display: flex; flex-direction: column; gap: 2px; min-width: 100px; }
.game-mode { font-size: var(--font-size-xs); color: var(--text-secondary); }
.champion { font-weight: 500; }
.kda { min-width: 80px; }
.score { min-width: 40px; font-weight: 600; }
.game-length { min-width: 60px; color: var(--text-secondary); }
.timestamp { color: var(--text-muted); font-size: var(--font-size-xs); margin-left: auto; }
.empty-state { text-align: center; padding: var(--spacing-xl); color: var(--text-muted); }
</style>
