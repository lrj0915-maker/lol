<template>
  <div class="radar-container">
    <!-- 模式切换 -->
    <div class="mode-toggle">
      <button class="toggle-btn" :class="{ active: !isMerged }" @click="isMerged = false">单人</button>
      <button class="toggle-btn" :class="{ active: isMerged }" @click="isMerged = true">合并</button>
    </div>

    <!-- 大六芒星区域 -->
    <div class="main-chart-area">
      <div class="main-chart" ref="mainChartRef"></div>
      
      <!-- 合并模式的图例 -->
      <div class="merge-legend" v-if="isMerged">
        <div 
          v-for="(player, idx) in sortedPlayers" 
          :key="idx"
          class="legend-item"
          :class="{ active: isActive(player), me: player.is_me }"
          @click="selectPlayer(player)"
          @mouseenter="hoverIdx = idx"
          @mouseleave="hoverIdx = -1"
        >
          <span class="legend-dot" :style="{ background: colors[idx] }"></span>
          <span class="legend-name">{{ getDisplayName(player, idx) }}</span>
          <span v-if="player.is_me" class="legend-star">★</span>
        </div>
      </div>
    </div>

    <!-- 底部迷你六芒星选择器 -->
    <div class="mini-selector">
      <div 
        v-for="(player, idx) in sortedPlayers" 
        :key="idx"
        class="mini-card"
        :class="{ active: isActive(player), me: player.is_me }"
        @click="selectPlayer(player)"
      >
        <div class="mini-chart" :ref="el => miniChartRefs[idx] = el"></div>
        <div class="mini-label">
          <span class="mini-color" :style="{ background: colors[idx] }"></span>
          <span class="mini-name">{{ getDisplayName(player, idx) }}</span>
          <span v-if="player.is_me" class="mini-star">★</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  radarData: Array,
  activePlayer: String
})

const emit = defineEmits(['select'])

const isMerged = ref(false)
const hoverIdx = ref(-1)
const mainChartRef = ref(null)
const miniChartRefs = ref([])

let mainChart = null
let miniCharts = []

const colors = ['#ffd700', '#00d4ff', '#39ff14', '#ff00ff', '#ff4500']

const dimensionNames = {
  output: '输出',
  survival: '生存', 
  development: '发育',
  teamfight: '团战',
  vision: '视野',
  objective: '参战'
}

const sortedPlayers = computed(() => {
  if (!props.radarData?.length) return []
  return [...props.radarData].sort((a, b) => (a.is_me ? -1 : b.is_me ? 1 : 0))
})

const activeIdx = computed(() => {
  return sortedPlayers.value.findIndex(p => 
    (p.summoner_name || p.champion_name) === props.activePlayer
  )
})

function getDisplayName(player, idx) {
  return player.champion_name || player.summoner_name || '玩家' + (idx + 1)
}

function isActive(player) {
  return (player.summoner_name || player.champion_name) === props.activePlayer
}

function selectPlayer(player) {
  emit('select', player.summoner_name || player.champion_name)
}

function updateMainChart() {
  if (!mainChart || !sortedPlayers.value?.length) return

  const indicator = Object.keys(dimensionNames).map(key => ({
    name: dimensionNames[key], max: 100
  }))

  let seriesData = []

  if (isMerged.value) {
    // 合并模式：显示所有玩家
    seriesData = sortedPlayers.value.map((player, idx) => {
      const isHover = hoverIdx.value === idx
      const isActiveP = activeIdx.value === idx
      const highlight = isHover || isActiveP

      return {
        value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
        name: getDisplayName(player, idx),
        lineStyle: {
          width: highlight ? 3.5 : 1.5,
          opacity: highlight ? 1 : 0.5,
          shadowColor: highlight ? colors[idx] : 'transparent',
          shadowBlur: highlight ? 10 : 0
        },
        areaStyle: { opacity: highlight ? 0.2 : 0, color: colors[idx] },
        itemStyle: { color: colors[idx] },
        symbol: highlight ? 'circle' : 'none',
        symbolSize: highlight ? 6 : 0
      }
    })
  } else {
    // 单人模式：只显示选中的玩家
    const idx = activeIdx.value >= 0 ? activeIdx.value : 0
    const player = sortedPlayers.value[idx]
    if (player) {
      seriesData = [{
        value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
        name: getDisplayName(player, idx),
        lineStyle: { width: 3, color: colors[idx], shadowColor: colors[idx], shadowBlur: 8 },
        areaStyle: { opacity: 0.35, color: colors[idx] },
        itemStyle: { color: colors[idx], borderWidth: 2, borderColor: '#fff' },
        symbol: 'circle',
        symbolSize: 8
      }]
    }
  }

  mainChart.setOption({
    color: colors,
    radar: {
      center: ['50%', '50%'],
      radius: '72%',
      indicator,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#fff', fontSize: 14, fontWeight: 600 },
      splitLine: { lineStyle: { color: 'rgba(60,80,110,0.4)' } },
      splitArea: { areaStyle: { color: ['rgba(12,16,24,0.95)', 'rgba(18,24,35,0.85)'] } },
      axisLine: { lineStyle: { color: 'rgba(60,80,110,0.4)' } }
    },
    series: [{ type: 'radar', data: seriesData }]
  }, true)
}

