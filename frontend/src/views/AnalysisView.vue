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
      
      <!-- 对方战力分析 -->
      <div class="team-card enemy">
        <div class="card-header">
          <span class="card-title">
            <span class="title-icon">⚔️</span>
            对方战力分析
          </span>
          <span class="card-avg" v-if="analysis.enemy_avg">
            平均 <strong>{{ analysis.enemy_avg.toFixed(1) }}</strong> 分
          </span>
        </div>
        
        <!-- 横向对比：最强 vs 最弱 -->
        <div class="enemy-comparison" v-if="analysis.enemy_highlights?.god || analysis.enemy_highlights?.noob">
          <div class="compare-card strongest" v-if="analysis.enemy_highlights?.god">
            <div class="compare-header">
              <span class="compare-badge god">🔥 最强威胁</span>
              <span class="compare-tip">重点关照</span>
            </div>
            <div class="compare-body">
              <img 
                v-if="analysis.enemy_highlights.god.champion_id" 
                :src="getChampionIcon(analysis.enemy_highlights.god.champion_id)" 
                class="compare-avatar"
                @error="(e) => e.target.style.display='none'"
              />
              <div class="compare-placeholder" v-else>?</div>
              <div class="compare-name">{{ analysis.enemy_highlights.god.name }}</div>
              <div class="compare-stats">
                <div class="stat-item">
                  <span class="stat-label">胜率</span>
                  <span class="stat-value">{{ analysis.enemy_highlights.god.win_rate }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">KDA</span>
                  <span class="stat-value">{{ analysis.enemy_highlights.god.kda }}</span>
                </div>
                <div class="stat-item" v-if="analysis.enemy_highlights.god.streak >= 2">
                  <span class="stat-label">状态</span>
                  <span class="stat-value streak" :class="analysis.enemy_highlights.god.streak_type">
                    {{ analysis.enemy_highlights.god.streak_type === 'win' ? '🔥' : '💀' }}{{ analysis.enemy_highlights.god.streak }}连
                  </span>
                </div>
              </div>
              <div class="compare-advice warn">⚠️ 小心被Carry，优先针对</div>
            </div>
          </div>
          
          <div class="compare-divider">VS</div>
          
          <div class="compare-card weakest" v-if="analysis.enemy_highlights?.noob">
            <div class="compare-header">
              <span class="compare-badge noob">💀 最弱突破口</span>
              <span class="compare-tip">集火目标</span>
            </div>
            <div class="compare-body">
              <img 
                v-if="analysis.enemy_highlights.noob.champion_id" 
                :src="getChampionIcon(analysis.enemy_highlights.noob.champion_id)" 
                class="compare-avatar"
                @error="(e) => e.target.style.display='none'"
              />
              <div class="compare-placeholder" v-else>?</div>
              <div class="compare-name">{{ analysis.enemy_highlights.noob.name }}</div>
              <div class="compare-stats">
                <div class="stat-item">
                  <span class="stat-label">胜率</span>
                  <span class="stat-value">{{ analysis.enemy_highlights.noob.win_rate }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">KDA</span>
                  <span class="stat-value">{{ analysis.enemy_highlights.noob.kda }}</span>
                </div>
                <div class="stat-item" v-if="analysis.enemy_highlights.noob.streak >= 2">
                  <span class="stat-label">状态</span>
                  <span class="stat-value streak" :class="analysis.enemy_highlights.noob.streak_type">
                    {{ analysis.enemy_highlights.noob.streak_type === 'win' ? '🔥' : '💀' }}{{ analysis.enemy_highlights.noob.streak }}连
                  </span>
                </div>
              </div>
              <div class="compare-advice success">✅ 送分童子，可以针对</div>
            </div>
          </div>
        </div>
        
        <!-- 展开查看全部对手 -->
        <div class="enemy-expand" v-if="analysis.enemy_team && analysis.enemy_team.length > 0">
          <button class="expand-btn" @click="showAllEnemies = !showAllEnemies">
            <span>{{ showAllEnemies ? '收起' : '查看全部对手' }}</span>
            <span class="expand-icon" :class="{ expanded: showAllEnemies }">▼</span>
          </button>
          
          <div class="enemy-list" v-show="showAllEnemies">
            <div 
              v-for="(player, index) in analysis.enemy_team" 
              :key="player.name"
              class="player-row enemy-row"
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
              <span class="player-name">{{ player.name || '未知' }}</span>
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
        
        <div class="no-highlight" v-if="!analysis.enemy_highlights?.god && !analysis.enemy_highlights?.noob">
          {{ analysis.enemy_avg > 0 ? '对方无特别关注目标' : '暂无对方数据 (选人阶段可获取)' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { bridge } from '@/utils/bridge'
import { getChampionIcon } from '@/utils/ddragon'
import EmptyStateCard from '@/components/EmptyStateCard.vue'

const loading = ref(false)
const analysis = ref(null)
const sendStatus = reactive({ msg: '', type: '' })
const ingameTauntEnabled = ref(false)
const showAllEnemies = ref(false)  // 新增：控制展开对方全部队员
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
  animation: pageEnter 0.5s ease;
  position: relative;
}

.analysis-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 250px;
  background: radial-gradient(ellipse at top center, rgba(78, 204, 163, 0.08) 0%, transparent 60%);
  pointer-events: none;
  z-index: 0;
}

@keyframes pageEnter {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  position: relative;
  z-index: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.title-icon {
  font-size: 32px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
  animation: iconPulse 3s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 12px 20px;
  border-radius: var(--border-radius-lg);
  font-size: var(--font-size-sm);
  font-weight: 500;
  background: var(--gradient-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%);
  transition: left 0.5s ease;
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color-light);
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.action-btn:hover:not(:disabled)::before {
  left: 100%;
}

.action-btn.primary {
  background: var(--gradient-primary);
  color: var(--bg-primary);
  border: none;
  box-shadow: var(--shadow-md);
}

.action-btn.primary:hover:not(:disabled) {
  box-shadow: 0 0 30px rgba(78, 204, 163, 0.4), var(--shadow-lg);
  transform: translateY(-3px);
}

.action-btn.taunt {
  background: linear-gradient(135deg, #ff6b35, #e94560);
  color: white;
  border: none;
  box-shadow: var(--shadow-md);
  animation: tauntPulse 2s ease-in-out infinite;
}

@keyframes tauntPulse {
  0%, 100% { box-shadow: 0 0 15px rgba(255, 107, 53, 0.3); }
  50% { box-shadow: 0 0 25px rgba(255, 107, 53, 0.5); }
}

.action-btn.taunt:hover {
  box-shadow: 0 0 40px rgba(255, 107, 53, 0.6), var(--shadow-lg);
  transform: translateY(-4px);
  animation: none;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
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
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--gradient-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-sm);
  box-shadow: var(--shadow-md);
  position: relative;
  z-index: 1;
}

.config-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
  opacity: 0.5;
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
  position: relative;
  z-index: 1;
}

.team-card {
  background: var(--gradient-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-normal);
  position: relative;
  animation: cardEnter 0.5s ease backwards;
}

.team-card:first-child { animation-delay: 0.1s; }
.team-card:last-child { animation-delay: 0.2s; }

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.team-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.team-card:hover {
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-xl), 0 0 40px rgba(0, 0, 0, 0.2);
  transform: translateY(-3px);
}

.team-card:hover::before {
  opacity: 1;
}

.team-card.enemy::before {
  background: var(--gradient-lose);
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
  border: 1px solid transparent;
}

.player-row:hover {
  background: var(--bg-hover);
  border-color: var(--border-color);
  transform: translateX(4px);
}

.player-row.is-me {
  border-left: 4px solid var(--radar-me);
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.02) 100%);
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.1);
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

