<template>
  <div ref="viewRef" class="runes-view">
    <!-- 状态横幅 -->
    <div v-if="showStatusBanner" class="status-banner">
      <span v-if="runesStatus.is_updating">⏳ 符文数据正在更新...</span>
      <span v-else-if="runesStatus.last_update_error">⚠️ 更新失败：{{ runesStatus.last_update_error }}</span>
      <span v-else-if="runesStatus.is_stale">📦 数据已过期（{{ runesStatus.days_old }} 天），建议刷新</span>
    </div>

    <div v-if="isLoading" class="loading-bar">加载中... {{ loadProgress }}%</div>
    <EmptyStateCard v-else-if="emptyStateConfig" v-bind="emptyStateConfig" />

    <div v-else class="main-layout" :class="{ 'is-revealing': visualLoadStep < 4 }">
      <!-- ========== 左栏：英雄面板 ========== -->
      <aside class="left-panel">
        <!-- 英雄头像 + 名字 -->
        <div class="champion-card">
          <img
            v-if="selectedChampion"
            :src="getChampionIcon(selectedChampion.id)"
            class="champion-avatar"
            loading="eager"
            decoding="async"
            fetchpriority="high"
          />
          <div class="champion-info">
            <div class="champion-name">{{ selectedChampion?.name || '符文推荐' }}</div>
            <div class="champion-sub">
              {{ selectedChampion?.nameEn || '' }}
              <span v-if="overview.version"> · {{ overview.version }}</span>
            </div>
            <div v-if="tierLabel" class="champion-tier">{{ tierLabel }}</div>
          </div>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
          <input
            v-model="searchKeyword"
            placeholder="搜索英雄..."
            @focus="searchFocused = true"
            @blur="onSearchBlur"
          />
          <div v-if="searchFocused && debouncedSearchKeyword && searchResults.length" class="dropdown">
            <div
              v-for="champion in searchResults"
              :key="champion.id"
              class="dropdown-item"
              @mousedown="selectChampion(champion, 'manual')"
            >
              <img :src="getChampionIcon(champion.id)" class="search-icon" loading="lazy" decoding="async" />
              <div>
                <div class="search-name">{{ champion.name }}</div>
                <div class="search-sub">{{ champion.nameEn }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分路选择 -->
        <div class="position-bar">
          <button
            v-for="position in availablePositions"
            :key="position"
            class="pos-btn"
            :class="{ active: selectedPosition === position }"
            @click="selectedPosition = position"
            @mouseenter="preLoadPosition(position)"
          >
            {{ getPositionName(position) }}
          </button>
        </div>

        <!-- 英雄数据 -->
        <div class="stats-list" :class="{ skeleton: !revealChampionStats }">
          <div class="stat-row"><span>胜率</span><strong :class="winRateClass(overviewPos.win_rate)">{{ revealChampionStats ? formatPercent(overviewPos.win_rate, 2) : '—' }}</strong></div>
          <div class="stat-row"><span>登场率</span><strong>{{ revealChampionStats ? formatPercent(overviewPos.pick_rate, 2) : '—' }}</strong></div>
          <div class="stat-row"><span>禁用率</span><strong>{{ revealChampionStats ? formatPercent(overviewPos.ban_rate, 2) : '—' }}</strong></div>
          <div class="stat-row"><span>KDA</span><strong>{{ revealChampionStats ? formatKda(overview.value.average_stats?.kda) : '—' }}</strong></div>
          <div class="stat-row"><span>全位置登场率</span><strong>{{ revealChampionStats ? formatPercent(overview.value.average_stats?.pick_rate, 2) : '—' }}</strong></div>
          <div class="stat-row"><span>全位置禁用率</span><strong>{{ revealChampionStats ? formatPercent(overview.value.average_stats?.ban_rate, 2) : '—' }}</strong></div>
          <div class="stat-row"><span>样本</span><strong>{{ revealChampionStats ? formatNumber(overviewPos.play || totalGames) : '—' }}</strong></div>
          <div class="stat-row highlight"><span>来源</span><strong>OP.GG</strong></div>
          <div class="stat-row dim"><span>更新</span><strong>{{ revealChampionStats ? dataAge : '加载中' }}</strong></div>
        </div>

        <!-- 出装推荐 -->
        <div class="items-section" :class="{ skeleton: !revealItemBlocks }">
          <div class="section-title items-title">出装推荐</div>
          <div class="item-group" v-if="revealItemBlocks && currentPositionData?.starter_items?.length">
            <span class="item-label">出门</span>
            <div v-for="(item, idx) in currentPositionData.starter_items.slice(0, 2)" :key="`starter-${idx}`" class="item-icons">
              <img v-for="id in item.ids" :key="id" :src="getItemIcon(id)" class="item-icon" loading="lazy" decoding="async" />
              <span class="item-wr">{{ formatWinRate(item) }}</span>
            </div>
          </div>
          <div class="item-group" v-if="revealItemBlocks && currentPositionData?.boots?.length">
            <span class="item-label">鞋子</span>
            <div v-for="(item, idx) in currentPositionData.boots.slice(0, 2)" :key="`boots-${idx}`" class="item-icons">
              <img v-for="id in item.ids" :key="id" :src="getItemIcon(id)" class="item-icon" loading="lazy" decoding="async" />
              <span class="item-wr">{{ formatWinRate(item) }}</span>
            </div>
          </div>
          <div class="item-group" v-if="revealItemBlocks && currentPositionData?.core_items?.length">
            <span class="item-label">核心</span>
            <div v-for="(item, idx) in currentPositionData.core_items.slice(0, 2)" :key="`core-${idx}`" class="item-icons">
              <img v-for="id in item.ids" :key="id" :src="getItemIcon(id)" class="item-icon" loading="lazy" decoding="async" />
              <span class="item-wr">{{ formatWinRate(item) }}</span>
            </div>
          </div>
          <div v-if="revealItemBlocks && !currentPositionData?.starter_items?.length && !currentPositionData?.boots?.length && !currentPositionData?.core_items?.length" class="muted">暂无出装数据</div>
        </div>

        <!-- 克制关系 -->
        <div class="counters-section" v-if="countersPreview.length">
          <div class="section-title">克制关系</div>
          <div v-for="counter in countersPreview.slice(0, 5)" :key="counter.champion_id" class="counter-row">
            <img :src="getChampionIcon(counter.champion_id)" class="counter-icon" loading="lazy" decoding="async" />
            <span class="counter-name">{{ getChampionName(counter.champion_id) }}</span>
            <span class="counter-wr">{{ formatWinRate(counter) }}</span>
          </div>
        </div>

        <!-- 对局时长胜率 -->
        <div class="gamelength-section" v-if="gameLengths.length">
          <div class="section-title">对局时长胜率</div>
          <div v-for="gl in gameLengths" :key="gl.minutes" class="gl-row">
            <span class="gl-label">{{ gl.label }}</span>
            <div class="gl-bar-wrap">
              <div class="gl-bar" :style="{ width: Math.min(gl.rate * 100, 100) + '%' }" :class="winRateClass(gl.rate)"></div>
            </div>
            <span class="gl-val" :class="winRateClass(gl.rate)">{{ (gl.rate * 100).toFixed(1) }}%</span>
          </div>
        </div>

        <!-- 版本趋势 -->
        <div class="trends-section" v-if="versionTrends.length">
          <div class="section-title">版本胜率趋势</div>
          <div class="trend-list">
            <div v-for="(t, i) in versionTrends" :key="t.version" class="trend-row">
              <span class="trend-ver">{{ t.version }}</span>
              <span class="trend-rate" :class="winRateClass(t.rate)">{{ (t.rate * 100).toFixed(1) }}%</span>
              <span v-if="i < versionTrends.length - 1 && versionTrends[i+1].rate > 0" class="trend-arrow" :class="t.rate > versionTrends[i+1].rate ? 'up' : t.rate < versionTrends[i+1].rate ? 'down' : ''">
                {{ t.rate > versionTrends[i+1].rate ? '▲' : t.rate < versionTrends[i+1].rate ? '▼' : '—' }}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ========== 右栏：符文推荐 ========== -->
      <main class="right-panel" @scroll.passive="onViewScroll">
        <!-- 操作栏 -->
        <div class="action-bar">
          <div class="sort-group">
            <button class="sort-btn" :class="{ active: sortBy === 'winRate' }" @click="sortBy = 'winRate'">按胜率</button>
            <button class="sort-btn" :class="{ active: sortBy === 'games' }" @click="sortBy = 'games'">按场次</button>
          </div>
          <div class="action-btns">
            <button class="act-btn" :disabled="isRefreshing || isLoading || autoPositionRefreshing || !selectedChampion" @click="refreshCurrentChampionData">
              {{ isRefreshing ? '⏳' : '🔄' }} 刷新
            </button>
            <button class="act-btn" :disabled="serverRefreshing || runesStatus.is_updating" @click="refreshRunesOnServer">
              {{ serverRefreshing ? '⏳' : '📦' }} 全量
            </button>
            <button
              class="act-btn primary"
              :disabled="isLoading || !selectedChampion || !currentRuneConfigs.length"
              @click="applyTopRecommendation"
            >
              ⚡ 一键应用 #1
            </button>
          </div>
        </div>

        <!-- 召唤师技能 -->
        <div class="section" v-if="currentPositionData?.summoner_spells?.length">
          <div class="section-title">召唤师技能</div>
          <SummonerSpellCard
            v-for="spell in currentPositionData.summoner_spells.slice(0,3)"
            :key="spell.spell_ids?.join('')"
            :spell="spell"
          />
        </div>

        <!-- 技能加点 -->
        <div class="section" v-if="currentPositionData?.skills?.length">
          <div class="section-title">技能加点</div>
          <SkillOrderCard
            v-for="skill in currentPositionData.skills.slice(0,3)"
            :key="skill.order"
            :skill="skill"
          />
        </div>

        <!-- 符文配置列表 -->
        <div class="rune-list" :class="{ skeleton: !revealRuneCards }">
          <div
            v-for="(config, idx) in currentRuneConfigs"
            :key="`${selectedChampion?.id}-${selectedPosition}-${idx}`"
            class="rune-card-wrap"
          >
            <div v-if="!revealRuneCards" class="card-skeleton" />
            <RuneConfigCard
              v-else
              :config="getPrimaryBuild(config)"
              :rank="idx + 1"
              :champion-id="String(selectedChampion?.id || '')"
              :champion-name="selectedChampion?.name || ''"
              :position="selectedPosition"
              :total-games="totalGames"
              @applied="onCardApplied"
            />
          </div>
        </div>

        <div v-if="autoPositionRefreshing" class="muted refreshing-hint">正在补充 {{ getPositionName(selectedPosition) }} 分路最新符文...</div>
      </main>
    </div>

    <div v-if="toast.show" class="toast" :class="toast.type">{{ toast.message }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { champions, getChampionById, searchChampions } from '@/data/champions'
import { getChampionIcon, getItemIcon } from '@/utils/ddragon'
import {
  buildCountersPreview,
  buildGameLengths,
  buildVersionTrends,
  formatCompactNumber as formatNumber,
  formatKda,
  formatRatePercent as formatPercent,
  formatWinRate,
  selectPrimaryBuild,
  sortRuneConfigs,
  winRateClass,
} from '@/utils/runesViewHelpers'
import { POSITION_NAMES, formatRelativeTime } from '@/utils/format'
import { getTreeById, preloadRuneIcons } from '@/data/runes'
import bridge from '@/utils/bridge'
import { useAppStore } from '@/stores/app'
import { useFavorites } from '@/composables/useFavorites'
import { useRunesData } from '@/composables/useRunesData'
import { useUserPreferences } from '@/composables/useUserPreferences'
import EmptyStateCard from '@/components/EmptyStateCard.vue'
import RuneConfigCard from '@/components/RuneConfigCard.vue'
// 召唤师技能和技能加点组件
import SummonerSpellCard from '@/components/SummonerSpellCard.vue'
import SkillOrderCard from '@/components/SkillOrderCard.vue'
import PageStatusBanner from '@/components/common/PageStatusBanner.vue'
import PageLoadingState from '@/components/common/PageLoadingState.vue'

const POS = POSITION_NAMES
const ALL_POSITIONS = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT']
const appStore = useAppStore()
const userPrefs = useUserPreferences()
useFavorites()

const {
  runesData,
  isLoading,
  loadError,
  loadProgress,
  loadRunesData,
  clearCache,
  getRunesStatus,
  refreshRunesDataOnServer,
  refreshSingleRunesEntry,
  getChampionOverview,
  preloadFromCache,
  silentRefresh,
} = useRunesData()

const selectedChampion = ref(null)
const selectedPosition = ref('MID')
const sortBy = ref('winRate')
const searchKeyword = ref('')
const searchFocused = ref(false)
const debouncedSearchKeyword = ref('')
const searchDebounceTimer = ref(null)

const runesStatus = ref({})
const isRefreshing = ref(false)
const autoPositionRefreshing = ref(false)
const serverRefreshing = ref(false)
const activeRegion = ref('CN')
const overview = ref({
  average_stats: {},
  position_stats: {},
  counters: [],
  version: '',
  cached_at: '',
  region: 'CN',
  source_region: 'CN',
})

const toast = ref({ show: false, type: 'info', message: '' })
let toastTimer = null

const viewRef = ref(null)
const backTop = ref(false)
let scrollRaf = 0

const visualLoadStep = ref(0)
let visualLoadTimers = []

const statusTimer = ref(null)
const manualChampionSelection = ref(false)
let refreshRunesStatusInflight = null
let refreshOverviewInflight = null

function showToast(message, type = 'info', timeout = 2200) {
  toast.value = { show: true, type, message }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value.show = false), timeout)
}

