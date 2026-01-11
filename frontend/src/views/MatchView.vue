<template>
  <div class="match-view">
    <!-- 加载状态 -->
    <div class="loading-state" v-if="matchStore.loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!matchStore.currentMatch || !matchStore.currentMatch.game_id">
      <div class="empty-icon">📊</div>
      <h3>暂无战绩数据</h3>
      <p>完成一局游戏后，这里会显示详细的战绩分析</p>
      <div class="tips">
        <p>💡 确保已连接到 LOL 客户端</p>
        <p>💡 游戏结束后自动获取数据</p>
      </div>
      <button class="test-btn" @click="loadTestData">🧪 加载测试数据</button>
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
            <p>点击左侧小六芒星选择玩家</p>
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

// 当前选中的玩家
const selectedPlayer = computed(() => {
  if (!activePlayer.value) return null
  // 先按 summoner_name 找，找不到再按 champion_name 找
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
  // 默认选中自己
  const me = myTeam.value.find(p => p.is_me)
  if (me) {
    activePlayer.value = me.summoner_name || me.champion_name
  }
}

onMounted(async () => {
  await matchStore.fetchCurrentMatch()
  // 默认选中自己
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
  padding: var(--spacing-sm);
  gap: var(--spacing-sm);
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
  width: 40px;
  height: 40px;
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.empty-state p {
  margin-bottom: var(--spacing-lg);
}

.tips {
  background: var(--bg-card);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius);
}

.tips p {
  margin: var(--spacing-xs) 0;
  font-size: var(--font-size-sm);
}

.test-btn {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary));
  border: none;
  border-radius: var(--border-radius);
  color: var(--text-primary);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(200, 155, 60, 0.3);
}

/* 主内容 - 固定高度 */
.main-content {
  display: flex;
  gap: var(--spacing-sm);
  height: 380px;
  min-height: 380px;
  max-height: 380px;
  flex-shrink: 0;
}

.left-panel {
  flex: 1;
  min-width: 420px;
  background: var(--bg-card);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.right-panel {
  flex: 0 0 320px;
  width: 320px;
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
  border-radius: var(--border-radius);
  color: var(--text-muted);
}

/* Tab区域 - 自适应剩余空间 */
.detail-section {
  flex: 1;
  min-height: 200px;
  overflow: hidden;
}

/* 响应式 - 小屏幕时上下布局 */
@media (max-width: 900px) {
  .main-content {
    flex-direction: column;
    min-height: auto;
  }
  
  .left-panel {
    flex: none;
    max-width: none;
    min-width: auto;
    min-height: 380px;
  }
  
  .right-panel {
    min-height: 200px;
  }
}
</style>
