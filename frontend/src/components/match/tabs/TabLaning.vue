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
.tab-laning { padding: var(--spacing-md); }
.laning-card { background: var(--bg-secondary); padding: var(--spacing-lg); border-radius: var(--border-radius); }
.laning-card h4 { text-align: center; margin-bottom: var(--spacing-lg); color: var(--text-secondary); }
.versus { display: flex; align-items: center; justify-content: center; gap: var(--spacing-xl); margin-bottom: var(--spacing-lg); }
.player-side { text-align: center; }
.player-side.enemy { color: var(--accent-primary); }
.avatar { width: 60px; height: 60px; border-radius: 50%; background: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto var(--spacing-sm); }
.name { font-weight: 600; }
.champion { font-size: var(--font-size-xs); color: var(--text-secondary); }
.vs-badge { font-size: var(--font-size-lg); font-weight: 700; color: var(--text-muted); }
.compare-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.compare-item { display: flex; align-items: center; padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--border-color); }
.my-val { flex: 1; text-align: right; color: var(--accent-secondary); }
.compare-label { width: 80px; text-align: center; color: var(--text-secondary); font-size: var(--font-size-xs); }
.enemy-val { flex: 1; text-align: left; color: var(--accent-primary); }
.result-text { text-align: center; margin-top: var(--spacing-lg); color: var(--text-muted); }
.result-text.win { color: var(--color-win); }
.no-data { text-align: center; color: var(--text-muted); padding: var(--spacing-xl); }
</style>
