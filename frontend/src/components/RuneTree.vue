<template>
  <div class="rune-tree" :class="`tree-${treeId}`">
    <!-- 符文树标题 -->
    <div class="tree-header" :style="{ borderColor: treeColor }">
      <img v-lazy="treeIconUrl" class="tree-icon" />
      <span class="tree-name">{{ treeName }}</span>
      <span class="tree-emoji">{{ treeEmoji }}</span>
      <span class="tree-type">{{ type === 'primary' ? '主系' : '副系' }}</span>
    </div>
    
    <!-- 主系：基石符文 + 3层符文 -->
    <div v-if="type === 'primary'" class="primary-runes">
      <!-- 基石符文 -->
      <div class="keystone-rune">
        <div class="rune-slot large" :style="{ borderColor: treeColor }">
          <img v-lazy="getRuneIconUrl(runeIds[0])" @error="handleImageError" />
          <div class="rune-tooltip">
            <span class="rune-name">{{ getRuneName(runeIds[0]) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 3层符文 -->
      <div class="rune-layers">
        <div v-for="layer in 3" :key="layer" class="rune-layer">
          <div class="rune-slot" :class="{ selected: true }">
            <img v-lazy="getRuneIconUrl(runeIds[layer])" @error="handleImageError" />
            <div class="rune-tooltip">
              <span class="rune-name">{{ getRuneName(runeIds[layer]) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 副系：2个符文 -->
    <div v-if="type === 'secondary'" class="secondary-runes">
      <div v-for="runeId in runeIds" :key="runeId" class="rune-slot">
        <img v-lazy="getRuneIconUrl(runeId)" @error="handleImageError" />
        <div class="rune-tooltip">
          <span class="rune-name">{{ getRuneName(runeId) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getTreeById, getRuneById, getRuneIconUrl } from '@/data/runes'

const props = defineProps({
  treeId: {
    type: Number,
    required: true
  },
  runeIds: {
    type: Array,
    required: true
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['primary', 'secondary'].includes(value)
  }
})

const tree = computed(() => getTreeById(props.treeId))
const treeName = computed(() => tree.value?.name || '未知')
const treeEmoji = computed(() => tree.value?.emoji || '')
const treeColor = computed(() => tree.value?.color || '#666')
const treeIconUrl = computed(() => {
  if (!tree.value) return ''
  return `https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/${tree.value.icon}`
})

function getRuneName(runeId) {
  const rune = getRuneById(runeId)
  return rune?.name || '未知符文'
}

function handleImageError(event) {
  event.target.style.opacity = '0.3'
}
</script>

<style scoped>
.rune-tree {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
}

.tree-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  border-bottom: 2px solid;
}

.tree-icon {
  width: 24px;
  height: 24px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.tree-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.tree-emoji {
  font-size: 18px;
}

.tree-type {
  margin-left: auto;
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  background: var(--bg-hover);
  border-radius: 10px;
  color: var(--text-muted);
}

.primary-runes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.keystone-rune {
  display: flex;
  justify-content: center;
}

.rune-layers {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rune-layer {
  display: flex;
  justify-content: center;
}

.secondary-runes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  align-items: center;
}

.rune-slot {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  background: var(--bg-card);
  overflow: hidden;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.rune-slot.large {
  width: 64px;
  height: 64px;
  border-width: 3px;
}

.rune-slot:hover {
  transform: scale(1.1);
  border-color: var(--accent-secondary);
  box-shadow: 0 4px 12px rgba(78, 204, 163, 0.3);
}

.rune-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity var(--transition-fast);
}

.rune-tooltip {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 4px 8px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 10;
  box-shadow: var(--shadow-lg);
}

.rune-slot:hover .rune-tooltip {
  opacity: 1;
}

.rune-name {
  font-size: var(--font-size-xs);
  color: var(--text-primary);
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .rune-tree {
    padding: var(--spacing-sm);
  }
  
  .tree-header {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .tree-icon {
    width: 20px;
    height: 20px;
  }
  
  .tree-name {
    font-size: var(--font-size-sm);
  }
  
  .rune-slot {
    width: 40px;
    height: 40px;
  }
  
  .rune-slot.large {
    width: 56px;
    height: 56px;
  }
  
  .rune-tooltip {
    bottom: -25px;
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .rune-slot {
    width: 36px;
    height: 36px;
  }
  
  .rune-slot.large {
    width: 48px;
    height: 48px;
  }
  
  .tree-name {
    font-size: 12px;
  }
  
  .tree-type {
    font-size: 10px;
  }
}
</style>
