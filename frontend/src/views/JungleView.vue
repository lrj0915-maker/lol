<template>
  <div class="jungle-view">
    <div class="view-header">
      <h1 class="view-title">🐉 野怪监控</h1>
      <p class="view-subtitle">自动识别野怪提示，转发到队伍聊天</p>
    </div>

    <div class="content-grid">
      <!-- 左侧：设置区域 -->
      <div class="settings-panel card-glass">
        <!-- 识别区域设置 -->
        <div class="section">
          <h3 class="section-title">📐 识别区域</h3>
          <div class="region-inputs">
            <div class="input-group">
              <label>X</label>
              <input type="number" v-model.number="config.region.x" :disabled="isRunning" />
            </div>
            <div class="input-group">
              <label>Y</label>
              <input type="number" v-model.number="config.region.y" :disabled="isRunning" />
            </div>
            <div class="input-group">
              <label>宽</label>
              <input type="number" v-model.number="config.region.width" :disabled="isRunning" />
            </div>
            <div class="input-group">
              <label>高</label>
              <input type="number" v-model.number="config.region.height" :disabled="isRunning" />
            </div>
          </div>
          <div class="region-actions">
            <button class="btn btn-primary" @click="openRegionSelector" :disabled="isRunning">
              🖥️ 全屏选择区域
            </button>
            <button class="btn btn-secondary" @click="testOCR" :disabled="isRunning">
              🔍 测试识别
            </button>
          </div>
          <p class="region-tip">
            点击"全屏选择区域"后，软件会最小化，然后在屏幕上框选区域
          </p>
          <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
            <template v-if="testResult.detected">
              ✅ 识别成功: {{ testResult.prefix }}{{ testResult.camp }}
            </template>
            <template v-else-if="testResult.success">
              ⚠️ {{ testResult.message }}
            </template>
            <template v-else>
              ❌ {{ testResult.error }}
            </template>
          </div>
        </div>

        <!-- 通知方式 -->
        <div class="section">
          <h3 class="section-title">📢 通知方式</h3>
          <div class="radio-group">
            <label class="radio-item">
              <input type="radio" v-model="config.notify_mode" value="text" :disabled="isRunning" />
              <span class="radio-label">仅文字</span>
              <span class="radio-desc">发送队伍聊天，自己静音</span>
            </label>
            <label class="radio-item">
              <input type="radio" v-model="config.notify_mode" value="voice" :disabled="isRunning" />
              <span class="radio-label">仅语音</span>
              <span class="radio-desc">本地播报，不发聊天</span>
            </label>
            <label class="radio-item">
              <input type="radio" v-model="config.notify_mode" value="both" :disabled="isRunning" />
              <span class="radio-label">文字+语音</span>
              <span class="radio-desc">都要</span>
            </label>
          </div>
        </div>

        <!-- 文字发送方式 -->
        <div class="section" v-if="config.notify_mode !== 'voice'">
          <h3 class="section-title">📝 文字发送方式</h3>
          <p class="region-tip">已固定为即时发送（已移除手动热键发送）。</p>
        </div>

        <!-- 监控设置 -->
        <div class="section">
          <h3 class="section-title">⚙️ 监控设置</h3>
          <div class="setting-item">
            <span class="setting-label">自动启停</span>
            <label class="switch">
              <input type="checkbox" v-model="autoStart" @change="toggleAutoStart" />
              <span class="slider"></span>
            </label>
            <span class="setting-hint">进入游戏自动启动，结束自动停止</span>
          </div>
          <div class="setting-row">
            <span class="setting-label">识别频率</span>
            <select v-model.number="config.interval" :disabled="isRunning">
              <option :value="200">200ms (极快)</option>
              <option :value="500">500ms (推荐)</option>
              <option :value="1000">1000ms (省资源)</option>
            </select>
          </div>
          <div class="setting-row">
            <span class="setting-label">防重复间隔</span>
            <select v-model.number="config.duplicate_interval" :disabled="isRunning">
              <option :value="3">3秒</option>
              <option :value="5">5秒 (推荐)</option>
              <option :value="10">10秒</option>
            </select>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="control-buttons">
          <button 
            v-if="!isRunning" 
            class="btn btn-primary btn-large"
            @click="startMonitor"
          >
            ▶ 开始监控
          </button>
          <button 
            v-else 
            class="btn btn-danger btn-large"
            @click="stopMonitor"
          >
            ⏹ 停止监控
          </button>
        </div>
      </div>

      <!-- 右侧：日志区域 -->
      <div class="logs-panel card-glass">
        <div class="logs-header">
          <h3 class="section-title">📋 识别记录</h3>
          <button class="btn btn-small" @click="clearLogs">清空</button>
        </div>
        <div class="logs-list" ref="logsContainer">
          <div 
            v-for="(log, index) in logs" 
            :key="index"
            class="log-item"
            :class="{ skipped: log.skipped }"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
            <span class="log-status">
              <template v-if="log.skipped">
                ⏭ 重复跳过
              </template>
              <template v-else>
                <span v-if="config.notify_mode !== 'voice'" :class="log.text_sent ? 'sent' : 'failed'">
                  📝{{ log.text_sent ? '✅' : '❌' }}
                </span>
                <span v-if="config.notify_mode !== 'text'" :class="log.voice_sent ? 'sent' : 'failed'">
                  🔊{{ log.voice_sent ? '✅' : '❌' }}
                </span>
              </template>
            </span>
          </div>
          <div v-if="logs.length === 0" class="logs-empty">
            暂无识别记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import bridge from '@/utils/bridge'

