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
.tab-objective {
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
  background: var(--gradient-gold);
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

.bar-fill.turret {
  background: linear-gradient(90deg, #f39c12 0%, #e67e22 50%, #d35400 100%);
  box-shadow: 0 0 12px rgba(243, 156, 18, 0.5);
}

.bar-value {
  width: 30px;
  text-align: right;
  font-size: var(--font-size-xs);
  font-family: 'Consolas', monospace;
}

.objective-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.obj-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
}

.obj-item:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.obj-icon {
  font-size: 24px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.obj-label {
  flex: 1;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.obj-value {
  font-weight: 600;
  font-size: var(--font-size-md);
  font-family: 'Consolas', monospace;
  color: var(--text-primary);
}

.objective-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.objective-table th,
.objective-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.objective-table th {
  color: var(--text-muted);
  font-weight: 500;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-primary);
}

.objective-table th:first-child {
  border-radius: var(--border-radius-sm) 0 0 0;
}

.objective-table th:last-child {
  border-radius: 0 var(--border-radius-sm) 0 0;
}

.objective-table tbody tr {
  transition: all var(--transition-fast);
}

.objective-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.objective-table tr.is-me {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.02) 100%);
}

.objective-table tr.is-me:hover {
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

.team-summary {
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.1) 0%, rgba(88, 166, 255, 0.1) 100%);
  border: 1px solid rgba(78, 204, 163, 0.2);
}

.team-summary .team-objectives {
  display: flex;
  gap: var(--spacing-xl);
  justify-content: center;
}

.team-summary .team-objectives span {
  color: var(--text-primary);
  font-size: var(--font-size-md);
  font-weight: 500;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--border-radius-sm);
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