function logRunesError(action, error) {
  console.error(`[RunesView] ${action}`, error)
}

function resetVisualLoadSequence() {
  cancelVisualLoadSequence()
  visualLoadStep.value = 0
  const steps = [120, 260, 420, 620]
  steps.forEach((delay, index) => {
    const timer = setTimeout(() => {
      visualLoadStep.value = Math.max(visualLoadStep.value, index + 1)
    }, delay)
    visualLoadTimers.push(timer)
  })
}

function cancelVisualLoadSequence() {
  visualLoadTimers.forEach((timer) => clearTimeout(timer))
  visualLoadTimers = []
}

function startVisualLoadSequence() {
  cancelVisualLoadSequence()
  resetVisualLoadSequence()
}

const searchResults = computed(() => {
  if (!debouncedSearchKeyword.value) return []
  return searchChampions(debouncedSearchKeyword.value).slice(0, 8)
})

const availablePositions = computed(() => ALL_POSITIONS)

const DEFAULT_FALLBACK_CHAMPION = computed(() => {
  const target = champions.find((champion) => String(champion.nameEn || champion.key || '').toLowerCase().startsWith('a'))
  return target || champions[0] || null
})

const currentSelectedChampion = computed(() => selectedChampion.value || DEFAULT_FALLBACK_CHAMPION.value)

