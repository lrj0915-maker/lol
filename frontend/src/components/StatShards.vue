<template>
  <div class="stat-shards">
    <div class="shard-title">【属性碎片】</div>
    
    <div class="shard-rows">
      <div class="shard-row">
        <span class="row-label">攻击：</span>
        <div class="shard-slot">
          <img v-lazy="getShardIconUrl(shardIds[0])" @error="handleImageError" />
          <div class="shard-tooltip">
            <span class="shard-name">{{ getShardName(shardIds[0]) }}</span>
            <span class="shard-desc">{{ getShardDesc(shardIds[0]) }}</span>
          </div>
        </div>
      </div>
      
      <div class="shard-row">
        <span class="row-label">灵活：</span>
        <div class="shard-slot">
          <img v-lazy="getShardIconUrl(shardIds[1])" @error="handleImageError" />
          <div class="shard-tooltip">
            <span class="shard-name">{{ getShardName(shardIds[1]) }}</span>
            <span class="shard-desc">{{ getShardDesc(shardIds[1]) }}</span>
          </div>
        </div>
      </div>
      
      <div class="shard-row">
        <span class="row-label">防御：</span>
        <div class="shard-slot">
          <img v-lazy="getShardIconUrl(shardIds[2])" @error="handleImageError" />
          <div class="shard-tooltip">
            <span class="shard-name">{{ getShardName(shardIds[2]) }}</span>
            <span class="shard-desc">{{ getShardDesc(shardIds[2]) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getStatShardById, getStatShardIconUrl as getIconUrl } from '@/data/runes'

const props = defineProps({
  shardIds: {
    type: Array,
    required: true,
    validator: (value) => value.length === 3
  }
})

function getShardName(shardId) {
  const shard = getStatShardById(shardId)
  return shard?.name || '未知'
}

function getShardDesc(shardId) {
  const shard = getStatShardById(shardId)
  return shard?.description || ''
}

function getShardIconUrl(shardId) {
  return getIconUrl(shardId)
}

function handleImageError(event) {
  event.target.style.opacity = '0.3'
}
</script>

<style scoped>
.stat-shards {
  flex: 0 0 200px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
}

.shard-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  text-align: center;
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.shard-rows {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.shard-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.row-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  min-width: 40px;
}

.shard-slot {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid var(--border-color);
  background: var(--bg-card);
  overflow: hidden;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.shard-slot:hover {
  transform: scale(1.15);
  border-color: var(--accent-secondary);
  box-shadow: 0 4px 12px rgba(78, 204, 163, 0.3);
}

.shard-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  padding: 4px;
}

.shard-tooltip {
  position: absolute;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: 6px 10px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 10;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.shard-slot:hover .shard-tooltip {
  opacity: 1;
}

.shard-name {
  font-size: var(--font-size-xs);
  color: var(--text-primary);
  font-weight: 600;
}

.shard-desc {
  font-size: 10px;
  color: var(--text-muted);
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .stat-shards {
    flex: 1;
    padding: var(--spacing-sm);
  }
  
  .shard-title {
    font-size: 12px;
  }
  
  .shard-rows {
    gap: var(--spacing-sm);
  }
  
  .shard-slot {
    width: 28px;
    height: 28px;
  }
  
  .row-label {
    font-size: 10px;
    min-width: 35px;
  }
}

@media (max-width: 480px) {
  .shard-slot {
    width: 24px;
    height: 24px;
  }
  
  .row-label {
    min-width: 30px;
  }
}
</style>
