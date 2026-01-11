<template>
  <div 
    class="player-card" 
    :class="{ 'is-me': player.is_me, active: isActive }"
    @click="$emit('select', player)"
  >
    <div class="card-header">
      <div class="champion-avatar">
        <img v-if="championIcon" :src="championIcon" :alt="player.champion_name" />
        <span v-else>{{ player.champion_name?.charAt(0) || '?' }}</span>
      </div>
      <div class="player-info">
        <div class="player-name">
          {{ player.summoner_name || player.champion_name }}
          <span class="me-badge" v-if="player.is_me">★</span>
        </div>
        <div class="champion-name">{{ player.champion_name }}</div>
      </div>
      <div class="score-badge" :style="{ color: getScoreColor(player.game_score) }">
        {{ player.game_score || '-' }}
      </div>
    </div>
    
    <div class="kda-row">
      <span class="kda-value">
        <span class="kills">{{ player.kills }}</span>
        <span class="sep">/</span>
        <span class="deaths">{{ player.deaths }}</span>
        <span class="sep">/</span>
        <span class="assists">{{ player.assists }}</span>
      </span>
      <span class="kda-ratio">KDA {{ formatKDA(player.kills, player.deaths, player.assists) }}</span>
    </div>
    
    <div class="participation-row">
      <span>参团 {{ participationPercent }}%</span>
      <span>死亡占比 {{ deathSharePercent }}%</span>
      <span>击杀参与 {{ killParticipation }}%</span>
    </div>
    
    <div class="badges-row" v-if="player.first_blood || player.triple_kills || player.quadra_kills || player.penta_kills">
      <span class="badge multi-kill" v-if="player.penta_kills">🔥五杀</span>
      <span class="badge multi-kill" v-else-if="player.quadra_kills">🔥四杀</span>
      <span class="badge multi-kill" v-else-if="player.triple_kills">🔥三杀</span>
      <span class="badge first-blood" v-if="player.first_blood">⚔️一血</span>
    </div>
    
    <div class="stats-bars">
      <div class="stat-group">
        <div class="stat-row">
          <span class="stat-label">伤害</span>
          <div class="stat-bar">
            <div class="stat-fill damage" :style="{ width: damagePercent + '%' }"></div>
          </div>
          <span class="stat-value">{{ formatNumber(player.total_damage) }} ({{ damagePercent }}%)</span>
        </div>
        <div class="stat-detail">DPM {{ dpm }} · 效率 {{ damageEfficiency }}</div>
      </div>
      
      <div class="stat-group">
        <div class="stat-row">
          <span class="stat-label">承伤</span>
          <div class="stat-bar">
            <div class="stat-fill tank" :style="{ width: tankPercent + '%' }"></div>
          </div>
          <span class="stat-value">{{ formatNumber(player.damage_taken) }} ({{ tankPercent }}%)</span>
        </div>
        <div class="stat-detail">DTPM {{ dtpm }}</div>
      </div>
      
      <div class="stat-group">
        <div class="stat-row">
          <span class="stat-label">经济</span>
          <div class="stat-bar">
            <div class="stat-fill gold" :style="{ width: goldPercent + '%' }"></div>
          </div>
          <span class="stat-value">{{ formatNumber(player.gold_earned) }} ({{ goldPercent }}%)</span>
        </div>
        <div class="stat-detail">GPM {{ gpm }}</div>
      </div>
      
      <div class="stat-group">
        <div class="stat-row">
          <span class="stat-label">视野</span>
          <div class="stat-bar">
            <div class="stat-fill vision" :style="{ width: visionPercent + '%' }"></div>
          </div>
          <span class="stat-value">{{ player.vision_score }}分 ({{ visionPercent }}%)</span>
        </div>
        <div class="stat-detail">插眼{{ player.wards_placed || 0 }} 排眼{{ player.wards_killed || 0 }} 控制守卫{{ player.control_wards || 0 }}</div>
      </div>
    </div>
    
    <div class="extra-stats">
      <span>补刀 {{ totalCS }} ({{ csPerMin }}/m)</span>
      <span>控制 {{ player.cc_time || 0 }}s</span>
      <span v-if="player.heal > 0">治疗 {{ formatNumber(player.heal) }}</span>
    </div>
    
    <div class="extra-stats">
      <span>推塔 {{ player.turrets_killed || 0 }} (伤害{{ formatNumber(player.damage_to_buildings || 0) }})</span>
      <span>小龙 {{ player.dragons_killed || 0 }}</span>
      <span>男爵 {{ player.barons_killed || 0 }}</span>
    </div>
    
    <div class="items-row">
      <div class="spells">
        <img class="spell-icon" v-if="getSpellIcon(player.spell1)" :src="getSpellIcon(player.spell1)" />
        <img class="spell-icon" v-if="getSpellIcon(player.spell2)" :src="getSpellIcon(player.spell2)" />
      </div>
      <div class="items">
        <template v-for="(item, idx) in player.items" :key="idx">
          <img v-if="item && getItemIcon(item)" class="item-icon" :src="getItemIcon(item)" />
          <div v-else class="item-icon empty"></div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatKDA, formatNumber, getScoreColor } from '@/utils/format'
