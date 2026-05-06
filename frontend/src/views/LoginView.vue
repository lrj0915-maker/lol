<template>
  <div class="login-view">
    <!-- 顶部栏 -->
    <div class="topbar">
      <div class="topbar-brand">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        游戏助手
      </div>
      <div class="connection-status">
        <span class="status-dot" :class="{ connected: appStore.connected }"></span>
        {{ appStore.connected ? '已连接' : '未连接' }}
      </div>
    </div>

    <!-- 验证码横幅 -->
    <div v-if="showCaptchaHint" class="captcha-banner">
      <span>⚠️ 需要验证码，请在桌面完成验证</span>
      <button class="captcha-btn" @click="focusCaptcha">找回验证码窗口</button>
    </div>

    <!-- 主体 -->
    <div class="main">
      <!-- 左栏：账号列表 -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="sidebar-title">我的账号 <span class="accent">({{ sortedAccounts.length }})</span></div>
          <div class="filter-row">
            <input v-model.trim="searchKeyword" placeholder="搜索账号..." class="filter-input" />
            <select v-model="serverFilter" class="filter-select">
              <option value="ALL">全部大区</option>
              <option v-for="(name, idx) in servers" :key="idx" :value="String(idx)">{{ name }}</option>
            </select>
          </div>
        </div>

        <div class="account-list">
          <div
            v-for="account in sortedAccounts"
            :key="account.id"
            class="account-item"
            :class="{ active: selectedId === account.id, banned: !!account.ban_info && getBanTag(account) }"
            @click="selectAccount(account)"
          >
            <div class="account-avatar" :class="{ banned: !!account.ban_info && getBanTag(account) }">
              {{ (getAccountDisplayName(account) || '?')[0].toUpperCase() }}
            </div>
            <div class="account-info">
              <div class="account-name">{{ getAccountDisplayName(account) }}</div>
              <div class="account-meta">
                {{ servers[account.server_index] || '未知' }}
                <span class="sep">·</span>
                {{ account.last_login ? formatLastLogin(account.last_login) : '' }}
                <span v-if="getBanTag(account)" class="ban-tag">{{ getBanTag(account) }}</span>
              </div>
            </div>
            <button class="account-delete" @click.stop="handleDeleteAccount(account)" title="删除账号">×</button>
          </div>
        </div>

        <div v-if="!sortedAccounts.length" class="empty-state">
          <p>没有匹配的账号</p>
        </div>
      </aside>

      <!-- 右栏 -->
      <main class="content">
        <!-- 登录面板 -->
        <div class="login-panel">
          <div class="panel-title">账号登录</div>
          <div class="login-form">
            <input v-model.trim="quickCredential" placeholder="QQ----密码" class="form-input" @keydown.enter="handleLogin" />
            <select v-model.number="quickServerIndex" class="form-select">
              <option v-for="(name, idx) in servers" :key="idx" :value="idx">{{ name }}</option>
            </select>
            <div class="form-actions">
              <button class="btn" @click="handleQuickSave" :disabled="!quickQQ || !quickPW">保存账号</button>
              <button class="btn btn-primary" @click="handleLogin" :disabled="isLoggingIn || (!quickQQ && !selectedAccount)">
                <span v-if="isLoggingIn" class="spinner"></span>
                {{ isLoggingIn ? '登录中...' : '▶ 执行登录' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 已选账号区 -->
        <div v-if="selectedAccount && !isLoggingIn" class="selected-zone">
          <div class="zone-label">已选账号</div>
          <div class="selected-name">{{ getAccountDisplayName(selectedAccount) }}</div>
          <div class="selected-meta">{{ servers[selectedAccount.server_index] || '未知' }}</div>
          <div v-if="getBanTag(selectedAccount)" class="ban-warn">
            <span class="dot"></span>
            {{ getBanTag(selectedAccount) }}
          </div>
        </div>

        <!-- 工具按钮 -->
        <div class="tool-row">
          <button class="tool-btn" :class="toolStates.addFriends" @click="runTool('addFriends')" :disabled="!appStore.connected || toolStates.addFriends === 'loading'" :title="toolTips.addFriends">
            <span v-if="toolStates.addFriends === 'idle'">✦</span>
            <span v-else-if="toolStates.addFriends === 'loading'" class="spinner"></span>
            <span v-else-if="toolStates.addFriends === 'success'" class="icon-success">✓</span>
            <span v-else-if="toolStates.addFriends === 'fail'" class="icon-fail">✗</span>
            <span>好友管理</span>
            <span v-if="toolMessages.addFriends" class="tool-msg">{{ toolMessages.addFriends }}</span>
          </button>
          <button class="tool-btn" :class="toolStates.deleteFriends" @click="runTool('deleteFriends')" :disabled="!appStore.connected || toolStates.deleteFriends === 'loading'" :title="toolTips.deleteFriends">
            <span v-if="toolStates.deleteFriends === 'idle'">✦</span>
            <span v-else-if="toolStates.deleteFriends === 'loading'" class="spinner"></span>
            <span v-else-if="toolStates.deleteFriends === 'success'" class="icon-success">✓</span>
            <span v-else-if="toolStates.deleteFriends === 'fail'" class="icon-fail">✗</span>
            <span>清理好友</span>
            <span v-if="toolMessages.deleteFriends" class="tool-msg">{{ toolMessages.deleteFriends }}</span>
          </button>
          <button class="tool-btn" :class="toolStates.disenchant" @click="runTool('disenchant')" :disabled="!appStore.connected || toolStates.disenchant === 'loading'" :title="toolTips.disenchant">
            <span v-if="toolStates.disenchant === 'idle'">✦</span>
            <span v-else-if="toolStates.disenchant === 'loading'" class="spinner"></span>
            <span v-else-if="toolStates.disenchant === 'success'" class="icon-success">✓</span>
            <span v-else-if="toolStates.disenchant === 'fail'" class="icon-fail">✗</span>
            <span>分解精粹</span>
            <span v-if="toolMessages.disenchant" class="tool-msg">{{ toolMessages.disenchant }}</span>
          </button>
          <button class="tool-btn danger" @click="handleCloseGame" title="强制关闭游戏和登录器">
            <span>✕</span> 关闭游戏
          </button>
        </div>

        <!-- 进度条 -->
        <div v-if="isLoggingIn && loginStatus.progress > 0" class="progress-section">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: loginStatus.progress + '%' }"></div>
          </div>
          <div class="progress-info">
            <span class="progress-phase">{{ loginStatus.message }}</span>
            <span class="progress-pct">{{ loginStatus.progress }}%</span>
          </div>
        </div>
      </main>
    </div>

    <!-- Toast -->
    <div v-if="feedbackMessage" class="toast" :class="{ success: feedbackSuccess }">
      {{ feedbackMessage }}
    </div>
  </div></template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { formatRelativeTime } from '@/utils/format'
import bridge from '@/utils/bridge'

const appStore = useAppStore()

const servers = ['艾欧尼亚', '祖安', '诺克萨斯', '班德尔城', '皮尔特沃夫', '战争学院', '巨神峰', '雷瑟守备', '钢铁烈阳', '裁决之地', '黑色玫瑰', '暗影岛', '均衡教派', '水晶之痕', '影流', '守望之海', '征服之海', '卡拉曼达', '皮城警备', '比尔吉沃特', '德玛西亚', '弗雷尔卓德', '无畏先锋', '恕瑞玛', '扭曲丛林', '巨龙之巢', '教育网专区', '男爵领域']

const accounts = ref([])
const selectedId = ref('')
const searchKeyword = ref('')
const serverFilter = ref('ALL')
const quickCredential = ref('')
const quickServerIndex = ref(18)
const loginStatus = ref({ status: 'idle', phase: 'idle', message: '', progress: 0 })
const statusTimer = ref(null)
const feedbackMessage = ref('')
const feedbackSuccess = ref(true)
const feedbackTimer = ref(null)
const loggingAccountId = ref('')

const toolStates = ref({
  addFriends: 'idle',
  deleteFriends: 'idle',
  disenchant: 'idle',
})

const toolMessages = ref({
  addFriends: '',
  deleteFriends: '',
  disenchant: '',
})

const toolTips = {
  addFriends: '按设置页中的白名单好友执行添加',
  deleteFriends: '保留设置页白名单，其余好友删除',
  disenchant: '将所有英雄碎片分解为蓝色精粹',
}

// 关闭游戏按钮防抖
let closeGameTimer = null

// 游戏阶段监听
const lastGamePhase = ref('')

async function handleCloseGame() {
  if (closeGameTimer) return
  closeGameTimer = setTimeout(() => {
    closeGameTimer = null
  }, 5000) // 5秒内防重复触发
  stopPolling()
  loggingAccountId.value = ''
  loginStatus.value = { status: 'idle', phase: 'idle', message: '', progress: 0 }
  try {
    const result = await bridge.forceCloseGame()
    showFeedback(result?.success, result?.message || '已关闭')
  } catch (error) {
    console.error('[LoginView] handleCloseGame error:', error)
    showFeedback(false, '关闭失败')
  }
}

const selectedAccount = computed(() => {
  const list = Array.isArray(accounts.value) ? accounts.value : []
  return list.find(a => a.id === selectedId.value) || null
})
const isLoggingIn = computed(() => loginStatus.value.status === 'logging_in')
const showCaptchaHint = computed(() => loginStatus.value.phase === 'waiting_captcha')

const quickQQ = computed(() => (quickCredential.value.split('----')[0] || '').trim())
const quickPW = computed(() => (quickCredential.value.split('----')[1] || '').trim())

const filteredAccounts = computed(() => {
  let result = Array.isArray(accounts.value) ? accounts.value : []

  if (serverFilter.value !== 'ALL') {
    result = result.filter(a => String(a.server_index) === serverFilter.value)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(a => {
      const text = [a.qq, a.nickname, a.summoner_name].join(' ').toLowerCase()
      return text.includes(keyword)
    })
  }

  return result
})

const sortedAccounts = computed(() => {
  return [...filteredAccounts.value].sort((a, b) => {
    const aBanned = !!a.ban_info
    const bBanned = !!b.ban_info
    if (aBanned !== bBanned) return aBanned ? 1 : -1

    const aTime = a.last_login || 0
    const bTime = b.last_login || 0
    return bTime - aTime
  })
})

function getAccountDisplayName(account) {
  return account.summoner_name || account.nickname || account.qq || '未获取'
}

function formatLastLogin(timestamp) {
  if (!timestamp) return ''
  return formatRelativeTime(timestamp)
}

function getBanTag(account) {
  if (!account.ban_info) return ''
  // 优先用 ban_end 判断剩余天数
  if (account.ban_end) {
    try {
      const end = new Date(account.ban_end)
      end.setHours(0, 0, 0, 0)
      const now = new Date()
      now.setHours(0, 0, 0, 0)
      const diff = Math.ceil((end - now) / 86400000)
      if (diff <= 0) return '' // 已解封
      if (account.ban_info.includes('永久') || account.ban_info.includes('permanent')) return '永久封号'
      return '封号 ' + diff + '天'
    } catch (e) {}
  }
  // 从 ban_info 文本解析日期
  const m = account.ban_info.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/)
  if (m) {
    const end = new Date(m[1], m[2] - 1, m[3])
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    const diff = Math.ceil((end - now) / 86400000)
    if (diff > 0) return '封号 ' + diff + '天'
    return ''
  }
  if (account.ban_info.includes('永久') || account.ban_info.includes('permanent')) return '永久封号'
  return '封号'
}

