<template>
  <div class="match-view">
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
        <div class="tips">
          <div class="tip-item">
            <span class="tip-icon">💡</span>
            <span>确保已连接到 LOL 客户端</span>
          </div>
          <div class="tip-item">
            <span class="tip-icon">💡</span>
            <span>游戏结束后自动获取数据</span>
          </div>
        </div>
        <button class="test-btn" @click="loadTestData">
          <span>🧪</span>
          加载测试数据
        </button>
      </div>
    </div>
    
    <!-- 有数据时显示 -->
    <template v-else-if="matchStore.currentMatch?.game_id">
      <OverviewBar :match="matchStore.currentMatch" />
      
      <div class="main-content">
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
            <div class="no-selection-content">
              <span class="no-selection-icon">👆</span>
              <p>点击左侧六芒星选择玩家</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="detail-section">
        <DetailTabs :match="matchStore.currentMatch" :team="myTeam" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMatchStore } from '@/stores/match'
import OverviewBar from '@/components/match/OverviewBar.vue'
import RadarChart from '@/components/match/RadarChart.vue'
import PlayerCard from '@/components/match/PlayerCard.vue'
import DetailTabs from '@/components/match/DetailTabs.vue'

const matchStore = useMatchStore()
const activePlayer = ref('')

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

function loadTestData() {
  matchStore.loadMockData()
  const me = myTeam.value.find(p => p.is_me)
  if (me) {
    activePlayer.value = me.summoner_name || me.champion_name
  }
}

onMounted(async () => {
  await matchStore.fetchCurrentMatch()
  const me = myTeam.value.find(p => p.is_me)
  if (me) {
    activePlayer.value = me.summoner_name || me.champion_name
  }
})
</script>

<style scoped>
.match-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--spacing-md);
  gap: var(--spacing-md);
  overflow-y: auto;
  overflow-x: hidden;
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  color: var(--text-secondary);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-secondary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-xl);
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  max-width: 400px;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.empty-content h3 {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.empty-content > p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.tips {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-lg);
}

.tip-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.tip-icon {
  font-size: var(--font-size-md);
}

.test-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--border-radius);
  color: var(--bg-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.test-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--glow-primary), var(--shadow-md);
}

/* 主内容 */
.main-content {
  display: flex;
  gap: var(--spacing-md);
  height: 380px;
  min-height: 380px;
  max-height: 380px;
  flex-shrink: 0;
}

.left-panel {
  flex: 1;
  min-width: 420px;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.right-panel {
  flex: 0 0 340px;
  width: 340px;
  display: flex;
  flex-direction: column;
}

.player-detail {
  flex: 1;
  overflow-y: auto;
}

.no-selection {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
}

.no-selection-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-muted);
}

.no-selection-icon {
  font-size: 32px;
  opacity: 0.5;
}

/* Tab区域 */
.detail-section {
  flex: 1;
  min-height: 200px;
  overflow: hidden;
}

/* 响应式 */
@media (max-width: 900px) {
  .main-content {
    flex-direction: column;
    height: auto;
    min-height: auto;
    max-height: none;
  }
  
  .left-panel {
    flex: none;
    max-width: none;
    min-width: auto;
    min-height: 380px;
  }
  
  .right-panel {
    flex: none;
    width: 100%;
    min-height: 200px;
  }
}
</style>
