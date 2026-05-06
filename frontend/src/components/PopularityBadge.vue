<template>
  <div class="popularity-badge" :class="popularityClass" :title="tooltip">
    <span class="badge-icon">{{ icon }}</span>
    <span class="badge-text">{{ text }}</span>
    <div class="badge-glow"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  games: {
    type: Number,
    required: true
  },
  totalGames: {
    type: Number,
    default: 0
  }
})

// 计算流行度百分比
const popularity = computed(() => {
  if (props.totalGames === 0) return 0
  return (props.games / props.totalGames) * 100
})

// 流行度等级
const popularityClass = computed(() => {
  const pop = popularity.value
  if (pop >= 40) return 'very-popular'
  if (pop >= 25) return 'popular'
  if (pop >= 15) return 'common'
  if (pop >= 5) return 'uncommon'
  return 'rare'
})

// 图标
const icon = computed(() => {
  const pop = popularity.value
  if (pop >= 40) return '🔥'
  if (pop >= 25) return '⭐'
  if (pop >= 15) return '✨'
  if (pop >= 5) return '💫'
  return '🌙'
})

// 文本
const text = computed(() => {
  const pop = popularity.value
  if (pop >= 40) return '热门'
  if (pop >= 25) return '流行'
  if (pop >= 15) return '常见'
  if (pop >= 5) return '少见'
  return '罕见'
})

// 提示文本
const tooltip = computed(() => {
  return `流行度: ${popularity.value.toFixed(1)}% (${props.games.toLocaleString()} 场)`
})
</script>

<style scoped>
.popularity-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: help;
  transition: all var(--transition-fast);
  overflow: hidden;
}

.popularity-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: inherit;
  opacity: 0.1;
  z-index: 0;
}

.badge-icon {
  font-size: 14px;
  position: relative;
  z-index: 1;
  animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.badge-text {
  position: relative;
  z-index: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.badge-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: inherit;
  opacity: 0;
  transition: opacity var(--transition-fast);
  pointer-events: none;
}

.popularity-badge:hover .badge-glow {
  opacity: 0.3;
  animation: glowPulse 1.5s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
  50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.5; }
}

/* 热门 */
.very-popular {
  background: linear-gradient(135deg, #FF6B6B, #FF8E53);
  color: white;
  border: 1px solid rgba(255, 107, 107, 0.5);
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.very-popular .badge-glow {
  background: radial-gradient(circle, #FF6B6B, transparent);
}

/* 流行 */
.popular {
  background: linear-gradient(135deg, #4ECCB3, #5dd4b4);
  color: white;
  border: 1px solid rgba(78, 204, 163, 0.5);
  box-shadow: 0 2px 8px rgba(78, 204, 163, 0.3);
}

.popular .badge-glow {
  background: radial-gradient(circle, #4ECCB3, transparent);
}

/* 常见 */
.common {
  background: linear-gradient(135deg, #58A6FF, #6bb6ff);
  color: white;
  border: 1px solid rgba(88, 166, 255, 0.5);
  box-shadow: 0 2px 8px rgba(88, 166, 255, 0.3);
}

.common .badge-glow {
  background: radial-gradient(circle, #58A6FF, transparent);
}

/* 少见 */
.uncommon {
  background: linear-gradient(135deg, #A855F7, #b865ff);
  color: white;
  border: 1px solid rgba(168, 85, 247, 0.5);
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.3);
}

.uncommon .badge-glow {
  background: radial-gradient(circle, #A855F7, transparent);
}

/* 罕见 */
.rare {
  background: linear-gradient(135deg, #6B7280, #9CA3AF);
  color: white;
  border: 1px solid rgba(107, 114, 128, 0.5);
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.rare .badge-glow {
  background: radial-gradient(circle, #6B7280, transparent);
}

/* 悬停效果 */
.popularity-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px currentColor;
}

/* 响应式 */
@media (max-width: 768px) {
  .popularity-badge {
    padding: 3px 8px;
    font-size: 10px;
  }
  
  .badge-icon {
    font-size: 12px;
  }
}
</style>
