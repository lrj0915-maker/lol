<template>
  <div class="cache-shell">
    <section class="hero-card" :class="{ processing: isProcessing }">
      <p class="badge">CUSTOM INJECT</p>
      <h1 class="title">定制缓存注入</h1>
      <p class="subtitle">后台自动识别路径并完成注入，无需手动选择目录。</p>

      <!-- 模板信息栏 -->
      <div class="template-info" v-if="!isProcessing">
        <span class="info-tag">config.ini</span>
        <span class="info-tag">saves: {{ savesCount }} 个</span>
        <span class="info-tag">shards: {{ shardsCount }} 个</span>
      </div>

      <!-- 目标目录选择区 -->
      <div class="target-row" v-if="!isProcessing">
        <div class="target-path">
          <span class="target-icon">📁</span>
          <span class="target-text">{{ targetPathDisplay }}</span>
        </div>
        <button class="change-target-btn" @click="changeTarget">
          更换目录
        </button>
      </div>

      <div class="status-row">
        <div class="status-pill" :class="statusTone">{{ statusText }}</div>
        <div class="status-meta">最近执行 {{ lastRunText }}</div>
      </div>

      <div v-if="isProcessing" class="progress-wrap">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <p class="progress-label">{{ progressLabel }} · {{ progress }}%</p>
      </div>

      <button class="inject-btn" :class="{ running: isProcessing }" :disabled="isProcessing" @click="startCacheInject">
        <span v-if="isProcessing" class="spinner"></span>
        <span>{{ buttonLabel }}</span>
      </button>

      <p class="hint">Ctrl + Enter</p>
    </section>

    <transition name="feedback-pop" mode="out-in">
      <section v-if="message" :key="feedbackKey" class="feedback-card" :class="messageTone" role="status">
        <h2>{{ messageTitle }}</h2>
        <p>{{ message }}</p>
        <div v-if="messageTone === 'success' && operationStats" class="operation-stats">
          <div class="stat-item" v-if="operationStats.configIniUpdated">
            <span class="stat-label">config.ini</span>
            <span class="stat-value">已覆盖</span>
          </div>
          <div class="stat-item" v-if="operationStats.savesUpdated !== undefined">
            <span class="stat-label">saves/</span>
            <span class="stat-value">更新 {{ operationStats.savesUpdated }} 个</span>
          </div>
          <div class="stat-item" v-if="operationStats.shardsUpdated !== undefined">
            <span class="stat-label">shards/</span>
            <span class="stat-value">更新 {{ operationStats.shardsUpdated }} 个</span>
          </div>
        </div>
        <p v-if="operationTime" class="feedback-meta">耗时 {{ operationTime }}s</p>
      </section>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import bridge from '@/utils/bridge'

const LAST_RUN_KEY = 'cache_last_run_at'
const TARGET_PATH_KEY = 'cache_target_path'

const isProcessing = ref(false)
const progress = ref(0)
const progressLabel = ref('')
const operationTime = ref('')
const lastRunAt = ref('')
const message = ref('')
const messageTone = ref('neutral')
const feedbackKey = ref(0)
const savesCount = ref(0)
const shardsCount = ref(0)
const targetPath = ref('')
const operationStats = ref(null)

const progressStages = [
  { percent: 15, label: '检查目标目录' },
  { percent: 36, label: '分析文件变化' },
  { percent: 62, label: '执行文件复制' },
  { percent: 84, label: 'MD5 校验' },
  { percent: 96, label: '完成收尾' },
]

const targetPathDisplay = computed(() => {
  if (!targetPath.value) return '未设置目标目录'
  const maxLen = 52
  const path = targetPath.value
  if (path.length <= maxLen) return path
  return '...' + path.slice(-(maxLen - 3))
})

const lastRunText = computed(() => {
  if (!lastRunAt.value) return '暂无'
  const date = new Date(lastRunAt.value)
  if (Number.isNaN(date.getTime())) return '暂无'
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
})

const statusTone = computed(() => {
  if (isProcessing.value) return 'running'
  if (messageTone.value === 'success') return 'success'
  if (messageTone.value === 'error') return 'error'
  return 'ready'
})