function selectAccount(account) {
  selectedId.value = account.id
}

// 统一的登录入口：优先用选中账号，否则用快速登录区信息
async function handleLogin() {
  if (isLoggingIn.value) return

  if (selectedAccount.value) {
    // 账号列表登录
    loggingAccountId.value = selectedId.value
    loginStatus.value = { status: 'logging_in', phase: 'preparing', message: '准备登录...', progress: 5 }
    startPolling()
    try {
      const result = await bridge.startLogin('', '', 0, '', selectedAccount.value.id)
      if (!result?.success) {
        stopPolling()
        loggingAccountId.value = ''
        loginStatus.value = { status: 'failed', phase: 'failed', message: result?.message || '登录失败', progress: 0 }
        showFeedback(false, result?.message || '登录失败')
      }
    } catch (error) {
      console.error('[LoginView] handleLogin error:', error)
      stopPolling()
      loggingAccountId.value = ''
      loginStatus.value = { status: 'idle', phase: 'idle', message: '', progress: 0 }
      showFeedback(false, '登录调用失败')
    }
  } else if (quickQQ.value && quickPW.value) {
    // 快速登录：先保存账号（如果不存在），并捕获返回的 id
    let targetAccountId = ''
    try {
      const existingAccount = accounts.value.find(a => a.qq === quickQQ.value)
      if (existingAccount) {
        targetAccountId = existingAccount.id
      } else {
        const result = await bridge.addAccount(quickQQ.value, quickPW.value, '', quickServerIndex.value, '')
        if (result?.id) {
          targetAccountId = result.id
        } else if (result?.success === false) {
          showFeedback(false, result.message || '保存账号失败')
          return
        }
        await loadAccounts()
      }
    } catch (error) {
      console.error('[LoginView] handleLogin - save account error:', error)
    }
    loggingAccountId.value = 'quick'
    loginStatus.value = { status: 'logging_in', phase: 'preparing', message: '准备登录...', progress: 5 }
    startPolling()
    try {
      const result = await bridge.startLogin(quickQQ.value, quickPW.value, quickServerIndex.value, '', targetAccountId)
      if (!result?.success) {
        stopPolling()
        loggingAccountId.value = ''
        loginStatus.value = { status: 'failed', phase: 'failed', message: result?.message || '登录失败', progress: 0 }
        showFeedback(false, result?.message || '登录失败')
      }
    } catch (error) {
      console.error('[LoginView] handleLogin error:', error)
      stopPolling()
      loggingAccountId.value = ''
      loginStatus.value = { status: 'idle', phase: 'idle', message: '', progress: 0 }
      showFeedback(false, '登录调用失败')
    }
  }
}

