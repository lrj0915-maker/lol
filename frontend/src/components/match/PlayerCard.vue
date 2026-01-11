<template>
  <div 
    class="player-card" 
    :class="{ 'is-me': player.is_me, active: isActive }"
    @click="$emit('select', player)"
  >
    <div class="card-header">
      <div class="champion-avatar">
        <img v-if="championIcon" :src="championIcon" :alt="player.champion_name" />
        <span v-else class="avatar-placeholder">{{ player.champion_name?.charAt(0) || '?' }}</span>
        <div class="avatar-ring" :class="{ win: player.win, lose: !player.win }"></div>
      </div>
      <div class="player-info">
        <div class="player-name">
          {{ player.summoner_name || player.champion_name }}
          <span class="me-badge" v-if="player.is_me">★</span>
        </div>
        <div class="champion-name">{{ player.champion_name }}</div>
      </div>
      <div class="score-badge" :class="scoreClass">
        <span class="score-value">{{ player.game_score || '-' }}</span>
        <span class="score-label">评分</span>
      </div>
    </div>
    
    <div class="kda-section">
      <div class="kda-main">
        <span class="kills">{{ player.kills }}</span>
        <span class="sep">/</span>
        <span class="deaths">{{ player.deaths }}</span>
        <span class="sep">/</span>
        <span class="assists">{{ player.assists }}</span>
      </div>
      <div class="kda-ratio" :class="kdaClass">
        {{ formatKDA(player.kills, player.deaths, player.assists) }} KDA
      </div>
    </div>
    
    <div class="participation-row">
      <div class="part-item">
        <span class="part-value">{{ participationPercent }}%</span>
        <span class="part-label">参团</span>
      </div>
      <div class="part-item">
        <span class="part-value">{{ deathSharePercent }}%</span>
        <span class="part-label">死亡占比</span>
      </div>
      <div class="part-item">
        <span class="part-value">{{ killParticipation }}%</span>
        <span class="part-label">击杀参与</span>
      </div>
    </div>
    
    <div class="badges-row" v-if="player.first_blood || player.triple_kills || player.quadra_kills || player.penta_kills">
      <span class="badge penta" v-if="player.penta_kills">🔥 五杀</span>
      <span class="badge quadra" v-else-if="player.quadra_kills">🔥 四杀</span>
      <span class="badge triple" v-else-if="player.triple_kills">⚡ 三杀</span>
      <span class="badge first-blood" v-if="player.first_blood">⚔️ 一血</span>
    </div>
    
    <div class="stats-section">
      <div class="stat-item">
        <div class="stat-header">
          <span class="stat-label">伤害</span>
          <span class="stat-value">{{ formatNumber(player.total_damage) }}</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill damage" :style="{ width: damagePercent + '%' }"></div>
        </div>
        <div class="stat-detail">
          <span>{{ damagePercent }}% 占比</span>
          <span>DPM {{ dpm }}</span>
          <span>效率 {{ damageEfficiency }}</span>
        </div>
      </div>
      
      <div class="stat-item">
        <div class="stat-header">
          <span class="stat-label">承伤</span>
          <span class="stat-value">{{ formatNumber(player.damage_taken) }}</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill tank" :style="{ width: tankPercent + '%' }"></div>
        </div>
        <div class="stat-detail">
          <span>{{ tankPercent }}% 占比</span>
          <span>DTPM {{ dtpm }}</span>
        </div>
      </div>
      
      <div class="stat-item">
        <div class="stat-header">
          <span class="stat-label">经济</span>
          <span class="stat-value">{{ formatNumber(player.gold_earned) }}</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill gold" :style="{ width: goldPercent + '%' }"></div>
        </div>
        <div class="stat-detail">
          <span>{{ goldPercent }}% 占比</span>
          <span>GPM {{ gpm }}</span>
        </div>
      </div>
      
      <div class="stat-item">
        <div class="stat-header">
          <span class="stat-label">视野</span>
          <span class="stat-value">{{ player.vision_score }}分</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill vision" :style="{ width: visionPercent + '%' }"></div>
        </div>
        <div class="stat-detail">
          <span>插眼 {{ player.wards_placed || 0 }}</span>
          <span>排眼 {{ player.wards_killed || 0 }}</span>
          <span>控制 {{ player.control_wards || 0 }}</span>
        </div>
      </div>
    </div>
    
    <div class="extra-section">
      <div class="extra-row">
        <span>补刀 {{ totalCS }} ({{ csPerMin }}/m)</span>
        <span>控制 {{ player.cc_time || 0 }}s</span>
        <span v-if="player.heal > 0">治疗 {{ formatNumber(player.heal) }}</span>
      </div>
      <div class="extra-row">
        <span>推塔 {{ player.turrets_killed || 0 }}</span>
        <span>小龙 {{ player.dragons_killed || 0 }}</span>
        <span>男爵 {{ player.barons_killed || 0 }}</span>
      </div>
    </div>
    
    <div class="items-section">
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

const scoreClass = computed(() => {
  const score = props.player?.game_score || 0
  if (score >= 80) return 'score-s'
  if (score >= 60) return 'score-a'
  if (score >= 40) return 'score-b'
  if (score >= 20) return 'score-c'
  return 'score-d'
})

