<template>
  <div class="settings-view">
    <div class="page-header">
      <h2 class="page-title">设置</h2>
      <p class="page-subtitle">登录页负责执行操作，这里负责长期配置与自动化策略。</p>
    </div>

    <div class="settings-grid">
      <section class="settings-section tools-section">
        <div class="section-header">
          <div>
            <h3>好友白名单</h3>
            <p>配置允许自动添加和保留的好友列表，登录页的"添加好友 / 清理好友"会读取这里。</p>
          </div>
          <span class="status-chip">{{ autoFriends.length }} 人</span>
        </div>

        <div class="tool-layout single-column">
          <div class="tool-card">
            <div class="tool-card-head">
              <div>
                <h4>指定好友列表</h4>
                <p>填写完整 Riot ID（名字#1123），作为自动添加与保留白名单。</p>
              </div>
            </div>

            <div class="friend-form single-input">
              <input
                v-model.trim="friendRiotId"
                placeholder="请输入完整 Riot ID，例如 名字#1123"
                @keydown.enter="handleAddFriend"
              />
              <button class="primary-btn" @click="handleAddFriend" :disabled="!friendRiotId || actionLoading">
                添加
              </button>
            </div>

            <div v-if="autoFriends.length" class="friend-list">
              <div v-for="friend in autoFriends" :key="`${friend.name}#${friend.tag}`" class="friend-item">
                <span class="friend-name">{{ friend.name }}#{{ friend.tag }}</span>
                <button class="ghost-btn danger" @click="handleRemoveFriend(friend)" :disabled="actionLoading">移除</button>
              </div>
            </div>
            <div v-else class="empty-copy">当前还没有配置白名单好友。</div>
          </div>
        </div>

        <div v-if="actionMessage" class="action-feedback" :class="actionSuccess ? 'success' : 'fail'">
          {{ actionMessage }}
        </div>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>自动化策略</h3>
            <p>控制游戏内自动行为的长期策略。</p>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">自动分解</span>
            <span class="setting-desc">进入客户端后按策略自动分解英雄碎片。</span>
          </div>
          <div class="toggle" :class="{ on: autoDisenchantEnabled }" @click="toggleAutoDisenchant">
            <div class="toggle-thumb"></div>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">启用自动准备</span>
            <span class="setting-desc">匹配成功后自动点击接受。</span>
          </div>
          <div class="toggle" :class="{ on: appStore.autoAcceptEnabled }" @click="toggleAutoAccept">
            <div class="toggle-thumb"></div>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">延迟范围</span>
            <span class="setting-desc">当前使用 1-3 秒随机延迟。</span>
          </div>
          <span class="setting-value">1-3 秒</span>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">启用自动选人</span>
            <span class="setting-desc">进入选人阶段后按配置执行。</span>
          </div>
          <div class="toggle" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
            <div class="toggle-thumb"></div>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">仅本局触发一次</span>
            <span class="setting-desc">锁定后自动关闭，不影响后续手动操作。</span>
          </div>
          <div class="toggle" :class="{ on: appStore.autoSelectOneShot }" @click="toggleAutoSelectOneShot">
            <div class="toggle-thumb"></div>
          </div>
        </div>

        <div class="setting-item clickable" @click="router.push('/select')">
          <div class="setting-info">
            <span class="setting-label">配置英雄列表</span>
            <span class="setting-desc">维护 Ban / Pick 优先级。</span>
          </div>
          <span class="setting-arrow">></span>
        </div>
      </section>

      <section class="settings-section settings-lock-section">
        <div class="section-header compact">
          <div class="header-left">
            <h3>游戏配置备份</h3>
            <span class="status-chip">{{ settingsLockEnabled ? '已开启' : '已关闭' }}</span>
          </div>
          <div class="toggle" :class="{ on: settingsLockEnabled }" @click="toggleSettingsLock">
            <div class="toggle-thumb"></div>
          </div>
        </div>

        <div class="setting-item-buttons compact">
          <button class="primary-btn" @click="handleSaveSettings" :disabled="actionLoading">
            保存现有配置
          </button>
          <button class="ghost-btn" @click="handleRestoreSettings" :disabled="actionLoading">
            应用已保存配置
          </button>
        </div>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>数据</h3>
            <p>基础存储和清理信息。</p>
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">历史记录保留</span>
            <span class="setting-desc">当前默认保留 30 天。</span>
          </div>
          <span class="setting-value">30 天</span>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">数据存储位置</span>
            <span class="setting-desc">本地 SQLite 数据库。</span>
          </div>
          <span class="setting-value tag">本地</span>
        </div>
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div>
            <h3>关于</h3>
            <p>当前应用构成。</p>
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">版本</span>
            <span class="setting-desc">当前软件版本。</span>
          </div>
          <span class="setting-value version">v1.0.0</span>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span class="setting-label">技术栈</span>
            <span class="setting-desc">桌面容器和前端框架。</span>
          </div>
          <span class="setting-value">Python + Vue</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import bridge from '@/utils/bridge'