async function handleQuickSave() {
  if (!quickQQ.value || !quickPW.value) return
  
  try {
    const result = await bridge.addAccount(quickQQ.value, quickPW.value, '', quickServerIndex.value, '')
    if (result?.success) {
      showFeedback(true, '账号已保存')
      quickCredential.value = ''
      await loadAccounts()
    } else {
      showFeedback(false, result?.message || '保存失败')
    }
  } catch (error) {
    console.error('[LoginView] handleQuickSave error:', error)
    showFeedback(false, '保存失败')
  }
}

// 并行执行三个工具操作
async function runAllTools() {
  await Promise.all([
    runTool('addFriends', true),
    runTool('deleteFriends', true),
    runTool('disenchant', true),
  ])
}

// 执行单个工具
function formatToolSummary(tool, result) {
  if (!result) return ''

  if (tool === 'addFriends') {
    const total = Number(result.total || (Number(result.added || 0) + Number(result.failed || 0)))
    const added = Number(result.added || 0)
    const failed = Number(result.failed || 0)
    if (failed > 0) return `添加 ${added}/${total} 个 / 失败 ${failed} 个`
    return `添加 ${added}/${total} 个`
  }

  if (tool === 'deleteFriends') {
    const deleted = Number(result.deleted || 0)
    const skipped = Number(result.skipped || 0)
    const failed = Number(result.failed || 0)
    const parts = [`删除 ${deleted} 个`]
    if (skipped > 0) parts.push(`保留 ${skipped} 个`)
    if (failed > 0) parts.push(`失败 ${failed} 个`)
    return parts.join(' / ')
  }

  if (tool === 'disenchant') {
    const count = Number(result.count || 0)
    const totalValue = Number(result.total_value || 0)
    if (totalValue > 0) return `分解 ${count} 个 / ${totalValue} 精粹`
    return `分解 ${count} 个`
  }

  return result.message || ''
}

