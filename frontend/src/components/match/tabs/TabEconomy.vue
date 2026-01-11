<template>
  <div class="tab-economy">
    <div class="charts-row">
      <div class="chart-card">
        <h4>经济对比</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name }}</span>
            <div class="bar-track">
              <div class="bar-fill gold" :style="{ width: getGoldPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ formatNumber(player.gold_earned) }}</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h4>补刀对比</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name }}</span>
            <div class="bar-track">
              <div class="bar-fill cs" :style="{ width: getCSPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ getCS(player) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({ match: Object, team: Array })

const maxGold = computed(() => Math.max(...(props.team?.map(p => p.gold_earned) || [1])))
const maxCS = computed(() => Math.max(...(props.team?.map(p => getCS(p)) || [1])))

function getGoldPercent(player) { return Math.round(player.gold_earned / maxGold.value * 100) }
function getCS(player) { return player.minions_killed + player.neutral_minions_killed }
function getCSPercent(player) { return Math.round(getCS(player) / maxCS.value * 100) }
</script>

<style scoped>
.tab-economy { display: flex; flex-direction: column; gap: var(--spacing-md); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
.chart-card { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--border-radius); }
.chart-card h4 { margin-bottom: var(--spacing-md); color: var(--text-secondary); font-size: var(--font-size-sm); }
.bar-chart { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.bar-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.bar-label { width: 80px; font-size: var(--font-size-xs); color: var(--text-secondary); }
.bar-track { flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-fill.gold { background: var(--radar-me); }
.bar-fill.cs { background: var(--radar-team2); }
.bar-value { width: 60px; text-align: right; font-size: var(--font-size-xs); }
</style>
