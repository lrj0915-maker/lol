<template>
  <div class="analysis-view">
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">📊</span>
        队伍分析
      </h2>
      <div class="header-actions">
        <button class="action-btn" @click="refreshAnalysis" :disabled="loading">
          <span class="btn-icon">🔄</span>
          {{ loading ? '分析中...' : '刷新' }}
        </button>
        <button class="action-btn primary" @click="sendToChat" :disabled="!analysis">
          <span class="btn-icon">📤</span>
          发送到聊天
        </button>
        <button class="action-btn taunt" @click="sendIngameTaunt">
          <span class="btn-icon">🔥</span>
          游戏内嘲讽
        </button>
      </div>
    </div>
    
    <!-- 发送配置 -->
    <div class="config-bar">
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.autoSend" @change="saveChatConfig" />
        <span class="checkmark"></span>
        <span>进入选人自动发送</span>
      </label>
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.sendMyTeam" @change="saveChatConfig" />
        <span class="checkmark"></span>
        <span>发送我方</span>
      </label>
      <label class="config-item">
        <input type="checkbox" v-model="chatConfig.sendEnemy" @change="saveChatConfig" />
        <span class="checkmark"></span>
        <span>发送对方</span>
      </label>
      <label class="config-item taunt">
        <input type="checkbox" v-model="ingameTauntEnabled" @change="setIngameTaunt" />
        <span class="checkmark"></span>
        <span>🔥进游戏自动嘲讽</span>
      </label>
      <div class="config-item hotkey">
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
      <div class="empty-content">
        <div class="empty-icon">📊</div>
        <p class="empty-text">进入选人阶段后自动分析队友战绩</p>
        <p class="empty-hint">或点击"刷新"手动获取当前/最近对局队友</p>
      </div>
    </div>
    
    <!-- 分析结果 -->
    <div class="analysis-content" v-else>
      <!-- 我方队伍 -->
      <div class="team-card">
        <div class="card-header">
          <span class="card-title">
            <span class="title-icon">👥</span>
            我方队伍
          </span>
          <span class="card-avg" v-if="analysis.my_team_avg">
            平均 <strong>{{ analysis.my_team_avg.toFixed(1) }}</strong> 分
          </span>
        </div>
        <div class="player-list">
          <div 
            v-for="(player, index) in analysis.my_team" 
            :key="player.name"
            class="player-row"
            :class="{ 'is-me': player.is_me }"
            :style="{ animationDelay: `${index * 0.05}s` }"
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
              <span class="stat">胜率 <strong>{{ player.win_rate }}%</strong></span>
              <span class="stat">KDA <strong>{{ player.kda }}</strong></span>
              <span class="streak" v-if="player.streak >= 2" :class="player.streak_type">
                {{ player.streak_type === 'win' ? '🔥连胜' : '💀连败' }}{{ player.streak }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 对方关注 -->
      <div class="team-card enemy">
        <div class="card-header">
          <span class="card-title">
            <span class="title-icon">⚔️</span>
            对方关注
          </span>
          <span class="card-avg" v-if="analysis.enemy_avg">
            平均 <strong>{{ analysis.enemy_avg.toFixed(1) }}</strong> 分
          </span>
        </div>
        <div class="enemy-content">
          <div class="highlight-row god" v-if="analysis.enemy_highlights?.god">
            <img 
              v-if="analysis.enemy_highlights.god.champion_id" 
              :src="getChampionIcon(analysis.enemy_highlights.god.champion_id)" 
              class="champion-icon"
              @error="(e) => e.target.style.display='none'"
            />
            <span class="highlight-badge god">🔥 超神</span>
            <span class="highlight-name">{{ analysis.enemy_highlights.god.name }}</span>
            <div class="highlight-stats">
              <span>胜率 {{ analysis.enemy_highlights.god.win_rate }}%</span>
              <span>KDA {{ analysis.enemy_highlights.god.kda }}</span>
            </div>
          </div>
          <div class="highlight-row noob" v-if="analysis.enemy_highlights?.noob">
            <img 
              v-if="analysis.enemy_highlights.noob.champion_id" 
              :src="getChampionIcon(analysis.enemy_highlights.noob.champion_id)" 
              class="champion-icon"
              @error="(e) => e.target.style.display='none'"
            />
            <span class="highlight-badge noob">💀 牛马</span>
            <span class="highlight-name">{{ analysis.enemy_highlights.noob.name }}</span>
            <div class="highlight-stats">
              <span>胜率 {{ analysis.enemy_highlights.noob.win_rate }}%</span>
              <span>KDA {{ analysis.enemy_highlights.noob.kda }}</span>
            </div>
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
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.title-icon {
  font-size: var(--font-size-xl);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 8px 16px;
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 500;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color-light);
}

