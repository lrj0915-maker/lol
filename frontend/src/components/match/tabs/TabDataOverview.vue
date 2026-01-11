<template>
  <div class="tab-data-overview">
    <table class="data-table">
      <thead>
        <tr>
          <th @click="sortBy('name')">玩家</th>
          <th @click="sortBy('kda')">KDA</th>
          <th @click="sortBy('damage')">伤害</th>
          <th @click="sortBy('tank')">承伤</th>
          <th @click="sortBy('gold')">经济</th>
          <th @click="sortBy('cs')">补刀</th>
          <th @click="sortBy('vision')">视野</th>
          <th @click="sortBy('participation')">参团</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="player in sortedTeam" 
          :key="player.summoner_name"
          :class="{ 'is-me': player.is_me }"
        >
          <td class="player-cell">
            <span class="me-badge" v-if="player.is_me">★</span>
            {{ player.summoner_name || player.champion_name }}
          </td>
          <td>{{ player.kills }}/{{ player.deaths }}/{{ player.assists }}</td>
          <td :class="{ max: isMax('total_damage', player) }">
            {{ formatK(player.total_damage) }}
            <span class="max-mark" v-if="isMax('total_damage', player)">▲</span>
          </td>
          <td :class="{ max: isMax('damage_taken', player) }">
            {{ formatK(player.damage_taken) }}
            <span class="max-mark" v-if="isMax('damage_taken', player)">▲</span>
          </td>
          <td :class="{ max: isMax('gold_earned', player) }">
            {{ formatK(player.gold_earned) }}
            <span class="max-mark" v-if="isMax('gold_earned', player)">▲</span>
          </td>
          <td>{{ getCS(player) }}</td>
          <td :class="{ max: isMax('vision_score', player) }">
            {{ player.vision_score }}
            <span class="max-mark" v-if="isMax('vision_score', player)">▲</span>
          </td>
          <td>{{ getParticipation(player) }}%</td>
        </tr>
      </tbody>
    </table>
    
    <div class="team-summary">
      <span>击杀 {{ totalKills }}</span>
      <span>输出 {{ formatK(totalDamage) }}</span>
      <span>经济 {{ formatK(totalGold) }}</span>
      <span>视野 {{ totalVision }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ match: Object, team: Array })

const sortKey = ref('damage')
const sortDesc = ref(true)

const totalKills = computed(() => props.team?.reduce((s, p) => s + p.kills, 0) || 0)
const totalDamage = computed(() => props.team?.reduce((s, p) => s + (p.total_damage || 0), 0) || 0)
const totalGold = computed(() => props.team?.reduce((s, p) => s + (p.gold_earned || 0), 0) || 0)
const totalVision = computed(() => props.team?.reduce((s, p) => s + (p.vision_score || 0), 0) || 0)

const sortedTeam = computed(() => {
  if (!props.team) return []
  return [...props.team].sort((a, b) => {
    const aVal = getValue(a, sortKey.value)
    const bVal = getValue(b, sortKey.value)
    return sortDesc.value ? bVal - aVal : aVal - bVal
  })
})

function getValue(p, key) {
  if (key === 'kda') return (p.kills + p.assists) / Math.max(1, p.deaths)
  if (key === 'damage') return p.total_damage || 0
  if (key === 'tank') return p.damage_taken || 0
  if (key === 'gold') return p.gold_earned || 0
  if (key === 'cs') return getCS(p)
  if (key === 'vision') return p.vision_score || 0
  if (key === 'participation') return getParticipation(p)
  return 0
}

function getCS(p) {
  return (p.minions_killed || 0) + (p.neutral_minions_killed || 0)
}

function getParticipation(p) {
  if (!totalKills.value) return 0
  return Math.round((p.kills + p.assists) / totalKills.value * 100)
}

function sortBy(key) {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value
  else { sortKey.value = key; sortDesc.value = true }
}

function isMax(key, player) {
  if (!props.team) return false
  const val = player[key] || 0
  if (val === 0) return false
  return val === Math.max(...props.team.map(p => p[key] || 0))
}

function formatK(num) {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}
</script>

<style scoped>
.tab-data-overview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th,
.data-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  color: var(--text-secondary);
  font-weight: 500;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.data-table th:hover {
  color: var(--text-primary);
}

.data-table tr.is-me {
  background: rgba(255, 215, 0, 0.1);
}

.player-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.me-badge {
  color: #ffd700;
}

.max {
  color: var(--accent-secondary);
  font-weight: 600;
}

.max-mark {
  color: #ffd700;
  font-size: 10px;
  margin-left: 2px;
}

.team-summary {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
