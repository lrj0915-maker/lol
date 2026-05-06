<template>
  <div class="overview-bar" :class="match.is_win ? 'win' : 'lose'">
    <div class="result-section">
      <span class="result-pill">{{ match.is_win ? '胜利' : '失败' }}</span>
      <div class="result-info">
        <span class="result-text">{{ gameModeText }}</span>
        <span class="game-mode">{{ formatGameLength(match.game_length || match.duration || 0) }}</span>
      </div>
    </div>

    <div class="score-section">
      <span class="score our">{{ ourKills }}</span>
      <span class="vs">VS</span>
      <span class="score enemy">{{ enemyKills }}</span>
    </div>

    <div class="stats-section">
      <div class="stat-item">
        <span class="stat-label">KDA</span>
        <span class="stat-value">{{ myPlayer?.kills || 0 }}/{{ myPlayer?.deaths || 0 }}/{{ myPlayer?.assists || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">经济</span>
        <span class="stat-value">{{ formatNumber(myPlayer?.gold_earned || 0) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">伤害</span>
        <span class="stat-value">{{ formatNumber(myPlayer?.total_damage || 0) }}</span>
      </div>
      <div class="stat-item highlight">
        <span class="stat-label">评分</span>
        <span class="stat-value" :style="{ color: getScoreColor(myPlayer?.game_score) }">{{ myPlayer?.game_score || '-' }}</span>
      </div>
    </div>

    <div class="time-section">
      <span class="timestamp">{{ formatTimestamp(match.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatGameLength, formatTimestamp, formatNumber, getScoreColor, gameModeNames } from '@/utils/format'

const props = defineProps({ match: { type: Object, default: () => ({}) } })

const gameModeText = computed(() => gameModeNames[props.match?.game_mode] || props.match?.queue_label || props.match?.game_mode || '未知模式')
const myPlayer = computed(() => props.match?.my_team?.find((player) => player.is_me) || null)
const ourKills = computed(() => props.match?.my_team?.reduce((sum, player) => sum + (player.kills || 0), 0) || 0)
const enemyKills = computed(() => props.match?.enemy_team?.reduce((sum, player) => sum + (player.kills || 0), 0) || 0)
</script>

<style scoped>
.overview-bar { display: grid; grid-template-columns: 170px 110px minmax(280px, 1fr) auto; align-items: center; gap: 10px; min-height: 48px; padding: 8px 10px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); background: rgba(20, 24, 31, 0.92); }
.overview-bar.win { box-shadow: inset 3px 0 0 #4ecca3; }
.overview-bar.lose { box-shadow: inset 3px 0 0 #e94560; }
.result-section { display: flex; align-items: center; gap: 8px; min-width: 0; }
.result-pill { padding: 4px 8px; border-radius: 999px; font-size: 11px; font-weight: 800; background: rgba(255, 255, 255, 0.07); color: var(--text-primary); }
.result-info { display: grid; gap: 2px; min-width: 0; }
.result-text { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.game-mode { font-size: 11px; color: var(--text-secondary); }
.score-section { display: flex; align-items: center; justify-content: center; gap: 8px; padding-left: 10px; border-left: 1px solid rgba(255, 255, 255, 0.06); }
.score { font-size: 18px; font-weight: 800; }
.score.our { color: #58a6ff; }
.score.enemy { color: #ff6b81; }
.vs { font-size: 11px; color: var(--text-secondary); }
.stats-section { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding-left: 10px; border-left: 1px solid rgba(255, 255, 255, 0.06); }
.stat-item { display: grid; gap: 2px; padding: 6px 8px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); }
.stat-item.highlight { background: rgba(255, 255, 255, 0.05); }
.stat-label { font-size: 10px; color: var(--text-secondary); }
.stat-value { font-size: 12px; font-weight: 700; color: var(--text-primary); }
.time-section { display: flex; justify-content: flex-end; }
.timestamp { font-size: 11px; color: var(--text-secondary); padding: 4px 8px; border-radius: 8px; background: rgba(255, 255, 255, 0.04); }
@media (max-width: 1180px) { .overview-bar { grid-template-columns: 1fr 1fr; } .stats-section, .time-section { grid-column: 1 / -1; } }
</style>
