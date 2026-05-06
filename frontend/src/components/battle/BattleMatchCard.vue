<template>
  <div class="battle-match-card" :class="[resultClass, { expanded }]">
    <button class="card-main" :aria-pressed="expanded ? 'true' : 'false'" @click="$emit('toggle', match.game_id)">
      <div class="left-meta compact-block result-block">
        <div class="result-badge">{{ resultText }}</div>
        <div class="mode-group">
          <span class="mode-chip">{{ match.queue_label || match.game_mode || '未知模式' }}</span>
          <span class="sub-chip">{{ resultSubtext }}</span>
        </div>
        <div class="time-group">
          <span class="time-chip primary numeric">{{ relativeTime }}</span>
          <span class="time-chip numeric">{{ absoluteTime }}</span>
          <span class="time-chip numeric">{{ formatGameLength(match.duration) }}</span>
        </div>
      </div>

      <div class="hero-area compact-block">
        <img v-if="championIcon" :src="championIcon" class="champion-icon" :alt="match.champion_name" />
        <div v-else class="champion-icon placeholder">无</div>

        <div class="hero-meta">
          <div class="hero-name-row">
            <div class="hero-name">{{ match.champion_name || '未知英雄' }}</div>
            <div class="score-tag numeric" :style="{ color: getScoreColor(match.game_score) }">{{ match.game_score || '-' }}</div>
          </div>
          <div class="hero-level numeric">等级 {{ match.level || 0 }} · {{ match.cs || 0 }} CS · {{ match.cs_per_min || 0 }}/分</div>
          <div class="kda numeric">{{ match.kills || 0 }} / {{ match.deaths || 0 }} / {{ match.assists || 0 }} · {{ match.kda || 0 }} KDA</div>
        </div>
      </div>

      <div class="icon-area compact-block">
        <div class="icon-group">
          <img v-if="getSpellIcon(match.spell1)" :src="getSpellIcon(match.spell1)" class="tiny-icon" alt="spell1" />
          <img v-if="getSpellIcon(match.spell2)" :src="getSpellIcon(match.spell2)" class="tiny-icon" alt="spell2" />
        </div>
        <div class="icon-group">
          <img v-for="perk in visiblePerks" :key="perk" :src="getRuneIconUrl(perk)" class="tiny-icon" alt="perk" />
          <span v-if="!visiblePerks.length" class="placeholder-text">无符文</span>
        </div>
        <div class="icon-group items">
          <img v-for="item in visibleItems" :key="item" :src="getItemIcon(item)" class="tiny-icon" alt="item" />
          <span v-if="!visibleItems.length" class="placeholder-text">无装备</span>
        </div>
      </div>

      <div class="share-area compact-block">
        <div class="share-item"><span>参团</span><b class="numeric">{{ percent(match.kill_participation) }}</b></div>
        <div class="share-item"><span>伤害</span><b class="numeric">{{ percent(match.damage_share) }}</b></div>
        <div class="share-item"><span>承伤</span><b class="numeric">{{ percent(match.tank_share) }}</b></div>
        <div class="share-item"><span>经济</span><b class="numeric">{{ percent(match.gold_share) }}</b></div>
      </div>

      <div class="teams-area compact-block">
        <div class="team-col">
          <div class="team-title">我方</div>
          <div v-for="player in match.ally_brief || []" :key="`${match.game_id}-ally-${player.identity || player.name}`" class="team-player" :class="{ me: player.is_me }">
            <img v-if="getChampionIcon(player.champion_id)" :src="getChampionIcon(player.champion_id)" class="team-icon" :alt="player.champion_name" />
            <span>{{ player.display_name || player.identity || player.name }}</span>
            <em v-if="player.is_me" class="me-badge">我</em>
          </div>
        </div>

        <div class="team-col">
          <div class="team-title">敌方</div>
          <div v-for="player in match.enemy_brief || []" :key="`${match.game_id}-enemy-${player.identity || player.name}`" class="team-player">
            <img v-if="getChampionIcon(player.champion_id)" :src="getChampionIcon(player.champion_id)" class="team-icon" :alt="player.champion_name" />
            <span>{{ player.display_name || player.identity || player.name }}</span>
          </div>
        </div>
      </div>

      <div class="tail-area compact-block">
        <div class="toggle-indicator">{{ expanded ? '收起详情' : '展开详情' }}</div>
      </div>
    </button>

    <Transition name="detail-expand">
      <div v-if="expanded" class="expanded-wrap">
        <div v-if="detailLoading" class="detail-loading">正在加载详情...</div>
        <div v-else-if="detailError" class="detail-error">
          <span>{{ detailError }}</span>
          <button class="retry-btn" @click.stop="$emit('retry', match.game_id)">重试</button>
        </div>
        <BattleMatchExpandedDetail v-else-if="detail && detail.game_id" :detail="detail" />
        <div v-else class="detail-loading">暂无可用详情</div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getChampionIcon, getItemIcon, getSpellIcon } from '@/utils/ddragon'
