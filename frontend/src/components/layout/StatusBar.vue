<template>
  <footer class="status-bar">
    <div class="status-cluster">
      <div class="status-chip" :class="appStore.connected ? 'is-good' : 'is-error'">
        <span class="status-dot"></span>
        <span>{{ appStore.connected ? '已连接' : '未连接' }}</span>
      </div>

      <div class="status-chip">
        <span class="status-label">阶段</span>
        <strong>{{ appStore.gamePhaseText }}</strong>
      </div>

      <div class="status-chip status-chip--wide">
        <span class="status-label">模式</span>
        <strong>{{ gameModeLabel }}</strong>
      </div>

      <div class="status-chip status-chip--wide hide-sm">
        <span class="status-label">推荐页面</span>
        <strong>{{ recommendedRouteLabel }}</strong>
      </div>
    </div>

    <div class="status-cluster status-cluster--actions">
      <button class="toggle-btn" :class="{ on: appStore.autoAcceptEnabled }" @click="toggleAutoAccept">
        <span class="toggle-indicator"></span>
        <span>自动准备</span>
      </button>
      <button class="toggle-btn" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
        <span class="toggle-indicator"></span>
        <span>自动选人</span>
      </button>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const gameModeLabel = computed(() => {
  const modeMap = {
    CLASSIC: '召唤师峡谷',
    ARAM: '极地大乱斗',
    ARENA: '斗魂竞技场',
    ARAM_MAYHEM: '极地乱斗强化',
  }
  return modeMap[appStore.gameModeType] || appStore.gameModeType || '未知模式'
})

const recommendedRouteLabel = computed(() => {
  const routeMap = {
    '/runes': '符文',
    '/augments': '强化',
    '/match': '战绩',
    '/analysis': '分析',
    '/select': '选人',
  }
  return routeMap[appStore.recommendedRoute] || appStore.recommendedRoute || '未推荐'
})

function toggleAutoAccept() {
  appStore.setAutoAccept(!appStore.autoAcceptEnabled)
}

function toggleAutoSelect() {
  appStore.setAutoSelect(!appStore.autoSelectEnabled)
}
</script>

<style scoped>
.status-bar {
  position: fixed;
  left: var(--sidebar-width, 88px);
  right: 0;
  bottom: 0;
  height: var(--statusbar-height, 56px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 14px;
  background: linear-gradient(180deg, rgba(18, 24, 38, 0.92), rgba(11, 16, 28, 0.98));
  border-top: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
  z-index: 100;
}

.status-cluster {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.status-cluster--actions {
  flex-shrink: 0;
}

.status-chip {
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: var(--text-primary);
  font-size: 12px;
}

.status-chip--wide {
  padding-right: 12px;
}

.status-chip strong {
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.status-chip.is-good {
  color: #8ff0cf;
  border-color: rgba(78,204,163,0.26);
}

.status-chip.is-error {
  color: #ff9aa8;
  border-color: rgba(233,69,96,0.24);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 10px currentColor;
}

.status-label {
  color: var(--text-secondary);
}

.toggle-btn {
  height: 34px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.035);
  color: var(--text-secondary);
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.toggle-btn.on {
  color: #ddfff4;
  background: rgba(78,204,163,0.14);
  border-color: rgba(78,204,163,0.32);
}

.toggle-indicator {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.8;
}

.hide-sm {
  display: inline-flex;
}

@media (max-width: 980px) {
  .hide-sm {
    display: none;
  }
}

@media (max-width: 760px) {
  .status-bar {
    padding: 0 10px;
  }

  .status-cluster--actions {
    display: none;
  }
}
</style>