const router = useRouter()
const appStore = useAppStore()

const autoFriends = ref([])
const autoDisenchantEnabled = ref(false)
const friendRiotId = ref('')
const actionLoading = ref(false)
const actionMessage = ref('')
const actionSuccess = ref(true)

// 设置锁定相关
const settingsLockEnabled = ref(false)
const settingsGamePath = ref('')
const settingsLastSave = ref('')
const settingsTemplateFiles = ref([])

function setFeedback(success, message) {
  actionSuccess.value = !!success
  actionMessage.value = message || (success ? '操作成功' : '操作失败')
}

async function loadConfigTools() {
  const [friends, disenchant] = await Promise.all([
    bridge.getAutoFriends(),
    bridge.getAutoDisenchant(),
  ])
  autoFriends.value = Array.isArray(friends) ? friends : []
  autoDisenchantEnabled.value = !!disenchant?.enabled
}

async function handleAddFriend() {
  const riotId = (friendRiotId.value || '').trim()
  if (!riotId) return

  const hashIndex = riotId.lastIndexOf('#')
  if (hashIndex <= 0 || hashIndex === riotId.length - 1) {
    setFeedback(false, '请输入完整 Riot ID，例如 名字#1123')
    return
  }

  const name = riotId.slice(0, hashIndex).trim()
  const tag = riotId.slice(hashIndex + 1).trim()
  if (!name || !tag) {
    setFeedback(false, '请输入完整 Riot ID，例如 名字#1123')
    return
  }

  actionLoading.value = true
  try {
    const result = await bridge.addAutoFriend(name, tag)
    if (result?.success) {
      friendRiotId.value = ''
      await loadConfigTools()
      setFeedback(true, '白名单好友已添加')
      return
    }
    setFeedback(false, result?.message || '添加失败')
  } finally {
    actionLoading.value = false
  }
}

async function handleRemoveFriend(friend) {
  actionLoading.value = true
  try {
    const result = await bridge.removeAutoFriend(friend.name, friend.tag)
    if (result?.success) {
      await loadConfigTools()
      setFeedback(true, '白名单好友已移除')
      return
    }
    setFeedback(false, result?.message || '移除失败')
  } finally {
    actionLoading.value = false
  }
}

async function toggleAutoDisenchant() {
  const nextValue = !autoDisenchantEnabled.value
  const result = await bridge.setAutoDisenchant(nextValue)
  if (result?.success) {
    autoDisenchantEnabled.value = nextValue
    setFeedback(true, nextValue ? '已开启自动分解' : '已关闭自动分解')
    return
  }
  setFeedback(false, result?.message || '自动分解开关更新失败')
}

async function toggleAutoAccept() {
  await appStore.setAutoAccept(!appStore.autoAcceptEnabled)
}

async function toggleAutoSelect() {
  await appStore.setAutoSelect(!appStore.autoSelectEnabled)
}

async function toggleAutoSelectOneShot() {
  await appStore.setAutoSelectOneShot(!appStore.autoSelectOneShot)
}

async function loadSettingsLockConfig() {
  try {
    const config = await bridge.getSettingsLockConfig()
    settingsLockEnabled.value = !!config.enabled
    settingsGamePath.value = config.game_path || ''
    settingsLastSave.value = config.last_save_at || ''

    const info = await bridge.getSettingsTemplateInfo()
    if (info?.success && info.files) {
      settingsTemplateFiles.value = info.files.map(f => f.name)
    } else {
      settingsTemplateFiles.value = []
    }
  } catch (e) {
    console.error('加载设置锁定配置失败:', e)
    settingsTemplateFiles.value = []
  }
}

async function toggleSettingsLock() {
  const nextValue = !settingsLockEnabled.value
  const result = await bridge.setSettingsLockConfig(nextValue, null, null)
  if (result?.success) {
    settingsLockEnabled.value = nextValue
    setFeedback(true, nextValue ? '已开启自动应用' : '已关闭自动应用')
  }
}

async function handleSaveSettings() {
  actionLoading.value = true
  try {
    const result = await bridge.saveCurrentSettings()
    if (result?.success) {
      await loadSettingsLockConfig()
      setFeedback(true, `已保存：${result.files?.join('、')}`)
    } else {
      setFeedback(false, result?.message || '保存失败')
    }
  } finally {
    actionLoading.value = false
  }
}

