<script setup>
import { computed } from 'vue'

// 技能加点顺序卡片组件
// 展示技能加点顺序和对应胜率
const props = defineProps({
  skill: {
    type: Object,
    required: true,
    // skill 结构: { order: string | string[], play: number, win: number, pick_rate?: number }
  },
})

const displayOrder = computed(() => {
  if (Array.isArray(props.skill?.order)) {
    return props.skill.order.join(' > ')
  }
  return props.skill?.order || ''
})
const winRate = computed(() => props.skill.play ? (props.skill.win / props.skill.play * 100) : 0)
</script>

<template>
  <div class="skill-card">
    <!-- 技能加点顺序 -->
    <div class="skill-order">{{ displayOrder }}</div>
    <!-- 胜率条 -->
    <div class="wr-bar">
      <div
        class="wr-fill"
        :style="{ width: winRate + '%' }"
      />
    </div>
    <!-- 胜率数字 -->
    <span class="skill-wr">
      {{ winRate.toFixed(1) }}%
      <span class="skill-games">({{ skill.play || 0 }}场)</span>
    </span>
  </div>
</template>

<style scoped>
.skill-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.skill-order {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  letter-spacing: 2px;
  flex-shrink: 0;
  min-width: 48px;
}

.wr-bar {
  flex: 1;
  height: 4px;
  background: #1e293b;
  border-radius: 2px;
  overflow: hidden;
}

.wr-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.skill-wr {
  font-size: 11px;
  color: #94a3b8;
  flex-shrink: 0;
}

.skill-games {
  color: #475569;
}
</style>
