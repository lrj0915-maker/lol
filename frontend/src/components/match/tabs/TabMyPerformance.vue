<template>
  <div class="tab-player-detail">
    <!-- 玩家选择器 -->
    <div class="player-selector">
      <div 
        v-for="player in team" 
        :key="player.champion_name"
        class="player-option"
        :class="{ active: selectedChampion === player.champion_name, me: player.is_me }"
        @click="selectedChampion = player.champion_name"
      >
        <span class="champ-name">{{ player.champion_name }}</span>
        <span class="me-badge" v-if="player.is_me">★</span>
      </div>
    </div>
    
    <!-- 玩家数据 -->
    <div class="perf-grid" v-if="currentPlayer">
      <div class="perf-card">
        <h4>伤害构成</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">物理伤害</span>
            <span class="stat-value">{{ formatK(currentPlayer.physical_damage || 0) }}</span>
            <span class="stat-percent">{{ getDmgPercent('physical') }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">魔法伤害</span>
            <span class="stat-value">{{ formatK(currentPlayer.magic_damage || 0) }}</span>
            <span class="stat-percent">{{ getDmgPercent('magic') }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">真实伤害</span>
            <span class="stat-value">{{ formatK(currentPlayer.true_damage || 0) }}</span>
            <span class="stat-percent">{{ getDmgPercent('true') }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大暴击</span>
            <span class="stat-value">{{ currentPlayer.largest_critical_strike || 0 }}</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>资源获取</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">补刀</span>
            <span class="stat-value">{{ totalCS }}</span>
            <span class="stat-percent">{{ csPerMin }}/分</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">经济</span>
            <span class="stat-value">{{ formatK(currentPlayer.gold_earned) }}</span>
            <span class="stat-percent">{{ gpm }}/分</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">花费金币</span>
            <span class="stat-value">{{ formatK(currentPlayer.gold_spent || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">购买装备</span>
            <span class="stat-value">{{ currentPlayer.items_purchased || 0 }}件</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>视野控制</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">视野得分</span>
            <span class="stat-value">{{ currentPlayer.vision_score }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">插眼</span>
            <span class="stat-value">{{ currentPlayer.wards_placed || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">排眼</span>
            <span class="stat-value">{{ currentPlayer.wards_killed || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">控制守卫</span>
            <span class="stat-value">{{ currentPlayer.control_wards || 0 }}</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>目标参与</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">推塔</span>
            <span class="stat-value">{{ currentPlayer.turrets_killed || 0 }}</span>
            <span class="stat-percent">伤害{{ formatK(currentPlayer.damage_to_buildings || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">目标伤害</span>
            <span class="stat-value">{{ formatK(currentPlayer.damage_to_objectives || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">小龙</span>
            <span class="stat-value">{{ currentPlayer.dragons_killed || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">男爵</span>
            <span class="stat-value">{{ currentPlayer.barons_killed || 0 }}</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>团战表现</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">参团率</span>
            <span class="stat-value">{{ participation }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">死亡占比</span>
            <span class="stat-value">{{ deathShare }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">控制时间</span>
            <span class="stat-value">{{ currentPlayer.cc_time || 0 }}秒</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大连杀</span>
            <span class="stat-value">{{ currentPlayer.largest_killing_spree || 0 }}</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>生存数据</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">最长存活</span>
            <span class="stat-value">{{ formatTime(currentPlayer.longest_time_living || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">死亡时间</span>
            <span class="stat-value">{{ formatTime(currentPlayer.time_spent_dead || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">减伤量</span>
            <span class="stat-value">{{ formatK(currentPlayer.damage_self_mitigated || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">治疗量</span>
            <span class="stat-value">{{ formatK(currentPlayer.heal || 0) }}</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>技能使用</h4>
        <div class="stat-list">
          <div class="stat-item">
            <span class="stat-label">召唤师技能1</span>
            <span class="stat-value">{{ currentPlayer.spell1_casts || 0 }}次</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">召唤师技能2</span>
            <span class="stat-value">{{ currentPlayer.spell2_casts || 0 }}次</span>
          </div>
        </div>
      </div>
      
      <div class="perf-card">
        <h4>亮点成就</h4>
        <div class="achievements">
          <span class="badge" v-if="currentPlayer.first_blood">⚔️ 一血</span>
          <span class="badge" v-if="currentPlayer.penta_kills">🔥 五杀 x{{ currentPlayer.penta_kills }}</span>
          <span class="badge" v-if="currentPlayer.quadra_kills">🔥 四杀 x{{ currentPlayer.quadra_kills }}</span>
          <span class="badge" v-if="currentPlayer.triple_kills">🔥 三杀 x{{ currentPlayer.triple_kills }}</span>
          <span class="badge" v-if="currentPlayer.double_kills">双杀 x{{ currentPlayer.double_kills }}</span>
          <span class="no-badge" v-if="!hasAchievements">无特殊成就</span>
        </div>
      </div>
    </div>
    
    <div class="no-data" v-else>未找到玩家数据</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ match: Object, team: Array })

const selectedChampion = ref('')

// 默认选中自己
watch(() => props.team, (team) => {
  if (team?.length && !selectedChampion.value) {
    const me = team.find(p => p.is_me)
    selectedChampion.value = me?.champion_name || team[0]?.champion_name || ''
  }
}, { immediate: true })

const currentPlayer = computed(() => {
  return props.team?.find(p => p.champion_name === selectedChampion.value)
})

const gameMinutes = computed(() => (props.match?.game_length || 1) / 60)
const totalKills = computed(() => props.team?.reduce((s, p) => s + p.kills, 0) || 1)
const totalDeaths = computed(() => props.team?.reduce((s, p) => s + p.deaths, 0) || 1)

const totalCS = computed(() => {
  if (!currentPlayer.value) return 0
  return (currentPlayer.value.minions_killed || 0) + (currentPlayer.value.neutral_minions_killed || 0)
})

const csPerMin = computed(() => (totalCS.value / gameMinutes.value).toFixed(1))
const gpm = computed(() => Math.round((currentPlayer.value?.gold_earned || 0) / gameMinutes.value))

const participation = computed(() => {
  if (!currentPlayer.value) return 0
  return Math.round((currentPlayer.value.kills + currentPlayer.value.assists) / totalKills.value * 100)
})

const deathShare = computed(() => {
  if (!currentPlayer.value) return 0
  return Math.round(currentPlayer.value.deaths / totalDeaths.value * 100)
})

const hasAchievements = computed(() => {
  if (!currentPlayer.value) return false
  return currentPlayer.value.first_blood || currentPlayer.value.double_kills || 
         currentPlayer.value.triple_kills || currentPlayer.value.quadra_kills || currentPlayer.value.penta_kills
})

function getDmgPercent(type) {
  if (!currentPlayer.value) return 0
  const total = (currentPlayer.value.physical_damage || 0) + 
                (currentPlayer.value.magic_damage || 0) + 
                (currentPlayer.value.true_damage || 0)
  if (!total) return 0
  const val = type === 'physical' ? (currentPlayer.value.physical_damage || 0)
            : type === 'magic' ? (currentPlayer.value.magic_damage || 0)
            : (currentPlayer.value.true_damage || 0)
  return Math.round(val / total * 100)
}

function formatK(num) {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.tab-player-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  height: 100%;
}

.player-selector {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  overflow-x: auto;
}

.player-option {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  font-size: var(--font-size-sm);
  white-space: nowrap;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.player-option:hover {
  background: var(--bg-hover);
}

.player-option.active {
  background: var(--gradient-primary);
  color: var(--bg-primary);
}

.player-option.me {
  border-left: 3px solid var(--radar-me);
}

.me-badge {
  color: var(--radar-me);
  font-size: var(--font-size-xs);
  text-shadow: 0 0 8px var(--radar-me);
}

.player-option.active .me-badge {
  color: var(--bg-primary);
  text-shadow: none;
}

.perf-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
  flex: 1;
  overflow-y: auto;
}

.perf-card {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.perf-card:hover {
  border-color: var(--border-color-light);
  background: var(--bg-card-hover);
}

.perf-card h4 {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
}

.stat-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-item {
  display: flex;
  align-items: center;
  font-size: var(--font-size-xs);
}

.stat-label {
  flex: 1;
  color: var(--text-muted);
}

.stat-value {
  font-weight: 600;
  margin-right: 4px;
  color: var(--text-primary);
}

.stat-percent {
  color: var(--text-disabled);
  font-size: 10px;
  min-width: 38px;
  text-align: right;
}

.achievements {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.badge {
  font-size: 10px;
  padding: 3px 8px;
  background: rgba(255, 107, 53, 0.2);
  color: #ff9966;
  border-radius: var(--border-radius-sm);
  border: 1px solid rgba(255, 107, 53, 0.3);
}

.no-badge {
  font-size: 10px;
  color: var(--text-muted);
}

.no-data {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-xl);
}

@media (max-width: 700px) {
  .perf-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
