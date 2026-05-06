<template>
  <section class="battle-panel battle-panel-summary">
    <div class="panel-head">
      <div>
        <div class="panel-title">总览</div>
        <div class="panel-subtitle">最近对局的核心表现指标</div>
      </div>
      <div class="record-pill numeric">{{ summary.wins || 0 }} 胜 {{ summary.losses || 0 }} 负</div>
    </div>

    <div class="summary-focus">
      <div class="focus-item">
        <span>总场次</span>
        <strong class="numeric">{{ summary.total_games ?? 0 }}</strong>
      </div>
      <div class="focus-item primary">
        <span>胜率</span>
        <strong class="numeric">{{ percent(summary.win_rate) }}</strong>
      </div>
      <div class="focus-item">
        <span>平均 KDA</span>
        <strong class="numeric">{{ decimal(summary.avg_kda) }}</strong>
      </div>
    </div>

    <div class="summary-grid">
      <div v-for="item in items" :key="item.label" class="summary-item">
        <div class="summary-label">{{ item.label }}</div>
        <div class="summary-value numeric">{{ item.value }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ summary: { type: Object, default: () => ({}) } })
const items = computed(() => [
  { label: '参团率', value: percent(props.summary?.avg_kill_participation) },
  { label: '伤害占比', value: percent(props.summary?.avg_damage_share) },
  { label: '承伤占比', value: percent(props.summary?.avg_tank_share) },
  { label: '经济占比', value: percent(props.summary?.avg_gold_share) },
  { label: '补刀效率', value: decimal(props.summary?.avg_cs_per_min) },
])
function percent(value) {
  const number = Number(value ?? 0)
  return `${Number.isFinite(number) ? number : 0}%`
}
function decimal(value) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? number.toFixed(2).replace(/\.00$/, '') : '0'
}
</script>

<style scoped>
.battle-panel { position: relative; padding: 14px; border-radius: 16px; background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.02)); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 12px 28px rgba(0,0,0,.18); overflow: hidden; }
.battle-panel::before { content: ''; position: absolute; inset: 0 0 auto 0; height: 2px; background: linear-gradient(90deg, rgba(78,204,163,.75), rgba(88,166,255,.55)); opacity: .9; }
.battle-panel::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at top right, rgba(88,166,255,.08), transparent 34%); pointer-events: none; }
.panel-head,.summary-focus,.summary-grid { position: relative; z-index: 1; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.panel-title { font-size: 16px; font-weight: 800; color: var(--text-primary); }
.panel-subtitle { margin-top: 2px; font-size: 11px; color: var(--text-secondary); }
.record-pill { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 999px; background: rgba(78,204,163,.08); color: var(--text-primary); font-size: 12px; border: 1px solid rgba(78,204,163,.18); }
.summary-focus { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-bottom: 10px; }
.focus-item { min-height: 68px; padding: 10px; border-radius: 12px; background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02)); border: 1px solid rgba(255,255,255,.05); display: grid; align-content: center; }
.focus-item.primary { background: linear-gradient(180deg, rgba(78,204,163,.12), rgba(88,166,255,.06)); }
.focus-item span { display: block; margin-bottom: 4px; color: var(--text-secondary); font-size: 11px; }
.focus-item strong { font-size: 18px; color: var(--text-primary); }
.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.summary-item { min-height: 58px; padding: 10px; border-radius: 12px; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.04); display: grid; align-content: center; }
.summary-label { color: var(--text-secondary); font-size: 11px; }
.summary-value { margin-top: 4px; font-size: 16px; font-weight: 700; color: var(--text-primary); }
.numeric { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
</style>
