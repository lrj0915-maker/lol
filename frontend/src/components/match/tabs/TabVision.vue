<template>
  <div class="tab-vision">
    <div class="charts-row">
      <div class="chart-card">
        <h4>插眼数</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name || player.champion_name }}</span>
            <div class="bar-track">
              <div class="bar-fill ward" :style="{ width: getWardPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ player.wards_placed }}</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h4>排眼数</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name || player.champion_name }}</span>
            <div class="bar-track">
              <div class="bar-fill deward" :style="{ width: getDewardPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ player.wards_killed }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chart-card">
      <h4>视野详情</h4>
      <table class="vision-table">
        <thead>
          <tr>
            <th>玩家</th>
            <th>视野分</th>
            <th>插眼</th>
            <th>排眼</th>
            <th>控制守卫</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="player in team" :key="player.summoner_name" :class="{ 'is-me': player.is_me }">
            <td class="player-cell">
              <span class="me-badge" v-if="player.is_me">★</span>
              {{ player.summoner_name || player.champion_name }}
            </td>
            <td :class="{ highlight: isMax('vision_score', player) }">
              {{ player.vision_score }}
              <span class="max-mark" v-if="isMax('vision_score', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('wards_placed', player) }">
              {{ player.wards_placed }}
              <span class="max-mark" v-if="isMax('wards_placed', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('wards_killed', player) }">
              {{ player.wards_killed }}
              <span class="max-mark" v-if="isMax('wards_killed', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('control_wards', player) }">
              {{ player.control_wards }}
              <span class="max-mark" v-if="isMax('control_wards', player)">▲</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ match: Object, team: Array })
const maxWard = computed(() => Math.max(...(props.team?.map(p => p.wards_placed) || [1]), 1))
const maxDeward = computed(() => Math.max(...(props.team?.map(p => p.wards_killed) || [1]), 1))
function getWardPercent(p) { return Math.round(p.wards_placed / maxWard.value * 100) }
function getDewardPercent(p) { return Math.round(p.wards_killed / maxDeward.value * 100) }
function isMax(key, player) {
  if (!props.team) return false
  const val = player[key] || 0
  if (val === 0) return false
  const max = Math.max(...props.team.map(p => p[key] || 0))
  return val === max
}
</script>

<style scoped>
.tab-vision { display: flex; flex-direction: column; gap: var(--spacing-md); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
.chart-card { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--border-radius); }
.chart-card h4 { margin-bottom: var(--spacing-md); color: var(--text-secondary); font-size: var(--font-size-sm); }
.bar-chart { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.bar-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.bar-label { width: 80px; font-size: var(--font-size-xs); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-fill.ward { background: var(--radar-team3); }
.bar-fill.deward { background: var(--radar-team4); }
.bar-value { width: 40px; text-align: right; font-size: var(--font-size-xs); }

.vision-table { width: 100%; border-collapse: collapse; }
.vision-table th, .vision-table td { padding: var(--spacing-sm) var(--spacing-md); text-align: left; border-bottom: 1px solid var(--border-color); }
.vision-table th { color: var(--text-secondary); font-weight: 500; font-size: var(--font-size-xs); }
.vision-table tr.is-me { background: rgba(255, 215, 0, 0.1); }
.player-cell { display: flex; align-items: center; gap: 4px; }
.me-badge { color: var(--radar-me); }
.highlight { color: var(--accent-secondary); font-weight: 600; }
.max-mark { color: #ffd700; font-size: 10px; margin-left: 2px; }
</style>