const currentPositionData = computed(() => {
  const champion = currentSelectedChampion.value
  if (!champion || !runesData.value?.data) return null
  const raw = runesData.value.data[champion.id]?.positions?.[selectedPosition.value] || null
  if (!raw) return null
  return {
    ...raw,
    rune_pages: Array.isArray(raw.rune_pages) ? raw.rune_pages : Array.isArray(raw.runes) ? raw.runes.map((rune) => ({ ...rune, builds: [rune] })) : [],
    runes: Array.isArray(raw.runes) ? raw.runes : Array.isArray(raw.rune_pages) ? raw.rune_pages : [],
    core_items: Array.isArray(raw.core_items) ? raw.core_items : Array.isArray(raw.items) ? raw.items : [],
    items: Array.isArray(raw.items) ? raw.items : Array.isArray(raw.core_items) ? raw.core_items : [],
    boots: Array.isArray(raw.boots) ? raw.boots : [],
    starter_items: Array.isArray(raw.starter_items) ? raw.starter_items : [],
    last_items: Array.isArray(raw.last_items) ? raw.last_items : [],
  }
})

const currentRuneConfigs = computed(() => {
  const configs = sortRuneConfigs(currentPositionData.value?.rune_pages || [], sortBy.value)
  return configs.slice(0, 10)
})

