<template>
  <div class="settings-view">
    <h2>设置</h2>
    
    <div class="settings-section">
      <h3>自动准备</h3>
      <div class="setting-item">
        <span class="setting-label">启用自动准备</span>
        <div class="toggle" :class="{ on: appStore.autoAcceptEnabled }" @click="toggleAutoAccept">
          <div class="toggle-thumb"></div>
        </div>
      </div>
      <div class="setting-item">
        <span class="setting-label">延迟范围</span>
        <span class="setting-value">1-3 秒</span>
      </div>
    </div>
    
    <div class="settings-section">
      <h3>自动选人</h3>
      <div class="setting-item">
        <span class="setting-label">启用自动选人</span>
        <div class="toggle" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
          <div class="toggle-thumb"></div>
        </div>
      </div>
    </div>
    
    <div class="settings-section">
      <h3>数据</h3>
      <div class="setting-item">
        <span class="setting-label">历史记录保留</span>
        <span class="setting-value">30 天</span>
      </div>
    </div>
    
    <div class="settings-section">
      <h3>关于</h3>
      <div class="setting-item">
        <span class="setting-label">版本</span>
        <span class="setting-value">1.0.0</span>
      </div>
    </div>
  </div>
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
.settings-view {
  padding: var(--spacing-md);
  height: 100%;
  overflow-y: auto;
}

.settings-view h2 {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-lg);
}

.settings-section {
  background: var(--bg-card);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.settings-section h3 {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  color: var(--text-primary);
}

.setting-value {
  color: var(--text-secondary);
}

.toggle {
  width: 44px;
  height: 24px;
  background: var(--bg-secondary);
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  transition: var(--transition-fast);
}

.toggle.on {
  background: var(--accent-secondary);
}

.toggle-thumb {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: var(--transition-fast);
}

.toggle.on .toggle-thumb {
  left: 22px;
}
</style>