.action-btn.primary {
  background: var(--gradient-primary);
  color: var(--bg-primary);
  border: none;
}

.action-btn.primary:hover:not(:disabled) {
  box-shadow: var(--glow-primary);
  transform: translateY(-1px);
}

.action-btn.taunt {
  background: linear-gradient(135deg, #ff6b35, #e94560);
  color: white;
  border: none;
}

.action-btn.taunt:hover {
  box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: var(--font-size-md);
}

/* Config Bar */
.config-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
}

.config-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.config-item:hover {
  color: var(--text-primary);
}

.config-item input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.config-item input:checked + .checkmark {
  background: var(--accent-secondary);
  border-color: var(--accent-secondary);
}

.config-item input:checked + .checkmark::after {
  content: '✓';
  color: var(--bg-primary);
  font-size: 12px;
  font-weight: bold;
}

.config-item.taunt span:last-child {
  color: #ff6b35;
}

.config-item.hotkey {
  cursor: default;
}

.hotkey-input {
  width: 44px;
  padding: 4px 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  color: var(--accent-secondary);
  font-size: var(--font-size-sm);
  text-align: center;
  font-weight: 600;
}

.send-status {
  margin-left: auto;
  padding: 4px 12px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.send-status.success {
  color: var(--color-win);
  background: rgba(78, 204, 163, 0.15);
}

.send-status.error {
  color: var(--color-lose);
  background: rgba(233, 69, 96, 0.15);
}

/* Empty State */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl) * 2;
}

.empty-content {
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
  opacity: 0.3;
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

/* Analysis Content */
.analysis-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.team-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: 600;
  font-size: var(--font-size-md);
}

.card-avg {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.card-avg strong {
  color: var(--accent-secondary);
}

.player-list {
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.player-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  transition: all var(--transition-fast);
  animation: fadeIn 0.3s ease forwards;
  opacity: 0;
}

.player-row:hover {
  background: var(--bg-hover);
}

.player-row.is-me {
  border-left: 3px solid var(--radar-me);
  background: rgba(255, 215, 0, 0.05);
}

.champion-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-color);
}

.champion-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.rank-badge {
  padding: 2px 10px;
  border-radius: var(--border-radius-sm);
  font-weight: 600;
  font-size: var(--font-size-xs);
  min-width: 50px;
  text-align: center;
}

.rank-badge.rank-S { background: rgba(255, 107, 53, 0.2); color: #ff6b35; }
.rank-badge.rank-A { background: rgba(255, 215, 0, 0.2); color: #ffd700; }
.rank-badge.rank-B { background: rgba(150, 150, 150, 0.2); color: #999; }
.rank-badge.rank-C { background: rgba(88, 166, 255, 0.2); color: #58a6ff; }
.rank-badge.rank-D { background: rgba(233, 69, 96, 0.2); color: #e94560; }

.player-name {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.me-tag {
  color: var(--radar-me);
  margin-left: 4px;
  text-shadow: 0 0 10px var(--radar-me);
}

.player-stats {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.stat strong {
  color: var(--text-primary);
}

.streak {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-weight: 500;
}

.streak.win {
  background: rgba(78, 204, 163, 0.2);
  color: var(--color-win);
}

.streak.lose {
  background: rgba(233, 69, 96, 0.2);
  color: var(--color-lose);
}

/* Enemy Content */
.enemy-content {
  padding: var(--spacing-sm);
}

.highlight-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-xs);
  transition: all var(--transition-fast);
}

.highlight-row:hover {
  background: var(--bg-hover);
}

.highlight-row.god {
  border-left: 3px solid #ff6b35;
}

.highlight-row.noob {
  border-left: 3px solid var(--color-lose);
}

.highlight-badge {
  padding: 2px 10px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.highlight-badge.god {
  background: rgba(255, 107, 53, 0.2);
  color: #ff6b35;
}

.highlight-badge.noob {
  background: rgba(233, 69, 96, 0.2);
  color: var(--color-lose);
}

.highlight-name {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.highlight-stats {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.no-highlight {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-lg);
  font-size: var(--font-size-sm);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
