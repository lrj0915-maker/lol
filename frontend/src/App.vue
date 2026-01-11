<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <StatusBar />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useMatchStore } from '@/stores/match'
import { bridge } from '@/utils/bridge'
import Sidebar from '@/components/layout/Sidebar.vue'
import StatusBar from '@/components/layout/StatusBar.vue'

const appStore = useAppStore()
const matchStore = useMatchStore()

let statusInterval = null
const chatHotkey = ref('F1')

// 加载聊天配置
async function loadChatConfig() {
  const config = await bridge.getChatConfig()
  if (config?.hotkey) {
    chatHotkey.value = config.hotkey
  }
}

// 全局快捷键监听
function onGlobalKeydown(e) {
  const key = e.key.toUpperCase()
  if (key === chatHotkey.value) {
    console.log('快捷键触发，发送分析到聊天')
    bridge.sendAnalysisToChat()
  }
}

onMounted(async () => {
  // 尝试连接
  await appStore.connect()
  
  // 加载聊天配置
  await loadChatConfig()
  
  // 定时刷新状态（每3秒）
  statusInterval = setInterval(async () => {
    await appStore.refreshStatus()
    // 同时刷新快捷键配置
    const config = await bridge.getChatConfig()
    if (config?.hotkey) {
      chatHotkey.value = config.hotkey
    }
  }, 3000)
  
  // 全局快捷键
  window.addEventListener('keydown', onGlobalKeydown)
  
  // 监听游戏结束事件
  window.addEventListener('game-end', (e) => {
    matchStore.setCurrentMatch(e.detail)
  })
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  position: relative;
}

.app-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: radial-gradient(ellipse at top, rgba(78, 204, 163, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: 44px;
  position: relative;
  z-index: 1;
}

/* 页面切换动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.25s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
