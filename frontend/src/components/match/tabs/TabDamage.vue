<template>
  <div class="tab-damage">
    <div class="charts-row">
      <div class="chart-card">
        <h4>队伍伤害占比</h4>
        <div class="bar-chart">
          <div v-for="player in sortedByDamage" :key="player.summoner_name" class="bar-item" :class="{ 'is-me': player.is_me }">
            <span class="bar-label">
              <span v-if="player.is_me" class="me-mark">★</span>
              {{ player.summoner_name }}
            </span>
            <div class="bar-track">
              <div class="bar-fill damage" :style="{ width: getDamagePercent(player) + '%' }"></div>
            </div>
            <span class="bar-value">{{ formatNumber(player.total_damage) }} ({{ getDamagePercent(player) }}%)</span>
          </div>
        </div>
      </div>
      
      <div class="chart-card">
        <h4>我的伤害构成</h4>
        <div class="damage-types" v-if="myPlayer">
          <div class="type-item physical">
            <span class="type-color"></span>
            <span class="type-label">物理伤害</span>
            <span class="type-value">{{ formatNumber(myPlayer.physical_damage || 0) }}</span>
            <span class="type-percent">{{ getTypePercent('physical') }}%</span>
          </div>
          <div class="type-item magic">
            <span class="type-color"></span>
            <span class="type-label">魔法伤害</span>
            <span class="type-value">{{ formatNumber(myPlayer.magic_damage || 0) }}</span>
            <span class="type-percent">{{ getTypePercent('magic') }}%</span>
          </div>
          <div class="type-item true-dmg">
            <span class="type-color"></span>
            <span class="type-label">真实伤害</span>
            <span class="type-value">{{ formatNumber(myPlayer.true_damage || 0) }}</span>
            <span class="type-percent">{{ getTypePercent('true') }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chart-card">
      <h4>承受伤害</h4>
      <div class="bar-chart">
        <div v-for="player in sortedByTank" :key="player.summoner_name" class="bar-item" :class="{ 'is-me': player.is_me }">
          <span class="bar-label">
            <span v-if="player.is_me" class="me-mark">★</span>
            {{ player.summoner_name }}
          </span>
          <div class="bar-track">
            <div class="bar-fill tank" :style="{ width: getTankPercent(player) + '%' }"></div>
          </div>
          <span class="bar-value">{{ formatNumber(player.damage_taken) }} ({{ getTankPercent(player) }}%)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({ match: Object, team: Array })

const totalDamage = computed(() => props.team?.reduce((s, p) => s + (p.total_damage || 0), 0) || 1)
const totalTank = computed(() => props.team?.reduce((s, p) => s + (p.damage_taken || 0), 0) || 1)
const myPlayer = computed(() => props.team?.find(p => p.is_me))

const sortedByDamage = computed(() => {
  if (!props.team) return []
  return [...props.team].sort((a, b) => b.total_damage - a.total_damage)
})

const sortedByTank = computed(() => {
  if (!props.team) return []
  return [...props.team].sort((a, b) => b.damage_taken - a.damage_taken)
})

function getDamagePercent(player) {
  return Math.round((player.total_damage || 0) / totalDamage.value * 100)
}

function getTankPercent(player) {
  return Math.round((player.damage_taken || 0) / totalTank.value * 100)
}

function getTypePercent(type) {
  if (!myPlayer.value) return 0
  const total = (myPlayer.value.physical_damage || 0) + (myPlayer.value.magic_damage || 0) + (myPlayer.value.true_damage || 0)
  if (!total) return 0
  const val = type === 'physical' ? (myPlayer.value.physical_damage || 0)
            : type === 'magic' ? (myPlayer.value.magic_damage || 0)
            : (myPlayer.value.true_damage || 0)
  return Math.round(val / total * 100)
}
</script>

<style scoped>
.tab-damage {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
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
  position: relative;
  overflow: hidden;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-danger);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.chart-card:hover {
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-lg), 0 0 30px rgba(0, 0, 0, 0.2);
  transform: translateY(-3px);
}

.chart-card:hover::before {
  opacity: 1;
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
  background: var(--gradient-danger);
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

.bar-item.is-me {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.15) 0%, rgba(255, 215, 0, 0.05) 100%);
  border: 1px solid rgba(255, 215, 0, 0.2);
}

.bar-label {
  width: 100px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.me-mark {
  color: var(--radar-me);
  font-size: 10px;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
  animation: pulse 2s ease-in-out infinite;
}

.bar-track {
  flex: 1;
  height: 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.bar-fill {
  height: 100%;
  border-radius: 6px;
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
  border-radius: 6px 6px 0 0;
}

.bar-fill.damage {
  background: linear-gradient(90deg, #e94560 0%, #ff6b6b 50%, #ff8a80 100%);
  box-shadow: 0 0 15px rgba(233, 69, 96, 0.5);
  animation: barGrow 0.8s ease-out;
}

.bar-fill.tank {
  background: linear-gradient(90deg, #4a9eff 0%, #22d3ee 50%, #67e8f9 100%);
  box-shadow: 0 0 15px rgba(34, 211, 238, 0.5);
  animation: barGrow 0.8s ease-out;
}

@keyframes barGrow {
  from { width: 0 !important; }
}

.bar-value {
  width: 110px;
  text-align: right;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-family: 'Consolas', monospace;
}

.damage-types {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.type-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.type-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%);
  transition: width var(--transition-normal);
}

.type-item:hover {
  background: var(--bg-hover);
  transform: translateX(6px);
}

.type-item:hover::before {
  width: 100%;
}

.type-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  box-shadow: 0 0 10px currentColor;
  animation: colorPulse 2s ease-in-out infinite;
}

@keyframes colorPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.type-item.physical .type-color {
  background: linear-gradient(135deg, #ff8c42, #ff6b35);
  box-shadow: 0 0 12px rgba(255, 140, 66, 0.6);
}

.type-item.magic .type-color {
  background: linear-gradient(135deg, #6c5ce7, #a855f7);
  box-shadow: 0 0 12px rgba(108, 92, 231, 0.6);
}

.type-item.true-dmg .type-color {
  background: linear-gradient(135deg, #fff, #e0e0e0);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.6);
}

.type-label {
  width: 70px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.type-value {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 500;
  font-family: 'Consolas', monospace;
}

.type-percent {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
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
