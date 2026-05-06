<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <div class="page-host">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
    <StatusBar />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useMatchStore } from '@/stores/match'
import { useRuntimeSync } from '@/composables/useRuntimeSync'
import { bridge } from '@/utils/bridge'
import Sidebar from '@/components/layout/Sidebar.vue'
import StatusBar from '@/components/layout/StatusBar.vue'

const appStore = useAppStore()
const matchStore = useMatchStore()
const chatHotkey = ref('F1')
let statusInterval = null

useRuntimeSync(appStore, matchStore)

async function loadChatConfig() {
  const cfg = await bridge.getChatConfig()
  if (cfg?.success && cfg?.hotkey) {
    chatHotkey.value = cfg.hotkey
  }
}

onMounted(async () => {
  await appStore.connect()
  await loadChatConfig()

  statusInterval = window.setInterval(async () => {
    await appStore.refreshStatus()
    const cfg = await bridge.getChatConfig()
    if (cfg?.success && cfg?.hotkey) {
      chatHotkey.value = cfg.hotkey
    }
  }, 5000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
})
</script>

<style scoped>
.app-container {
  --sidebar-width: 88px;
  --statusbar-height: 56px;
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding-bottom: var(--statusbar-height);
  position: relative;
  z-index: 1;
}

.page-host {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  background: var(--bg-primary);
}

.page-host > * {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.page-host :deep(*) {
  min-height: 0;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(14px) scale(0.99);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.99);
}
</style>
