<template>
  <div class="match-view">
    <!-- 游戏中：顶部 Tab 栏 -->
    <div class="live-tab-bar" v-if="isInGame">
      <button
        class="live-tab" :class="{ active: activeTab === 'live' }"
        @click="activeTab = 'live'"
      >
        <span class="live-dot"></span> 实时对局
      </button>
      <button
        class="live-tab" :class="{ active: activeTab === 'match' }"
        @click="activeTab = 'match'"
      >
        上局战绩
      </button>
      <span class="game-timer" v-if="activeTab === 'live' && matchStore.liveGameData">
        ⏱️ {{ formatGameTime(matchStore.liveGameData.game_time) }}
      </span>
    </div>

    <!-- 实时对局面板 -->
    <LiveGamePanel
      v-if="isInGame && activeTab === 'live'"
      :data="matchStore.liveGameData"
    />

    <!-- 以下是原有逻辑（非实时 Tab 或非游戏中） -->
    <template v-else>
      <!-- 加载状态 -->
      <div class="loading-state" v-if="matchStore.loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else-if="!matchStore.currentMatch || !matchStore.currentMatch.game_id">
        <div class="empty-content">
          <div class="empty-icon">📊</div>
          <h3>暂无战绩数据</h3>
          <p>完成一局游戏后，这里会显示详细的战绩分析</p>
          <button v-if="matchStore.canUseMockData" class="test-btn" @click="loadTestData">
            <span>🧪</span>
            加载测试数据
          </button>
        </div>
      </div>

      <!-- 有数据时显示 -->
      <div class="data-content" v-else>
        <OverviewBar :match="matchStore.currentMatch" />
        <div class="middle-section">
          <div class="left-panel">
            <RadarChart
              :radar-data="radarData"
              :active-player="activePlayer"
              @select="activePlayer = $event"
            />
          </div>
          <div class="right-panel">
            <div class="player-detail" v-if="selectedPlayer">
              <PlayerCard
                :player="selectedPlayer"
                :team-totals="teamTotals"
                :is-active="true"
                :game-length="matchStore.currentMatch?.game_length"
              />
            </div>
            <div class="no-selection" v-else>
              <span class="no-selection-icon">👆</span>
              <p>点击左侧选择玩家</p>
            </div>
          </div>
        </div>
        <div class="detail-section">
          <DetailTabs :match="matchStore.currentMatch" :team="myTeam" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref, watch } from 'vue'
import { useMatchStore } from '@/stores/match'
import { useAppStore } from '@/stores/app'
import OverviewBar from '@/components/match/OverviewBar.vue'
import PlayerCard from '@/components/match/PlayerCard.vue'
import DetailTabs from '@/components/match/DetailTabs.vue'
import LiveGamePanel from '@/components/match/LiveGamePanel.vue'
import EmptyStateCard from '@/components/EmptyStateCard.vue'

const RadarChart = defineAsyncComponent(() => import('@/components/match/RadarChart.vue'))

const matchStore = useMatchStore()
const appStore = useAppStore()
const activePlayer = ref('')
const activeTab = ref('live')

const isInGame = computed(() => appStore.gamePhase === 'InProgress')

const myTeam = computed(() => matchStore.currentMatch?.my_team || [])
const radarData = computed(() => matchStore.currentMatch?.radar_data || [])

const selectedPlayer = computed(() => {
  if (!activePlayer.value) return null
  return myTeam.value.find(p => p.summoner_name === activePlayer.value) ||
         myTeam.value.find(p => p.champion_name === activePlayer.value)
})

const teamTotals = computed(() => {
  const team = myTeam.value
  return {
    damage: team.reduce((s, p) => s + (p.total_damage || 0), 0),
    tank: team.reduce((s, p) => s + (p.damage_taken || 0), 0),
    gold: team.reduce((s, p) => s + (p.gold_earned || 0), 0),
    vision: team.reduce((s, p) => s + (p.vision_score || 0), 0),
    kills: team.reduce((s, p) => s + (p.kills || 0), 0),
    deaths: team.reduce((s, p) => s + (p.deaths || 0), 0)
  }
})

