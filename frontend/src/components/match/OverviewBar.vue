<template>
  <div class="overview-bar" :class="{ win: isWin, lose: !isWin }">
    <div class="result-badge">
      <span class="result-icon">{{ isWin ? '🏆' : '❌' }}</span>
      <span class="result-text">{{ isWin ? '胜利' : '失败' }}</span>
    </div>
    
    <div class="game-info">
      <span class="game-mode">{{ gameModeText }}</span>
      <span class="game-length">{{ formatGameLength(match?.game_length || 0) }}</span>
    </div>
    
    <div class="player-info" v-if="myPlayer">
      <div class="champion-avatar">
        <img v-if="championIcon" :src="championIcon" />
        <span v-else>{{ myPlayer.champion_name?.charAt(0) || '?' }}</span>
      </div>
      <div class="kda">
        <span class="kills">{{ myPlayer.kills }}</span>
        <span class="separator">/</span>
        <span class="deaths">{{ myPlayer.deaths }}</span>
        <span class="separator">/</span>
        <span class="assists">{{ myPlayer.assists }}</span>
      </div>
    </div>
    
    <div class="score-info" v-if="myPlayer">
      <span class="score" :style="{ color: getScoreColor(myPlayer.game_score) }">
        {{ myPlayer.game_score || '-' }}
      </span>
      <span class="mvp-badge" v-if="isMVP">MVP</span>
    </div>
    
    <!-- 成就徽章 -->
    <div class="achievements" v-if="myPlayer">
      <span class="achievement" v-if="myPlayer.penta_kills">🔥 五杀</span>
      <span class="achievement" v-else-if="myPlayer.quadra_kills">🔥 四杀</span>
      <span class="achievement" v-else-if="myPlayer.triple_kills">🔥 三杀</span>
      <span class="achievement" v-if="myPlayer.first_blood">⚔️ 一血</span>
      <span class="achievement" v-if="myPlayer.largest_killing_spree >= 5">🗡️ 连杀{{ myPlayer.largest_killing_spree }}</span>
    </div>
    
    <div class="lp-change" v-if="lpChange">
      <span :class="lpChange > 0 ? 'positive' : 'negative'">
        {{ lpChange > 0 ? '+' : '' }}{{ lpChange }} LP
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatGameLength, getScoreColor, gameModeNames } from '@/utils/format'
import { getChampionIcon } from '@/utils/ddragon'

const props = defineProps({
  match: Object
})

const isWin = computed(() => props.match?.win ?? props.match?.is_win ?? false)

const myPlayer = computed(() => {
  return props.match?.my_team?.find(p => p.is_me)
})

const championIcon = computed(() => getChampionIcon(myPlayer.value?.champion_id))

const gameModeText = computed(() => {
  const mode = props.match?.game_mode
  // 如果后端已经转换了，直接用
  if (mode && !mode.includes('_') && mode !== 'CLASSIC') {
    return mode
  }
  return gameModeNames[mode] || mode || '对局'
})

const isMVP = computed(() => {
  if (!props.match?.my_team || !myPlayer.value) return false
  const myKDA = (myPlayer.value.kills + myPlayer.value.assists) / Math.max(1, myPlayer.value.deaths)
  return props.match.my_team.every(p => {
    const pKDA = (p.kills + p.assists) / Math.max(1, p.deaths)
    return p.is_me || myKDA >= pKDA
  })
})

const lpChange = computed(() => null)
</script>

<style scoped>
.overview-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  border-radius: var(--border-radius);
  border-left: 4px solid var(--border-color);
}

.overview-bar.win {
  border-left-color: var(--color-win);
}

.overview-bar.lose {
  border-left-color: var(--color-lose);
}

.result-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.result-icon {
  font-size: 24px;
}

.result-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.win .result-text {
  color: var(--color-win);
}

.lose .result-text {
  color: var(--color-lose);
}

.game-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.game-mode {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}

.game-length {
  font-size: var(--font-size-md);
  font-weight: 500;
}

.player-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.champion-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  font-weight: 600;
  overflow: hidden;
}

.champion-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.kda {
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.kills {
  color: var(--color-win);
}

.deaths {
  color: var(--color-lose);
}

.assists {
  color: var(--text-secondary);
}

.separator {
  color: var(--text-muted);
  margin: 0 2px;
}

.score-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.score {
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.mvp-badge {
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #000;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.achievements {
  display: flex;
  gap: var(--spacing-sm);
  margin-left: var(--spacing-md);
}

.achievement {
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: var(--font-size-xs);
  color: var(--text-primary);
}

.lp-change {
  margin-left: auto;
  font-size: var(--font-size-md);
  font-weight: 600;
}

.positive {
  color: var(--color-win);
}

.negative {
  color: var(--color-lose);
}
</style>
