<template>
  <div class="detail-tabs">
    <div class="tabs-header">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>
    
    <div class="tabs-content">
      <component :is="currentTabComponent" :match="match" :team="team" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, markRaw } from 'vue'
import TabHighlights from './tabs/TabHighlights.vue'
import TabDataOverview from './tabs/TabDataOverview.vue'
import TabMyPerformance from './tabs/TabMyPerformance.vue'

const props = defineProps({
  match: Object,
  team: Array
})

const tabs = [
  { key: 'highlights', label: '本局亮点', component: markRaw(TabHighlights) },
  { key: 'overview', label: '数据总览', component: markRaw(TabDataOverview) },
  { key: 'myPerf', label: '玩家详情', component: markRaw(TabMyPerformance) }
]

const activeTab = ref('highlights')

const currentTabComponent = computed(() => {
  return tabs.find(t => t.key === activeTab.value)?.component
})
</script>

<style scoped>
.detail-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  gap: 4px;
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  overflow-x: auto;
}

.tab-btn {
  padding: 8px 16px;
  background: transparent;
  color: var(--text-muted);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 500;
  white-space: nowrap;
  transition: all var(--transition-fast);
  position: relative;
}

.tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--gradient-primary);
  color: var(--bg-primary);
  box-shadow: var(--shadow-sm);
}

.tabs-content {
  flex: 1;
  padding: var(--spacing-md);
  overflow: auto;
}
</style>
