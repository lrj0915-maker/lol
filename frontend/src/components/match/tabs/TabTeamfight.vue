<template>
  <div class="tab-teamfight">
    <div class="charts-row">
      <div class="chart-card">
        <h4>参团率</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name }}</span>
            <div class="bar-track">
              <div class="bar-fill participation" :style="{ width: getParticipation(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ getParticipation(player) }}%</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h4>击杀助攻</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name }}</span>
            <div class="bar-track">
              <div class="bar-fill ka" :style="{ width: getKAPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ player.kills + player.assists }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="chart-card" v-if="myPlayer">
      <h4>多杀统计</h4>
      <div class="multikill-stats">
        <span v-if="myPlayer.double_kills">双杀 x{{ myPlayer.double_kills }}</span>
        <span v-if="myPlayer.triple_kills">三杀 x{{ myPlayer.triple_kills }}</span>
        <span v-if="myPlayer.quadra_kills">四杀 x{{ myPlayer.quadra_kills }}</span>
        <span v-if="myPlayer.penta_kills">五杀 x{{ myPlayer.penta_kills }}</span>
        <span v-if="!myPlayer.double_kills && !myPlayer.triple_kills && !myPlayer.quadra_kills && !myPlayer.penta_kills">无多杀</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ match: Object, team: Array })
const totalKills = computed(() => props.team?.reduce((s, p) => s + p.kills, 0) || 1)
const maxKA = computed(() => Math.max(...(props.team?.map(p => p.kills + p.assists) || [1])))
const myPlayer = computed(() => props.team?.find(p => p.is_me))
function getParticipation(p) { return Math.round((p.kills + p.assists) / totalKills.value * 100) }
function getKAPercent(p) { return Math.round((p.kills + p.assists) / maxKA.value * 100) }
</script>

<style scoped>
.tab-teamfight { display: flex; flex-direction: column; gap: var(--spacing-md); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
.chart-card { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--border-radius); }
.chart-card h4 { margin-bottom: var(--spacing-md); color: var(--text-secondary); font-size: var(--font-size-sm); }
.bar-chart { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.bar-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.bar-label { width: 80px; font-size: var(--font-size-xs); color: var(--text-secondary); }
.bar-track { flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-fill.participation { background: var(--accent-secondary); }
.bar-fill.ka { background: var(--radar-team1); }
.bar-value { width: 50px; text-align: right; font-size: var(--font-size-xs); }
.multikill-stats { display: flex; gap: var(--spacing-lg); color: var(--accent-primary); font-weight: 500; }
</style>