const statusText = computed(() => {
  if (isProcessing.value) return '正在替换'
  if (messageTone.value === 'success') return '替换完成'
  if (messageTone.value === 'error') return '替换失败'
  return '就绪'
})

const buttonLabel = computed(() => (isProcessing.value ? '正在注入...' : '立即注入'))

const messageTitle = computed(() => {
  if (messageTone.value === 'success') return '替换完成'
  if (messageTone.value === 'error') return '替换失败'
  return '状态提示'
})

function setFeedback(text, tone = 'neutral') {
  message.value = text
  messageTone.value = tone
  feedbackKey.value += 1
}

function loadLastRun() {
  lastRunAt.value = localStorage.getItem(LAST_RUN_KEY) || ''
}

function loadTargetPath() {
  targetPath.value = localStorage.getItem(TARGET_PATH_KEY) || ''
}

function saveLastRun(timestamp) {
  lastRunAt.value = timestamp
  localStorage.setItem(LAST_RUN_KEY, timestamp)
}

function saveTargetPath(path) {
  targetPath.value = path
  localStorage.setItem(TARGET_PATH_KEY, path)
}

async function loadTemplateInfo() {
  try {
    const info = await bridge.getCacheTemplateInfo()
    if (info?.success) {
      const files = info.files || []
      savesCount.value = files.filter(f => f.type === 'save').length
      shardsCount.value = files.filter(f => f.type === 'shard').length
    }
  } catch (e) {
    console.warn('loadTemplateInfo failed', e)
  }
}

async function changeTarget() {
  const result = await bridge.checkTargetSafety?.('')
  if (result) {
    // 调用后端选择目录
  }
}

function parseFailureMessage(result) {
  const rawText = String(result?.message || result?.details || '').replace(/[\r\n]+/g, ' ').trim()
  if (!rawText || rawText.length > 42) return '本次注入未生效，请重试。'
  return rawText
}

function parseSuccessStats(result) {
  const stats = result?.stats || {}
  const files = result?.files || []
  const changes = { configIniUpdated: false, savesUpdated: 0, shardsUpdated: 0 }

  if (files) {
    for (const f of files) {
      if (f.type === 'config') changes.configIniUpdated = true
      if (f.type === 'save') changes.savesUpdated++
      if (f.type === 'shard') changes.shardsUpdated++
    }
  }
  return changes
}

function simulateProgress() {
  progress.value = 0
  progressLabel.value = '准备中'

  let stageIndex = 0
  const timer = setInterval(() => {
    if (!isProcessing.value || stageIndex >= progressStages.length) {
      clearInterval(timer)
      return
    }

    const stage = progressStages[stageIndex]
    progress.value = stage.percent
    progressLabel.value = stage.label
    stageIndex += 1
  }, 650)

  return timer
}

async function startCacheInject() {
  if (isProcessing.value) return

  isProcessing.value = true
  operationTime.value = ''
  message.value = ''
  messageTone.value = 'neutral'
  progress.value = 0
  progressLabel.value = ''
  operationStats.value = null

  const startedAt = Date.now()
  const progressTimer = simulateProgress()

  try {
    const result = await bridge.replaceCacheFiles()

    if (result?.cancelled) {
      progress.value = 0
      progressLabel.value = ''
      setFeedback('注入已取消。')
      return
    }

    if (result?.success) {
      progress.value = 100
      progressLabel.value = '注入完成'
      operationTime.value = ((Date.now() - startedAt) / 1000).toFixed(2)
      setFeedback('定制缓存已注入，可直接开始对局。', 'success')
      saveLastRun(new Date().toISOString())
      // 从结果中解析统计信息
      const files = (result.stats || {}).files || []
      operationStats.value = parseSuccessStats(result)
      return
    }

    progress.value = 0
    progressLabel.value = ''
    setFeedback(parseFailureMessage(result), 'error')
  } catch (error) {
    progress.value = 0
    progressLabel.value = ''
    setFeedback('注入调用失败，请稍后重试。', 'error')
    console.error('cache inject failed', error)
  } finally {
    clearInterval(progressTimer)
    isProcessing.value = false
  }
}

