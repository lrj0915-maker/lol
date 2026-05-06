<template>
  <div class="trend-indicator" :class="trendClass" :title="tooltip">
    <span class="trend-icon">{{ icon }}</span>
    <span class="trend-value">{{ displayValue }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    required: true
  },
  previous: {
    type: Number,
    default: null
  },
  type: {
    type: String,
    default: 'winrate', // 'winrate' | 'games'
    validator: (value) => ['winrate', 'games'].includes(value)
  }
})

// 计算变化
const change = computed(() => {
  if (props.previous === null || props.previous === 0) return 0
  return props.current - props.previous
})

// 计算变化百分比
const changePercent = computed(() => {
  if (props.previous === null || props.previous === 0) return 0
  return ((props.current - props.previous) / props.previous) * 100
})

// 趋势类型
const trendClass = computed(() => {
  const ch = change.value
  if (Math.abs(ch) < 0.1) return 'stable'
  if (ch > 0) return 'rising'
  return 'falling'
})

// 图标
const icon = computed(() => {
  const ch = change.value
  if (Math.abs(ch) < 0.1) return '━'
  if (ch > 0) return '↗'
  return '↘'
})

// 显示值
const displayValue = computed(() => {
  const ch = change.value
  if (Math.abs(ch) < 0.1) return '持平'
  
  if (props.type === 'winrate') {
    return `${ch > 0 ? '+' : ''}${ch.toFixed(1)}%`
  } else {
    return `${ch > 0 ? '+' : ''}${Math.abs(ch).toLocaleString()}`
  }
})

// 提示文本
const tooltip = computed(() => {
  if (props.previous === null) return '暂无历史数据'
  
  const trend = trendClass.value === 'rising' ? '上升' : 
                trendClass.value === 'falling' ? '下降' : '持平'
  
  if (props.type === 'winrate') {
    return `胜率${trend}: ${props.previous.toFixed(1)}% → ${props.current.toFixed(1)}%`
  } else {
    return `场次${trend}: ${props.previous.toLocaleString()} → ${props.current.toLocaleString()}`
  }
})
</script>

<style scoped>
.trend-indicator {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  cursor: help;
  transition: all var(--transition-fast);
  border: 1px solid;
}

.trend-icon {
  font-size: 14px;
  font-weight: bold;
}

.trend-value {
  font-size: 10px;
}

/* 上升趋势 */
.rising {
  background: rgba(78, 204, 163, 0.15);
  color: #4ECCB3;
  border-color: rgba(78, 204, 163, 0.3);
}

.rising:hover {
  background: rgba(78, 204, 163, 0.25);
  box-shadow: 0 2px 8px rgba(78, 204, 163, 0.3);
  transform: translateY(-1px);
}

.rising .trend-icon {
  animation: riseAnimation 1.5s ease-in-out infinite;
}

@keyframes riseAnimation {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

/* 下降趋势 */
.falling {
  background: rgba(239, 68, 68, 0.15);
  color: #EF4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.falling:hover {
  background: rgba(239, 68, 68, 0.25);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
  transform: translateY(-1px);
}

.falling .trend-icon {
  animation: fallAnimation 1.5s ease-in-out infinite;
}

@keyframes fallAnimation {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(2px); }
}

/* 持平 */
.stable {
  background: rgba(107, 114, 128, 0.15);
  color: #6B7280;
  border-color: rgba(107, 114, 128, 0.3);
}

.stable:hover {
  background: rgba(107, 114, 128, 0.25);
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
  transform: translateY(-1px);
}

/* 响应式 */
@media (max-width: 768px) {
  .trend-indicator {
    padding: 2px 6px;
    font-size: 10px;
  }
  
  .trend-icon {
    font-size: 12px;
  }
  
  .trend-value {
    font-size: 9px;
  }
}
</style>
