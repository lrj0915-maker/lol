<template>
  <div class="settings-view">
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">⚙️</span>
        设置
      </h2>
    </div>
    
    <div class="settings-grid">
      <div class="settings-section">
        <div class="section-header">
          <span class="section-icon">🎯</span>
          <h3>自动准备</h3>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">启用自动准备</span>
            <span class="setting-desc">匹配成功后自动点击接受</span>
          </div>
          <div class="toggle" :class="{ on: appStore.autoAcceptEnabled }" @click="toggleAutoAccept">
            <div class="toggle-thumb"></div>
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">延迟范围</span>
            <span class="setting-desc">随机延迟避免检测</span>
          </div>
          <span class="setting-value">1-3 秒</span>
        </div>
      </div>
      
      <div class="settings-section">
        <div class="section-header">
          <span class="section-icon">🎮</span>
          <h3>自动选人</h3>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">启用自动选人</span>
            <span class="setting-desc">按预设列表自动Ban/Pick</span>
          </div>
          <div class="toggle" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
            <div class="toggle-thumb"></div>
          </div>
        </div>
        <div class="setting-item clickable" @click="$router.push('/select')">
          <div class="setting-info">
            <span class="setting-label">配置英雄列表</span>
            <span class="setting-desc">设置Ban/Pick优先级</span>
          </div>
          <span class="setting-arrow">→</span>
        </div>
      </div>
      
      <div class="settings-section">
        <div class="section-header">
          <span class="section-icon">💾</span>
          <h3>数据</h3>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">历史记录保留</span>
            <span class="setting-desc">超过时间自动清理</span>
          </div>
          <span class="setting-value">30 天</span>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">数据存储位置</span>
            <span class="setting-desc">本地SQLite数据库</span>
          </div>
          <span class="setting-value tag">本地</span>
        </div>
      </div>
      
      <div class="settings-section">
        <div class="section-header">
          <span class="section-icon">ℹ️</span>
          <h3>关于</h3>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">版本</span>
            <span class="setting-desc">当前软件版本</span>
          </div>
          <span class="setting-value version">v1.0.0</span>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">技术栈</span>
            <span class="setting-desc">PyWebView + Vue 3</span>
          </div>
          <span class="setting-value">Python + JS</span>
        </div>
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
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.title-icon {
  font-size: var(--font-size-xl);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: var(--spacing-md);
}

.settings-section {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.section-icon {
  font-size: var(--font-size-lg);
}

.section-header h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-fast);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item.clickable {
  cursor: pointer;
}

.setting-item.clickable:hover {
  background: var(--bg-hover);
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.setting-desc {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.setting-value {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.setting-value.tag {
  padding: 4px 10px;
  background: rgba(78, 204, 163, 0.15);
  color: var(--color-win);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
}

.setting-value.version {
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius-sm);
  font-family: monospace;
}

.setting-arrow {
  font-size: var(--font-size-md);
  color: var(--text-muted);
  transition: transform var(--transition-fast);
}

.setting-item.clickable:hover .setting-arrow {
  transform: translateX(4px);
  color: var(--accent-secondary);
}

.toggle {
  width: 48px;
  height: 26px;
  background: var(--bg-secondary);
  border-radius: 13px;
  cursor: pointer;
  position: relative;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
}

.toggle:hover {
  border-color: var(--border-color-light);
}

.toggle.on {
  background: var(--color-win);
  border-color: var(--color-win);
  box-shadow: var(--glow-win);
}

.toggle-thumb {
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 1px;
  left: 1px;
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-sm);
}

.toggle.on .toggle-thumb {
  left: 23px;
}
</style>
