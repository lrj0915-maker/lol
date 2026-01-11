<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon">
        <span>⚔️</span>
      </div>
      <div class="logo-glow"></div>
    </div>
    
    <nav class="nav-menu">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
        <div class="nav-indicator"></div>
      </router-link>
    </nav>
    
    <div class="sidebar-footer">
      <div class="version">v1.0</div>
    </div>
  </aside>
</template>

<script setup>
const menuItems = [
  { path: '/match', icon: '📊', label: '战绩' },
  { path: '/analysis', icon: '👥', label: '分析' },
  { path: '/select', icon: '🎮', label: '选人' },
  { path: '/history', icon: '📜', label: '历史' },
  { path: '/settings', icon: '⚙️', label: '设置' }
]
</script>

<style scoped>
.sidebar {
  width: 76px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-sm);
  border-right: 1px solid var(--border-color);
  position: relative;
  z-index: 10;
}

.logo {
  position: relative;
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-sm);
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: var(--gradient-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: var(--shadow-md);
  position: relative;
  z-index: 1;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: var(--accent-secondary);
  border-radius: 50%;
  filter: blur(20px);
  opacity: 0.3;
  animation: pulse 3s ease-in-out infinite;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  width: 100%;
  flex: 1;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-xs);
  border-radius: var(--border-radius);
  text-decoration: none;
  color: var(--text-muted);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item:hover .nav-icon {
  transform: scale(1.1);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.15) 0%, rgba(88, 166, 255, 0.1) 100%);
  color: var(--accent-secondary);
}

.nav-item.active .nav-indicator {
  opacity: 1;
  transform: scaleY(1);
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 24px;
  background: var(--gradient-primary);
  border-radius: 0 2px 2px 0;
  opacity: 0;
  transition: all var(--transition-normal);
}

.nav-icon {
  font-size: 20px;
  margin-bottom: 2px;
  transition: transform var(--transition-fast);
}

.nav-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: var(--spacing-md);
}

.version {
  font-size: 10px;
  color: var(--text-disabled);
  padding: 4px 8px;
  background: var(--bg-primary);
  border-radius: var(--border-radius-sm);
}
</style>
