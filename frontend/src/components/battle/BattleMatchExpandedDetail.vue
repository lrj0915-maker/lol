<template>
  <div class="battle-expanded-detail">
    <div class="metric-row">
      <div class="metric-item"><span>KDA</span><strong>{{ metrics.kda || 0 }}</strong></div>
      <div class="metric-item"><span>参团率</span><strong>{{ percent(metrics.kill_participation) }}</strong></div>
      <div class="metric-item"><span>伤害占比</span><strong>{{ percent(metrics.damage_share) }}</strong></div>
      <div class="metric-item"><span>承伤占比</span><strong>{{ percent(metrics.tank_share) }}</strong></div>
      <div class="metric-item"><span>经济占比</span><strong>{{ percent(metrics.gold_share) }}</strong></div>
      <div class="metric-item"><span>补刀效率</span><strong>{{ metrics.cs_per_min || 0 }}</strong></div>
    </div>

    <OverviewBar :match="detail" />

    <div class="detail-tabs-wrap">
      <DetailTabs :match="detail" :team="detail.my_team || []" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import OverviewBar from '@/components/match/OverviewBar.vue'
import DetailTabs from '@/components/match/DetailTabs.vue'
const props = defineProps({ detail: { type: Object, default: () => ({}) } })
const metrics = computed(() => props.detail?.overview_metrics || {})
function percent(value) {
  const number = Number(value ?? 0)
  return `${Number.isFinite(number) ? number : 0}%`
}
</script>

<style scoped>
.battle-expanded-detail { display:flex; flex-direction:column; gap:8px; padding-top: 10px; }
.metric-row { display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap:8px; }
.metric-item { display:grid; gap:3px; padding: 8px 10px; border-radius: 10px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04); }
.metric-item span { font-size: 10px; color: var(--text-secondary); }
.metric-item strong { font-size: 13px; color: var(--text-primary); }
.detail-tabs-wrap { min-height: 250px; }
@media (max-width: 1280px) { .metric-row { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
</style>
