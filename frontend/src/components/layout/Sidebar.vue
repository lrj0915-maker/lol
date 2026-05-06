<template>
  <aside class="sidebar">
    <div class="sidebar-top">
      <router-link to="/match" class="brand" title="LOL 战绩助手">
        <div class="brand-mark">L</div>
        <div class="brand-copy">
          <strong>LOL</strong>
          <span>战绩助手</span>
        </div>
      </router-link>
    </div>

    <nav class="nav-menu">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
        :title="item.label"
      >
        <span class="nav-indicator"></span>
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <span class="version">v1.0</span>
    </div>
  </aside>
</template>

<script setup>
const menuItems = [
  { path: '/login', icon: '登', label: '登录' },
  { path: '/cache', icon: '注', label: '注入' },
  { path: '/match', icon: '战', label: '战绩' },
  { path: '/analysis', icon: '析', label: '分析' },
  { path: '/select', icon: '选', label: '选人' },
  { path: '/runes', icon: '符', label: '符文' },
  { path: '/runes-preview', icon: '预', label: '预览' },
  { path: '/augments', icon: '强', label: '强化' },
  { path: '/jungle', icon: '野', label: '野怪' },
  { path: '/history', icon: '史', label: '历史' },
  { path: '/settings', icon: '设', label: '设置' },
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width, 88px);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 12px 10px;
  gap: 12px;
  position: relative;
  z-index: 10;
}

.sidebar-top {
  display: flex;
  justify-content: center;
}

.brand {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 16px;
  text-decoration: none;
  color: var(--text-primary);
  background: var(--surface-subtle);
  border: 1px solid var(--border-subtle);
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 900;
  color: var(--text-inverse);
  background: var(--accent-gradient);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.brand-copy strong {
  font-size: 11px;
  letter-spacing: 0.08em;
}

.brand-copy span {
  font-size: 10px;
  color: var(--text-secondary);
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
}

.nav-menu::-webkit-scrollbar {
  display: none;
}

.nav-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 8px 4px;
  border-radius: 14px;
  text-decoration: none;
  color: var(--text-tertiary);
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--surface-hover);
}

.nav-item.active {
  color: var(--text-primary);
  background: var(--surface-active);
}

.nav-item.active .nav-icon {
  border-color: var(--accent-border);
  background: var(--surface-muted);
}

.nav-item.active .nav-indicator {
  opacity: 1;
  transform: scaleY(1);
}

.nav-indicator {
  position: absolute;
  left: -10px;
  top: 50%;
  width: 3px;
  height: 24px;
  border-radius: 0 999px 999px 0;
  background: var(--accent-gradient);
  opacity: 0;
  transform: translateY(-50%) scaleY(0.65);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.nav-icon {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-subtle);
  background: var(--surface-muted);
  font-size: 13px;
  font-weight: 800;
}

.nav-label {
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
}

.sidebar-footer {
  display: flex;
  justify-content: center;
}

.version {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  color: var(--text-muted);
  background: var(--surface-muted);
  border: 1px solid var(--border-subtle);
}
</style>
