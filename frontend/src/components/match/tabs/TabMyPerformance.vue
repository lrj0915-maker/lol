<template>
  <div class="tab-player-detail">
    <div class="player-selector">
      <div
        v-for="player in team"
        :key="player.champion_name"
        class="player-option"
        :class="{ active: selectedChampion === player.champion_name, me: player.is_me }"
        @click="selectedChampion = player.champion_name"
      >
        <span class="champ-name">{{ player.champion_name }}</span>
        <span class="me-badge" v-if="player.is_me">我</span>
      </div>
    </div>

    <div class="perf-grid" v-if="currentPlayer">
      <div class="perf-card">
        <h4>伤害构成</h4>
        <div class="stat-item"><span>物理伤害</span><b>{{ formatK(currentPlayer.physical_damage || 0) }}</b><em>{{ getDmgPercent('physical') }}%</em></div>
        <div class="stat-item"><span>魔法伤害</span><b>{{ formatK(currentPlayer.magic_damage || 0) }}</b><em>{{ getDmgPercent('magic') }}%</em></div>
        <div class="stat-item"><span>真实伤害</span><b>{{ formatK(currentPlayer.true_damage || 0) }}</b><em>{{ getDmgPercent('true') }}%</em></div>
        <div class="stat-item"><span>最大暴击</span><b>{{ currentPlayer.largest_critical_strike || 0 }}</b></div>
      </div>

      <div class="perf-card">
        <h4>资源获取</h4>
        <div class="stat-item"><span>补刀</span><b>{{ totalCS }}</b><em>{{ csPerMin }}/分</em></div>
        <div class="stat-item"><span>经济</span><b>{{ formatK(currentPlayer.gold_earned) }}</b><em>{{ gpm }}/分</em></div>
        <div class="stat-item"><span>消费金币</span><b>{{ formatK(currentPlayer.gold_spent || 0) }}</b></div>
        <div class="stat-item"><span>购买装备</span><b>{{ currentPlayer.items_purchased || 0 }} 件</b></div>
      </div>

      <div class="perf-card">
        <h4>视野控制</h4>
        <div class="stat-item"><span>视野得分</span><b>{{ currentPlayer.vision_score }}</b></div>
        <div class="stat-item"><span>插眼</span><b>{{ currentPlayer.wards_placed || 0 }}</b></div>
        <div class="stat-item"><span>排眼</span><b>{{ currentPlayer.wards_killed || 0 }}</b></div>
        <div class="stat-item"><span>控制守卫</span><b>{{ currentPlayer.control_wards || 0 }}</b></div>
      </div>

      <div class="perf-card">
        <h4>团战表现</h4>
        <div class="stat-item"><span>参团率</span><b>{{ participation }}%</b></div>
        <div class="stat-item"><span>死亡占比</span><b>{{ deathShare }}%</b></div>
        <div class="stat-item"><span>控制时间</span><b>{{ currentPlayer.cc_time || 0 }} 秒</b></div>
        <div class="stat-item"><span>最大连杀</span><b>{{ currentPlayer.largest_killing_spree || 0 }}</b></div>
      </div>
    </div>

    <div v-else class="no-data">未找到玩家数据</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
const props = defineProps({ match: Object, team: Array })
const selectedChampion = ref('')

watch(() => props.team, (team) => {
  if (team?.length && !selectedChampion.value) {
    const me = team.find((player) => player.is_me)
    selectedChampion.value = me?.champion_name || team[0]?.champion_name || ''
  }
}, { immediate: true })

const currentPlayer = computed(() => props.team?.find((player) => player.champion_name === selectedChampion.value))
const gameMinutes = computed(() => (props.match?.game_length || props.match?.duration || 1) / 60)
const totalKills = computed(() => props.team?.reduce((sum, player) => sum + player.kills, 0) || 1)
const totalDeaths = computed(() => props.team?.reduce((sum, player) => sum + player.deaths, 0) || 1)
const totalCS = computed(() => currentPlayer.value ? (currentPlayer.value.minions_killed || 0) + (currentPlayer.value.neutral_minions_killed || 0) : 0)
const csPerMin = computed(() => (totalCS.value / gameMinutes.value).toFixed(1))
const gpm = computed(() => Math.round((currentPlayer.value?.gold_earned || 0) / gameMinutes.value))
const participation = computed(() => currentPlayer.value ? Math.round(((currentPlayer.value.kills + currentPlayer.value.assists) / totalKills.value) * 100) : 0)
const deathShare = computed(() => currentPlayer.value ? Math.round((currentPlayer.value.deaths / totalDeaths.value) * 100) : 0)

function getDmgPercent(type) {
  if (!currentPlayer.value) return 0
  const total = (currentPlayer.value.physical_damage || 0) + (currentPlayer.value.magic_damage || 0) + (currentPlayer.value.true_damage || 0)
  if (!total) return 0
  const value = type === 'physical' ? (currentPlayer.value.physical_damage || 0) : type === 'magic' ? (currentPlayer.value.magic_damage || 0) : (currentPlayer.value.true_damage || 0)
  return Math.round((value / total) * 100)
}
function formatK(value) {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value || 0
}
</script>

<style scoped>
.tab-player-detail { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.player-selector { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 2px; }
.player-option { display: flex; align-items: center; gap: 5px; padding: 6px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; white-space: nowrap; color: var(--text-secondary); border: 1px solid var(--border-color); background: rgba(255, 255, 255, 0.03); transition: all .18s ease; }
.player-option:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); }
.player-option.active { background: linear-gradient(90deg, rgba(78, 204, 163, 0.22), rgba(88, 166, 255, 0.18)); color: var(--text-primary); border-color: rgba(78, 204, 163, 0.28); }
.player-option.me { border-left: 3px solid #4ecca3; }
.me-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px; border-radius: 999px; background: rgba(78, 204, 163, 0.18); color: #4ecca3; font-size: 10px; font-weight: 800; }
.player-option.active .me-badge { color: var(--text-primary); }
.perf-grid { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 10px; min-height: 0; }
.perf-card { display: flex; flex-direction: column; padding: 10px; border-radius: 10px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); }
.perf-card h4 { margin: 0 0 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(255, 255, 255, 0.06); font-size: 12px; color: var(--text-primary); }
.stat-item { display: flex; align-items: center; font-size: 11px; padding: 4px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
.stat-item:last-child { border-bottom: none; }
.stat-item span { flex: 1; color: var(--text-secondary); }
.stat-item b { color: var(--text-primary); font-weight: 600; margin-right: 6px; }
.stat-item em { font-style: normal; min-width: 40px; text-align: right; color: var(--text-secondary); }
.no-data { text-align: center; color: var(--text-secondary); padding: 18px; font-size: 12px; }
@media (max-width: 1280px) { .perf-grid { grid-template-columns: repeat(2, minmax(180px, 1fr)); } }
</style>