/* 横向对比布局 */
.enemy-comparison {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  align-items: stretch;
}

.compare-card {
  background: var(--bg-secondary);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  transition: all var(--transition-normal);
  border: 2px solid transparent;
  box-shadow: var(--shadow-md);
}

.compare-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-xl);
}

.compare-card.strongest {
  border-color: rgba(255, 107, 53, 0.3);
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.05) 0%, var(--bg-secondary) 50%);
  animation: godGlow 3s ease-in-out infinite;
}

.compare-card.weakest {
  border-color: rgba(233, 69, 96, 0.3);
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.05) 0%, var(--bg-secondary) 50%);
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.compare-badge {
  padding: 6px 14px;
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.compare-badge.god {
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.25) 0%, rgba(255, 107, 53, 0.15) 100%);
  color: #ff6b35;
  border: 1px solid rgba(255, 107, 53, 0.3);
}

.compare-badge.noob {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.25) 0%, rgba(233, 69, 96, 0.15) 100%);
  color: var(--color-lose);
  border: 1px solid rgba(233, 69, 96, 0.3);
}

.compare-tip {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  font-weight: 500;
}

.compare-body {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.compare-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-normal);
}

.compare-card:hover .compare-avatar {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.4);
}

.compare-card.strongest .compare-avatar {
  border-color: #ff6b35;
}