async function handleRestoreSettings() {
  actionLoading.value = true
  try {
    const result = await bridge.restoreSettings()
    if (result?.success) {
      setFeedback(true, `已应用：${result.files?.join('、')}`)
    } else {
      setFeedback(false, result?.message || '应用失败')
    }
  } finally {
    actionLoading.value = false
  }
}

onMounted(async () => {
  await loadConfigTools()
  await loadSettingsLockConfig()
})
</script>

<style scoped>
.settings-view {
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
  animation: pageEnter 0.4s ease;
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-title {
  margin: 0;
  font-size: 28px;
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: var(--spacing-lg);
}

.settings-section {
  background: var(--gradient-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.tools-section {
  grid-column: 1 / -1;
}

.settings-lock-section .section-header {
  padding: var(--spacing-sm) var(--spacing-lg);
}

.settings-lock-section .section-header.compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
}

.settings-lock-section .header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-lock-section .header-left h3 {
  margin: 0;
  font-size: 15px;
}

.settings-lock-section .setting-item-buttons.compact {
  padding: 8px 14px 12px;
}

.settings-lock-section .setting-item-buttons.compact .primary-btn,
.settings-lock-section .setting-item-buttons.compact .ghost-btn {
  height: 34px;
  font-size: 13px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(90deg, var(--bg-secondary) 0%, transparent 100%);
}

.section-header h3,
.tool-card-head h4 {
  margin: 0;
}

.section-header p,
.tool-card-head p,
.setting-desc,
.empty-copy {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  line-height: 1.5;
}

.status-chip,
.setting-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.tool-layout {
  display: grid;
  gap: 16px;
  padding: var(--spacing-lg);
}

.tool-layout.single-column {
  grid-template-columns: 1fr;
}

.tool-card {
  padding: 18px;
  border-radius: var(--border-radius);
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(6, 12, 22, 0.5);
}

.tool-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.friend-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 96px;
  gap: 10px;
  margin-top: 16px;
}

.friend-form.single-input {
  grid-template-columns: minmax(0, 1fr) 96px;
}

.friend-form input,
.setting-item,
.primary-btn,
.ghost-btn {
  box-sizing: border-box;
}

.friend-form input {
  height: 40px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
}

.friend-form input:focus {
  border-color: rgba(78, 204, 163, 0.6);
}

.friend-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.friend-item,
.setting-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 14px 18px;
}

.friend-item {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
}

.friend-name {
  color: var(--text-primary);
  font-weight: 500;
}

.action-feedback {
  margin: 0 var(--spacing-lg) var(--spacing-lg);
  padding: 12px 14px;
  border-radius: 12px;
  font-size: var(--font-size-sm);
}

.action-feedback.success {
  background: rgba(78, 204, 163, 0.12);
  color: var(--color-win);
}

.action-feedback.fail {
  background: rgba(239, 68, 68, 0.12);
  color: #fda4af;
}

.setting-item {
  border-bottom: 1px solid rgba(48, 54, 61, 0.4);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item.clickable {
  cursor: pointer;
}

.tip-card {
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.02);
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.setting-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.setting-value.tag {
  color: var(--color-win);
}

.setting-value.version {
  color: var(--accent-tertiary);
}

.setting-arrow {
  color: var(--text-muted);
  font-weight: 700;
}

.toggle {
  width: 58px;
  height: 32px;
  border-radius: 16px;
  cursor: pointer;
  position: relative;
  border: 2px solid var(--border-color);
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.toggle.on {
  background: linear-gradient(135deg, var(--color-win) 0%, #3db892 100%);
  border-color: var(--color-win);
}

.toggle-thumb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  position: absolute;
  top: 1px;
  left: 1px;
  background: linear-gradient(135deg, #fff 0%, #e8e8e8 100%);
  transition: transform var(--transition-bounce);
}

.toggle.on .toggle-thumb {
  transform: translateX(26px);
}

.primary-btn,
.ghost-btn {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
}

.primary-btn {
  border: none;
  background: linear-gradient(135deg, #4eccb3, #2fb4a0);
  color: #06121a;
}

.ghost-btn {
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.ghost-btn.danger {
  color: #fda4af;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.setting-item-buttons {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
}

.setting-item-buttons .primary-btn,
.setting-item-buttons .ghost-btn {
  flex: 1;
}

@media (max-width: 900px) {
  .friend-form {
    grid-template-columns: 1fr;
  }
}

.setting-item-buttons {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
}

.setting-item-buttons .primary-btn,
.setting-item-buttons .ghost-btn {
  flex: 1;
}
</style>
