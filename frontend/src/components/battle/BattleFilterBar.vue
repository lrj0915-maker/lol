<template>
  <div class="battle-filter-bar">
    <div class="filter-group">
      <span class="filter-label">模式</span>
      <select :value="filters.game_mode" @change="$emit('change', { game_mode: $event.target.value })">
        <option value="">全部模式</option>
        <option v-for="mode in modes" :key="mode" :value="mode">{{ mode }}</option>
      </select>
    </div>

    <div class="filter-group">
      <span class="filter-label">结果</span>
      <select :value="filters.result" @change="$emit('change', { result: $event.target.value })">
        <option value="">全部结果</option>
        <option value="win">胜利</option>
        <option value="lose">失败</option>
      </select>
    </div>

    <div class="filter-group">
      <span class="filter-label">时间</span>
      <select :value="filters.time_range" @change="$emit('change', { time_range: $event.target.value })">
        <option value="">全部时间</option>
        <option value="7d">近 7 天</option>
        <option value="15d">近 15 天</option>
        <option value="30d">近 30 天</option>
      </select>
    </div>

    <div class="active-tips">
      <span v-if="filters.game_mode" class="tip">模式：{{ filters.game_mode }}</span>
      <span v-if="filters.result" class="tip">结果：{{ filters.result === 'win' ? '胜利' : '失败' }}</span>
      <span v-if="filters.time_range" class="tip">时间：{{ filters.time_range }}</span>
      <span v-if="filters.champion_id" class="tip">已按英雄筛选</span>
      <span v-if="filters.teammate" class="tip">队友：{{ filters.teammate }}</span>
      <span v-if="!hasActiveFilter" class="tip muted">当前显示全部对局</span>
    </div>

    <button class="clear-btn" @click="$emit('reset')">重置筛选</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
  modes: { type: Array, default: () => [] },
})

defineEmits(['change', 'reset'])

const hasActiveFilter = computed(() => {
  return !!(
    props.filters?.game_mode ||
    props.filters?.result ||
    props.filters?.time_range ||
    props.filters?.champion_id ||
    props.filters?.teammate
  )
})
</script>

<style scoped>
.battle-filter-bar { display: flex; align-items: flex-end; gap: 10px; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 5px; min-width: 114px; }
.filter-label { color: var(--text-secondary); font-size: 11px; }
select,.clear-btn { height: 36px; padding: 0 11px; border-radius: 10px; border: 1px solid var(--border-color); background: rgba(255, 255, 255, 0.04); color: var(--text-primary); }
.active-tips { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; min-height: 36px; font-size: 12px; color: var(--text-secondary); }
.tip { padding: 4px 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.06); }
.tip.muted { background: transparent; border-style: dashed; }
.clear-btn { cursor: pointer; }
</style>