function formatGameTime(seconds) {
  if (!seconds) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function loadTestData() {
  matchStore.loadMockData()
  const me = myTeam.value.find(p => p.is_me)
  if (me) {
    activePlayer.value = me.summoner_name || me.champion_name
  }
}

// 监听游戏状态变化，控制轮询
watch(isInGame, (inGame, wasInGame) => {
  if (inGame) {
    activeTab.value = 'live'
    matchStore.startLivePolling()
  } else {
    matchStore.stopLivePolling()
    // 游戏结束 → 自动切到上局战绩
    if (wasInGame) {
      activeTab.value = 'match'
    }
  }
}, { immediate: true })

onMounted(async () => {
  // 从历史记录跳转过来时，currentMatch 已设置，不覆盖
  if (!matchStore.consumeFromHistory()) {
    await matchStore.fetchCurrentMatch()
  }
  const me = myTeam.value.find(p => p.is_me)
  if (me) {
    activePlayer.value = me.summoner_name || me.champion_name
  }
})

onUnmounted(() => {
  matchStore.stopLivePolling()
})
</script>

<style scoped>
.match-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 顶部 Tab 栏 */
.live-tab-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: linear-gradient(180deg, rgba(15,21,37,0.95), rgba(10,14,26,0.95));
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  position: relative;
}

.live-tab-bar::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(78,204,163,0.3), transparent);
}

.live-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.live-tab::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(78,204,163,0.15) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.2s;
}

.live-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.1);
}

.live-tab:hover::before { opacity: 1; }

.live-tab.active {
  background: rgba(78, 204, 163, 0.12);
  border-color: rgba(78, 204, 163, 0.35);
  color: var(--accent-secondary);
  box-shadow: 0 0 12px rgba(78,204,163,0.15), inset 0 0 12px rgba(78,204,163,0.05);
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e94560;
  animation: livePulse 1.5s ease-in-out infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 4px #e94560; }
  50% { opacity: 0.4; box-shadow: 0 0 8px #e94560; }
}

.game-timer {
  margin-left: auto;
  font-size: 14px;
  font-family: 'Consolas', monospace;
  color: var(--text-secondary);
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary);
}

.spinner {
  width: 44px;
  height: 44px;
  border: 3px solid rgba(78,204,163,0.15);
  border-top-color: var(--accent-secondary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  box-shadow: 0 0 20px rgba(78,204,163,0.1);
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 50px 60px;
  background: linear-gradient(135deg, rgba(17,24,39,0.9), rgba(15,21,37,0.95));
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(78, 204, 163, 0.2);
  box-shadow:
    0 8px 32px rgba(0,0,0,0.4),
    0 0 40px rgba(78, 204, 163, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.empty-content:hover {
  transform: translateY(-5px) scale(1.02);
  border-color: rgba(78, 204, 163, 0.4);
  box-shadow:
    0 12px 48px rgba(0,0,0,0.5),
    0 0 60px rgba(78, 204, 163, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.empty-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(78,204,163,0.6), rgba(88,166,255,0.6), transparent);
  animation: borderFlow 3s linear infinite;
}

@keyframes borderFlow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.empty-content::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 50%, rgba(78, 204, 163, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 20px;
  filter: drop-shadow(0 8px 16px rgba(0,0,0,0.4));
  animation: emptyFloat 3s ease-in-out infinite, emptyRotate 6s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

@keyframes emptyFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-10px) scale(1.05); }
}

@keyframes emptyRotate {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-5deg); }
  75% { transform: rotate(5deg); }
}

.empty-content h3 {
  font-size: 22px;
  color: var(--text-primary);
  margin-bottom: 12px;
  font-weight: 700;
  position: relative;
  z-index: 1;
}

.empty-content > p {
  color: var(--text-secondary);
  margin-bottom: 24px;
  font-size: 15px;
  line-height: 1.6;
  position: relative;
  z-index: 1;
}

.test-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--gradient-primary);
  border: none;
  border-radius: 10px;
  color: var(--bg-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 15px rgba(78, 204, 163, 0.3);
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.test-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.test-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(78, 204, 163, 0.5);
}

.test-btn:hover::before {
  opacity: 1;
}

.test-btn:active {
  transform: translateY(-1px) scale(1.02);
}

/* 有数据时的容器 */
.data-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 10px;
  gap: 10px;
  overflow: hidden;
  animation: fadeIn 0.4s ease;
}

.middle-section {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.left-panel {
  flex: 1;
  min-width: 0;
  background: linear-gradient(135deg, rgba(17,24,39,0.85), rgba(15,21,37,0.85));
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: border-color 0.3s;
  position: relative;
}

.left-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(78,204,163,0.2), transparent);
}

.left-panel:hover { border-color: rgba(78,204,163,0.2); }

.right-panel { width: 280px; flex-shrink: 0; }
.player-detail { height: 100%; overflow-y: auto; }

.no-selection {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: linear-gradient(135deg, rgba(17,24,39,0.85), rgba(15,21,37,0.85));
  border-radius: 12px;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  position: relative;
  overflow: hidden;
}

.no-selection::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(78,204,163,0.2), transparent);
}

.no-selection-icon {
  font-size: 36px;
  animation: emptyFloat 3s ease-in-out infinite;
}

.no-selection p { font-size: 13px; }

.detail-section {
  height: 280px;
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
}
</style>
