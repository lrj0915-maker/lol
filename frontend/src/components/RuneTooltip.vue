<template>
  <Teleport to="body">
    <Transition name="tooltip-fade">
      <div 
        v-if="visible"
        ref="tooltipRef"
        class="rune-tooltip"
        :style="tooltipStyle"
        @mouseenter="onMouseEnter"
        @mouseleave="onMouseLeave"
      >
        <div class="tooltip-header">
          <img v-if="rune.icon" :src="getRuneIconUrl(rune.id)" class="tooltip-icon" />
          <div class="tooltip-title-section">
            <h4 class="tooltip-title">{{ rune.name }}</h4>
            <span class="tooltip-subtitle">{{ rune.nameEn }}</span>
          </div>
        </div>
        
        <div class="tooltip-divider"></div>
        
        <div class="tooltip-description">
          {{ rune.description || '暂无描述' }}
        </div>
        
        <div v-if="rune.stats" class="tooltip-stats">
          <div class="stat-item" v-for="(value, key) in rune.stats" :key="key">
            <span class="stat-label">{{ key }}:</span>
            <span class="stat-value">{{ value }}</span>
          </div>
        </div>
        
        <div v-if="calculatedValue" class="tooltip-calculated">
          <div class="calculated-header">
            <span class="calc-icon">🧮</span>
            <span>实际收益</span>
          </div>
          <div class="calculated-value">{{ calculatedValue }}</div>
        </div>
        
        <div class="tooltip-footer">
          <span class="tooltip-hint">按 ESC 关闭</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { getRuneById, getRuneIconUrl } from '@/data/runes'

const props = defineProps({
  runeId: {
    type: Number,
    default: null
  },
  targetElement: {
    type: Object,
    default: null
  },
  championLevel: {
    type: Number,
    default: 1
  },
  championStats: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const visible = ref(false)
const tooltipRef = ref(null)
const position = ref({ x: 0, y: 0 })
const showDelay = 200 // 200ms延迟
let showTimer = null
let hideTimer = null

const rune = computed(() => {
  if (!props.runeId) return {}
  const runeData = getRuneById(props.runeId)
  return {
    ...runeData,
    description: getRuneDescription(props.runeId)
  }
})

// 获取符文描述（实际应该从数据文件读取）
function getRuneDescription(runeId) {
  const descriptions = {
    8010: '持续对同一个敌方英雄造成伤害会提供额外的自适应之力。',
    8005: '连续3次攻击或技能命中同一目标会造成额外伤害。',
    8008: '提升攻击速度上限，超过2.5后转化为额外伤害。',
    8021: '移动和攻击会提供治疗效果和移动速度。',
    // ... 更多符文描述
  }
  return descriptions[runeId] || '暂无详细描述'
}

// 计算实际收益
const calculatedValue = computed(() => {
  if (!props.championStats || !rune.value) return null
  
  // 示例：计算征服者的实际伤害加成
  if (props.runeId === 8010) {
    const baseAD = props.championStats.attackDamage || 60
    const bonus = Math.floor(baseAD * 0.06 * 12) // 满层6%
    return `满层提供 ${bonus} 攻击力`
  }
  
  return null
})

// Tooltip定位
const tooltipStyle = computed(() => {
  if (!props.targetElement || !tooltipRef.value) {
    return {
      left: `${position.value.x}px`,
      top: `${position.value.y}px`,
      opacity: 0
    }
  }
  
  const target = props.targetElement.getBoundingClientRect()
  const tooltip = tooltipRef.value.getBoundingClientRect()
  const padding = 10
  
  let left = target.left + target.width / 2 - tooltip.width / 2
  let top = target.top - tooltip.height - padding
  
  // 防止超出屏幕左侧
  if (left < padding) {
    left = padding
  }
  
  // 防止超出屏幕右侧
  if (left + tooltip.width > window.innerWidth - padding) {
    left = window.innerWidth - tooltip.width - padding
  }
  
  // 如果上方空间不足，显示在下方
  if (top < padding) {
    top = target.bottom + padding
  }
  
  return {
    left: `${left}px`,
    top: `${top}px`,
    opacity: 1
  }
})

function show() {
  clearTimeout(hideTimer)
  showTimer = setTimeout(() => {
    visible.value = true
  }, showDelay)
}

function hide() {
  clearTimeout(showTimer)
  hideTimer = setTimeout(() => {
    visible.value = false
  }, 100)
}

function onMouseEnter() {
  clearTimeout(hideTimer)
}

function onMouseLeave() {
  hide()
}

function handleEscape(e) {
  if (e.key === 'Escape' && visible.value) {
    visible.value = false
    emit('close')
  }
}

watch(() => props.runeId, (newId) => {
  if (newId) {
    show()
  } else {
    hide()
  }
})

watch(() => props.targetElement, (newTarget) => {
  if (newTarget) {
    show()
  } else {
    hide()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
})

defineExpose({
  show,
  hide
})
</script>

<style scoped>
.rune-tooltip {
  position: fixed;
  z-index: 9999;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 2px solid var(--accent-secondary);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  max-width: 320px;
  min-width: 280px;
  pointer-events: auto;
  backdrop-filter: blur(10px);
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.tooltip-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--accent-secondary);
  box-shadow: 0 0 12px rgba(78, 204, 163, 0.4);
}

.tooltip-title-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tooltip-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--accent-secondary);
  margin: 0;
}

.tooltip-subtitle {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.tooltip-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-secondary), transparent);
  margin: var(--spacing-sm) 0;
}

.tooltip-description {
  font-size: var(--font-size-sm);
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.tooltip-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--spacing-sm);
  background: rgba(78, 204, 163, 0.1);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
}

.stat-label {
  color: var(--text-muted);
}

.stat-value {
  color: var(--accent-secondary);
  font-weight: 600;
}

.tooltip-calculated {
  padding: var(--spacing-sm);
  background: rgba(255, 215, 0, 0.1);
  border-left: 3px solid #FFD700;
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
}

.calculated-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: #FFD700;
  font-weight: 600;
  margin-bottom: 4px;
}

.calc-icon {
  font-size: 14px;
}

.calculated-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.tooltip-footer {
  display: flex;
  justify-content: center;
  padding-top: var(--spacing-sm);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.tooltip-hint {
  font-size: 10px;
  color: var(--text-disabled);
  font-style: italic;
}

/* 动画 */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.95);
}

/* 响应式 */
@media (max-width: 480px) {
  .rune-tooltip {
    max-width: calc(100vw - 40px);
    min-width: 260px;
  }
  
  .tooltip-icon {
    width: 40px;
    height: 40px;
  }
}
</style>