const totalGames = computed(() => {
  const allConfigs = currentPositionData.value?.rune_pages || []
  return allConfigs.reduce((sum, item) => sum + (item.play || 0), 0)
})
const showStatusBanner = computed(() => Boolean(runesStatus.value?.exists && (runesStatus.value?.is_stale || runesStatus.value?.last_update_error || runesStatus.value?.is_updating)))
const revealRuneCards = computed(() => visualLoadStep.value >= 2)
const revealChampionStats = computed(() => visualLoadStep.value >= 3)
const revealItemBlocks = computed(() => visualLoadStep.value >= 4)
const overviewPos = computed(() => overview.value.position_stats || {})
const overviewCounters = computed(() => overview.value.counters || [])
const cachedMeta = computed(() => runesData.value?.meta || {})
const displayRegionLabel = computed(() => {
  const requestedRegion = overview.value.region || activeRegion.value || cachedMeta.value.region || 'CN'
  const sourceRegion = overview.value.source_region || cachedMeta.value.source_region || requestedRegion
  return requestedRegion === sourceRegion ? requestedRegion : `${requestedRegion} (${sourceRegion})`
})

const tierLabel = computed(() => {
  const tierData = overviewPos.value?.tier_data || overview.value.average_stats?.tier_data
  if (!tierData || tierData.tier === undefined || tierData.rank === undefined) return ''
  return `T${tierData.tier} #${tierData.rank}`
})

const dataAge = computed(() => {
  const updateTime = runesData.value?.updateTime
  if (!updateTime) return '-'
  try {
    const ts = new Date(updateTime.replace(' ', 'T')).getTime() / 1000
    return formatRelativeTime(ts) || updateTime
  } catch { return updateTime }
})

const countersPreview = computed(() => {
  return buildCountersPreview(overviewCounters.value, currentPositionData.value?.counters, 5)
})

const gameLengths = computed(() => {
  return buildGameLengths(currentPositionData.value?.game_lengths)
})

const versionTrends = computed(() => {
  return buildVersionTrends(currentPositionData.value?.trends, 4)
})

const emptyStateConfig = computed(() => {
  if (isLoading.value) return null
  if (loadError.value) {
    return {
      type: 'error', icon: '⚠️', title: '符文数据加载失败', description: loadError.value,
      actions: [
        { icon: '🔁', text: '重试', type: 'primary', handler: () => loadData(true) },
        { icon: '🧹', text: '清理缓存', type: 'secondary', handler: async () => { await clearCache(); await loadData(true) } },
      ],
      hints: ['请确认应用已正常连接客户端。', '请确认 data/runes.json 文件存在。'],
    }
  }
  if (!runesData.value) {
    return {
      type: 'first-use', icon: '📌', title: '欢迎使用符文推荐',
      description: '加载后可按英雄和位置查看推荐符文，并一键应用。',
      actions: [{ icon: '🚀', text: '加载数据', type: 'primary', handler: () => loadData() }],
      hints: ['数据来源为 OP.GG Ranked API（CN）。'],
    }
  }
  if (selectedChampion.value && currentRuneConfigs.value.length === 0) {
    if (autoPositionRefreshing.value) return null
    return {
      type: 'no-data', icon: '📭', title: '该位置暂时无推荐数据',
      description: `${selectedChampion.value.name} 在 ${getPositionName(selectedPosition.value)} 暂无可用符文或装备推荐。`,
      actions: [
        { icon: '🔄', text: '刷新该位置', type: 'primary', handler: () => refreshCurrentChampionData() },
        { icon: '↩️', text: '切换位置', type: 'secondary', handler: () => { if (availablePositions.value.length > 0) selectedPosition.value = availablePositions.value[0] } },
      ],
      hints: ['数据可能尚未加载，点击刷新即可获取。', '如果是结构变更，后端会尝试自动兼容。'],
    }
  }
  return null
})

function getPositionName(position) { return POS[position] || position }

function getPrimaryBuild(config) {
  return selectPrimaryBuild(config, sortBy.value)
}

