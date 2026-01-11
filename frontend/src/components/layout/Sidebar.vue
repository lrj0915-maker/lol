<template>
  <aside class="sidebar">
    <div class="logo">
      <span class="logo-icon">⚔️</span>
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
      </router-link>
    </nav>
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
  width: 72px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md) 0;
  border-right: 1px solid var(--border-color);
}

.logo {
  margin-bottom: var(--spacing-xl);
}

.logo-icon {
  font-size: 28px;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  width: 100%;
  padding: 0 var(--spacing-sm);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-radius: var(--border-radius);
  text-decoration: none;
  color: var(--text-secondary);
  transition: var(--transition-fast);
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-secondary);
  color: var(--bg-primary);
}

.nav-icon {
  font-size: 20px;
  margin-bottom: 2px;
}

.nav-label {
  font-size: var(--font-size-xs);
}
</style>
