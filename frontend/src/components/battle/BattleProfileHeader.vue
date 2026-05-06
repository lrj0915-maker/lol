<template>
  <section class="battle-profile-header">
    <div class="profile-main">
      <div class="avatar-wrap">
        <div class="avatar-glow"></div>
        <img v-if="iconUrl" :src="iconUrl" class="avatar" alt="avatar" />
        <div v-else class="avatar placeholder">无</div>
      </div>

      <div class="identity">
        <div class="name-line">
          <span class="display-name">{{ displayName }}</span>
          <span class="status-pill" :class="profile?.is_online ? 'online' : 'offline'">
            {{ profile?.is_online ? '在线' : '离线缓存' }}
          </span>
        </div>
        <div class="sub-line">{{ fullTagName }}</div>
        <div class="meta-row">
          <span class="meta-chip">最近刷新 {{ lastUpdatedText }}</span>
          <span class="meta-chip">{{ profile?.is_online ? '数据来自在线同步' : '数据来自本地缓存' }}</span>
        </div>
      </div>
    </div>

    <div class="rank-grid">
      <div class="rank-card">
        <div class="rank-title">单双排位</div>
        <div class="rank-main">{{ formatRank(rankedSolo) }}</div>
        <div class="rank-sub">{{ formatRankRecord(rankedSolo) }}</div>
        <div class="rank-meta">{{ formatRankHint(rankedSolo) }}</div>
      </div>
      <div class="rank-card">
        <div class="rank-title">灵活排位</div>
        <div class="rank-main">{{ formatRank(rankedFlex) }}</div>
        <div class="rank-sub">{{ formatRankRecord(rankedFlex) }}</div>
        <div class="rank-meta">{{ formatRankHint(rankedFlex) }}</div>
      </div>
    </div>

    <div class="actions">
      <button class="action-btn primary" :disabled="refreshing" @click="$emit('refresh')">
        {{ refreshing ? '刷新中...' : '刷新' }}
      </button>
      <div class="action-hint">离线优先展示</div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { DDRAGON_BASE } from '@/utils/ddragon'

const props = defineProps({
  profile: { type: Object, default: () => ({}) },
  rankedSolo: { type: Object, default: () => ({}) },
  rankedFlex: { type: Object, default: () => ({}) },
  refreshing: { type: Boolean, default: false },
})

defineEmits(['refresh'])

const iconUrl = computed(() => {
  const iconId = props.profile?.icon_id
  if (iconId === null || iconId === undefined || iconId === '') {
    return ''
  }
  return `${DDRAGON_BASE}/img/profileicon/${iconId}.png`
})

const displayName = computed(() => props.profile?.display_name || props.profile?.game_name || '未连接账号')

const fullTagName = computed(() => {
  const gameName = props.profile?.game_name || props.profile?.display_name || '--'
  const tagLine = props.profile?.tag_line || '--'
  return `${gameName}#${tagLine}`
})

const lastUpdatedText = computed(() => {
  const timestamp = Number(props.profile?.last_updated_at || 0)
  if (!timestamp) {
    return '暂无记录'
  }
  const date = new Date(timestamp * 1000)
  return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
})

function formatRank(rank) {
  if (!rank || rank.is_placement || !rank.tier) {
    return '未定级'
  }
  const division = rank.division || ''
  const lp = typeof rank.lp === 'number' ? `${rank.lp} LP` : ''
  return [rank.tier, division, lp].filter(Boolean).join(' ')
}

function formatRankRecord(rank) {
  if (!rank || rank.is_placement || (!rank.wins && !rank.losses)) {
    return '暂无线下对局记录'
  }
  return `${rank.wins || 0} 胜 ${rank.losses || 0} 负`
}

function formatRankHint(rank) {
  if (!rank || rank.is_placement || !rank.tier) {
    return '等待排位数据同步'
  }
  const total = Number(rank.wins || 0) + Number(rank.losses || 0)
  const winRate = total ? Math.round((Number(rank.wins || 0) / total) * 100) : 0
  return `胜率 ${winRate}%`
}
</script>

<style scoped>
.battle-profile-header {
  display: grid;
  grid-template-columns: minmax(300px, 1.3fr) minmax(280px, 1fr) auto;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.02));
  border: 1px solid var(--border-color);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(12px);
}
.profile-main { display: flex; align-items: center; gap: 14px; min-width: 0; }
.avatar-wrap { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.avatar-glow { position: absolute; inset: -8px; border-radius: 22px; background: radial-gradient(circle, rgba(88, 166, 255, 0.18), transparent 70%); }
.avatar { position: relative; width: 100%; height: 100%; object-fit: cover; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28); }
.avatar.placeholder { display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); font-size: 24px; font-weight: 700; }
.identity { min-width: 0; display: flex; flex-direction: column; gap: 5px; }
.name-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.display-name { font-size: 26px; line-height: 1.05; font-weight: 800; color: var(--text-primary); }
.sub-line { color: var(--text-secondary); font-size: 13px; }
.meta-row { display: flex; gap: 8px; flex-wrap: wrap; }
.meta-chip { padding: 4px 9px; border-radius: 999px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.06); color: var(--text-secondary); font-size: 12px; }
.status-pill { padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.status-pill.online { background: rgba(78, 204, 163, 0.12); color: #4ecca3; }
.status-pill.offline { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }
.rank-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.rank-card { display: flex; flex-direction: column; gap: 6px; padding: 12px; border-radius: 14px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); }
.rank-title { font-size: 12px; color: var(--text-secondary); }
.rank-main { font-size: 17px; font-weight: 800; color: var(--text-primary); }
.rank-sub { font-size: 12px; color: var(--text-primary); }
.rank-meta { font-size: 12px; color: var(--text-secondary); }
.actions { display: flex; flex-direction: column; align-items: flex-end; justify-content: space-between; gap: 8px; }
.action-btn { min-width: 78px; height: 38px; padding: 0 14px; border-radius: 11px; border: 1px solid var(--border-color); background: rgba(255, 255, 255, 0.04); color: var(--text-primary); cursor: pointer; }
.action-btn.primary { background: rgba(78, 204, 163, 0.16); }
.action-btn:disabled { opacity: 0.65; cursor: not-allowed; }
.action-hint { padding: 4px 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); color: var(--text-secondary); font-size: 11px; }
@media (max-width: 1280px) { .battle-profile-header { grid-template-columns: 1fr; } .actions { align-items: flex-start; } }
</style>
