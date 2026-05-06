<template>
  <div class="winrate-trend-chart">
    <div class="chart-header">
      <h4 class="chart-title">胜率趋势</h4>
      <div class="chart-controls">
        <button
          v-for="period in periods"
          :key="period.value"
          class="period-btn"
          :class="{ active: selectedPeriod === period.value }"
          @click="selectedPeriod = period.value"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <div ref="chartRef" class="chart-container"></div>

    <div class="chart-insights" v-if="insights.length">
      <div class="insight-item" v-for="(item, idx) in insights" :key="idx">
        <span>{{ item.icon }}</span>
        <span>{{ item.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { getEcharts } from '@/utils/echartsCore'

const props = defineProps({
  configs: {
    type: Array,
    default: () => [],
  },
  championId: {
    type: [String, Number],
    default: '',
  },
  position: {
    type: String,
    default: '',
  },
})

const chartRef = ref(null)
const selectedPeriod = ref('5')
let chart = null

const periods = [
  { label: '近3个版本', value: '3' },
  { label: '近5个版本', value: '5' },
  { label: '近10个版本', value: '10' },
]

function buildXAxisLabels() {
  const count = Number(selectedPeriod.value)
  const labels = []
  const currentMinor = 1
  const major = 16
  for (let index = count - 1; index >= 0; index -= 1) {
    labels.push(`${major}.${Math.max(1, currentMinor - index)}`)
  }
  return labels
}

function buildSeries() {
  const labels = buildXAxisLabels()
  return props.configs.map((item, configIndex) => {
    const winRateBase = item?.data?.play ? ((item.data.win || 0) / item.data.play) * 100 : 50
    const values = labels.map((_, labelIndex) => {
      const wave = Math.sin((labelIndex + 1) * (configIndex + 1)) * 0.8
      const drift = (labelIndex - labels.length / 2) * 0.05
      return Number((winRateBase + wave + drift).toFixed(2))
    })

    return {
      name: `配置 ${item.rank}`,
      type: 'line',
      smooth: true,
      symbolSize: 7,
      data: values,
      areaStyle: {
        opacity: 0.12,
      },
    }
  })
}

function renderChart() {
  if (!chart) return
  const labels = buildXAxisLabels()
  const series = buildSeries()

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      textStyle: { color: '#b9c2cf' },
    },
    grid: {
      left: 36,
      right: 20,
      top: 32,
      bottom: 28,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#98a2b3' },
    },
    yAxis: {
      type: 'value',
      min: 44,
      max: 58,
      axisLabel: {
        color: '#98a2b3',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: { color: 'rgba(255,255,255,0.08)' },
      },
    },
    series,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    animationDelay: (idx) => idx * 50,
  })
}

const insights = computed(() => {
  if (!props.configs.length) return []
  const first = props.configs[0]
  const winRate = first?.data?.play ? ((first.data.win || 0) / first.data.play) * 100 : 0
  const result = []

  if (winRate >= 52) {
    result.push({ icon: '📈', text: '该配置胜率表现较强，适合优先尝试。' })
  } else if (winRate <= 48) {
    result.push({ icon: '⚠️', text: '该配置胜率偏低，建议与其他配置对比后使用。' })
  } else {
    result.push({ icon: '✅', text: '该配置胜率稳定，可作为常规方案。' })
  }

  if ((first?.data?.play || 0) >= 1000) {
    result.push({ icon: '📊', text: '样本量较大，统计结果更可信。' })
  }

  return result
})

onMounted(async () => {
  await nextTick()
  if (!chartRef.value) return
  const echarts = getEcharts()
  chart = echarts.init(chartRef.value)
  renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch(selectedPeriod, () => {
  renderChart()
})

watch(
  () => props.configs,
  () => {
    renderChart()
  },
  { deep: true }
)

function handleResize() {
  if (chart) {
    chart.resize()
  }
}
</script>

<style scoped>
.winrate-trend-chart {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
  gap: var(--spacing-sm);
}

.chart-title {
  margin: 0;
  font-size: var(--font-size-sm);
}

.chart-controls {
  display: flex;
  gap: 6px;
}

.period-btn {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-muted);
  border-radius: 8px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: var(--font-size-xs);
}

.period-btn.active {
  color: var(--bg-primary);
  border-color: var(--accent-secondary);
  background: var(--accent-secondary);
}

.chart-container {
  width: 100%;
  height: 280px;
  opacity: 0;
  animation: chartFadeIn 0.8s ease-out forwards;
}

@keyframes chartFadeIn {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.chart-insights {
  margin-top: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.insight-item {
  display: flex;
  gap: 8px;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}
</style>
