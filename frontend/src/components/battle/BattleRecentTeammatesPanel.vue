<template>
  <section class="battle-panel battle-panel-mate">
    <div class="panel-head">
      <div>
        <div class="panel-title">最近队友</div>
        <div class="panel-subtitle">按同队次数和最近时间排序</div>
      </div>
      <div class="panel-tip">最近 50 场</div>
    </div>

    <div v-if="teammates.length" class="teammate-list">
      <button
        v-for="player in teammates"
        :key="player.identity || `${player.name}-${player.tag}`"
        class="teammate-item"
        :class="{ active: activeTeammate === (player.identity || player.display_name || player.name) }"
        @click="$emit('select', player)"
      >
        <div class="teammate-main">
          <div class="teammate-name">{{ player.display_name || player.identity || player.name }}</div>
          <div class="teammate-sub-row">
            <span class="teammate-stat numeric">{{ player.games }} 场</span>
            <span class="teammate-stat numeric">{{ player.wins }} 胜</span>
            <span class="teammate-stat numeric">{{ player.losses }} 负</span>
          </div>
        </div>
        <div class="teammate-side">
          <div class="teammate-label">最近同队</div>
          <div class="teammate-extra numeric">{{ formatLastPlayed(player.last_played_at) }}</div>
        </div>
      </button>
    </div>

    <div v-else class="empty-tip empty-block">暂无最近队友统计</div>
  </section>
</template>

<script setup>
defineProps({ teammates: { type: Array, default: () => [] }, activeTeammate: { type: String, default: '' } })
defineEmits(['select'])
function formatLastPlayed(timestamp) {
  const value = Number(timestamp || 0)
  if (!value) return '暂无记录'
  const date = new Date(value * 1000)
  return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.battle-panel { position: relative; padding: 14px; border-radius: 16px; background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.02)); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 12px 28px rgba(0,0,0,.18); overflow: hidden; }
.battle-panel::before { content: ''; position: absolute; inset: 0 0 auto 0; height: 2px; background: linear-gradient(90deg, rgba(88,166,255,.82), rgba(168,85,247,.52)); opacity: .92; }
.battle-panel::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at top right, rgba(168,85,247,.08), transparent 34%); pointer-events: none; }
.panel-head,.teammate-list,.empty-block { position: relative; z-index: 1; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.panel-title { font-size: 16px; font-weight: 800; color: var(--text-primary); }
.panel-subtitle { margin-top: 2px; font-size: 11px; color: var(--text-secondary); }
.panel-tip,.empty-tip { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 999px; font-size: 12px; color: var(--text-secondary); background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.06); }
.teammate-list { display: flex; flex-direction: column; gap: 8px; }
.teammate-item { display: grid; grid-template-columns: 1fr 120px; align-items: center; gap: 10px; width: 100%; min-height: 68px; padding: 10px; border: 1px solid transparent; border-radius: 12px; background: rgba(255,255,255,.03); color: inherit; cursor: pointer; text-align: left; transition: all .18s ease; }
.teammate-item:hover { transform: translateY(-1px); border-color: rgba(255,255,255,.12); background: rgba(255,255,255,.05); }
.teammate-item.active { border-color: rgba(88,166,255,.42); background: linear-gradient(90deg, rgba(88,166,255,.14), rgba(168,85,247,.08)); box-shadow: inset 3px 0 0 rgba(88,166,255,.9), 0 10px 24px rgba(88,166,255,.08); }
.teammate-main { min-width: 0; display: grid; gap: 5px; }
.teammate-name { color: var(--text-primary); font-weight: 700; word-break: break-all; }
.teammate-sub-row { display: flex; gap: 8px; flex-wrap: wrap; }
.teammate-stat { font-size: 11px; color: var(--text-secondary); }
.teammate-side { display: grid; justify-items: end; gap: 3px; }
.teammate-label { font-size: 10px; color: var(--text-secondary); }
.teammate-extra { font-size: 11px; color: var(--text-primary); }
.numeric { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
</style>