import { getRuneIconUrl } from '@/data/runes'
import { formatGameLength, getScoreColor } from '@/utils/format'
import BattleMatchExpandedDetail from './BattleMatchExpandedDetail.vue'

const props = defineProps({
  match: { type: Object, required: true },
  expanded: { type: Boolean, default: false },
  detail: { type: Object, default: null },
  detailLoading: { type: Boolean, default: false },
  detailError: { type: String, default: '' },
})
defineEmits(['toggle', 'retry'])

const championIcon = computed(() => getChampionIcon(props.match.champion_id))
const visibleItems = computed(() => (props.match.items || []).filter(Boolean).slice(0, 6))
const visiblePerks = computed(() => (props.match.perks || []).filter(Boolean).slice(0, 2))
const resultClass = computed(() => {
  const queueText = String(props.match.queue_label || props.match.game_mode || '').toLowerCase()
  if (queueText.includes('custom') || queueText.includes('practice') || queueText.includes('tutorial') || queueText.includes('训练')) return 'neutral'
  return props.match.is_win ? 'win' : 'lose'
})
const resultText = computed(() => resultClass.value === 'neutral' ? '对局' : (props.match.is_win ? '胜利' : '失败'))
const resultSubtext = computed(() => resultClass.value === 'neutral' ? '自定义 / 练习' : (props.match.is_win ? '蓝侧表现' : '红侧回顾'))
const relativeTime = computed(() => {
  const timestamp = Number(props.match.timestamp || 0) * 1000
  if (!timestamp) return '时间未知'
  const diff = Math.max(0, Date.now() - timestamp)
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  return `${Math.floor(hours / 24)} 天前`
})
const absoluteTime = computed(() => {
  const timestamp = Number(props.match.timestamp || 0)
  if (!timestamp) return '暂无时间'
  const date = new Date(timestamp * 1000)
  return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
})
function percent(value) {
  const number = Number(value ?? 0)
  return `${Number.isFinite(number) ? number : 0}%`
}
</script>