function onHotkey(event) {
  if (event.ctrlKey && event.key === 'Enter' && !isProcessing.value) {
    event.preventDefault()
    startCacheInject()
  }
}

onMounted(() => {
  loadLastRun()
  loadTargetPath()
  loadTemplateInfo()
  window.addEventListener('keydown', onHotkey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onHotkey)
})
</script>

<style scoped>
.cache-shell {
  position: relative;
  height: 100%;
  min-height: 0;
  display: grid;
  place-items: center;
  padding: clamp(20px, 5vw, 52px);
  overflow: auto;
  background:
    radial-gradient(1200px circle at 15% 10%, rgba(78, 204, 163, 0.12), transparent 50%),
    radial-gradient(1000px circle at 85% 90%, rgba(88, 166, 255, 0.08), transparent 45%),
    repeating-linear-gradient(
      -32deg,
      rgba(255, 255, 255, 0.02) 0,
      rgba(255, 255, 255, 0.02) 1px,
      transparent 1px,
      transparent 14px
    ),
    linear-gradient(160deg, #0d1117 0%, #121820 58%, #0d131b 100%);
}

.hero-card {
  position: relative;
  width: min(780px, 100%);
  padding: clamp(24px, 4vw, 42px);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(20, 26, 34, 0.92), rgba(14, 19, 26, 0.92));
  border: 1px solid rgba(78, 204, 163, 0.22);
  box-shadow:
    0 25px 70px rgba(0, 0, 0, 0.48),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.hero-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.04);
  pointer-events: none;
}

.hero-card::after {
  content: '';
  position: absolute;
  top: -120%;
  left: -20%;
  width: 50%;
  height: 240%;
  background: linear-gradient(180deg, transparent, rgba(94, 208, 176, 0.08), transparent);
  transform: rotate(18deg);
  opacity: 0;
  pointer-events: none;
}

.hero-card.processing::after {
  opacity: 1;
  animation: cardSweep 2s linear infinite;
}

.badge {
  width: fit-content;
  margin: 0;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(78, 204, 163, 0.45);
  background: rgba(78, 204, 163, 0.12);
  color: #a9edd9;
  font-size: 11px;
  letter-spacing: 0.14em;
}

.title {
  margin: 16px 0 0;
  color: #f0f6fc;
  font-weight: 700;
  font-size: clamp(28px, 5vw, 42px);
  letter-spacing: 0.02em;
}

.subtitle {
  margin: 12px 0 0;
  color: #9aa7b5;
  font-size: clamp(14px, 2vw, 16px);
  line-height: 1.65;
}

/* 模板信息栏 */
.template-info {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.info-tag {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a4b0bd;
}

/* 目标目录选择区 */
.target-row {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.target-path {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
}

.target-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.target-text {
  color: #c9d1d9;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.change-target-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #8b949e;
  cursor: pointer;
  transition: all 160ms ease;
}

.change-target-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #c9d1d9;
  border-color: rgba(255, 255, 255, 0.25);
}

/* 操作统计 */
.operation-stats {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.stat-label {
  color: #8b949e;
}

.stat-value {
  color: #c9d1d9;
  font-weight: 500;
}

.status-row {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  align-items: center;
}

.status-pill {
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid transparent;
  transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease;
}

.status-pill.ready {
  color: #b9c7d4;
  background: rgba(104, 118, 132, 0.2);
  border-color: rgba(117, 133, 149, 0.4);
}

.status-pill.running {
  color: #d8f4eb;
  background: rgba(78, 204, 163, 0.16);
  border-color: rgba(78, 204, 163, 0.5);
  animation: runningPulse 1.2s ease-in-out infinite;
}

.status-pill.success {
  color: #e2fff6;
  background: rgba(64, 200, 153, 0.2);
  border-color: rgba(64, 200, 153, 0.55);
}

.status-pill.error {
  color: #ffe8e8;
  background: rgba(205, 93, 98, 0.22);
  border-color: rgba(205, 93, 98, 0.5);
}

.status-meta {
  color: #7f8d9c;
  font-size: 13px;
}

.progress-wrap {
  margin-top: 22px;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  position: relative;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4ecca3, #58a6ff);
  transition: width 360ms ease;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -30%;
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent);
  animation: progressSweep 1.4s linear infinite;
}

.progress-label {
  margin: 10px 0 0;
  color: #a4b0bd;
  font-size: 13px;
}

.inject-btn {
  margin-top: 26px;
  width: 100%;
  height: 52px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #07120d;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  background: linear-gradient(120deg, #4ecca3 0%, #61d5b0 48%, #5bc3ff 100%);
  background-size: 120% 120%;
  box-shadow: 0 16px 34px rgba(48, 163, 130, 0.28);
  transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
}

.inject-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 40px rgba(48, 163, 130, 0.35);
}

