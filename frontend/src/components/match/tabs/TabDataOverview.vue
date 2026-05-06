<template>
  <div class="tab-data-overview">
    <div class="table-wrap">
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
          <tr v-for="player in sortedTeam" :key="player.summoner_name" :class="{ 'is-me': player.is_me }">
            <td class="player-cell">
              <span class="me-badge" v-if="player.is_me">我</span>
              {{ player.summoner_name || player.champion_name }}
            </td>
            <td>{{ player.kills }}/{{ player.deaths }}/{{ player.assists }}</td>
            <td :class="{ max: isMax('total_damage', player) }">{{ formatK(player.total_damage) }}</td>
            <td :class="{ max: isMax('damage_taken', player) }">{{ formatK(player.damage_taken) }}</td>
            <td :class="{ max: isMax('gold_earned', player) }">{{ formatK(player.gold_earned) }}</td>
            <td>{{ getCS(player) }}</td>
            <td :class="{ max: isMax('vision_score', player) }">{{ player.vision_score }}</td>
            <td>{{ getParticipation(player) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

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

const totalKills = computed(() => props.team?.reduce((sum, player) => sum + player.kills, 0) || 0)
const totalDamage = computed(() => props.team?.reduce((sum, player) => sum + (player.total_damage || 0), 0) || 0)
const totalGold = computed(() => props.team?.reduce((sum, player) => sum + (player.gold_earned || 0), 0) || 0)
const totalVision = computed(() => props.team?.reduce((sum, player) => sum + (player.vision_score || 0), 0) || 0)

const sortedTeam = computed(() => {
  if (!props.team) return []
  return [...props.team].sort((left, right) => {
    const leftValue = getValue(left, sortKey.value)
    const rightValue = getValue(right, sortKey.value)
    return sortDesc.value ? rightValue - leftValue : leftValue - rightValue
  })
})

function getValue(player, key) {
  if (key === 'name') return player.is_me ? Number.MAX_SAFE_INTEGER : 0
  if (key === 'kda') return (player.kills + player.assists) / Math.max(1, player.deaths)
  if (key === 'damage') return player.total_damage || 0
  if (key === 'tank') return player.damage_taken || 0
  if (key === 'gold') return player.gold_earned || 0
  if (key === 'cs') return getCS(player)
  if (key === 'vision') return player.vision_score || 0
  if (key === 'participation') return getParticipation(player)
  return 0
}

function getCS(player) {
  return (player.minions_killed || 0) + (player.neutral_minions_killed || 0)
}
function getParticipation(player) {
  if (!totalKills.value) return 0
  return Math.round(((player.kills + player.assists) / totalKills.value) * 100)
}
function sortBy(key) {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value
  else { sortKey.value = key; sortDesc.value = true }
}
function isMax(key, player) {
  if (!props.team?.length) return false
  const value = player[key] || 0
  if (!value) return false
  return value === Math.max(...props.team.map((item) => item[key] || 0))
}
function formatK(value) {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value || 0
}
</script>

<style scoped>
.tab-data-overview { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.table-wrap { overflow: auto; border: 1px solid var(--border-color); border-radius: 12px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; background: rgba(255, 255, 255, 0.02); }
.data-table th,.data-table td { padding: 9px 10px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.05); white-space: nowrap; }
.data-table th { position: sticky; top: 0; background: rgba(22, 27, 34, 0.95); color: var(--text-secondary); font-size: 11px; cursor: pointer; }
.data-table tbody tr:hover { background: rgba(255, 255, 255, 0.03); }
.data-table tbody tr.is-me { background: rgba(78, 204, 163, 0.08); }
.player-cell { color: var(--text-primary); font-weight: 600; }
.me-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px; margin-right: 6px; border-radius: 999px; background: rgba(78, 204, 163, 0.18); color: #4ecca3; font-size: 10px; font-weight: 800; }
.max { color: #58a6ff; font-weight: 700; }
.team-summary { display: flex; gap: 8px; flex-wrap: wrap; }
.team-summary span { padding: 5px 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); color: var(--text-secondary); font-size: 11px; }
</style>