function getChampionName(championId) {
  return getChampionById(championId)?.name || `#${championId}`
}

function primaryTreeName(config) {
  return getTreeById(config?.primary_page_id)?.name || '未知'
}

function secondaryTreeName(config) {
  return getTreeById(config?.secondary_page_id)?.name || '未知'
}

// 分路预加载防抖计时器（300ms）
let positionDebounce = null

function preLoadPosition(position) {
  if (!selectedChampion.value) return
  // 300ms 防抖：连续悬停只触发最后一次，避免重复API请求
  if (positionDebounce) return
  positionDebounce = window.setTimeout(() => {
    refreshSingleRunesEntry(selectedChampion.value.id, selectedChampion.value.key, position, activeRegion.value)
    positionDebounce = null
  }, 300)
}

function resetVirtualViewport() {}

function onSearchBlur() { setTimeout(() => { searchFocused.value = false }, 150) }

function onViewScroll() {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => {
    backTop.value = (viewRef.value?.scrollTop || 0) > 360
    scrollRaf = 0
  })
}

function mapApplyCodeToMessage(code) {
  const map = {
    RUNE_EDIT_NOT_ALLOWED: '当前阶段不允许修改符文，请在对局外操作。',
    RUNE_PAGE_FULL: '符文页已满，请先删除一个自定义页。',
    RUNE_CONFIG_INVALID: '符文配置无效，请切换到其他方案。',
    RUNE_UPDATE_FAILED: '复用当前页失败，且无法删除旧页。',
    RUNE_CREATE_FAILED: '创建符文页失败，请稍后重试。',
    RUNE_CURRENT_PAGE_MISSING: '无法读取当前符文页，请检查客户端状态。',
  }
  return map[code] || '应用失败，请稍后重试。'
}

function onCardApplied(payload) {
  if (!payload) return
  const success = Boolean(payload.success)
  const message = payload.message || (success ? '应用成功' : mapApplyCodeToMessage(payload.code))
  showToast(message, success ? 'success' : 'error', success ? 2200 : 2600)
}

function rememberChampion(champion, position) {
  if (!champion) return
  userPrefs.rememberSelectedChampion(champion, position || selectedPosition.value)
}

async function loadChampionOverview() {
  if (!selectedChampion.value) return
  const inflightKey = `${selectedChampion.value.id}:${selectedPosition.value}:${activeRegion.value}`
  if (refreshOverviewInflight && refreshOverviewInflight.key === inflightKey) {
    return refreshOverviewInflight.promise
  }
  const promise = (async () => {
    const result = await getChampionOverview(selectedChampion.value.key, selectedPosition.value, activeRegion.value)
    if (!result?.success) {
      overview.value = {
        average_stats: {}, position_stats: {}, counters: [], version: '', cached_at: '',
        region: activeRegion.value || cachedMeta.value.region || 'CN',
        source_region: cachedMeta.value.source_region || activeRegion.value || 'CN',
      }
      return
    }
    overview.value = {
      average_stats: result.average_stats || {},
      position_stats: result.position_stats || {},
      counters: result.counters || [],
      version: result.version || '',
      cached_at: result.cached_at || '',
      region: result.region || activeRegion.value || cachedMeta.value.region || 'CN',
      source_region: result.source_region || cachedMeta.value.source_region || result.region || activeRegion.value || 'CN',
    }
  })()
  refreshOverviewInflight = { key: inflightKey, promise }
  try { await promise } finally {
    if (refreshOverviewInflight?.key === inflightKey) refreshOverviewInflight = null
  }
}

function selectChampion(champion, source = 'manual') {
  selectedChampion.value = champion
  manualChampionSelection.value = source === 'manual'
  searchKeyword.value = ''
  debouncedSearchKeyword.value = ''
  searchFocused.value = false
  if (availablePositions.value.length > 0 && !availablePositions.value.includes(selectedPosition.value)) {
    selectedPosition.value = availablePositions.value[0]
  }
  rememberChampion(champion, selectedPosition.value)
  resetVirtualViewport()
  startVisualLoadSequence()
  setTimeout(async () => {
    await loadData(false)
    backgroundRefreshSelectedChampion()
  }, 80)
}

async function backgroundRefreshSelectedChampion() {
  if (!selectedChampion.value || !selectedPosition.value) return
  if (isRefreshing.value || isLoading.value || autoPositionRefreshing.value) return
  try {
    const result = await refreshSingleRunesEntry(selectedChampion.value.id, selectedChampion.value.key, selectedPosition.value, activeRegion.value)
    if (!result?.success) return
    await loadRunesData(true, selectedChampion.value.id, selectedPosition.value)
  } catch (error) {
    logRunesError('backgroundRefreshSelectedChampion', error)
  }
}

async function ensureCurrentPositionData() {
  if (!selectedChampion.value || !selectedPosition.value) return
  if (currentPositionData.value) return
  if (autoPositionRefreshing.value || isRefreshing.value || isLoading.value) return
  autoPositionRefreshing.value = true
  try {
    const result = await refreshSingleRunesEntry(selectedChampion.value.id, selectedChampion.value.key, selectedPosition.value, activeRegion.value)
    if (result?.success) {
      await loadRunesData(true, selectedChampion.value.id, selectedPosition.value)
      await loadChampionOverview()
      await refreshRunesStatus()
    }
  } catch (error) {
    logRunesError('ensureCurrentPositionData', error)
  } finally { autoPositionRefreshing.value = false }
}