async function runTool(tool, isAuto = false) {
  if (toolStates.value[tool] === 'loading') return

  toolStates.value[tool] = 'loading'
  toolMessages.value[tool] = ''

  try {
    let result
    if (tool === 'addFriends') {
      result = await bridge.triggerAddFriends()
    } else if (tool === 'deleteFriends') {
      result = await bridge.deleteAllFriends()
    } else if (tool === 'disenchant') {
      result = await bridge.disenchantAllShards()
    }

    if (result?.success) {
      toolStates.value[tool] = 'success'
      const summary = formatToolSummary(tool, result)
      toolMessages.value[tool] = isAuto && summary ? `自动 · ${summary}` : (summary || result.message || '完成')
    } else {
      toolStates.value[tool] = 'fail'
      toolMessages.value[tool] = formatToolSummary(tool, result) || result?.message || '失败'
    }

    // 3秒后自动恢复 idle
    setTimeout(() => {
      if (toolStates.value[tool] !== 'loading') {
        toolStates.value[tool] = 'idle'
        toolMessages.value[tool] = ''
      }
    }, 3000)
  } catch (error) {
    toolStates.value[tool] = 'fail'
    toolMessages.value[tool] = formatToolSummary(tool, null) || '执行异常'
    setTimeout(() => {
      toolStates.value[tool] = 'idle'
      toolMessages.value[tool] = ''
    }, 3000)
  }
}