const isRunning = ref(false)
const autoStart = ref(true)
const logs = ref([])
const testResult = ref(null)
const logsContainer = ref(null)

const config = reactive({
  region: { x: 50, y: 50, width: 400, height: 80 },
  interval: 500,
  duplicate_interval: 5,
  notify_mode: 'both'
})

// 加载配置
async function loadConfig() {
  try {
    const result = await bridge.getJungleMonitorStatus()
    if (result.config) {
      Object.assign(config, result.config)
    }
    if (result.auto_start !== undefined) {
      autoStart.value = result.auto_start
    }
    isRunning.value = result.running
    // 如果后端监控已在运行，自动启动轮询并加载已有日志
    if (result.running) {
      const existingLogs = await bridge.getJungleMonitorLogs()
      if (existingLogs && existingLogs.length > 0) {
        logs.value = existingLogs
      }
      startPollingLogs()
    }
  } catch (e) {
    // 加载配置失败，静默处理
  }
}

// 保存配置
async function saveConfig() {
  try {
    await bridge.setJungleMonitorConfig({
      region: { ...config.region },
      interval: config.interval,
      duplicate_interval: config.duplicate_interval,
      notify_mode: config.notify_mode
    })
  } catch (e) {
    // 保存配置失败，静默处理
  }
}

// 切换自动启停
async function toggleAutoStart() {
  try {
    await bridge.setJungleMonitorAutoStart(autoStart.value)
  } catch (e) {
    // 设置失败，静默处理
  }
}

// 开始监控
async function startMonitor() {
  await saveConfig()
  try {
    const result = await bridge.startJungleMonitor()
    if (result.success) {
      isRunning.value = true
      startPollingLogs()
    }
  } catch (e) {
    // 启动失败，静默处理
  }
}

// 停止监控
async function stopMonitor() {
  try {
    await bridge.stopJungleMonitor()
    isRunning.value = false
    stopPollingLogs()
  } catch (e) {
    // 停止失败，静默处理
  }
}

// 测试OCR
async function testOCR() {
  await saveConfig()
  testResult.value = null
  try {
    testResult.value = await bridge.testJungleOcr()
  } catch (e) {
    testResult.value = { success: false, error: e.message }
  }
}

// 清空日志
async function clearLogs() {
  try {
    await bridge.clearJungleMonitorLogs()
    logs.value = []
  } catch (e) {
    // 清空失败，静默处理
  }
}

// 轮询日志
let logPollingTimer = null
let statusPollingTimer = null

function startPollingLogs() {
  if (logPollingTimer) return
  logPollingTimer = setInterval(async () => {
    try {
      const newLogs = await bridge.getJungleMonitorLogs()
      if (!newLogs) return
      // 比较最后一条记录判断是否有新数据，比纯长度比较更可靠
      const oldLen = logs.value.length
      const newLen = newLogs.length
      if (newLen !== oldLen || (newLen > 0 && oldLen > 0 && newLogs[newLen - 1].time !== logs.value[oldLen - 1].time)) {
        logs.value = newLogs
        await nextTick()
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      }
    } catch (e) {
      // 获取日志失败，静默处理
    }
  }, 1000)
}

function stopPollingLogs() {
  if (logPollingTimer) {
    clearInterval(logPollingTimer)
    logPollingTimer = null
  }
}

async function syncMonitorStatus() {
  try {
    const status = await bridge.getJungleMonitorStatus()
    const running = !!status?.running

    if (status?.auto_start !== undefined) {
      autoStart.value = !!status.auto_start
    }

    if (running !== isRunning.value) {
      isRunning.value = running
      if (running) {
        const existingLogs = await bridge.getJungleMonitorLogs()
        if (existingLogs && existingLogs.length > 0) {
          logs.value = existingLogs
        }
        startPollingLogs()
      } else {
        stopPollingLogs()
      }
    }
  } catch (e) {
    // 状态同步失败，静默处理
  }
}

