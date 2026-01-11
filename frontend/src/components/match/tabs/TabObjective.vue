<template>
  <div class="tab-objective">
    <div class="charts-row">
      <div class="chart-card">
        <h4>推塔参与</h4>
        <div class="bar-chart">
          <div v-for="player in team" :key="player.summoner_name" class="bar-item">
            <span class="bar-label">{{ player.summoner_name || player.champion_name }}</span>
            <div class="bar-track">
              <div class="bar-fill turret" :style="{ width: getTurretPercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ player.turrets_killed }}</span>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h4>野怪参与</h4>
        <div class="objective-list">
          <div class="obj-item">
            <span class="obj-icon">🐉</span>
            <span class="obj-label">小龙</span>
            <span class="obj-value">{{ teamDragons }}</span>
          </div>
          <div class="obj-item">
            <span class="obj-icon">🦎</span>
            <span class="obj-label">先锋</span>
            <span class="obj-value">-</span>
          </div>
          <div class="obj-item">
            <span class="obj-icon">👹</span>
            <span class="obj-label">男爵</span>
            <span class="obj-value">{{ teamBarons }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chart-card">
      <h4>目标详情</h4>
      <table class="objective-table">
        <thead>
          <tr>
            <th>玩家</th>
            <th>推塔数</th>
            <th>推塔伤害</th>
            <th>小龙</th>
            <th>男爵</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="player in team" :key="player.summoner_name" :class="{ 'is-me': player.is_me }">
            <td class="player-cell">
              <span class="me-badge" v-if="player.is_me">★</span>
              {{ player.summoner_name || player.champion_name }}
            </td>
            <td :class="{ highlight: isMax('turrets_killed', player) }">
              {{ player.turrets_killed }}
              <span class="max-mark" v-if="isMax('turrets_killed', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('damage_to_buildings', player) }">
              {{ formatNumber(player.damage_to_buildings || 0) }}
              <span class="max-mark" v-if="isMax('damage_to_buildings', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('dragons_killed', player) }">
              {{ player.dragons_killed || 0 }}
              <span class="max-mark" v-if="isMax('dragons_killed', player)">▲</span>
            </td>
            <td :class="{ highlight: isMax('barons_killed', player) }">
              {{ player.barons_killed || 0 }}
              <span class="max-mark" v-if="isMax('barons_killed', player)">▲</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="chart-card team-summary">
      <h4>队伍目标总览</h4>
      <div class="team-objectives">
        <span>推塔 {{ teamTurrets }}</span>
        <span>小龙 {{ teamDragons }}</span>
        <span>男爵 {{ teamBarons }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({ match: Object, team: Array })
const maxTurret = computed(() => Math.max(...(props.team?.map(p => p.turrets_killed) || [1]), 1))
const teamTurrets = computed(() => props.team?.reduce((s, p) => s + p.turrets_killed, 0) || 0)
const teamDragons = computed(() => props.team?.reduce((s, p) => s + (p.dragons_killed || 0), 0) || 0)
const teamBarons = computed(() => props.team?.reduce((s, p) => s + (p.barons_killed || 0), 0) || 0)
function getTurretPercent(p) { return Math.round(p.turrets_killed / maxTurret.value * 100) }
function isMax(key, player) {
  if (!props.team) return false
  const val = player[key] || 0
  if (val === 0) return false
  const max = Math.max(...props.team.map(p => p[key] || 0))
  return val === max
}
</script>

<style scoped>
.tab-objective { display: flex; flex-direction: column; gap: var(--spacing-md); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
.chart-card { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--border-radius); }
.chart-card h4 { margin-bottom: var(--spacing-md); color: var(--text-secondary); font-size: var(--font-size-sm); }
.bar-chart { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.bar-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.bar-label { width: 80px; font-size: var(--font-size-xs); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-fill.turret { background: var(--color-warning); }
.bar-value { width: 30px; text-align: right; font-size: var(--font-size-xs); }
.objective-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.obj-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.obj-icon { font-size: 20px; }
.obj-label { flex: 1; color: var(--text-secondary); }
.obj-value { font-weight: 600; }

.objective-table { width: 100%; border-collapse: collapse; }
.objective-table th, .objective-table td { padding: var(--spacing-sm) var(--spacing-md); text-align: left; border-bottom: 1px solid var(--border-color); }
.objective-table th { color: var(--text-secondary); font-weight: 500; font-size: var(--font-size-xs); }
.objective-table tr.is-me { background: rgba(255, 215, 0, 0.1); }
.player-cell { display: flex; align-items: center; gap: 4px; }
.me-badge { color: var(--radar-me); }
.highlight { color: var(--accent-secondary); font-weight: 600; }
.max-mark { color: #ffd700; font-size: 10px; margin-left: 2px; }

.team-summary .team-objectives { display: flex; gap: var(--spacing-lg); color: var(--text-secondary); font-size: var(--font-size-sm); }
</style>
