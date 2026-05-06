<template>
  <div class="winrate-bar">
    <div class="bar-container">
      <div 
        class="bar-fill" 
        :class="barClass"
        :style="{ width: `${winRate}%` }"
      >
        <span class="bar-label">{{ winRate.toFixed(1) }}%</span>
      </div>
    </div>
    <div class="bar-info">
      <span class="games-count">{{ games.toLocaleString() }} 场</span>
      <span class="win-count">{{ wins.toLocaleString() }} 胜</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  wins: {
    type: Number,
    required: true
  },
  games: {
    type: Number,
    required: true
  }
})

const winRate = computed(() => {
  if (props.games === 0) return 0
  return (props.wins / props.games) * 100
})

const barClass = computed(() => {
  const rate = winRate.value
  if (rate >= 55) return 'excellent'
  if (rate >= 52) return 'good'
  if (rate >= 48) return 'normal'
  if (rate >= 45) return 'low'
  return 'poor'
})
</script>

<style scoped>
.winrate-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-container {
  position: relative;
  width: 100%;
  height: 24px;
  background: var(--bg-secondary);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.bar-fill {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

/* 胜率等级颜色 */
.bar-fill.excellent {
  background: linear-gradient(90deg, #4ECCB3, #5dd4b4);
  box-shadow: inset 0 0 20px rgba(78, 204, 163, 0.3);
}

.bar-fill.good {
  background: linear-gradient(90deg, #58A6FF, #6bb6ff);
  box-shadow: inset 0 0 20px rgba(88, 166, 255, 0.3);
}

.bar-fill.normal {
  background: linear-gradient(90deg, #A855F7, #b865ff);
  box-shadow: inset 0 0 20px rgba(168, 85, 247, 0.3);
}

.bar-fill.low {
  background: linear-gradient(90deg, #F59E0B, #ffa91f);
  box-shadow: inset 0 0 20px rgba(245, 158, 11, 0.3);
}

.bar-fill.poor {
  background: linear-gradient(90deg, #EF4444, #ff5555);
  box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.3);
}

/* 闪光效果 */
.bar-fill::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shine 2s ease-in-out infinite;
}

@keyframes shine {
  0%, 70%, 100% { left: -100%; }
  85% { left: 100%; }
}

.bar-label {
  font-size: 12px;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  position: relative;
  z-index: 1;
}

.bar-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 4px;
}

.games-count {
  font-weight: 500;
}

.win-count {
  color: var(--accent-secondary);
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .bar-container {
    height: 20px;
  }
  
  .bar-label {
    font-size: 10px;
  }
  
  .bar-info {
    font-size: 10px;
  }
}
</style>
