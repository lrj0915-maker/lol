<template>
  <footer class="status-bar">
    <div class="status-left">
      <div class="status-item connection">
        <span class="status-dot" :class="{ connected: appStore.connected }"></span>
        <span class="status-text">{{ appStore.connected ? '已连接' : '未连接' }}</span>
      </div>
      
      <div class="status-divider"></div>
      
      <div class="status-item phase">
        <span class="phase-label">当前阶段</span>
        <span class="phase-value">{{ appStore.gamePhaseText }}</span>
      </div>
    </div>
    
    <div class="status-right">
      <button class="toggle-btn" :class="{ on: appStore.autoAcceptEnabled }" @click="toggleAutoAccept">
        <span class="toggle-indicator"></span>
        <span class="toggle-label">自动准备</span>
      </button>
      
      <button class="toggle-btn" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
        <span class="toggle-indicator"></span>
        <span class="toggle-label">自动选人</span>
      </button>
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
  left: 76px;
  right: 0;
  height: 44px;
  background: rgba(22, 27, 34, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-md);
  z-index: 100;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-lose);
  box-shadow: 0 0 8px var(--color-lose);
  transition: all var(--transition-normal);
}

.status-dot.connected {
  background: var(--color-win);
  box-shadow: 0 0 8px var(--color-win);
  animation: pulse 2s ease-in-out infinite;
}

.status-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.status-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
}

.phase-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.phase-value {
  font-size: var(--font-size-xs);
  color: var(--accent-secondary);
  font-weight: 500;
  padding: 2px 8px;
  background: rgba(78, 204, 163, 0.1);
  border-radius: var(--border-radius-sm);
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-color-light);
}

.toggle-btn.on {
  background: rgba(78, 204, 163, 0.15);
  border-color: rgba(78, 204, 163, 0.3);
}

.toggle-btn.on .toggle-indicator {
  background: var(--color-win);
  box-shadow: 0 0 8px var(--color-win);
}

.toggle-btn.on .toggle-label {
  color: var(--color-win);
}

.toggle-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all var(--transition-fast);
}

.toggle-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-weight: 500;
  transition: color var(--transition-fast);
}
</style>
