<template>
  <div class="rune-compare-modal" v-if="show" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2>符文配置对比</h2>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="compare-container">
        <div 
          v-for="(config, idx) in configs" 
          :key="idx"
          class="compare-column"
        >
          <div class="column-header">
            <span class="config-rank">配置 {{ config.rank }}</span>
            <span class="config-trees">
              {{ getTreeName(config.data.primary_page_id) }} + 
              {{ getTreeName(config.data.secondary_page_id) }}
            </span>
          </div>
          
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">胜率</span>
              <span class="stat-value" :class="getWinRateClass(config.winRate)">
                {{ config.winRate.toFixed(1) }}%
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">场次</span>
              <span class="stat-value">{{ config.data.play.toLocaleString() }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">流行度</span>
              <span class="stat-value">{{ config.popularity.toFixed(1) }}%</span>
            </div>
          </div>
          
          <div class="runes-preview">
            <div class="rune-tree-mini">
              <span class="tree-icon">{{ getTreeEmoji(config.data.primary_page_id) }}</span>
              <div class="rune-slots">
                <div 
                  v-for="runeId in config.data.primary_rune_ids" 
                  :key="runeId"
                  class="rune-mini"
                  :title="getRuneName(runeId)"
                >
                  <img :src="getRuneIconUrl(runeId)" />
                </div>
              </div>
            </div>
            
            <div class="rune-tree-mini secondary">
              <span class="tree-icon">{{ getTreeEmoji(config.data.secondary_page_id) }}</span>
              <div class="rune-slots">
                <div 
                  v-for="runeId in config.data.secondary_rune_ids" 
                  :key="runeId"
                  class="rune-mini"
                  :title="getRuneName(runeId)"
                >
                  <img :src="getRuneIconUrl(runeId)" />
                </div>
              </div>
            </div>
          </div>
          
          <button 
            class="apply-btn"
            @click="applyConfig(config)"
          >
            <span>⚡</span>
            <span>应用此配置</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getTreeById, getRuneById, getRuneIconUrl } from '@/data/runes'

const props = defineProps({
  configs: {
    type: Array,
    default: () => []
  },
  totalGames: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['close', 'apply'])

const show = ref(true)

function close() {
  show.value = false
  emit('close')
}

function getTreeName(treeId) {
  const tree = getTreeById(treeId)
  return tree ? tree.name : '未知'
}

function getTreeEmoji(treeId) {
  const tree = getTreeById(treeId)
  return tree ? tree.emoji : '❓'
}

function getRuneName(runeId) {
  const rune = getRuneById(runeId)
  return rune ? rune.name : '未知'
}

function getWinRateClass(winRate) {
  if (winRate >= 53) return 'high'
  if (winRate <= 48) return 'low'
  return 'normal'
}

function applyConfig(config) {
  emit('apply', config)
  close()
}

defineExpose({
  show() {
    show.value = true
  }
})
</script>

<style scoped>
.rune-compare-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.modal-header h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  background: var(--bg-hover);
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
}

.close-btn:hover {
  background: rgba(255, 100, 100, 0.2);
  border-color: #ff6b6b;
  color: #ff6b6b;
  transform: rotate(90deg);
}

.compare-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.compare-column {
  background: var(--gradient-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: all var(--transition-fast);
}

.compare-column:hover {
  border-color: var(--accent-secondary);
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.column-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.config-rank {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--accent-secondary);
}

.config-trees {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stat-value {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.high {
  color: var(--color-success);
}

.stat-value.low {
  color: var(--color-error);
}

.runes-preview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rune-tree-mini {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.tree-icon {
  font-size: 24px;
}

.rune-slots {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.rune-mini {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.rune-mini:hover {
  transform: scale(1.1);
  border-color: var(--accent-secondary);
  box-shadow: 0 0 12px rgba(78, 204, 163, 0.3);
}

.rune-mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.apply-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
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

.apply-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(78, 204, 163, 0.4);
}

/* 响应式 */
@media (max-width: 768px) {
  .compare-container {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
