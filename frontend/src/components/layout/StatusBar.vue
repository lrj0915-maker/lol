<template>
  <footer class="status-bar">
    <div class="status-item">
      <span class="status-dot" :class="{ connected: appStore.connected }"></span>
      <span>{{ appStore.connected ? '已连接' : '未连接' }}</span>
    </div>
    
    <div class="status-divider"></div>
    
    <div class="status-item clickable" @click="toggleAutoAccept">
      <span>自动准备:</span>
      <span class="status-value" :class="{ on: appStore.autoAcceptEnabled }">
        {{ appStore.autoAcceptEnabled ? 'ON' : 'OFF' }}
      </span>
    </div>
    
    <div class="status-divider"></div>
    
    <div class="status-item clickable" @click="toggleAutoSelect">
      <span>自动选人:</span>
      <span class="status-value" :class="{ on: appStore.autoSelectEnabled }">
        {{ appStore.autoSelectEnabled ? 'ON' : 'OFF' }}
      </span>
    </div>
    
    <div class="status-divider"></div>
    
    <div class="status-item">
      <span>当前:</span>
      <span class="status-phase">{{ appStore.gamePhaseText }}</span>
    </div>
  </footer>
</template>

<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

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
  bottom: 0;
  left: 72px;
  right: 0;
  height: 40px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-md);
  gap: var(--spacing-md);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  z-index: 100;
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.status-item.clickable {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: var(--transition-fast);
}

.status-item.clickable:hover {
  background: var(--bg-hover);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-primary);
}

.status-dot.connected {
  background: var(--color-win);
}

.status-value {
  font-weight: 600;
  color: var(--text-muted);
}

.status-value.on {
  color: var(--color-win);
}

.status-phase {
  color: var(--accent-secondary);
}

.status-divider {
  width: 1px;
  height: 16px;
  background: var(--border-color);
}
</style>
