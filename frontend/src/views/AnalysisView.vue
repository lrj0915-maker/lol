<template>
  <div class="analysis-view">
    <div class="page-header">
      <h2>📊 队伍分析</h2>
      <div class="header-actions">
        <button class="action-btn" @click="refreshAnalysis" :disabled="loading">
          {{ loading ? '分析中...' : '🔄 刷新' }}
        </button>
        <button class="action-btn primary" @click="sendToChat" :disabled="!analysis">
          📤 发送到聊天
        </button>
        <button class="action-btn taunt-btn" @click="sendIngameTaunt">
          🔥 游戏内嘲讽
        </button>
      </div>
    </div>
    
    <!-- 发送配置 -->
    <div class="config-bar">
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.autoSend" @change="saveChatConfig" />
        <span>进入选人自动发送</span>
      </label>
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.sendMyTeam" @change="saveChatConfig" />
        <span>发送我方</span>
      </label>
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.sendEnemy" @change="saveChatConfig" />
        <span>发送对方</span>
      </label>
      <label class="config-item taunt">
        <input type="checkbox" v-model="ingameTauntEnabled" @change="setIngameTaunt" />
        <span>🔥进游戏自动嘲讽</span>
      </label>
      <div class="config-item">
        <span>快捷键:</span>
        <input 
          type="text" 
          v-model="chatConfig.hotkey" 
          class="hotkey-input"
          @keydown="captureHotkey"
          readonly
        />
      </div>
      <span class="send-status" :class="sendStatus.type" v-if="sendStatus.msg">
        {{ sendStatus.msg }}
      </span>
    </div>
    
    <!-- 无数据状态 -->
    <div class="empty-state" v-if="!analysis">
      <div class="empty-icon">📊</div>
      <p>进入选人阶段后自动分析队友战绩</p>
      <p class="tip">或点击"刷新"手动获取当前/最近对局队友</p>
    </div>
    
    <!-- 分析结果 -->
    <div class="analysis-content" v-else>
      <!-- 我方队伍 -->
      <div class="team-card">
        <div class="card-header">
          <span class="card-title">👥 我方队伍</span>
          <span class="card-avg" v-if="analysis.my_team_avg">
            平均 {{ analysis.my_team_avg.toFixed(1) }}分
          </span>
        </div>
        <div class="player-list">
          <div 
            v-for="player in analysis.my_team" 
            :key="player.name"
            class="player-row"
            :class="{ 'is-me': player.is_me }"
          >
            <img 
              v-if="player.champion_id" 
              :src="getChampionIcon(player.champion_id)" 
              class="champion-icon"
              @error="(e) => e.target.style.display='none'"
            />
            <span v-else class="champion-placeholder">?</span>
            <span class="rank-badge" :class="`rank-${player.rank}`">
              {{ getRankIcon(player.rank) }}{{ player.rank }}
            </span>
            <span class="player-name">
              {{ player.name || '未知' }}
              <span v-if="player.is_me" class="me-tag">★</span>
            </span>
            <div class="player-stats">
              <span>胜率 {{ player.win_rate }}%</span>
              <span>KDA {{ player.kda }}</span>
              <span class="streak" v-if="player.streak >= 2" :class="player.streak_type">
                {{ player.streak_type === 'win' ? '连胜' : '连败' }}{{ player.streak }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 对方关注 -->
      <div class="team-card enemy">
        <div class="card-header">
          <span class="card-title">⚔️ 对方关注</span>
          <span class="card-avg" v-if="analysis.enemy_avg">
            平均 {{ analysis.enemy_avg.toFixed(1) }}分
          </span>
        </div>
        <div class="enemy-content">
          <div class="highlight-row" v-if="analysis.enemy_highlights?.god">
            <img 
              v-if="analysis.enemy_highlights.god.champion_id" 
              :src="getChampionIcon(analysis.enemy_highlights.god.champion_id)" 
              class="champion-icon"
              @error="(e) => e.target.style.display='none'"
            />
            <span class="highlight-badge god">🔥 超神</span>
            <span class="highlight-name">{{ analysis.enemy_highlights.god.name }}</span>
            <span class="highlight-stat">胜率 {{ analysis.enemy_highlights.god.win_rate }}%</span>
            <span class="highlight-stat">KDA {{ analysis.enemy_highlights.god.kda }}</span>
          </div>
          <div class="highlight-row" v-if="analysis.enemy_highlights?.noob">
            <img 
              v-if="analysis.enemy_highlights.noob.champion_id" 
              :src="getChampionIcon(analysis.enemy_highlights.noob.champion_id)" 
              class="champion-icon"
              @error="(e) => e.target.style.display='none'"
            />
            <span class="highlight-badge noob">💀 牛马</span>
            <span class="highlight-name">{{ analysis.enemy_highlights.noob.name }}</span>
            <span class="highlight-stat">胜率 {{ analysis.enemy_highlights.noob.win_rate }}%</span>
            <span class="highlight-stat">KDA {{ analysis.enemy_highlights.noob.kda }}</span>
          </div>
          <div class="no-highlight" v-if="!analysis.enemy_highlights?.god && !analysis.enemy_highlights?.noob">
            {{ analysis.enemy_avg > 0 ? '对方无特别关注目标' : '暂无对方数据 (选人阶段可获取)' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { bridge } from '@/utils/bridge'
import { champions } from '@/data/champions'

const loading = ref(false)
const analysis = ref(null)
const sendStatus = reactive({ msg: '', type: '' })
const ingameTauntEnabled = ref(false)
const chatConfig = reactive({
  autoSend: false,
  sendMyTeam: true,
  sendEnemy: true,
  hotkey: 'F1'
})

function getRankIcon(rank) {
  const icons = { S: '🔥', A: '⭐', B: '😐', C: '😰', D: '💀' }
  return icons[rank] || ''
}

function getChampionIcon(championId) {
  const champ = champions.find(c => c.id === championId)
  if (champ) {
    return `https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/${champ.key}.png`
  }
  return ''
}

function showStatus(msg, type = 'info') {
  sendStatus.msg = msg
  sendStatus.type = type
  setTimeout(() => { sendStatus.msg = '' }, 3000)
}

async function refreshAnalysis() {
  loading.value = true
  try {
    await bridge.refreshTeamAnalysis()
    setTimeout(async () => {
      const result = await bridge.getTeamAnalysis()
      if (result) analysis.value = result
      loading.value = false
    }, 2000)
  } catch (e) {
    loading.value = false
  }
}

async function sendToChat() {
  const result = await bridge.sendAnalysisToChat()
  if (result?.success) {
    showStatus('✓ 已发送', 'success')
  } else {
    showStatus('✗ ' + (result?.error || '发送失败'), 'error')
  }
}

async function sendIngameTaunt() {
  showStatus('正在发送...', 'info')
  const result = await bridge.sendIngameTaunt()
  if (result?.success) {
    showStatus('✓ 嘲讽已发送', 'success')
  } else {
    showStatus('✗ 发送失败: ' + (result?.error || '未知错误'), 'error')
  }
}

async function loadChatConfig() {
  const config = await bridge.getChatConfig()
  if (config) {
    chatConfig.autoSend = config.auto_send
    chatConfig.sendMyTeam = config.send_my_team
    chatConfig.sendEnemy = config.send_enemy
    chatConfig.hotkey = config.hotkey || 'F1'
  }
  
  const ingameStatus = await bridge.getIngameChatStatus()
  if (ingameStatus) {
    ingameTauntEnabled.value = ingameStatus.enabled
  }
}

async function setIngameTaunt() {
  await bridge.setIngameChat(ingameTauntEnabled.value)
}

async function saveChatConfig() {
  await bridge.setChatConfig({
    auto_send: chatConfig.autoSend,
    send_my_team: chatConfig.sendMyTeam,
    send_enemy: chatConfig.sendEnemy,
    hotkey: chatConfig.hotkey
  })
}

function captureHotkey(e) {
  e.preventDefault()
  const key = e.key.toUpperCase()
  if (key.length === 1 || key.startsWith('F')) {
    chatConfig.hotkey = key
    saveChatConfig()
  }
}

function onTeamAnalysis(e) {
  analysis.value = e.detail
  loading.value = false
  if (chatConfig.autoSend) {
    sendToChat()
  }
}

onMounted(async () => {
  await loadChatConfig()
  const result = await bridge.getTeamAnalysis()
  if (result) analysis.value = result
  window.addEventListener('team-analysis', onTeamAnalysis)
})

onUnmounted(() => {
  window.removeEventListener('team-analysis', onTeamAnalysis)
})
</script>

<style scoped>
.analysis-view {
  padding: var(--spacing-md);
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.page-header h2 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  padding: 6px 14px;
  border-radius: var(--border-radius);
  font-size: var(--font-size-xs);
  background: var(--bg-card);
  color: var(--text-secondary);
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.action-btn.primary {
  background: var(--accent-secondary);
  color: var(--bg-primary);
}

.action-btn.taunt-btn {
  background: #ff6b35;
  color: white;
}

.action-btn.taunt-btn:hover {
  background: #ff8555;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-xs);
}

.config-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
}

.config-item input[type="checkbox"] {
  accent-color: var(--accent-secondary);
}

.config-item.taunt span {
  color: #ff6b35;
}

.hotkey-input {
  width: 40px;
  padding: 2px 6px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--accent-secondary);
  font-size: 11px;
  text-align: center;
}

.send-status {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.send-status.success { color: #4ecca3; background: rgba(78,204,163,0.15); }
.send-status.error { color: #e94560; background: rgba(233,69,96,0.15); }

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.empty-icon { font-size: 48px; margin-bottom: var(--spacing-md); opacity: 0.5; }
.empty-state .tip { font-size: var(--font-size-xs); color: var(--text-muted); margin-top: var(--spacing-sm); }

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.team-card {
  background: var(--bg-card);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(0,0,0,0.2);
}

.card-title { font-weight: 600; font-size: var(--font-size-sm); }
.card-avg { font-size: var(--font-size-xs); color: var(--text-secondary); }

.player-list {
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 8px 10px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.player-row.is-me { border-left: 3px solid var(--accent-secondary); }

.champion-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-color);
}

.champion-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--text-muted);
}

.rank-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  min-width: 45px;
  text-align: center;
}

.rank-badge.rank-S { background: rgba(255,100,50,0.2); color: #ff6b35; }
.rank-badge.rank-A { background: rgba(255,215,0,0.2); color: #ffd700; }
.rank-badge.rank-B { background: rgba(150,150,150,0.2); color: #999; }
.rank-badge.rank-C { background: rgba(100,150,200,0.2); color: #6496c8; }
.rank-badge.rank-D { background: rgba(200,50,50,0.2); color: #c83232; }

.player-name { flex: 1; font-size: var(--font-size-sm); }
.me-tag { color: var(--accent-secondary); margin-left: 4px; }

.player-stats {
  display: flex;
  gap: var(--spacing-sm);
  font-size: 11px;
  color: var(--text-secondary);
}

.streak {
  padding: 1px 6px;
  border-radius: 3px;
}

.streak.win { background: rgba(78,204,163,0.2); color: #4ecca3; }
.streak.lose { background: rgba(233,69,96,0.2); color: #e94560; }

.enemy-content { padding: var(--spacing-sm); }

.highlight-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 8px 10px;
  background: var(--bg-secondary);
  border-radius: 6px;
  margin-bottom: 6px;
}

.highlight-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.highlight-badge.god { background: rgba(255,100,50,0.2); color: #ff6b35; }
.highlight-badge.noob { background: rgba(233,69,96,0.2); color: #e94560; }

.highlight-name { flex: 1; font-size: var(--font-size-sm); }
.highlight-stat { font-size: 11px; color: var(--text-secondary); }

.no-highlight {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-md);
  font-size: var(--font-size-xs);
}
</style>