async function handleDeleteAccount(account) {
  if (!confirm(`确定要删除账号 "${getAccountDisplayName(account)}" 吗？`)) {
    return
  }
  
  try {
    const result = await bridge.deleteAccount(account.id)
    if (result?.success) {
      showFeedback(true, '账号已删除')
      if (selectedId.value === account.id) {
        selectedId.value = ''
      }
      await loadAccounts()
    } else {
      showFeedback(false, result?.message || '删除失败')
    }
  } catch (error) {
    console.error('[LoginView] handleDeleteAccount error:', error)
    showFeedback(false, '删除失败')
  }
}

async function focusCaptcha() {
  const result = await bridge.focusLoginCaptcha()
  showFeedback(result?.success, result?.message || '操作完成')
}

function showFeedback(success, message) {
  feedbackSuccess.value = !!success
  feedbackMessage.value = message
  if (feedbackTimer.value) clearTimeout(feedbackTimer.value)
  feedbackTimer.value = setTimeout(() => {
    feedbackMessage.value = ''
  }, 3000)
}

async function pollStatus() {
  try {
    const [payload, phase] = await Promise.all([
      bridge.getLoginStatus(),
      bridge.getGameflowPhase(),
    ])

    if (payload && typeof payload.status === 'string') {
      loginStatus.value = { ...loginStatus.value, ...payload }

      if (payload.status === 'success') {
        if (payload.phase === 'connected') {
          // 客户端真正连接成功
          stopPolling()
          loggingAccountId.value = ''
          await loadAccounts()
          showFeedback(true, '登录成功')
          setTimeout(() => {
            loginStatus.value = { status: 'idle', phase: 'idle', message: '', progress: 0 }
          }, 2000)
        } else if (payload.phase === 'connecting_client') {
          // 登录器成功但客户端还在连接中，继续轮询
          loginStatus.value.message = payload.message || '登录成功，正在连接客户端...'
        }
        return
      }

      if (['failed', 'banned', 'password_leaked'].includes(payload.status)) {
        stopPolling()
        loggingAccountId.value = ''
        await loadAccounts()

        if (payload.status === 'banned') {
          showFeedback(false, '账号封号')
          bridge.forceCloseGame()
        } else if (payload.status === 'password_leaked') {
          showFeedback(false, payload.message || '检测到密码泄露，已关闭登录器')
          bridge.forceCloseGame()
        } else {
          // failed：显示具体失败原因，并关闭登录器
          const msg = payload.message || '登录失败'
          showFeedback(false, msg)
          bridge.forceCloseGame()
        }

        setTimeout(() => {
          loginStatus.value = { status: 'idle', phase: 'idle', message: '', progress: 0 }
        }, 2000)
      }
    }
  } catch (error) {
    console.error('[LoginView] pollStatus error:', error)
  }
}

