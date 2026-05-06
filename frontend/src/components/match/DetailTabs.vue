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

defineProps({ match: Object, team: Array })

const tabs = [
  { key: 'highlights', label: '本局亮点', component: markRaw(TabHighlights) },
  { key: 'overview', label: '数据总览', component: markRaw(TabDataOverview) },
  { key: 'myPerf', label: '玩家详情', component: markRaw(TabMyPerformance) },
]

const activeTab = ref('highlights')
const currentTabComponent = computed(() => tabs.find((tab) => tab.key === activeTab.value)?.component)
</script>

<style scoped>
.detail-tabs { display: flex; flex-direction: column; height: 100%; background: rgba(255, 255, 255, 0.025); border-radius: 12px; border: 1px solid var(--border-color); overflow: hidden; }
.tabs-header { display: flex; gap: 6px; padding: 8px 10px; background: rgba(22, 27, 34, 0.88); border-bottom: 1px solid var(--border-color); flex-shrink: 0; overflow-x: auto; }
.tab-btn { height: 32px; padding: 0 12px; background: transparent; color: var(--text-secondary); border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid transparent; cursor: pointer; white-space: nowrap; transition: all .18s ease; }
.tab-btn:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); }
.tab-btn.active { background: linear-gradient(90deg, rgba(78, 204, 163, 0.22), rgba(88, 166, 255, 0.18)); color: var(--text-primary); border-color: rgba(78, 204, 163, 0.28); }
.tabs-content { flex: 1; min-height: 0; overflow: auto; padding: 10px; }
</style>
