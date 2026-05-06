<template>
  <div class="first-time-guide" v-if="show">
    <div class="guide-overlay" @click="close"></div>
    <div class="guide-content">
      <button class="close-btn" @click="close">×</button>
      
      <div class="guide-header">
        <span class="guide-icon">👋</span>
        <h2>欢迎使用符文推荐</h2>
        <p class="guide-subtitle">让我们快速了解如何使用这个功能</p>
      </div>
      
      <div class="guide-steps">
        <div class="step" v-for="(step, idx) in steps" :key="idx">
          <div class="step-number">{{ idx + 1 }}</div>
          <div class="step-content">
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
            <div class="step-visual" v-if="step.visual">
              <span class="visual-icon">{{ step.visual }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="guide-footer">
        <label class="dont-show-again">
          <input type="checkbox" v-model="dontShowAgain" />
          <span>不再显示此引导</span>
        </label>
        <button class="start-btn" @click="start">
          <span class="btn-icon">🚀</span>
          <span>开始使用</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close', 'start'])

const show = ref(false)
const dontShowAgain = ref(false)

const steps = [
  {
    title: '选择英雄',
    description: '使用搜索框搜索英雄，或从默认列表中选择',
    visual: '🔍'
  },
  {
    title: '选择位置',
    description: '点击位置按钮（上单、打野、中单、下路、辅助）',
    visual: '🎯'
  },
  {
    title: '查看推荐',
    description: '浏览符文配置列表，查看胜率、流行度和趋势',
    visual: '📊'
  },
  {
    title: '展开详情',
    description: '点击配置卡片展开，查看完整的符文树和属性碎片',
    visual: '📖'
  },
  {
    title: '一键应用',
    description: '点击"一键应用符文"按钮，自动应用到游戏客户端',
    visual: '⚡'
  }
]

onMounted(() => {
  // 检查是否已经显示过引导
  const hasShown = localStorage.getItem('runes_guide_shown')
  if (!hasShown) {
    show.value = true
  }
})

function close() {
  if (dontShowAgain.value) {
    localStorage.setItem('runes_guide_shown', 'true')
  }
  show.value = false
  emit('close')
}

function start() {
  if (dontShowAgain.value) {
    localStorage.setItem('runes_guide_shown', 'true')
  }
  show.value = false
  emit('start')
}

// 暴露方法供父组件调用
defineExpose({
  showGuide() {
    show.value = true
  }
})
</script>

<style scoped>
.first-time-guide {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.guide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
}

.guide-content {
  position: relative;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xl);
  overflow-y: auto;
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  color: var(--text-muted);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.close-btn:hover {
  background: rgba(255, 100, 100, 0.2);
  border-color: #ff6b6b;
  color: #ff6b6b;
  transform: rotate(90deg);
}

.guide-header {
  text-align: center;
  padding: var(--spacing-xl) var(--spacing-lg) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.guide-icon {
  font-size: 64px;
  display: block;
  margin-bottom: var(--spacing-md);
  animation: wave 2s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(20deg); }
  75% { transform: rotate(-20deg); }
}

.guide-header h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.guide-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.guide-steps {
  padding: var(--spacing-lg);
}

.step {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  animation: slideInLeft 0.5s ease-out backwards;
}

.step:nth-child(1) { animation-delay: 0.1s; }
.step:nth-child(2) { animation-delay: 0.2s; }
.step:nth-child(3) { animation-delay: 0.3s; }
.step:nth-child(4) { animation-delay: 0.4s; }
.step:nth-child(5) { animation-delay: 0.5s; }

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.step-number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent-secondary), var(--accent-tertiary));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--bg-primary);
  box-shadow: 0 4px 12px rgba(78, 204, 163, 0.3);
}

.step-content {
  flex: 1;
}

.step-content h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.step-content p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.step-visual {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  display: inline-block;
}

.visual-icon {
  font-size: 24px;
}

.guide-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.dont-show-again {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}

.dont-show-again input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent-secondary), var(--accent-tertiary));
  border: none;
  border-radius: var(--border-radius);
  color: var(--bg-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 4px 12px rgba(78, 204, 163, 0.3);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(78, 204, 163, 0.4);
}

.btn-icon {
  font-size: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .guide-content {
    width: 95%;
    max-height: 95vh;
  }
  
  .guide-header {
    padding: var(--spacing-lg) var(--spacing-md) var(--spacing-md);
  }
  
  .guide-icon {
    font-size: 48px;
  }
  
  .guide-header h2 {
    font-size: var(--font-size-lg);
  }
  
  .guide-steps {
    padding: var(--spacing-md);
  }
  
  .step {
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }
  
  .step-number {
    width: 32px;
    height: 32px;
    font-size: var(--font-size-sm);
  }
  
  .guide-footer {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .start-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