function startPolling() {
  stopPolling()
  statusTimer.value = setInterval(pollStatus, 800)
}

function stopPolling() {
  if (statusTimer.value) {
    clearInterval(statusTimer.value)
    statusTimer.value = null
  }
}

async function loadAccounts() {
  try {
    const result = await bridge.getAccounts()
    if (Array.isArray(result)) {
      accounts.value = result
    } else if (result && Array.isArray(result.data)) {
      accounts.value = result.data
    } else {
      accounts.value = []
      console.warn('[LoginView] getAccounts 返回非数组:', result)
    }

    if (selectedId.value && !accounts.value.some(account => account.id === selectedId.value)) {
      selectedId.value = ''
    }
  } catch (error) {
    console.error('[LoginView] loadAccounts error:', error)
    accounts.value = []
    selectedId.value = ''
  }
}

function handlePostLoginTools(event) {
  const { tool, state, result } = event.detail
  if (!tool || !state) return

  // 更新对应工具状态
  toolStates.value[tool] = state
  if (result) {
    toolMessages.value[tool] = formatToolSummary(tool, result)
  }

  // 3秒后自动恢复 idle（loading 状态不自动恢复）
  if (state !== 'loading') {
    setTimeout(() => {
      if (toolStates.value[tool] === state) {
        toolStates.value[tool] = 'idle'
        toolMessages.value[tool] = ''
      }
    }, 3000)
  }
}

onMounted(async () => {
  await loadAccounts()
  // 启动时就查询当前阶段，避免错过已经在选人阶段的情况
  try {
    const phase = await bridge.getGameflowPhase()
    if (phase) lastGamePhase.value = phase
  } catch (e) {
    // ignore
  }
  window.addEventListener('post-login-tools', handlePostLoginTools)
})

onUnmounted(() => {
  stopPolling()
  if (feedbackTimer.value) clearTimeout(feedbackTimer.value)
  window.removeEventListener('post-login-tools', handlePostLoginTools)
})
</script>