.compare-card.weakest .compare-avatar {
  border-color: var(--color-lose);
}

.compare-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 3px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xl);
  color: var(--text-muted);
}

.compare-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}

.compare-stats {
  display: flex;
  gap: var(--spacing-lg);
  width: 100%;
  justify-content: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  font-weight: 500;
}

.stat-value {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Consolas', monospace;
}

.stat-value.streak.win {
  color: var(--color-win);
}

.stat-value.streak.lose {
  color: var(--color-lose);
}

.compare-advice {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-align: center;
}

.compare-advice.warn {
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.compare-advice.success {
  background: rgba(78, 204, 163, 0.15);
  color: var(--color-win);
  border: 1px solid rgba(78, 204, 163, 0.3);
}

.compare-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-muted);
  opacity: 0.5;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 展开按钮 */
.enemy-expand {
  padding: var(--spacing-sm) var(--spacing-lg) var(--spacing-lg);
}

.expand-btn {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.expand-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color-light);
}

.expand-icon {
  transition: transform var(--transition-fast);
  font-size: var(--font-size-xs);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.enemy-list {
  margin-top: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.enemy-row {
  border-left: 3px solid var(--border-color);
}

.enemy-row:hover {
  border-left-color: var(--accent-secondary);
}

.highlight-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.highlight-row:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.highlight-row.god {
  border-left: 4px solid #ff6b35;
  background: linear-gradient(90deg, rgba(255, 107, 53, 0.12) 0%, transparent 50%);
  box-shadow: 0 0 20px rgba(255, 107, 53, 0.15);
  animation: godGlow 3s ease-in-out infinite;
}

@keyframes godGlow {
  0%, 100% { box-shadow: 0 0 15px rgba(255, 107, 53, 0.1); }
  50% { box-shadow: 0 0 30px rgba(255, 107, 53, 0.25); }
}

.highlight-row.noob {
  border-left: 4px solid var(--color-lose);
  background: linear-gradient(90deg, rgba(233, 69, 96, 0.12) 0%, transparent 50%);
  box-shadow: 0 0 20px rgba(233, 69, 96, 0.15);
}

.highlight-badge {
  padding: 4px 12px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.highlight-badge.god {
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.25) 0%, rgba(255, 107, 53, 0.15) 100%);
  color: #ff6b35;
  border: 1px solid rgba(255, 107, 53, 0.3);
}

.highlight-badge.noob {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.25) 0%, rgba(233, 69, 96, 0.15) 100%);
  color: var(--color-lose);
  border: 1px solid rgba(233, 69, 96, 0.3);
}

.highlight-name {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.highlight-stats {
  display: flex;
  gap: var(--spacing-lg);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-family: 'Consolas', monospace;
}

.no-highlight {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-xl);
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
