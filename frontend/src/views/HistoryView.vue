<template>
  <div class="battle-history-view">
    <div class="battle-shell">
      <BattleProfileHeader
        :profile="matchStore.battleProfile"
        :ranked-solo="battleData.ranked_solo"
        :ranked-flex="battleData.ranked_flex"
        :refreshing="matchStore.battleLoadingStates.refreshing"
        @refresh="handleRefresh"
      />

      <PageStatusBanner
        v-if="matchStore.battleStatus.message"
        :message="matchStore.battleStatus.message"
        :tone="matchStore.battleStatus.type || 'info'"
      />

      <div class="content-grid">
        <aside class="left-column">
          <div class="left-sticky">
            <BattleSummaryPanel :summary="matchStore.battleSummary" />
            <BattleHeroUsagePanel
              :heroes="matchStore.battleHeroUsage"
              :active-champion-id="Number(matchStore.battleFilters.champion_id || 0) || null"
              @select="handleHeroSelect"
            />
            <BattleRecentTeammatesPanel
              :teammates="matchStore.battleRecentTeammates"
              :active-teammate="matchStore.battleFilters.teammate"
              @select="handleTeammateSelect"
            />
          </div>
        </aside>

        <section class="right-column">
          <div class="toolbar-panel">
            <div class="toolbar-head">
              <div>
                <div class="toolbar-title">历史对局</div>
                <div class="toolbar-subtitle">按时间倒序展示，支持模式、结果、时间、英雄与最近队友联动筛选。</div>
              </div>
              <div class="toolbar-stats">
                <div class="toolbar-stat">
                  <span>当前页场次</span>
                  <strong>{{ matchStore.battleHistoryPage.items.length }}</strong>
                </div>
                <div class="toolbar-stat">
                  <span>筛选后总数</span>
                  <strong>{{ matchStore.battleHistoryPage.total }}</strong>
                </div>
              </div>
            </div>

            <div class="toolbar-controls">
              <BattleFilterBar
                :filters="matchStore.battleFilters"
                :modes="availableModes"
                @change="handleFilterChange"
                @reset="handleResetFilters"
              />
              <BattlePagination
                :page="matchStore.battleHistoryPage.page"
                :total-pages="matchStore.battleHistoryPage.total_pages"
                :page-size="matchStore.battleHistoryPage.page_size"
                :total="matchStore.battleHistoryPage.total"
                @page-change="handlePageChange"
                @page-size-change="handlePageSizeChange"
              />
            </div>
          </div>

          <div v-if="matchStore.battleLoadingStates.history && !matchStore.battleHistoryPage.items.length" class="skeleton-list">
            <div v-for="index in 4" :key="`skeleton-${index}`" class="skeleton-card">
              <div class="skeleton shimmer w-12"></div>
              <div class="skeleton-main">
                <div class="skeleton shimmer w-24"></div>
                <div class="skeleton shimmer w-36"></div>
                <div class="skeleton-row">
                  <div class="skeleton shimmer w-16"></div>
                  <div class="skeleton shimmer w-16"></div>
                  <div class="skeleton shimmer w-16"></div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="!matchStore.battleHistoryPage.items.length" class="state-panel empty">
            <div class="state-icon">空</div>
            <div class="empty-title">暂无战绩数据</div>
            <div class="empty-subtitle">完成游戏后会自动记录，并在这里以战绩中心形式展示。</div>
          </div>

          <TransitionGroup v-else name="battle-list" tag="div" class="match-list">
            <BattleMatchCard
              v-for="match in matchStore.battleHistoryPage.items"
              :key="match.game_id"
              :match="match"
              :expanded="matchStore.battleExpandedMatchId === match.game_id"
              :detail="matchStore.getBattleMatchDetailFromCache(match.game_id)"
              :detail-loading="!!matchStore.battleLoadingStates.detailIds[match.game_id]"
              :detail-error="matchStore.battleDetailErrors[match.game_id] || ''"
              @toggle="handleToggleDetail"
              @retry="handleRetryDetail"
            />
          </TransitionGroup>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useMatchStore } from '@/stores/match'
import BattleProfileHeader from '@/components/battle/BattleProfileHeader.vue'
import BattleSummaryPanel from '@/components/battle/BattleSummaryPanel.vue'
import BattleHeroUsagePanel from '@/components/battle/BattleHeroUsagePanel.vue'
import BattleRecentTeammatesPanel from '@/components/battle/BattleRecentTeammatesPanel.vue'
import BattleFilterBar from '@/components/battle/BattleFilterBar.vue'
import BattlePagination from '@/components/battle/BattlePagination.vue'
import BattleMatchCard from '@/components/battle/BattleMatchCard.vue'
import PageStatusBanner from '@/components/common/PageStatusBanner.vue'
import EmptyStateCard from '@/components/EmptyStateCard.vue'

const matchStore = useMatchStore()
const battleData = ref({ ranked_solo: {}, ranked_flex: {} })

const availableModes = computed(() => {
  const set = new Set()
  for (const item of matchStore.battleHistoryPage.items || []) {
    if (item?.game_mode) {
      set.add(item.game_mode)
    }
  }
  return Array.from(set)
})

async function loadBattlePage() {
  const [summaryResult, historyResult] = await Promise.allSettled([
    matchStore.fetchBattleProfileSummary(),
    matchStore.fetchBattleHistoryPage(),
  ])

  if (summaryResult.status === 'fulfilled') {
    battleData.value = summaryResult.value || { ranked_solo: {}, ranked_flex: {} }
  }

  if (historyResult.status === 'rejected') {
    console.error('load battle history failed', historyResult.reason)
  }
}