function updateMiniChart(idx) {
  const chart = miniCharts[idx]
  const player = sortedPlayers.value[idx]
  if (!chart || !player) return

  chart.setOption({
    radar: {
      center: ['50%', '50%'],
      radius: '75%',
      indicator: Object.keys(dimensionNames).map(() => ({ name: '', max: 100 })),
      shape: 'polygon',
      splitNumber: 2,
      axisName: { show: false },
      splitLine: { lineStyle: { color: 'rgba(60,80,110,0.25)' } },
      splitArea: { areaStyle: { color: ['rgba(15,20,30,0.8)', 'rgba(20,28,40,0.6)'] } },
      axisLine: { lineStyle: { color: 'rgba(60,80,110,0.25)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
        lineStyle: { width: 2, color: colors[idx] },
        areaStyle: { opacity: 0.5, color: colors[idx] },
        symbol: 'none'
      }]
    }]
  }, true)
}

function initCharts() {
  if (mainChartRef.value) {
    mainChart = echarts.init(mainChartRef.value)
    updateMainChart()
  }
  nextTick(() => {
    miniChartRefs.value.forEach((el, idx) => {
      if (el && !miniCharts[idx]) {
        miniCharts[idx] = echarts.init(el)
        updateMiniChart(idx)
      }
    })
  })
}

function handleResize() {
  mainChart?.resize()
  miniCharts.forEach(c => c?.resize())
}

watch([() => props.radarData, () => props.activePlayer, isMerged, hoverIdx], () => {
  nextTick(() => {
    updateMainChart()
    sortedPlayers.value.forEach((_, idx) => {
      if (!miniCharts[idx] && miniChartRefs.value[idx]) {
        miniCharts[idx] = echarts.init(miniChartRefs.value[idx])
      }
      updateMiniChart(idx)
    })
  })
}, { deep: true })

onMounted(() => {
  window.addEventListener('resize', handleResize)
  nextTick(initCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  mainChart?.dispose()
  miniCharts.forEach(c => c?.dispose())
})
</script>

<style scoped>
.radar-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--spacing-md);
  gap: var(--spacing-sm);
}

.mode-toggle {
  display: flex;
  gap: var(--spacing-xs);
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--border-radius);
  width: fit-content;
}

.toggle-btn {
  padding: 6px 16px;
  font-size: var(--font-size-xs);
  background: transparent;
  color: var(--text-muted);
  border: none;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.toggle-btn:hover {
  color: var(--text-secondary);
}

.toggle-btn.active {
  background: var(--gradient-primary);
  color: var(--bg-primary);
  box-shadow: var(--shadow-sm);
}

.main-chart-area {
  flex: 1;
  position: relative;
  min-height: 200px;
  max-height: 260px;
}

.main-chart {
  width: 100%;
  height: 100%;
}

.merge-legend {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: rgba(13, 17, 23, 0.95);
  backdrop-filter: blur(8px);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 4px 8px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.legend-item:hover {
  background: var(--bg-hover);
}

.legend-item.active {
  background: rgba(78, 204, 163, 0.15);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 6px currentColor;
}

.legend-name {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.legend-item.active .legend-name {
  color: var(--text-primary);
  font-weight: 600;
}

.legend-star {
  color: var(--radar-me);
  font-size: 10px;
  text-shadow: 0 0 8px var(--radar-me);
}

.mini-selector {
  display: flex;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  flex-shrink: 0;
}

.mini-card {
  width: 68px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xs);
  background: var(--bg-card);
  border-radius: var(--border-radius);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.mini-card:hover {
  background: var(--bg-card-hover);
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.mini-card.active {
  border-color: var(--accent-secondary);
  background: var(--bg-elevated);
  box-shadow: var(--glow-primary);
}

.mini-card.me {
  border-left: 3px solid var(--radar-me);
}

.mini-chart {
  width: 48px;
  height: 48px;
}

.mini-label {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: 4px;
}

.mini-color {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.mini-name {
  font-size: 10px;
  color: var(--text-muted);
  max-width: 44px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-card.active .mini-name {
  color: var(--text-primary);
  font-weight: 600;
}

.mini-star {
  color: var(--radar-me);
  font-size: 10px;
  text-shadow: 0 0 6px var(--radar-me);
}
</style>