const kdaClass = computed(() => {
  const kda = (props.player.kills + props.player.assists) / Math.max(1, props.player.deaths)
  if (kda >= 5) return 'kda-excellent'
  if (kda >= 3) return 'kda-good'
  if (kda >= 2) return 'kda-normal'
  return 'kda-poor'
})

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

const deathSharePercent = computed(() => {
  if (!props.teamTotals?.deaths) return 0
  return Math.round(props.player.deaths / props.teamTotals.deaths * 100)
})

const killParticipation = computed(() => {
  if (!props.teamTotals?.kills) return 0
  return Math.round((props.player.kills + props.player.assists) / props.teamTotals.kills * 100)
})

const gameMinutes = computed(() => (props.gameLength || 1) / 60)
const dpm = computed(() => Math.round(props.player.total_damage / gameMinutes.value))
const dtpm = computed(() => Math.round(props.player.damage_taken / gameMinutes.value))
const gpm = computed(() => Math.round(props.player.gold_earned / gameMinutes.value))

const damageEfficiency = computed(() => {
  if (!props.player.gold_earned) return '0.00'
  return (props.player.total_damage / props.player.gold_earned).toFixed(2)
})
</script>

<style scoped>
.player-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
}

.player-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  transition: background var(--transition-normal);
}

.player-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-color-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.player-card.active {
  border-color: var(--accent-secondary);
  box-shadow: var(--glow-primary);
}

.player-card.active::before {
  background: var(--gradient-primary);
}

.player-card.is-me::before {
  background: var(--gradient-gold);
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.champion-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  position: relative;
  flex-shrink: 0;
}

.champion-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--font-size-lg);
  color: var(--text-muted);
}

.avatar-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid transparent;
}

.avatar-ring.win { border-color: var(--color-win); }
.avatar-ring.lose { border-color: var(--color-lose); }

.player-info {
  flex: 1;
  min-width: 0;
}

.player-name {
  font-weight: 600;
  font-size: var(--font-size-md);
  display: flex;
  align-items: center;
  gap: 4px;
}

.me-badge {
  color: var(--radar-me);
  text-shadow: 0 0 10px var(--radar-me);
}

.champion-name {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.score-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background: var(--bg-secondary);
}

.score-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

.score-s .score-value { color: #ff6b35; text-shadow: 0 0 10px rgba(255, 107, 53, 0.5); }
.score-a .score-value { color: #ffd700; }
.score-b .score-value { color: var(--text-secondary); }
.score-c .score-value { color: var(--color-info); }
.score-d .score-value { color: var(--color-lose); }

/* KDA */
.kda-section {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.kda-main {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.kills { color: var(--color-win); }
.deaths { color: var(--color-lose); }
.assists { color: var(--text-secondary); }
.sep { color: var(--text-disabled); margin: 0 2px; }

.kda-ratio {
  font-size: var(--font-size-sm);
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  background: var(--bg-secondary);
}

.kda-excellent { color: #ff6b35; background: rgba(255, 107, 53, 0.15); }
.kda-good { color: var(--color-win); background: rgba(78, 204, 163, 0.15); }
.kda-normal { color: var(--text-secondary); }
.kda-poor { color: var(--color-lose); background: rgba(233, 69, 96, 0.15); }

/* Participation */
.participation-row {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.part-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.part-value {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.part-label {
  font-size: 10px;
  color: var(--text-muted);
}

/* Badges */
.badges-row {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.badge {
  font-size: var(--font-size-xs);
  padding: 3px 8px;
  border-radius: var(--border-radius-sm);
  font-weight: 500;
}

.badge.penta {
  background: linear-gradient(135deg, #ff6b35, #e94560);
  color: white;
  animation: glow 2s ease-in-out infinite;
}

.badge.quadra {
  background: rgba(255, 107, 53, 0.2);
  color: #ff6b35;
  border: 1px solid rgba(255, 107, 53, 0.3);
}

.badge.triple {
  background: rgba(255, 215, 0, 0.15);
  color: #ffd700;
  border: 1px solid rgba(255, 215, 0, 0.3);
}

.badge.first-blood {
  background: rgba(233, 69, 96, 0.15);
  color: var(--color-lose);
  border: 1px solid rgba(233, 69, 96, 0.3);
}

/* Stats */
.stats-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.stat-value {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-bar {
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-normal);
}

.stat-fill.damage { background: linear-gradient(90deg, #e94560, #ff6b35); }
.stat-fill.tank { background: linear-gradient(90deg, #58a6ff, #22d3ee); }
.stat-fill.gold { background: linear-gradient(90deg, #ffd700, #f39c12); }
.stat-fill.vision { background: linear-gradient(90deg, #a855f7, #ec4899); }

.stat-detail {
  display: flex;
  gap: var(--spacing-sm);
  font-size: 10px;
  color: var(--text-disabled);
}

/* Extra */
.extra-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.extra-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

/* Items */
.items-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.spells {
  display: flex;
  gap: 3px;
}

.spell-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid var(--border-color);
}

.items {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  object-fit: cover;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.item-icon.empty {
  opacity: 0.3;
}
</style>