async function handleRefresh() {
  const summaryResult = await Promise.allSettled([
    matchStore.fetchBattleProfileSummary({ refresh: true }),
  ])
  const payload = summaryResult[0]
  if (payload?.status === 'fulfilled') {
    battleData.value = payload.value || battleData.value
  }
  await matchStore.fetchBattleHistoryPage({ page: matchStore.battleHistoryPage.page || 1 })
}

async function handleFilterChange(patch) {
  matchStore.setBattleFilter(patch)
  await matchStore.fetchBattleHistoryPage({ page: 1 })
}

async function handleResetFilters() {
  matchStore.resetBattleFilters()
  await matchStore.fetchBattleHistoryPage({ page: 1 })
}

async function handleHeroSelect(hero) {
  const nextChampionId = matchStore.battleFilters.champion_id === hero.champion_id ? null : hero.champion_id
  matchStore.setBattleFilter({ champion_id: nextChampionId })
  await matchStore.fetchBattleHistoryPage({ page: 1 })
}

async function handleTeammateSelect(player) {
  const teammateKey = player.identity || player.display_name || player.name || ''
  const nextTeammate = matchStore.battleFilters.teammate === teammateKey ? '' : teammateKey
  matchStore.setBattleFilter({ teammate: nextTeammate })
  await matchStore.fetchBattleHistoryPage({ page: 1 })
}

async function handlePageChange(page) {
  await matchStore.setBattlePage(page)
}

async function handlePageSizeChange(size) {
  await matchStore.setBattlePageSize(size)
}

async function handleToggleDetail(gameId) {
  await matchStore.toggleBattleMatchDetail(gameId)
}

async function handleRetryDetail(gameId) {
  await matchStore.retryBattleMatchDetail(gameId)
}

onMounted(async () => {
  await loadBattlePage()
})
</script>

<style scoped>
.battle-history-view {
  --battle-radius-lg: 16px;
  --battle-radius-md: 12px;
  --battle-surface: rgba(255, 255, 255, 0.03);
  --battle-border-soft: rgba(255, 255, 255, 0.06);
  --battle-shadow: 0 10px 28px rgba(0, 0, 0, 0.2);
  --battle-gap: 10px;
  height: 100%;
  overflow: auto;
  padding: 10px;
  background:
    radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 28%),
    radial-gradient(circle at top left, rgba(78, 204, 163, 0.08), transparent 24%),
    #0a0e1a;
}

.battle-shell {
  display: flex;
  flex-direction: column;
  gap: var(--battle-gap);
  min-height: 100%;
}

.status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 11px;
  border-radius: var(--battle-radius-md);
  border: 1px solid var(--border-color);
  font-size: 12px;
  box-shadow: var(--battle-shadow);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.85;
}

.status-banner.info {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
}

.status-banner.success {
  background: rgba(78, 204, 163, 0.12);
  color: #4ecca3;
}

.status-banner.warning {
  background: rgba(255, 184, 77, 0.12);
  color: #ffb84d;
}

.content-grid {
  display: grid;
  grid-template-columns: 288px minmax(0, 1fr);
  gap: var(--battle-gap);
  min-height: 0;
}

.left-column,
.right-column {
  min-width: 0;
}

.left-sticky {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: var(--battle-gap);
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--battle-gap);
}

.toolbar-panel {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border-radius: var(--battle-radius-lg);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.02));
  border: 1px solid var(--border-color);
  box-shadow: var(--battle-shadow);
  backdrop-filter: blur(10px);
}

.toolbar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--text-primary);
}

.toolbar-subtitle {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.toolbar-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-stat {
  min-width: 94px;
  padding: 8px 10px;
  border-radius: var(--battle-radius-md);
  background: var(--battle-surface);
  border: 1px solid var(--battle-border-soft);
}

.toolbar-stat span {
  display: block;
  color: var(--text-secondary);
  font-size: 11px;
}

.toolbar-stat strong {
  display: block;
  margin-top: 4px;
  color: var(--text-primary);
  font-size: 16px;
}

.toolbar-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.match-list,
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-card {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
  padding: 12px;
  border-radius: var(--battle-radius-lg);
  background: var(--battle-surface);
  border: 1px solid var(--battle-border-soft);
}

.skeleton-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-row {
  display: flex;
  gap: 8px;
}

.skeleton {
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
}

.w-12 { width: 72px; }
.w-16 { width: 64px; }
.w-24 { width: 132px; }
.w-36 { width: 210px; }

.shimmer {
  position: relative;
  overflow: hidden;
}

.shimmer::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
  animation: shimmer 1.6s infinite;
}

.state-panel {
  padding: 32px 18px;
  border-radius: var(--battle-radius-lg);
  border: 1px solid var(--border-color);
  background: var(--battle-surface);
  text-align: center;
  color: var(--text-secondary);
  box-shadow: var(--battle-shadow);
}

.state-panel.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.state-icon {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 800;
}

.empty-title {
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 700;
}

.empty-subtitle {
  font-size: 12px;
  max-width: 340px;
}

.battle-list-enter-active,
.battle-list-leave-active {
  transition: all 0.18s ease;
}

.battle-list-enter-from,
.battle-list-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@keyframes shimmer {
  to {
    transform: translateX(100%);
  }
}

@media (max-width: 1360px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .left-sticky,
  .toolbar-panel {
    position: static;
  }
}
</style>