<style scoped>
.login-view{height:100%;display:flex;flex-direction:column;background:#070b14;color:#e8edf5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
.login-view::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(78,204,179,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(78,204,179,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}

/* Topbar */
.topbar{display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;border-bottom:1px solid rgba(78,204,179,.25);background:rgba(13,21,37,.9);backdrop-filter:blur(12px);flex-shrink:0;z-index:10}
.topbar-brand{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:700;letter-spacing:.05em;color:#4ECCB3}
.topbar-brand svg{width:18px;height:18px}
.connection-status{display:flex;align-items:center;gap:8px;font-size:13px;color:#5a6a7a}
.status-dot{width:8px;height:8px;border-radius:50%;background:#64748b;transition:background .3s}
.status-dot.connected{background:#4ade80;box-shadow:0 0 8px rgba(74,222,128,.6)}

/* Captcha banner */
.captcha-banner{display:flex;justify-content:space-between;align-items:center;padding:10px 24px;background:rgba(245,158,11,.12);border-bottom:1px solid rgba(245,158,11,.25);color:#fbbf24;font-size:13px;flex-shrink:0}
.captcha-btn{height:28px;padding:0 12px;border-radius:6px;border:1px solid rgba(245,158,11,.4);background:rgba(245,158,11,.15);color:#fbbf24;font-size:12px;font-weight:600;cursor:pointer}

/* Main layout */
.main{display:flex;flex:1;min-height:0;position:relative;z-index:1}

/* Sidebar */
.sidebar{width:300px;min-width:260px;border-right:1px solid rgba(78,204,179,.25);display:flex;flex-direction:column;background:rgba(7,11,20,.5)}
.sidebar-header{padding:14px 16px 10px;border-bottom:1px solid rgba(78,204,179,.1);flex-shrink:0}
.sidebar-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#5a6a7a;margin-bottom:10px}
.sidebar-title .accent{color:#4ECCB3}
.filter-row{display:flex;gap:8px}
.filter-input,.filter-select{height:32px;padding:0 10px;border-radius:8px;border:1px solid rgba(78,204,179,.2);background:rgba(13,21,37,.8);color:#e8edf5;font-size:13px;outline:none;transition:border-color .2s}
.filter-input{flex:1}
.filter-select{width:100px}
.filter-input:focus,.filter-select:focus{border-color:#4ECCB3}

/* Account list */
.account-list{flex:1;overflow-y:auto;padding:8px 10px}
.account-item{display:flex;align-items:center;gap:10px;padding:10px 10px 10px 12px;border-radius:10px;border:1px solid transparent;cursor:pointer;transition:all .15s;position:relative;margin-bottom:4px}
.account-item::before{content:'';position:absolute;left:0;top:6px;bottom:6px;width:3px;border-radius:0 2px 2px 0;background:transparent;transition:background .15s}
.account-item:hover{background:rgba(78,204,179,.05);border-color:rgba(78,204,179,.12)}
.account-item.active{background:rgba(78,204,179,.12);border-color:rgba(78,204,179,.35)}
.account-item.active::before{background:#4ECCB3}
.account-item.banned{border-color:rgba(255,107,107,.18)}
.account-item.banned::before{background:#ff6b6b}
.account-avatar{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#1a2a4a,#0d1a30);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#4ECCB3;flex-shrink:0;border:1px solid rgba(78,204,179,.25);transition:all .15s}
.account-item.banned .account-avatar{border-color:rgba(255,107,107,.35);color:#ff6b66}
.account-info{flex:1;min-width:0}
.account-name{font-size:13px;font-weight:600;color:#e8edf5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}
.account-meta{display:flex;align-items:center;gap:4px;font-size:11px;color:#5a6a7a;flex-wrap:wrap}
.account-meta .sep{color:#3a4a5a}
.ban-tag{display:inline-flex;align-items:center;padding:1px 6px;border-radius:4px;background:rgba(255,107,107,.12);border:1px solid rgba(255,107,107,.3);color:#ff8080;font-size:10px;font-weight:700;white-space:nowrap}
.account-delete{width:24px;height:24px;border-radius:6px;border:none;background:transparent;color:#3a4a5a;cursor:pointer;opacity:0;transition:all .15s;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.account-item:hover .account-delete{opacity:1}
.account-delete:hover{background:rgba(255,107,107,.15);color:#ff6b6b}
.empty-state{padding:40px 20px;text-align:center;color:#3a4a5a;font-size:13px}

/* Content area */
.content{flex:1;display:flex;flex-direction:column;padding:20px 28px;gap:14px;min-width:0;min-height:200px;overflow-y:auto}

/* Login panel */
.login-panel{background:#0d1525;border:1px solid rgba(78,204,179,.25);border-radius:14px;padding:20px 22px;flex-shrink:0}
.panel-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#5a6a7a;margin-bottom:14px}

/* Form */
.login-form{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.form-input,.form-select{height:42px;padding:0 14px;border-radius:8px;border:1px solid rgba(78,204,179,.2);background:rgba(7,11,20,.8);color:#e8edf5;font-size:14px;outline:none;transition:border-color .2s,box-shadow .2s;width:100%}
.form-input:focus,.form-select:focus{border-color:#4ECCB3;box-shadow:0 0 0 3px rgba(78,204,179,.08)}
.form-input::placeholder{color:#3a4a5a}
.form-actions{grid-column:1/-1;display:flex;gap:8px;margin-top:2px}

/* Buttons */
.btn{height:40px;padding:0 18px;border-radius:8px;border:1px solid rgba(78,204,179,.25);background:transparent;color:#5a6a7a;font-size:13px;font-weight:600;cursor:pointer;transition:all .15s;white-space:nowrap;flex-shrink:0;display:flex;align-items:center;gap:6px}
.btn:hover{border-color:#4ECCB3;color:#4ECCB3;background:rgba(78,204,179,.08)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-primary{background:#4ECCB3;color:#070b14;border-color:#4ECCB3;font-weight:700;flex:1;justify-content:center}
.btn-primary:hover{background:#3db89e;box-shadow:0 4px 16px rgba(78,204,179,.25);transform:translateY(-1px)}
.btn-primary:active{transform:translateY(0)}

/* Selected zone */
.selected-zone{background:#0d1525;border:1px solid rgba(78,204,179,.25);border-radius:14px;padding:14px 18px;flex-shrink:0}
.zone-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#5a6a7a;margin-bottom:8px}
.selected-name{font-size:14px;font-weight:700;color:#e8edf5}
.selected-meta{font-size:12px;color:#5a6a7a;margin-top:2px}
.ban-warn{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:6px;background:rgba(255,107,107,.12);border:1px solid rgba(255,107,107,.3);color:#ff8080;font-size:12px;font-weight:700;margin-top:8px}
.ban-warn .dot{width:6px;height:6px;border-radius:50%;background:#ff6b6b;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* Tool row */
.tool-row{display:flex;gap:8px;flex-wrap:wrap}
.tool-btn{display:flex;align-items:center;gap:6px;height:36px;padding:0 14px;border-radius:8px;border:1px solid rgba(78,204,179,.2);background:#0d1525;color:#5a6a7a;font-size:13px;font-weight:500;cursor:pointer;transition:all .15s;white-space:nowrap}
.tool-btn:hover{border-color:#4ECCB3;color:#4ECCB3;background:rgba(78,204,179,.08);transform:translateY(-1px)}
.tool-btn:disabled{opacity:.4;cursor:not-allowed}
.tool-btn.success{border-color:rgba(74,222,128,.5);background:rgba(74,222,128,.1);color:#86efac}
.tool-btn.fail{border-color:rgba(255,107,107,.5);background:rgba(255,107,107,.1);color:#ff8080}
.tool-btn.danger{border-color:rgba(255,107,107,.3);color:#ff8080}
.tool-btn.danger:hover{border-color:#ff6b6b;background:rgba(255,107,107,.1)}
.tool-msg{font-size:11px;font-weight:400;opacity:.75;max-width:160px;overflow:hidden;text-overflow:ellipsis}
.icon-success{color:#86efac}
.icon-fail{color:#ff8080}
.spinner{width:12px;height:12px;border:2px solid rgba(78,204,179,.3);border-top-color:#4ECCB3;border-radius:50%;animation:spin .6s linear infinite;flex-shrink:0}
@keyframes spin{to{transform:rotate(360deg)}}

/* Progress */
.progress-section{flex-shrink:0}
.progress-track{height:6px;background:rgba(78,204,179,.1);border-radius:3px;overflow:hidden;margin-bottom:8px}
.progress-fill{height:100%;background:linear-gradient(90deg,#4ECCB3,#3db89e);border-radius:3px;transition:width .4s ease;position:relative}
.progress-fill::after{content:'';position:absolute;right:0;top:0;bottom:0;width:20px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.35));animation:shimmer 1.5s infinite}
@keyframes shimmer{0%,100%{opacity:.3}50%{opacity:1}}
.progress-info{display:flex;justify-content:space-between;align-items:center}
.progress-phase{font-size:12px;color:#5a6a7a}
.progress-pct{font-size:12px;font-weight:700;color:#4ECCB3;font-variant-numeric:tabular-nums}

/* Toast */
.toast{position:fixed;bottom:24px;right:24px;padding:12px 18px;border-radius:10px;background:rgba(255,107,107,.95);color:#fff;font-size:13px;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.5);animation:slideIn .25s ease;z-index:999}
.toast.success{background:rgba(34,197,94,.95)}
@keyframes slideIn{from{transform:translateX(40px);opacity:0}to{transform:translateX(0);opacity:1}}

/* Scrollbar */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(78,204,179,.2);border-radius:2px}
</style>