function startPollingStatus() {
  if (statusPollingTimer) return
  statusPollingTimer = setInterval(syncMonitorStatus, 1500)
}

function stopPollingStatus() {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
    statusPollingTimer = null
  }
}

// 全屏区域选择 - 调用后端
async function openRegionSelector() {
  try {
    const result = await bridge.startRegionSelect()
    
    if (result && result.success && result.region) {
      config.region.x = result.region.x
      config.region.y = result.region.y
      config.region.width = result.region.width
      config.region.height = result.region.height
      await saveConfig()
    } else {
      // 可能是从配置文件加载的，重新加载配置
      await loadConfig()
    }
  } catch (e) {
    // 区域选择错误，静默处理
  }
}

onMounted(() => {
  loadConfig()
  startPollingStatus()
})

onUnmounted(() => {
  stopPollingLogs()
  stopPollingStatus()
})
</script>

<style scoped>
.jungle-view {
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
  animation: jungleEnter 0.4s ease;
}

@keyframes jungleEnter {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.view-header {
  margin-bottom: var(--spacing-lg);
}

.view-title {
  font-size: 20px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.view-subtitle {
  color: var(--text-muted);
  font-size: 14px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.card-glass {
  background: rgba(22, 27, 34, 0.85);
  border-radius: var(--border-radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: var(--spacing-lg);
}

.section {
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
}

.section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

/* 区域输入 */
.region-inputs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-group label {
  font-size: 12px;
  color: var(--text-muted);
}

.input-group input {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--border-radius-sm);
  padding: 8px;
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
}

.input-group input:focus {
  border-color: rgba(78,204,163,0.5);
  box-shadow: 0 0 0 3px rgba(78,204,163,0.1);
  outline: none;
}

.input-group input:disabled {
  opacity: 0.5;
}

.region-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.region-tip {
  margin-top: var(--spacing-sm);
  font-size: 12px;
  color: var(--text-muted);
}

.region-tip code {
  background: rgba(78, 204, 163, 0.2);
  color: var(--accent-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.test-result {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 13px;
}

.test-result.success {
  background: rgba(78, 204, 163, 0.2);
  color: var(--accent-secondary);
}

.test-result.error {
  background: rgba(248, 81, 73, 0.2);
  color: var(--accent-danger);
}

/* 单选组 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.radio-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.radio-item:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(78, 204, 163, 0.3);
}

.radio-item input[type="radio"] {
  accent-color: var(--accent-secondary);
}

.radio-label {
  font-weight: 500;
  color: var(--text-primary);
}

.radio-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
}

/* 设置行 */
.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
}

.setting-label {
  color: var(--text-secondary);
}

.setting-row select {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--border-radius-sm);
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
}

.setting-row select:focus {
  border-color: rgba(78,204,163,0.5);
  box-shadow: 0 0 0 3px rgba(78,204,163,0.1);
  outline: none;
}

/* 按钮 */
.btn {
  padding: 8px 16px;
  border-radius: var(--border-radius-sm);
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-primary:hover {
  filter: brightness(1.1);
  box-shadow: 0 0 16px rgba(78,204,163,0.2);
}

.btn-danger {
  background: linear-gradient(135deg, #f85149, #da3633);
  color: white;
}

.btn-danger:hover {
  filter: brightness(1.1);
}

.btn-large {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  letter-spacing: 0.5px;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-muted);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-buttons {
  margin-top: var(--spacing-lg);
}

/* 日志面板 */
.logs-panel {
  display: flex;
  flex-direction: column;
  max-height: 600px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.logs-list {
  flex: 1;
  overflow-y: auto;
  background: transparent;
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  border: 1px solid rgba(255,255,255,0.04);
}

.log-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  font-size: 13px;
  transition: background 0.15s;
}

.log-item:hover {
  background: rgba(255,255,255,0.02);
}

.log-item:last-child {
  border-bottom: none;
}

.log-item + .log-item {
  border-top: 1px solid rgba(255, 255, 255, 0.03);
}

.log-item.skipped {
  opacity: 0.5;
}

.log-time {
  color: var(--text-muted);
  font-family: monospace;
}

.log-message {
  flex: 1;
  color: var(--text-primary);
}

.log-status {
  display: flex;
  gap: 4px;
}

.log-status .sent {
  color: var(--accent-secondary);
}

.log-status .failed {
  color: var(--accent-danger);
}

.logs-empty {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-xl);
}

</style>