async function applyTopRecommendation() {
  if (!currentRuneConfigs.value.length) { showToast('当前没有可应用的符文配置', 'error'); return }
  const topBuild = getPrimaryBuild(currentRuneConfigs.value[0])
  const treeLabel = `${primaryTreeName(topBuild)}+${secondaryTreeName(topBuild)}`
  try {
    const result = await bridge.applyRuneConfig(topBuild, selectedChampion.value?.name || '', selectedPosition.value || '')
    if (result?.success) {
      showToast(`已应用：${treeLabel}`, 'success')
    } else {
      showToast(result?.message || mapApplyCodeToMessage(result?.code), 'error', 2600)
    }
  } catch (error) { showToast(`应用失败：${error?.message || '未知异常'}`, 'error', 2600) }
}

async function refreshRunesStatus() {
  if (refreshRunesStatusInflight) return refreshRunesStatusInflight
  refreshRunesStatusInflight = (async () => {
    const status = await getRunesStatus()
    if (status) runesStatus.value = status
  })()
  try { await refreshRunesStatusInflight } finally { refreshRunesStatusInflight = null }
}

async function refreshCurrentChampionData() {
  if (!selectedChampion.value || isRefreshing.value || isLoading.value) return
  isRefreshing.value = true
  try {
    const result = await refreshSingleRunesEntry(selectedChampion.value.id, selectedChampion.value.key, selectedPosition.value, activeRegion.value)
    if (!result?.success) { showToast(result?.message || '刷新失败', 'error', 2600); return }
    await loadRunesData(true, selectedChampion.value.id, selectedPosition.value)
    await loadChampionOverview()
    await refreshRunesStatus()
    showToast(result.message || '已刷新', 'success')
  } catch (error) { showToast(`刷新失败：${error?.message || '未知异常'}`, 'error', 2600) }
  finally { isRefreshing.value = false }
}

async function refreshRunesOnServer() {
  if (serverRefreshing.value) return
  serverRefreshing.value = true
  try {
    const result = await refreshRunesDataOnServer()
    if (result?.success) showToast(result.message || '全量更新已触发', 'success')
    else showToast(result?.message || '触发失败', 'error', 2600)
    await refreshRunesStatus()
  } catch (error) { showToast(`触发失败：${error?.message || '未知异常'}`, 'error', 2600) }
  finally { serverRefreshing.value = false }
}

async function loadData(force = false) {
  const champion = selectedChampion.value || DEFAULT_FALLBACK_CHAMPION.value
  if (!champion) return
  selectedChampion.value = champion
  if (force) startVisualLoadSequence()
  else if (visualLoadStep.value === 0) startVisualLoadSequence()
  await loadRunesData(false, champion.id, selectedPosition.value)
  await Promise.all([
    refreshRunesStatus(),
    ensureCurrentPositionData(),
    loadChampionOverview(),
  ])
  resetVirtualViewport()
}

function onKeydown(event) {
  if (event.key === '/' && document.activeElement?.tagName !== 'INPUT') {
    event.preventDefault()
    viewRef.value?.querySelector('.search-box input')?.focus()
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'j') {
    event.preventDefault()
    applyTopRecommendation()
  }
}

onMounted(async () => {
  sortBy.value = userPrefs.getSortBy()
  selectedPosition.value = userPrefs.getLastPosition() || 'MID'
  activeRegion.value = userPrefs.getActiveRegion() || 'CN'
  const storeChampId = appStore.currentChampionId
  if (storeChampId) {
    const storeChamp = getChampionById(storeChampId)
    if (storeChamp) {
      selectedChampion.value = storeChamp
    }
  }
  if (!selectedChampion.value) {
    const preferred = champions.find((champion) => String(champion?.key || '').toLowerCase().startsWith('a'))
    selectedChampion.value = preferred || champions[0] || null
  }
  if (selectedChampion.value) {
    rememberChampion(selectedChampion.value, selectedPosition.value)
  }
  preloadRuneIcons()
  startVisualLoadSequence()

  // 第一步：秒开 — 直接用 IndexedDB 缓存回填，不设 isLoading，阻塞式 await 确保数据就绪
  const cacheHit = await preloadFromCache(selectedChampion.value?.id, selectedPosition.value)
  if (cacheHit) {
    // 缓存命中 → UI 立即渲染已有数据
    refreshRunesStatus()
    // 第二步：后台静默从 bridge 拉最新数据，不阻塞，无感更新
    silentRefresh(selectedChampion.value?.id, selectedPosition.value)
    loadChampionOverview()
  } else {
    // 缓存未命中 → 首次使用，走正常加载流程（有 loading bar）
    try {
      await loadData(true)
    } catch (error) {
      logRunesError('onMounted.loadData', error)
      showToast('初始化加载失败，请稍后重试', 'error', 2600)
    }
  }

  statusTimer.value = setInterval(() => refreshRunesStatus(), 15000)
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  if (statusTimer.value) clearInterval(statusTimer.value)
  if (toastTimer) clearTimeout(toastTimer)
  if (searchDebounceTimer.value) clearTimeout(searchDebounceTimer.value)
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  // 清理分路预加载防抖计时器
  if (positionDebounce) clearTimeout(positionDebounce)
  cancelVisualLoadSequence()
  window.removeEventListener('keydown', onKeydown)
})