<style scoped>
.battle-match-card { position: relative; border-radius: 16px; border: 1px solid var(--border-color); overflow: hidden; box-shadow: 0 10px 24px rgba(0,0,0,.18); transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.battle-match-card::before { content: ''; position: absolute; inset: 0 0 auto 0; height: 2px; opacity: 0; transition: opacity .18s ease; }
.battle-match-card:hover { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(0,0,0,.22); border-color: rgba(255,255,255,.12); }
.battle-match-card:hover::before,.battle-match-card.expanded::before { opacity: .95; }
.battle-match-card.expanded { border-color: rgba(88,166,255,.38); box-shadow: 0 18px 34px rgba(0,0,0,.26); }
.battle-match-card.win { background: linear-gradient(90deg, rgba(88,166,255,.14), rgba(255,255,255,.03)); }
.battle-match-card.win::before { background: linear-gradient(90deg, rgba(88,166,255,.95), rgba(78,204,163,.65)); }
.battle-match-card.lose { background: linear-gradient(90deg, rgba(233,69,96,.14), rgba(255,255,255,.03)); }
.battle-match-card.lose::before { background: linear-gradient(90deg, rgba(233,69,96,.95), rgba(255,159,67,.6)); }
.battle-match-card.neutral { background: linear-gradient(90deg, rgba(180,180,180,.14), rgba(255,255,255,.03)); }
.battle-match-card.neutral::before { background: linear-gradient(90deg, rgba(180,180,180,.95), rgba(255,255,255,.42)); }
.card-main { width: 100%; display: grid; grid-template-columns: 144px 220px 154px 150px minmax(220px, 1fr) 74px; gap: 8px; align-items: stretch; padding: 10px; background: transparent; border: none; color: inherit; text-align: left; cursor: pointer; outline: none; }
.card-main:focus-visible { box-shadow: inset 0 0 0 1px rgba(88,166,255,.45); }
.card-main:active { transform: scale(.998); }
.compact-block { min-width: 0; padding: 8px; border-radius: 10px; background: rgba(255,255,255,.025); border: 1px solid rgba(255,255,255,.04); transition: background .18s ease, border-color .18s ease, box-shadow .18s ease; }
.battle-match-card:hover .compact-block { border-color: rgba(255,255,255,.08); }
.battle-match-card.expanded .compact-block { background: rgba(255,255,255,.04); border-color: rgba(255,255,255,.1); }
.result-block { display: grid; gap: 6px; align-content: start; }
.result-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 58px; width: fit-content; padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 800; background: rgba(255,255,255,.08); transition: transform .18s ease, background .18s ease; }
.battle-match-card.expanded .result-badge { transform: translateX(2px); background: rgba(255,255,255,.12); }
.mode-group { display: grid; gap: 5px; }
.mode-chip,.sub-chip,.time-chip { display: inline-flex; align-items: center; width: fit-content; max-width: 100%; padding: 4px 8px; border-radius: 999px; font-size: 11px; }
.mode-chip { background: rgba(255,255,255,.08); color: var(--text-primary); font-weight: 700; }
.sub-chip { background: rgba(255,255,255,.04); color: var(--text-secondary); }
.time-group { display: flex; flex-direction: column; gap: 5px; }
.time-chip { background: rgba(255,255,255,.04); color: var(--text-secondary); }
.time-chip.primary { background: rgba(88,166,255,.12); color: #8cc2ff; }
.hero-area { display: flex; align-items: center; gap: 10px; }
.champion-icon { width: 52px; height: 52px; border-radius: 12px; object-fit: cover; box-shadow: 0 8px 20px rgba(0,0,0,.2); }
.champion-icon.placeholder { display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,.04); color: var(--text-secondary); font-weight: 700; }
.hero-meta { min-width: 0; display: grid; gap: 4px; }
.hero-name-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.hero-name { font-weight: 800; color: var(--text-primary); }
.score-tag { font-size: 16px; font-weight: 900; }
.hero-level,.kda,.placeholder-text,.team-title,.toggle-indicator { color: var(--text-secondary); font-size: 11px; }
.kda { color: var(--text-primary); }
.icon-area { display:flex; flex-direction:column; gap:6px; }
.icon-group { display:flex; gap:5px; align-items:center; min-height: 22px; flex-wrap: wrap; }
.tiny-icon { width: 22px; height: 22px; border-radius: 6px; border: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.04); }
.share-area { display:grid; gap:6px; grid-template-columns: 1fr 1fr; font-size:12px; }
.share-item { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:5px 6px; border-radius: 8px; background: rgba(255,255,255,.04); }
.share-item span { color: var(--text-secondary); }
.share-item b { color: var(--text-primary); }
.teams-area { display:grid; grid-template-columns: 1fr 1fr; gap:8px; }
.team-col { display:grid; gap:4px; }
.team-player { display:flex; align-items:center; gap:6px; min-width:0; font-size: 12px; color: var(--text-secondary); }
.team-player span { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.team-player.me { color: var(--text-primary); font-weight: 800; }
.team-icon { width: 18px; height: 18px; border-radius: 4px; flex-shrink: 0; }
.me-badge { padding: 1px 6px; border-radius: 999px; background: rgba(78,204,163,.12); color: #4ecca3; font-style: normal; font-size: 10px; font-weight: 800; }
.tail-area { display:flex; align-items:center; justify-content:flex-end; }
.toggle-indicator { font-weight:700; color: var(--text-primary); }
.battle-match-card.expanded .toggle-indicator { color: #58a6ff; }
.expanded-wrap { padding: 0 10px 10px; border-top: 1px solid rgba(255,255,255,.06); background: linear-gradient(180deg, rgba(5,9,18,.18), rgba(5,9,18,.28)); }
.detail-loading,.detail-error { display:flex; align-items:center; justify-content:space-between; gap:12px; padding: 12px 2px 4px; color: var(--text-secondary); }
.retry-btn { height: 32px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--border-color); background: rgba(255,255,255,.04); color: var(--text-primary); cursor: pointer; }
.detail-expand-enter-active,.detail-expand-leave-active { transition: all .2s ease; }
.detail-expand-enter-from,.detail-expand-leave-to { opacity: 0; transform: translateY(-4px); }
.numeric { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
@media (max-width: 1720px) { .card-main { grid-template-columns: 144px 220px 154px minmax(220px, 1fr); } .tail-area,.share-area { display:none; } }
@media (max-width: 1380px) { .card-main { grid-template-columns: 1fr 1fr; } .teams-area { grid-column: 1 / -1; } }
@media (max-width: 980px) { .card-main { grid-template-columns: 1fr; } }
</style>
