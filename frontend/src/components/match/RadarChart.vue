<template>
  <div class="radar-container">
    <div class="chart-header">
      <div class="mode-toggle">
        <button :class="{ active: !isMerged }" @click="isMerged = false">单人</button>
        <button :class="{ active: isMerged }" @click="isMerged = true">合并</button>
      </div>
      
      <div class="merge-legend" v-if="isMerged">
        <div 
          v-for="(player, idx) in sortedPlayers" 
          :key="idx"
          class="legend-item"
          :class="{ active: isActive(player) }"
          @click="selectPlayer(player)"
        >
          <span class="legend-dot" :style="{ background: colors[idx] }"></span>
          <span class="legend-name">{{ getDisplayName(player, idx) }}</span>
        </div>
      </div>
    </div>

    <div class="main-chart" ref="mainChartRef"></div>

    <div class="player-selector">
      <div 
        v-for="(player, idx) in sortedPlayers" 
        :key="idx"
        class="player-item"
        :class="{ active: isActive(player), me: player.is_me }"
        @click="selectPlayer(player)"
      >
        <div class="mini-chart" :ref="el => miniChartRefs[idx] = el"></div>
        <div class="player-name">
          <span class="color-dot" :style="{ background: colors[idx] }"></span>
          <span>{{ getDisplayName(player, idx) }}</span>
          <span v-if="player.is_me" class="star">★</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getEcharts } from '@/utils/echartsCore'

const props = defineProps({ radarData: Array, activePlayer: String })
const emit = defineEmits(['select'])

const isMerged = ref(false)
const mainChartRef = ref(null)
const miniChartRefs = ref([])
let mainChart = null
let miniCharts = []

const colors = ['#ffd700', '#00d4ff', '#39ff14', '#ff00ff', '#ff4500']
const dimensionNames = { output: '输出', survival: '生存', development: '发育', teamfight: '团战', vision: '视野', objective: '参战' }

const sortedPlayers = computed(() => {
  if (!props.radarData?.length) return []
  return [...props.radarData].sort((a, b) => (a.is_me ? -1 : b.is_me ? 1 : 0))
})

const activeIdx = computed(() => sortedPlayers.value.findIndex(p => (p.summoner_name || p.champion_name) === props.activePlayer))

function getDisplayName(player, idx) { return player.champion_name || player.summoner_name || '玩家' + (idx + 1) }
function isActive(player) { return (player.summoner_name || player.champion_name) === props.activePlayer }
function selectPlayer(player) { emit('select', player.summoner_name || player.champion_name) }

function updateMainChart() {
  if (!mainChart || !sortedPlayers.value?.length) return
  const indicator = Object.keys(dimensionNames).map(key => ({ name: dimensionNames[key], max: 100 }))
  let seriesData = []

  if (isMerged.value) {
    seriesData = sortedPlayers.value.map((player, idx) => {
      const isActiveP = activeIdx.value === idx
      return {
        value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
        name: getDisplayName(player, idx),
        lineStyle: { width: isActiveP ? 3 : 1.5, opacity: isActiveP ? 1 : 0.5 },
        areaStyle: { opacity: isActiveP ? 0.25 : 0.05, color: colors[idx] },
        itemStyle: { color: colors[idx] },
        symbol: isActiveP ? 'circle' : 'none',
        symbolSize: isActiveP ? 6 : 0
      }
    })
  } else {
    const idx = activeIdx.value >= 0 ? activeIdx.value : 0
    const player = sortedPlayers.value[idx]
    if (player) {
      seriesData = [{
        value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
        lineStyle: { width: 3, color: colors[idx] },
        areaStyle: { opacity: 0.35, color: colors[idx] },
        itemStyle: { color: colors[idx] },
        symbol: 'circle',
        symbolSize: 6
      }]
    }
  }

  mainChart.setOption({
    radar: {
      center: ['50%', '50%'], radius: '72%', indicator, shape: 'polygon', splitNumber: 4,
      axisName: { color: '#fff', fontSize: 12 },
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
      center: ['50%', '50%'], radius: '70%',
      indicator: Object.keys(dimensionNames).map(() => ({ name: '', max: 100 })),
      shape: 'polygon', splitNumber: 2, axisName: { show: false },
      splitLine: { lineStyle: { color: 'rgba(60,80,110,0.2)' } },
      splitArea: { areaStyle: { color: ['rgba(15,20,30,0.8)', 'rgba(20,28,40,0.6)'] } },
      axisLine: { lineStyle: { color: 'rgba(60,80,110,0.2)' } }
    },
    series: [{ type: 'radar', data: [{
      value: Object.keys(dimensionNames).map(key => player.dimensions?.[key] || 0),
      lineStyle: { width: 2, color: colors[idx] },
      areaStyle: { opacity: 0.5, color: colors[idx] },
      symbol: 'none'
    }] }]
  }, true)
}

