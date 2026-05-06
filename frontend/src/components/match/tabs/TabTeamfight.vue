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
.tab-teamfight {
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
  background: var(--gradient-primary);
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

.bar-fill.participation {
  background: linear-gradient(90deg, #4ecca3 0%, #2ecc71 50%, #27ae60 100%);
  box-shadow: 0 0 12px rgba(78, 204, 163, 0.4);
}

.bar-fill.ka {
  background: linear-gradient(90deg, #58a6ff 0%, #4a9eff 50%, #3b82f6 100%);
  box-shadow: 0 0 12px rgba(88, 166, 255, 0.4);
}

.bar-value {
  width: 50px;
  text-align: right;
  font-size: var(--font-size-xs);
  font-family: 'Consolas', monospace;
  color: var(--text-secondary);
}

.multikill-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
}

.multikill-stats span {
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  border: 1px solid rgba(233, 69, 96, 0.3);
  border-radius: var(--border-radius-sm);
  color: var(--accent-primary);
  font-weight: 600;
  font-size: var(--font-size-sm);
  box-shadow: 0 0 15px rgba(233, 69, 96, 0.2);
  transition: all var(--transition-fast);
}

.multikill-stats span:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(233, 69, 96, 0.4);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