import { getChampionIcon, getItemIcon, getSpellIcon } from '@/utils/ddragon'

const props = defineProps({
  player: Object,
  teamTotals: Object,
  isActive: Boolean,
  gameLength: Number
})

defineEmits(['select'])

const championIcon = computed(() => getChampionIcon(props.player?.champion_id))

const damagePercent = computed(() => {
  if (!props.teamTotals?.damage) return 0
  return Math.round(props.player.total_damage / props.teamTotals.damage * 100)
})

const tankPercent = computed(() => {
  if (!props.teamTotals?.tank) return 0
  return Math.round(props.player.damage_taken / props.teamTotals.tank * 100)
})

const goldPercent = computed(() => {
  if (!props.teamTotals?.gold) return 0
  return Math.round(props.player.gold_earned / props.teamTotals.gold * 100)
})

const visionPercent = computed(() => {
  if (!props.teamTotals?.vision) return 0
  return Math.round(props.player.vision_score / props.teamTotals.vision * 100)
})

const csPerMin = computed(() => {
  if (!props.gameLength) return 0
  const cs = totalCS.value
  return (cs / (props.gameLength / 60)).toFixed(1)
})

const totalCS = computed(() => {
  return (props.player.minions_killed || 0) + (props.player.neutral_minions_killed || 0) || props.player.cs || 0
})

const participationPercent = computed(() => {
  if (!props.teamTotals?.kills) return 0
  return Math.round((props.player.kills + props.player.assists) / props.teamTotals.kills * 100)
})

// 死亡占比
const deathSharePercent = computed(() => {
  if (!props.teamTotals?.deaths) return 0
  return Math.round(props.player.deaths / props.teamTotals.deaths * 100)
})

// 击杀参与率 (击杀+助攻)/队伍总击杀
const killParticipation = computed(() => {
  if (!props.teamTotals?.kills) return 0
  return Math.round((props.player.kills + props.player.assists) / props.teamTotals.kills * 100)
})

// 每分钟数据
const gameMinutes = computed(() => (props.gameLength || 1) / 60)

const dpm = computed(() => Math.round(props.player.total_damage / gameMinutes.value))
const dtpm = computed(() => Math.round(props.player.damage_taken / gameMinutes.value))
const gpm = computed(() => Math.round(props.player.gold_earned / gameMinutes.value))

// 伤害效率 = 伤害/经济
const damageEfficiency = computed(() => {
  if (!props.player.gold_earned) return '0.00'
  return (props.player.total_damage / props.player.gold_earned).toFixed(2)
})
</script>

<style scoped>
.player-card {
  background: var(--bg-card);
  border-radius: var(--border-radius);
  padding: var(--spacing-sm);
  cursor: pointer;
  transition: var(--transition-fast);
  border: 2px solid transparent;
  font-size: 13px;
}

.player-card:hover {
  background: var(--bg-hover);
}

.player-card.active {
  border-color: var(--accent-secondary);
}

.player-card.is-me {
  border-left: 3px solid var(--radar-me);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.champion-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  overflow: hidden;
  flex-shrink: 0;
}

.champion-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.player-info {
  flex: 1;
}

.player-name {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.me-badge {
  color: var(--radar-me);
}

.champion-name {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.score-badge {
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.kda-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.kda-value {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.kills { color: var(--color-win); }
.deaths { color: var(--color-lose); }
.assists { color: var(--text-secondary); }
.sep { color: var(--text-muted); margin: 0 2px; }

.kda-ratio {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.participation-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.badges-row {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
}

.badge {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
}

.badge.multi-kill {
  background: rgba(255, 100, 50, 0.2);
  color: #ff9966;
}

.badge.first-blood {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
}

.stats-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--spacing-xs);
}

.stat-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.stat-label {
  width: 28px;
  font-size: 11px;
  color: var(--text-secondary);
}

.stat-bar {
  flex: 1;
  height: 5px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-normal);
}

.stat-fill.damage { background: var(--accent-primary); }
.stat-fill.tank { background: var(--radar-team1); }
.stat-fill.gold { background: var(--radar-me); }
.stat-fill.vision { background: var(--radar-team3); }

.stat-value {
  width: 90px;
  font-size: 11px;
  color: var(--text-secondary);
  text-align: right;
}

.stat-group {
  margin-bottom: 2px;
}

.stat-detail {
  font-size: 10px;
  color: var(--text-muted);
  padding-left: 32px;
  margin-top: 1px;
}

.extra-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.items-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xs);
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--border-color);
}

.spells {
  display: flex;
  gap: 2px;
}

.spell-icon {
  width: 20px;
  height: 20px;
  background: var(--bg-secondary);
  border-radius: 3px;
  object-fit: cover;
}

.items {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
}

.item-icon {
  width: 20px;
  height: 20px;
  background: var(--bg-secondary);
  border-radius: 3px;
  object-fit: cover;
}

.item-icon.empty {
  opacity: 0.3;
}
</style>
