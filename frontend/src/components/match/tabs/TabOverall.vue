<template>
  <div class="tab-overall">
    <table class="data-table">
      <thead>
        <tr>
          <th @click="sortBy('summoner_name')">玩家</th>
          <th @click="sortBy('kda')">KDA</th>
          <th @click="sortBy('total_damage')">伤害</th>
          <th @click="sortBy('dpm')">DPM</th>
          <th @click="sortBy('gold_earned')">经济</th>
          <th @click="sortBy('gpm')">GPM</th>
          <th @click="sortBy('cs')">补刀</th>
          <th @click="sortBy('vision_score')">视野</th>
          <th @click="sortBy('participation')">参团</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="player in sortedTeam" :key="player.summoner_name" :class="{ 'is-me': player.is_me }">
          <td class="player-cell">
            <span class="me-badge" v-if="player.is_me">★</span>
            {{ player.summoner_name || player.champion_name }}
          </td>
          <td>{{ player.kills }}/{{ player.deaths }}/{{ player.assists }}</td>
          <td :class="{ highlight: isMax('total_damage', player) }">
            {{ formatNumber(player.total_damage) }}
            <span class="max-mark" v-if="isMax('total_damage', player)">▲</span>
          </td>
          <td :class="{ highlight: isMaxCalc('dpm', player) }">
            {{ getDPM(player) }}
            <span class="max-mark" v-if="isMaxCalc('dpm', player)">▲</span>
          </td>
          <td :class="{ highlight: isMax('gold_earned', player) }">
            {{ formatNumber(player.gold_earned) }}
            <span class="max-mark" v-if="isMax('gold_earned', player)">▲</span>
          </td>
          <td :class="{ highlight: isMaxCalc('gpm', player) }">
            {{ getGPM(player) }}
            <span class="max-mark" v-if="isMaxCalc('gpm', player)">▲</span>
          </td>
          <td>{{ getCS(player) }}</td>
          <td :class="{ highlight: isMax('vision_score', player) }">
            {{ player.vision_score }}
            <span class="max-mark" v-if="isMax('vision_score', player)">▲</span>
          </td>
          <td>{{ getParticipation(player) }}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({ match: Object, team: Array })

const sortKey = ref('total_damage')
const sortDesc = ref(true)

const totalKills = computed(() => props.team?.reduce((sum, p) => sum + p.kills, 0) || 1)
const gameMinutes = computed(() => (props.match?.game_length || 1) / 60)

const sortedTeam = computed(() => {
  if (!props.team) return []
  return [...props.team].sort((a, b) => {
    let aVal = getValue(a, sortKey.value)
    let bVal = getValue(b, sortKey.value)
    return sortDesc.value ? bVal - aVal : aVal - bVal
  })
})

function getValue(player, key) {
  if (key === 'kda') return (player.kills + player.assists) / Math.max(1, player.deaths)
  if (key === 'cs') return getCS(player)
  if (key === 'participation') return (player.kills + player.assists) / totalKills.value
  if (key === 'dpm') return getDPM(player)
  if (key === 'gpm') return getGPM(player)
  return player[key] || 0
}

function getCS(player) {
  return (player.minions_killed || 0) + (player.neutral_minions_killed || 0) || player.cs || 0
}

function getDPM(player) {
  return Math.round(player.total_damage / gameMinutes.value)
}

function getGPM(player) {
  return Math.round(player.gold_earned / gameMinutes.value)
}

function sortBy(key) {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value
  else { sortKey.value = key; sortDesc.value = true }
}

function isMax(key, player) {
  if (!props.team) return false
  const val = player[key] || 0
  if (val === 0) return false
  const max = Math.max(...props.team.map(p => p[key] || 0))
  return val === max
}

function isMaxCalc(key, player) {
  if (!props.team) return false
  const val = key === 'dpm' ? getDPM(player) : getGPM(player)
  if (val === 0) return false
  const max = Math.max(...props.team.map(p => key === 'dpm' ? getDPM(p) : getGPM(p)))
  return val === max
}

function getParticipation(player) {
  return Math.round((player.kills + player.assists) / totalKills.value * 100)
}
</script>

<style scoped>
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  animation: fadeIn 0.3s ease;
}

.data-table th,
.data-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  color: var(--text-muted);
  font-weight: 500;
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-secondary);
  cursor: pointer;
  user-select: none;
  transition: all var(--transition-fast);
  position: relative;
}

.data-table th:first-child {
  border-radius: var(--border-radius-sm) 0 0 0;
}

.data-table th:last-child {
  border-radius: 0 var(--border-radius-sm) 0 0;
}

.data-table th:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.data-table th::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: transparent;
  transition: all var(--transition-fast);
}

.data-table th:hover::after {
  background: var(--accent-secondary);
}

.data-table tbody tr {
  transition: all var(--transition-fast);
}

.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.data-table tr.is-me {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.12) 0%, rgba(255, 215, 0, 0.02) 100%);
}

.data-table tr.is-me:hover {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.18) 0%, rgba(255, 215, 0, 0.05) 100%);
}

.data-table td {
  font-family: 'Consolas', monospace;
  font-size: var(--font-size-xs);
}

.player-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-family);
}

.me-badge {
  color: var(--radar-me);
  font-size: 10px;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
  animation: pulse 2s ease-in-out infinite;
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