.inject-btn:active:not(:disabled) {
  transform: translateY(0);
}

.inject-btn.running {
  animation: buttonFlow 1.3s linear infinite;
}

.inject-btn:disabled {
  cursor: not-allowed;
  filter: grayscale(0.16);
  opacity: 0.86;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(7, 18, 13, 0.3);
  border-top-color: rgba(7, 18, 13, 0.85);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.hint {
  margin: 10px 0 0;
  text-align: center;
  color: #748291;
  font-size: 12px;
  letter-spacing: 0.06em;
}

.feedback-card {
  position: relative;
  margin-top: 16px;
  width: min(780px, 100%);
  border-radius: 14px;
  padding: 16px 18px 16px 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 20, 27, 0.9);
  overflow: hidden;
}

.feedback-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
}

.feedback-card h2 {
  margin: 0;
  font-size: 15px;
}

.feedback-card p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.6;
}

.feedback-card.success {
  border-color: rgba(64, 200, 153, 0.5);
  color: #dffbf2;
  animation: successBreath 2s ease-in-out;
}

.feedback-card.success::before {
  background: linear-gradient(180deg, rgba(64, 200, 153, 0.95), rgba(91, 195, 255, 0.8));
}

.feedback-card.error {
  border-color: rgba(205, 93, 98, 0.5);
  color: #ffe3e3;
  animation: errorShake 280ms ease-out;
}

.feedback-card.error::before {
  background: linear-gradient(180deg, rgba(205, 93, 98, 0.95), rgba(232, 138, 138, 0.8));
}

.feedback-card.neutral {
  border-color: rgba(140, 154, 168, 0.36);
  color: #d2dce7;
}

.feedback-card.neutral::before {
  background: rgba(140, 154, 168, 0.75);
}

.feedback-meta {
  color: #8da2b5;
}

.feedback-pop-enter-active,
.feedback-pop-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.feedback-pop-enter-from,
.feedback-pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes runningPulse {
  0%,
  100% {
    box-shadow: 0 0 0 rgba(78, 204, 163, 0);
  }
  50% {
    box-shadow: 0 0 12px rgba(78, 204, 163, 0.24);
  }
}

@keyframes progressSweep {
  to {
    left: 130%;
  }
}

@keyframes cardSweep {
  to {
    top: 120%;
  }
}

@keyframes buttonFlow {
  from {
    background-position: 0% 50%;
  }
  to {
    background-position: 100% 50%;
  }
}

@keyframes successBreath {
  0% {
    box-shadow: 0 0 0 rgba(64, 200, 153, 0);
  }
  45% {
    box-shadow: 0 0 24px rgba(64, 200, 153, 0.2);
  }
  100% {
    box-shadow: 0 0 0 rgba(64, 200, 153, 0);
  }
}

@keyframes errorShake {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-3px);
  }
  50% {
    transform: translateX(3px);
  }
  75% {
    transform: translateX(-2px);
  }
  100% {
    transform: translateX(0);
  }
}

@media (max-width: 640px) {
  .cache-shell {
    padding: 16px;
  }

  .hero-card {
    border-radius: 16px;
    padding: 20px;
  }

  .status-row {
    gap: 8px;
  }

  .inject-btn {
    height: 48px;
    font-size: 15px;
  }
}
</style>