watch(selectedPosition, async (value) => {
  userPrefs.setLastPosition(value)
  if (selectedChampion.value) rememberChampion(selectedChampion.value, value)
  // 走 loadData 流程，内部已用 Promise.all 并行，后台静默刷新
  await loadData(false)
  resetVirtualViewport()
})

watch(sortBy, (value) => { userPrefs.setSortBy(value); resetVirtualViewport() })
watch(activeRegion, (value) => { userPrefs.setActiveRegion(value) })

watch(searchKeyword, (value) => {
  if (searchDebounceTimer.value) clearTimeout(searchDebounceTimer.value)
  searchDebounceTimer.value = setTimeout(() => { debouncedSearchKeyword.value = (value || '').trim() }, 120)
})

watch(availablePositions, (positions) => {
  if (!positions || positions.length === 0) return
  if (!positions.includes(selectedPosition.value)) selectedPosition.value = positions[0]
})

watch(() => appStore.gamePhase, (phase) => {
  if (phase === 'ChampSelect') {
    // 进入新的选人阶段，重置手动选择标记，恢复自动跟随
    manualChampionSelection.value = false
  }
}, { immediate: true })

watch(() => appStore.currentChampionId, async (championId) => {
  if (!championId) return
  if (manualChampionSelection.value) return
  const champion = getChampionById(championId)
  if (champion && champion.id !== selectedChampion.value?.id) {
    // selectChampion 内部已通过 setTimeout 调用 loadData，无需重复触发
    selectChampion(champion, 'lcu')
    return
  }
  if (champion && champion.id === selectedChampion.value?.id) await loadData(false)
}, { immediate: true })
</script>

<style scoped>
/* ===== 根布局 ===== */
.runes-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #0a0e1a;
}

.status-banner {
  flex: 0 0 auto;
  padding: 6px 14px;
  font-size: 12px;
  color: #fde68a;
  background: #2f2513;
  border-bottom: 1px solid #6b4f1d;
}

.loading-bar {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  position: relative;
  overflow: hidden;
}

.loading-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(78, 204, 163, 0.8), transparent);
  animation: loadingSlide 1.5s ease-in-out infinite;
}

@keyframes loadingSlide {
  0% { left: -100%; }
  100% { left: 100%; }
}

/* ===== 双栏主布局 ===== */
.main-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  align-items: stretch;
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}

/* ===== 左栏 ===== */
.left-panel {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  gap: 2px;
  padding: 12px;
  background: #0f1525;
  border-right: 1px solid #1e293b;
}

.champion-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #1e293b;
}

.champion-avatar {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  border: 2px solid #334155;
  flex-shrink: 0;
}

.champion-info { min-width: 0; }

