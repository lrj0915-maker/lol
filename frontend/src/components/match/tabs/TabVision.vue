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
.tab-vision {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  animation: fadeIn 0.3s ease;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.chart-card {
  background: var(--gradient-card);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
}

.chart-card:hover {
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.chart-card h4 {
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.chart-card h4::before {
  content: '';
  width: 3px;
  height: 14px;
  background: linear-gradient(135deg, #a855f7 0%, #22d3ee 100%);
  border-radius: 2px;
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.bar-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 6px 8px;
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
}

.bar-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.bar-label {
  width: 80px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  flex: 1;
  height: 10px;
  background: var(--bg-primary);
  border-radius: 5px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.2) 0%, transparent 100%);
  border-radius: 5px 5px 0 0;
}

.bar-fill.ward {
  background: linear-gradient(90deg, #a855f7 0%, #8b5cf6 50%, #7c3aed 100%);
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.4);
}

.bar-fill.deward {
  background: linear-gradient(90deg, #22d3ee 0%, #06b6d4 50%, #0891b2 100%);
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.4);
}

.bar-value {
  width: 40px;
  text-align: right;
  font-size: var(--font-size-xs);
  font-family: 'Consolas', monospace;
  color: var(--text-secondary);
}

.vision-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.vision-table th,
.vision-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.vision-table th {
  color: var(--text-muted);
  font-weight: 500;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-primary);
}

.vision-table th:first-child {
  border-radius: var(--border-radius-sm) 0 0 0;
}

.vision-table th:last-child {
  border-radius: 0 var(--border-radius-sm) 0 0;
}

.vision-table tbody tr {
  transition: all var(--transition-fast);
}

.vision-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.vision-table tr.is-me {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.02) 100%);
}

.vision-table tr.is-me:hover {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.15) 0%, rgba(255, 215, 0, 0.05) 100%);
}

.player-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.me-badge {
  color: var(--radar-me);
  font-size: 10px;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
}

.highlight {
  color: var(--accent-secondary);
  font-weight: 600;
}

.max-mark {
  color: var(--radar-me);
  font-size: 10px;
  margin-left: 4px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
