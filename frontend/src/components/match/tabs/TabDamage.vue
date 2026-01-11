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
.tab-damage { display: flex; flex-direction: column; gap: var(--spacing-md); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }
.chart-card { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--border-radius); }
.chart-card h4 { margin-bottom: var(--spacing-md); color: var(--text-secondary); font-size: var(--font-size-sm); }

.bar-chart { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.bar-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.bar-item.is-me { background: rgba(255, 215, 0, 0.1); padding: 4px; margin: -4px; border-radius: 4px; }
.bar-label { width: 100px; font-size: var(--font-size-xs); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.me-mark { color: #ffd700; margin-right: 2px; }
.bar-track { flex: 1; height: 10px; background: var(--bg-primary); border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; transition: width 0.3s; }
.bar-fill.damage { background: linear-gradient(90deg, #e94560, #ff6b6b); }
.bar-fill.tank { background: linear-gradient(90deg, #4a9eff, #22d3ee); }
.bar-value { width: 110px; text-align: right; font-size: var(--font-size-xs); color: var(--text-secondary); }

.damage-types { display: flex; flex-direction: column; gap: var(--spacing-md); }
.type-item { display: flex; align-items: center; gap: var(--spacing-sm); }
.type-color { width: 12px; height: 12px; border-radius: 3px; }
.type-item.physical .type-color { background: #ff8c42; }
.type-item.magic .type-color { background: #6c5ce7; }
.type-item.true-dmg .type-color { background: #fff; }
.type-label { width: 70px; color: var(--text-secondary); font-size: var(--font-size-sm); }
.type-value { flex: 1; font-size: var(--font-size-sm); }
.type-percent { color: var(--text-muted); font-size: var(--font-size-sm); font-weight: 600; }
</style>