.champion-name {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.champion-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.champion-tier {
  font-size: 11px;
  font-weight: 600;
  color: #fb7185;
  margin-top: 2px;
}

/* ===== 搜索框 ===== */
.search-box {
  position: relative;
  margin-top: 10px;
}

.search-box input {
  width: 100%;
  height: 32px;
  border: 1px solid #1e293b;
  border-radius: 6px;
  background: #0a0e1a;
  color: #e2e8f0;
  padding: 0 10px;
  font-size: 12px;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s;
}

.search-box input:focus { border-color: #4ECCB3; }

.dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #111827;
  border: 1px solid #1e293b;
  border-radius: 6px;
  max-height: 220px;
  overflow-y: auto;
  z-index: 40;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  transition: background 0.1s;
}

.dropdown-item:hover { background: #1a2236; }

.search-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #1e293b;
}

.search-name { font-size: 12px; color: #e2e8f0; }
.search-sub { font-size: 10px; color: #64748b; }

/* ===== 分路按钮 ===== */
.position-bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  margin-top: 10px;
}

.pos-btn {
  height: 28px;
  border: 1px solid #1e293b;
  border-radius: 5px;
  background: #0a0e1a;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.pos-btn:hover { border-color: #4ECCB3; color: #e2e8f0; }

.pos-btn.active {
  background: #4ECCB3;
  border-color: #4ECCB3;
  color: #0a0e1a;
  font-weight: 700;
}

/* ===== 数据列表 ===== */
.stats-list {
  display: flex;
  flex-direction: column;
  margin-top: 10px;
  border: 1px solid #1e293b;
  border-radius: 6px;
  overflow: hidden;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  font-size: 12px;
  border-bottom: 1px solid #141c2e;
}

.stat-row:last-child { border-bottom: none; }
.stat-row span { color: #64748b; }
.stat-row strong { color: #e2e8f0; font-weight: 600; }
.stat-row.dim strong { color: #64748b; font-weight: 400; }
.stat-row.highlight span { color: #4ECCB3; }
.stat-row.highlight strong { color: #4ECCB3; font-weight: 700; }

.wr-high { color: #4ECCB3 !important; }
.wr-ok { color: #e2e8f0 !important; }
.wr-low { color: #fb7185 !important; }

/* ===== 出装推荐 ===== */
.items-section {
  margin-top: 10px;
  background: #111827;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 8px 10px;
}

.skeleton {
  position: relative;
  overflow: hidden;
}

.skeleton::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.08), transparent);
  transform: translateX(-100%);
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

.rune-card-wrap {
  min-height: 100px;
}

.card-skeleton {
  min-height: 100px;
  border: 1px solid #1e293b;
  border-radius: 8px;
  background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.items-title { color: #4ECCB3 !important; }

.item-group {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.item-label {
  font-size: 11px;
  color: #475569;
  min-width: 28px;
}

.item-icons {
  display: flex;
  align-items: center;
  gap: 3px;
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #1e293b;
}

.item-wr {
  font-size: 11px;
  color: #94a3b8;
  margin-left: 4px;
}

/* ===== 克制关系 ===== */
.counters-section {
  margin-top: 10px;
}

.counter-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
}

.counter-icon {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: 1px solid #1e293b;
}

.counter-name {
  font-size: 11px;
  color: #cbd5e1;
  flex: 1;
}

.counter-wr {
  font-size: 11px;
  color: #94a3b8;
}

/* ===== 对局时长胜率 ===== */
.gamelength-section {
  margin-top: 10px;
}

.gl-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
}

.gl-label {
  font-size: 11px;
  color: #64748b;
  min-width: 28px;
}

.gl-bar-wrap {
  flex: 1;
  height: 6px;
  background: #1e293b;
  border-radius: 3px;
  overflow: hidden;
}

.gl-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.gl-bar.wr-high { background: #4ECCB3; }
.gl-bar.wr-ok { background: #94a3b8; }
.gl-bar.wr-low { background: #fb7185; }

.gl-val {
  font-size: 11px;
  font-weight: 600;
  min-width: 38px;
  text-align: right;
}

/* ===== 版本趋势 ===== */
.trends-section {
  margin-top: 10px;
}

.trend-list {
  display: flex;
  flex-direction: column;
}

.trend-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
}

.trend-ver {
  font-size: 11px;
  color: #64748b;
  min-width: 36px;
}

.trend-rate {
  font-size: 11px;
  font-weight: 600;
  min-width: 38px;
}

.trend-arrow {
  font-size: 10px;
}

.trend-arrow.up { color: #4ECCB3; }
.trend-arrow.down { color: #fb7185; }

/* ===== 右栏 ===== */
.right-panel {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  gap: 10px;
  flex: 1 1 0;
  min-height: 0;
}

/* ===== 操作栏 ===== */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 10;
  background: #0a0e1a;
  padding-bottom: 4px;
}

.sort-group {
  display: flex;
  gap: 4px;
}

.sort-btn {
  height: 30px;
  padding: 0 12px;
  border: 1px solid #1e293b;
  border-radius: 5px;
  background: #0f1525;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.sort-btn:hover { border-color: #4ECCB3; color: #e2e8f0; }

.sort-btn.active {
  background: #4ECCB3;
  border-color: #4ECCB3;
  color: #0a0e1a;
  font-weight: 700;
}

.action-btns {
  display: flex;
  gap: 6px;
}

.act-btn {
  height: 30px;
  padding: 0 10px;
  border: 1px solid #1e293b;
  border-radius: 5px;
  background: #0f1525;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.act-btn:hover { border-color: #334155; color: #e2e8f0; }
.act-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.act-btn.primary {
  background: #4ECCB3;
  border-color: #4ECCB3;
  color: #0a0e1a;
  font-weight: 700;
}

.act-btn.primary:hover { background: #5dd4b4; }

/* ===== 符文列表 ===== */
.rune-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1 1 auto;
  min-height: 0;
}

.refreshing-hint {
  text-align: center;
  padding: 8px;
}

.muted {
  color: #64748b;
  font-size: 12px;
}

/* ===== Toast ===== */
.toast {
  position: fixed;
  right: 20px;
  bottom: 20px;
  padding: 12px 18px;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 1200;
  max-width: 320px;
  line-height: 1.4;
}

.toast.info { background: #334155; }
.toast.success {
  background: #15803d;
  border: 1px solid #22c55e;
}
.toast.error { background: #b91c1c; }

/* ===== 响应式：窄屏 ===== */
@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .left-panel {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px;
    border-right: none;
    border-bottom: 1px solid #1e293b;
    overflow-y: visible;
    max-height: none;
  }

  .champion-card {
    border-bottom: none;
    padding-bottom: 0;
  }

  .champion-avatar {
    width: 40px;
    height: 40px;
  }

  .search-box {
    flex: 1;
    min-width: 140px;
    margin-top: 0;
  }

  .position-bar {
    margin-top: 0;
    width: 100%;
  }

  .stats-list,
  .items-section,
  .counters-section,
  .gamelength-section,
  .trends-section {
    display: none;
  }
}
</style>