function initCharts() {
  const echarts = getEcharts()
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

watch([() => props.radarData, () => props.activePlayer, isMerged], () => {
  nextTick(() => {
    updateMainChart()
    const echarts = getEcharts()
    sortedPlayers.value.forEach((_, idx) => {
      if (!miniCharts[idx] && miniChartRefs.value[idx]) {
        miniCharts[idx] = echarts.init(miniChartRefs.value[idx])
      }
      updateMiniChart(idx)
    })
  })
}, { deep: true })

onMounted(() => { window.addEventListener('resize', handleResize); nextTick(() => initCharts()) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); mainChart?.dispose(); miniCharts.forEach(c => c?.dispose()) })
</script>

<style scoped>
.radar-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 10px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.mode-toggle {
  display: flex;
  gap: 4px;
  background: var(--bg-primary);
  padding: 3px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.mode-toggle button {
  padding: 5px 14px;
  font-size: 12px;
  background: transparent;
  color: var(--text-muted);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-normal);
}
.mode-toggle button:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.mode-toggle button.active {
  background: var(--gradient-primary);
  color: var(--bg-primary);
  box-shadow: 0 0 10px rgba(78, 204, 163, 0.25);
}

.merge-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 3px 8px;
  border-radius: 4px;
  transition: all var(--transition-normal);
}

.legend-item:hover { background: var(--bg-hover); }
.legend-item.active {
  background: rgba(78, 204, 163, 0.15);
  box-shadow: 0 0 8px rgba(78, 204, 163, 0.15);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-name {
  font-size: 11px;
  color: var(--text-secondary);
}

.main-chart {
  flex: 1;
  min-height: 200px;
  opacity: 0;
  animation: radarFadeIn 0.8s ease-out 0.2s forwards;
}

@keyframes radarFadeIn {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.player-selector {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-top: 8px;
  border: 1px solid var(--border-color);
}

.player-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px;
  background: var(--bg-card);
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition-normal);
  opacity: 0;
  animation: playerItemFadeIn 0.5s ease-out forwards;
}

.player-item:nth-child(1) { animation-delay: 0.1s; }
.player-item:nth-child(2) { animation-delay: 0.2s; }
.player-item:nth-child(3) { animation-delay: 0.3s; }
.player-item:nth-child(4) { animation-delay: 0.4s; }
.player-item:nth-child(5) { animation-delay: 0.5s; }

@keyframes playerItemFadeIn {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.player-item:hover {
  background: var(--bg-card-hover);
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.05);
  transform: translateY(-2px) scale(1.05);
}

.player-item.active {
  border-color: var(--accent-secondary);
  box-shadow: 0 0 12px rgba(78, 204, 163, 0.2);
  transform: translateY(-2px) scale(1.05);
}

.player-item.me { border-left: 3px solid var(--radar-me); }

.mini-chart {
  width: 50px;
  height: 50px;
}

.player-name {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 10px;
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.player-item.active .player-name { color: var(--text-primary); font-weight: 600; }

.color-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.star {
  color: var(--radar-me);
  font-size: 10px;
}
</style>
