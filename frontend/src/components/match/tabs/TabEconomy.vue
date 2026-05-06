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
.tab-economy {
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
  background: linear-gradient(180deg, rgba(255,255,255,0.25) 0%, transparent 100%);
  border-radius: 5px 5px 0 0;
}

.bar-fill.gold {
  background: linear-gradient(90deg, #ffd700 0%, #f39c12 50%, #e67e22 100%);
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.5);
}

.bar-fill.cs {
  background: linear-gradient(90deg, #4ecca3 0%, #2ecc71 50%, #27ae60 100%);
  box-shadow: 0 0 12px rgba(78, 204, 163, 0.4);
}

.bar-value {
  width: 60px;
  text-align: right;
  font-size: var(--font-size-xs);
  font-family: 'Consolas', monospace;
  color: var(--text-secondary);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
