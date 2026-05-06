<template>
  <div class="augments-history-view">
    <div class="augments-shell">
      <div v-if="showStatusBanner" class="status-banner" :class="statusBannerTone">
        <span class="status-dot"></span>
        <span>{{ statusBannerText }}</span>
      </div>

      <div v-if="isLoading && !augmentsData?.data" class="loading-panel">
        <div class="loading-spinner"></div>
        <div class="loading-title">正在整理强化面板</div>
        <div class="loading-subtitle">正在读取强化数据与英雄概览… {{ loadProgress }}%</div>
      </div>

      <div v-else class="content-grid">
        <aside class="left-column">
          <div class="left-sticky">
            <section class="surface-panel sidebar-panel">
              <div class="panel-head">
                <div>
                  <div class="panel-title">英雄选择</div>
                  <div class="panel-subtitle">按 `History` 左栏语法重组，搜索与切换都固定在左侧。</div>
                </div>
                <span class="soft-badge">{{ championList.length }} 个</span>
              </div>

              <label class="search-field">
                <span>搜索英雄</span>
                <input v-model="searchKeyword" type="text" class="search-input" placeholder="搜索英雄名称、英文名或别名" />
              </label>

              <button v-if="selectedChampion" type="button" class="hero-focus-card">
                <img :src="getChampionIcon(selectedChampion.id)" :alt="selectedChampion.name" class="hero-focus-avatar" loading="eager" decoding="async" />
                <div class="hero-focus-main">
                  <div class="hero-focus-title">
                    <strong>{{ selectedChampion.name }}</strong>
                    <span>{{ selectedChampion.nameEn }}</span>
                  </div>
                  <div class="hero-focus-meta">
                    <span class="tier-pip" :class="heroTierClass">{{ heroTierLabel }}</span>
                    <span>{{ getChampionPlayLabel(selectedChampion.id) }}</span>
                  </div>
                </div>
              </button>

              <div class="champion-list">
                <button
                  v-for="champion in championList"
                  :key="champion.id"
                  type="button"
                  class="champion-row"
                  :class="{ active: selectedChampion?.id === champion.id }"
                  @click="selectChampion(champion, 'manual')"
                >
                  <img :src="getChampionIcon(champion.id)" :alt="champion.name" class="champion-row__icon" loading="lazy" decoding="async" />
                  <div class="champion-row__main">
                    <strong>{{ champion.name }}</strong>
                    <span>{{ champion.nameEn }}</span>
                  </div>
                  <div class="champion-row__meta">{{ getChampionPlayLabel(champion.id) }}</div>
                </button>
              </div>
            </section>

            <section class="surface-panel sidebar-panel">
              <div class="panel-head">
                <div>
                  <div class="panel-title">数据状态</div>
                  <div class="panel-subtitle">单独标记当前文件是否来自真实接口，避免把抓取缓存误认成官方统计。</div>
                </div>
              </div>

              <div class="meta-grid">
                <div class="meta-row">
                  <span>数据源</span>
                  <strong>{{ dataSourceLabel }}</strong>
                </div>
                <div class="meta-row">
                  <span>可信度</span>
                  <strong :class="sourceTrustClass">{{ sourceTrustLabel }}</strong>
                </div>
                <div class="meta-row">
                  <span>模式</span>
                  <strong>{{ modeLabel }}</strong>
                </div>
                <div class="meta-row">
                  <span>地区</span>
                  <strong>{{ currentRegionLabel }}</strong>
                </div>
                <div class="meta-row">
                  <span>覆盖英雄</span>
                  <strong>{{ dataStats?.champions || 0 }}</strong>
                </div>
                <div class="meta-row">
                  <span>更新时间</span>
                  <strong>{{ dataUpdateLabel }}</strong>
                </div>
              </div>

              <div class="source-note" :class="sourceNoteClass">
                {{ sourceSummaryText }}
              </div>
            </section>
          </div>
        </aside>

        <section class="right-column">
          <section class="surface-panel toolbar-panel">
            <div class="toolbar-head">
              <div>
                <div class="toolbar-title">强化总览</div>
                <div class="toolbar-subtitle">按 `History` 的面板层级重写：顶部工具栏、完整英雄概览、下方精致表格，不再互相遮挡。</div>
              </div>

              <div class="toolbar-stats">
                <div class="toolbar-stat">
                  <span>当前英雄</span>
                  <strong>{{ selectedChampion?.name || '未选择' }}</strong>
                </div>
                <div class="toolbar-stat">
                  <span>强化结果</span>
                  <strong>{{ rankedAugments.length }}</strong>
                </div>
                <div class="toolbar-stat">
                  <span>数据状态</span>
                  <strong>{{ sourceTrustLabel }}</strong>
                </div>
              </div>
            </div>

            <div class="toolbar-controls">
              <div class="toolbar-chip-group">
                <span class="toolbar-chip">{{ modeLabel }}</span>
                <span class="toolbar-chip">{{ currentRegionLabel }}</span>
                <span class="toolbar-chip">{{ currentRankScopeLabel }}</span>
                <span class="toolbar-chip" :class="sourceChipClass">{{ sourceTrustLabel }}</span>
              </div>

              <div class="toolbar-actions">
                <label class="toolbar-search">
                  <span>强化搜索</span>
                  <input v-model="augmentKeyword" type="text" placeholder="搜索强化中文或英文名" />
                </label>
                <button type="button" class="refresh-btn" :disabled="serverRefreshing || isLoading" @click="refreshOnServer">
                  {{ serverRefreshing ? '刷新中…' : '刷新数据' }}
                </button>
              </div>
            </div>
          </section>

          <section class="surface-panel hero-overview-panel">
            <div class="hero-overview-main">
              <img v-if="selectedChampion" :src="getChampionIcon(selectedChampion.id)" :alt="selectedChampion.name" class="hero-overview-avatar" loading="eager" decoding="async" />

              <div class="hero-overview-copy">
                <div class="hero-overview-title-row">
                  <div>
                    <h1>{{ selectedChampion?.name || '强化推荐' }}</h1>
                    <p>{{ selectedChampion?.nameEn || '请选择英雄查看强化' }}</p>
                  </div>
                  <div class="hero-tier-badge" :class="heroTierClass">{{ heroTierLabel }} 级别</div>
                </div>

                <div class="hero-overview-tags">
                  <span class="hero-tag">{{ modeLabel }}</span>
                  <span class="hero-tag">{{ currentRegionLabel }}</span>
                  <span class="hero-tag">{{ currentRankScopeLabel }}</span>
                  <span class="hero-tag">{{ sampleQualityLabel }}</span>
                </div>
              </div>
            </div>

            <div class="hero-metrics-grid">
              <div v-for="metric in overviewMetrics" :key="metric.label" class="metric-card" :class="metric.tone">
                <span>{{ metric.label }}</span>
                <strong>{{ metric.value }}</strong>
              </div>
            </div>

            <div class="tier-summary">
              <span class="tier-summary__item tier-summary__item--silver">白银 {{ tierCounts.silver }}</span>
              <span class="tier-summary__item tier-summary__item--gold">黄金 {{ tierCounts.gold }}</span>
              <span class="tier-summary__item tier-summary__item--prismatic">棱彩 {{ tierCounts.prismatic }}</span>
            </div>
          </section>

          <section class="surface-panel augments-panel">
            <div class="panel-head panel-head--spaced">
              <div>
                <div class="panel-title">强化符文</div>
                <div class="panel-subtitle">{{ rankingSubtitle }}</div>
              </div>

              <div class="panel-actions">
                <div class="filter-tabs">
                  <button
                    v-for="tab in tierTabs"
                    :key="tab.key"
                    type="button"
                    class="filter-tab"
                    :class="[`filter-tab--${tab.key}`, { active: selectedTier === tab.key }]"
                    @click="selectedTier = tab.key"
                  >
                    {{ tab.label }}
                  </button>
                </div>

                <div class="sort-tabs" role="tablist" aria-label="强化排序方式">
                  <button
                    v-for="sort in sortOptions"
                    :key="sort.key"
                    type="button"
                    class="sort-tab"
                    :class="{ active: selectedSort === sort.key }"
                    @click="selectedSort = sort.key"
                  >
                    {{ sort.label }}
                  </button>
                </div>
              </div>
            </div>

            <div v-if="rankedAugments.length" class="ranking-table">
              <div class="ranking-head" :class="{ 'ranking-head--mayhem': isMayhemScrapedData }">
                <span>#</span>
                <span>强化</span>
                <span>阶级</span>
                <template v-if="isMayhemScrapedData">
                  <span>强度</span>
                  <span>欢迎度</span>
                </template>
                <template v-else>
                  <span>综合</span>
                  <span>登场率</span>
                  <span>胜率</span>
                  <span>场次</span>
                </template>
              </div>

              <div class="ranking-body">
                <button
                  v-for="(augment, index) in rankedAugments"
                  :key="getAugmentKey(augment)"
                  type="button"
                  class="ranking-row"
                  :class="[
                    `tier-${getAugTier(augment)}`,
                    { active: selectedAugment && getAugmentKey(selectedAugment) === getAugmentKey(augment), 'ranking-row--mayhem': isMayhemScrapedData },
                  ]"
                  @click="selectAugment(augment)"
                >
                  <div class="ranking-col ranking-col--index">#{{ index + 1 }}</div>

                  <div class="ranking-col ranking-col--main">
                    <div class="augment-icon-shell">
                      <img :src="getAugmentIconUrl(augment.icon || augment.name)" :alt="getAugmentChineseName(augment.name)" loading="lazy" decoding="async" @error="handleAugmentIconError" />
                    </div>

                    <div class="augment-main-copy">
                      <strong>{{ getAugmentChineseName(augment.name) }}</strong>
                      <span>{{ augment.name }}</span>
                    </div>
                  </div>

                  <div class="ranking-col ranking-col--tier">
                    <span class="tier-pill" :class="`tier-pill--${getAugTier(augment)}`">{{ getTierName(getAugTier(augment)) }}</span>
                  </div>

                  <template v-if="isMayhemScrapedData">
                    <div class="ranking-col ranking-col--metric">
                      <strong>{{ formatScore(getDisplayStrength(augment)) }}</strong>
                      <span>强度</span>
                    </div>
                    <div class="ranking-col ranking-col--metric">
                      <strong>{{ formatScore(getDisplayPopularity(augment)) }}</strong>
                      <span>欢迎度</span>
                    </div>
                  </template>

                  <template v-else>
                    <div class="ranking-col ranking-col--metric ranking-col--metric-highlight">
                      <strong>{{ formatScore(calculateStrengthScore(augment)) }}</strong>
                      <span>综合</span>
                    </div>
                    <div class="ranking-col ranking-col--metric">
                      <strong>{{ formatPercent(augment.pickRate) }}</strong>
                      <span>登场率</span>
                    </div>
                    <div class="ranking-col ranking-col--metric">
                      <strong>{{ formatPercent(augment.winRate) }}</strong>
                      <span>胜率</span>
                    </div>
                    <div class="ranking-col ranking-col--metric">
                      <strong>{{ formatGames(augment.games) }}</strong>
                      <span>场次</span>
                    </div>
                  </template>
                </button>
              </div>
            </div>

            <div v-else class="state-panel empty">
              <div class="state-icon">空</div>
              <div class="empty-title">暂无强化结果</div>
              <div class="empty-subtitle">{{ rankingEmptyMessage }}</div>
            </div>
          </section>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { champions, getChampionById, searchChampions } from '@/data/champions'
import { getAugmentChineseName, getAugmentIconUrl, getAugmentTier, getTierName } from '@/data/augments'
import { getChampionIcon } from '@/utils/ddragon'
import { useAppStore } from '@/stores/app'
import { useAugmentsData } from '@/composables/useAugmentsData'
import PageStatusBanner from '@/components/common/PageStatusBanner.vue'
import PageLoadingState from '@/components/common/PageLoadingState.vue'
import EmptyStateCard from '@/components/EmptyStateCard.vue'

const appStore = useAppStore()

const searchKeyword = ref('')
const augmentKeyword = ref('')
const selectedChampion = ref(null)
const selectedAugment = ref(null)
const manualSelection = ref(false)
const serverRefreshing = ref(false)
const augmentsStatus = ref(null)
const selectedTier = ref('all')
const selectedSort = ref('default')
const selectedRegion = ref('GLOBAL')
const selectedRankScope = ref('all')

const tierTabs = [
  { key: 'all', label: '全部' },
  { key: 'silver', label: '白银阶' },
  { key: 'gold', label: '黄金阶' },
  { key: 'prismatic', label: '棱彩阶' },
]

const hotChampionKeys = ['Graves', 'Pantheon', 'Yasuo', 'Yone', 'Jinx', 'Kaisa', 'Aatrox', 'LeeSin', 'Sett', 'Lux', 'Darius', 'Ahri']

const {
  augmentsData,
  isLoading,
  loadError,
  loadProgress,
  dataStats,
  loadAugmentsData,
  getAugmentsStatus,
  refreshAugmentsDataOnServer,
  abortPendingLoad,
} = useAugmentsData()

const sourceMeta = computed(() => augmentsData.value?.meta || {})
const dataSourceLabel = computed(() => String(sourceMeta.value.source || '未知数据源'))
const isMayhemScrapedData = computed(() => {
  const mode = String(sourceMeta.value.mode || '').toLowerCase()
  const source = dataSourceLabel.value.toLowerCase()
  return mode === 'aram-mayhem' || source.includes('aram: mayhem') || source.includes('aram mayhem') || source.includes('scraped')
})
const isTrustedSource = computed(() => {
  const source = dataSourceLabel.value.toLowerCase()
  return !!source && !source.includes('scraped')
})

const sortOptions = computed(() => {
  if (isMayhemScrapedData.value) {
    return [
      { key: 'default', label: '默认' },
      { key: 'popularity', label: '欢迎度' },
      { key: 'strength', label: '强度' },
    ]
  }
  return [
    { key: 'default', label: '默认' },
    { key: 'pickRate', label: '登场率' },
    { key: 'winRate', label: '胜率' },
    { key: 'games', label: '场次' },
  ]
})

const modeLabel = computed(() => {
  const mode = String(sourceMeta.value.mode || '').toLowerCase()
  if (mode === 'aram-mayhem') return '海克斯大乱斗'
  if (mode === 'arena') return '斗魂竞技场'
  if (dataSourceLabel.value.toLowerCase().includes('arena api')) return '斗魂竞技场'
  if (appStore.gameModeType === 'ARENA') return '斗魂竞技场'
  if (appStore.gameModeType === 'ARAM_MAYHEM') return '海克斯大乱斗'
  return '强化面板'
})

const currentRegionLabel = computed(() => {
  const region = String(sourceMeta.value.region || selectedRegion.value || 'GLOBAL').toUpperCase()
  return region === 'GLOBAL' ? '全球' : region
})
const currentRankScopeLabel = computed(() => selectedRankScope.value === 'all' ? '全部段位' : selectedRankScope.value)
const dataUpdateLabel = computed(() => augmentsData.value?.updateTime || '--')
const sourceTrustLabel = computed(() => isTrustedSource.value ? '真实接口' : '抓取缓存')
const sourceTrustClass = computed(() => isTrustedSource.value ? 'is-good' : 'is-warn')
const sourceChipClass = computed(() => isTrustedSource.value ? 'toolbar-chip--good' : 'toolbar-chip--warn')
const sourceNoteClass = computed(() => isTrustedSource.value ? 'source-note--good' : 'source-note--warn')

const statusBannerTone = computed(() => {
  if (loadError.value) return 'error'
  if (dataStats.value?.stale) return 'warning'
  return 'info'
})
const statusBannerText = computed(() => {
  if (serverRefreshing.value || augmentsStatus.value?.is_updating) return '强化数据正在刷新中…'
  if (loadError.value) return `加载失败：${loadError.value}`
  if (dataStats.value?.stale) return '当前展示的是缓存数据，建议刷新后再确认强化结果。'
  return ''
})
const showStatusBanner = computed(() => serverRefreshing.value || augmentsStatus.value?.is_updating || !!loadError.value || !!dataStats.value?.stale)

const sourceSummaryText = computed(() => {
  if (isTrustedSource.value) {
    return '当前文件来自 OP.GG Arena API 结构化接口，后端能直接拿到 play / win / pick_rate 等真实统计字段。'
  }
  return '当前文件来自网页抓取缓存（例如 ARAM: Mayhem scraped），更适合展示参考样式，不应当被当成真实 Arena API 统计。'
})

const championsWithData = computed(() => {
  const data = augmentsData.value?.data || {}
  return new Set(Object.keys(data))
})

const hotChampions = computed(() => {
  const keySet = new Set(hotChampionKeys.map((value) => value.toLowerCase()))
  return champions.filter((champion) => keySet.has(String(champion.key || '').toLowerCase()))
})

const championList = computed(() => {
  const keyword = searchKeyword.value.trim()
  const baseList = keyword ? searchChampions(keyword) : hotChampions.value
  const withData = baseList.filter((champion) => !augmentsData.value?.data || championsWithData.value.has(String(champion.id)))
  const current = selectedChampion.value ? [selectedChampion.value] : []
  const unique = [...current, ...withData].filter((champion, index, list) => list.findIndex((item) => item.id === champion.id) === index)
  return unique.slice(0, keyword ? 18 : 12)
})

const currentChampionData = computed(() => {
  if (!selectedChampion.value || !augmentsData.value?.data) return null
  return augmentsData.value.data[String(selectedChampion.value.id)] || null
})
const summaryData = computed(() => currentChampionData.value?.summary || null)

function isMayhemAugmentValid(item) {
  if (!isMayhemScrapedData.value) return true
  const strength = Number(item?.winRate || 0)
  const popularity = Number(item?.pickRate || 0)
  return strength > 0 && strength <= 100 && popularity > 0
}

const championAugments = computed(() => {
  const raw = currentChampionData.value?.augments
  if (!raw) return []

  let flattened = []
  if (Array.isArray(raw)) {
    flattened = raw.map((item) => ({ ...item, tier: item.tier || getAugmentTier(item.name) }))
  } else {
    flattened = ['silver', 'gold', 'prismatic'].flatMap((tier) => (
      Array.isArray(raw[tier]) ? raw[tier].map((item) => ({ ...item, tier: item.tier || tier || getAugmentTier(item.name) })) : []
    ))
  }

  return flattened.filter((item) => isMayhemAugmentValid(item))
})

const tierCounts = computed(() => championAugments.value.reduce((result, item) => {
  const tier = getAugTier(item)
  result[tier] = (result[tier] || 0) + 1
  return result
}, { silver: 0, gold: 0, prismatic: 0 }))

const filteredAugments = computed(() => {
  const keyword = augmentKeyword.value.trim().toLowerCase()
  return championAugments.value.filter((item) => {
    const matchesTier = selectedTier.value === 'all' || getAugTier(item) === selectedTier.value
    if (!matchesTier) return false
    if (!keyword) return true
    const chineseName = String(getAugmentChineseName(item.name) || '').toLowerCase()
    const englishName = String(item.name || '').toLowerCase()
    return chineseName.includes(keyword) || englishName.includes(keyword)
  })
})

function calculateStrengthScore(augment) {
  const winRate = Number(augment?.winRate || 0)
  const pickRate = Number(augment?.pickRate || 0)
  const games = Number(augment?.games || 0)
  return winRate * 0.65 + pickRate * 0.2 + Math.min(games / 1500, 20)
}

function getDisplayStrength(augment) {
  return Number(augment?.winRate || 0)
}

function getDisplayPopularity(augment) {
  return Number(augment?.pickRate || 0)
}

const rankedAugments = computed(() => {
  const list = [...filteredAugments.value]

  if (isMayhemScrapedData.value) {
    const sorters = {
      default: (left, right) => getDisplayPopularity(right) - getDisplayPopularity(left),
      popularity: (left, right) => getDisplayPopularity(right) - getDisplayPopularity(left),
      strength: (left, right) => getDisplayStrength(right) - getDisplayStrength(left),
    }
    const sorter = sorters[selectedSort.value] || sorters.default
    return list.sort((left, right) => sorter(left, right) || getDisplayStrength(right) - getDisplayStrength(left) || getDisplayPopularity(right) - getDisplayPopularity(left))
  }

  const sorters = {
    default: (left, right) => calculateStrengthScore(right) - calculateStrengthScore(left),
    pickRate: (left, right) => Number(right.pickRate || 0) - Number(left.pickRate || 0),
    winRate: (left, right) => Number(right.winRate || 0) - Number(left.winRate || 0),
    games: (left, right) => Number(right.games || 0) - Number(left.games || 0),
  }
  const sorter = sorters[selectedSort.value] || sorters.default
  return list.sort((left, right) => sorter(left, right) || Number(right.games || 0) - Number(left.games || 0))
})

const rankingEmptyMessage = computed(() => {
  if (isLoading.value && !augmentsData.value?.data) return '正在读取强化数据…'
  if (!selectedChampion.value) return '请先选择英雄，再查看强化推荐。'
  if (augmentKeyword.value.trim() || selectedTier.value !== 'all') return '当前筛选条件下没有结果，建议清空筛选或切换阶级。'
  return '当前英雄暂无强化数据。'
})

const sampleQualityLabel = computed(() => {
  const play = Number(summaryData.value?.play || 0)
  if (play >= 30000) return '样本质量：高'
  if (play >= 10000) return '样本质量：中'
  if (play > 0) return '样本质量：低'
  return '样本质量：暂无'
})

const heroStrengthScore = computed(() => {
  const winRate = Number(summaryData.value?.win_rate || 0)
  const pickRate = Number(summaryData.value?.pick_rate || 0)
  const play = Number(summaryData.value?.play || 0)
  return winRate * 0.7 + pickRate * 0.25 + Math.min(play / 3000, 10)
})

const heroOverviewScore = computed(() => {
  if (Number(summaryData.value?.play || 0) > 0) return heroStrengthScore.value
  if (rankedAugments.value.length) {
    const topList = rankedAugments.value.slice(0, 5)
    const total = topList.reduce((sum, item) => sum + getDisplayStrength(item), 0)
    return total / Math.max(1, topList.length)
  }
  return 0
})

const heroTierLabel = computed(() => {
  if (heroOverviewScore.value >= 57) return 'T1'
  if (heroOverviewScore.value >= 51) return 'T2'
  if (heroOverviewScore.value >= 45) return 'T3'
  return 'T4'
})
const heroTierClass = computed(() => `hero-tier-badge--${heroTierLabel.value.toLowerCase()}`)

const overviewMetrics = computed(() => {
  if (isMayhemScrapedData.value) {
    return [
      { label: '平均强度', value: formatScore(heroOverviewScore.value), tone: 'metric-card--highlight' },
      { label: '最高欢迎度', value: formatScore(Math.max(0, ...rankedAugments.value.slice(0, 10).map((item) => getDisplayPopularity(item)))), tone: '' },
      { label: '可用强化', value: formatGames(championAugments.value.length), tone: '' },
      { label: '当前样本', value: getChampionPlayLabel(selectedChampion.value?.id), tone: '' },
    ]
  }

  return [
    { label: '综合强度', value: formatScore(heroOverviewScore.value), tone: 'metric-card--highlight' },
    { label: '胜率', value: formatPercent(summaryData.value?.win_rate), tone: '' },
    { label: '登场率', value: formatPercent(summaryData.value?.pick_rate), tone: '' },
    { label: '场次', value: formatGames(summaryData.value?.play), tone: '' },
  ]
})

const rankingSubtitle = computed(() => {
  const championName = selectedChampion.value?.name || '当前英雄'
  const sourceTag = isTrustedSource.value ? '真实接口' : '抓取缓存'
  return `${championName} · ${sourceTag} · 共 ${rankedAugments.value.length} 条结果`
})

function getAugTier(augment) {
  if (!augment) return 'silver'
  return augment.tier || getAugmentTier(augment.name)
}

function getAugmentKey(augment) {
  return `${augment?.id || augment?.name || 'unknown'}-${getAugTier(augment)}`
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(2)}%`
}

function formatGames(value) {
  return Number(value || 0).toLocaleString()
}

function formatScore(value) {
  return Number(value || 0).toFixed(2)
}

function getChampionPlayLabel(championId) {
  if (!championId || !augmentsData.value?.data) return '暂无数据'
  const play = Number(augmentsData.value.data[String(championId)]?.summary?.play || 0)
  if (!play) return isMayhemScrapedData.value ? '抓取数据' : '暂无样本'
  return `${formatGames(play)} 场`
}

function buildFallbackIconDataUrl() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#14233f"/>
          <stop offset="100%" stop-color="#1c3f66"/>
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="14" fill="url(#bg)"/>
      <path d="M20 44L32 19L44 44H38.9L36.5 38.4H27.5L25.1 44H20ZM29.6 33.6H34.4L32 28.1L29.6 33.6Z" fill="#dff7ff"/>
    </svg>
  `.trim()
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

const fallbackAugmentIconUrl = buildFallbackIconDataUrl()

function handleAugmentIconError(event) {
  const target = event?.target
  if (!target || target.dataset.fallbackApplied === '1') return
  target.dataset.fallbackApplied = '1'
  target.src = fallbackAugmentIconUrl
}

function hasChampionData(champion) {
  if (!champion) return false
  return championsWithData.value.has(String(champion.id))
}

function selectChampion(champion, source = 'manual') {
  selectedChampion.value = champion
  if (source === 'manual') manualSelection.value = true
}

function selectAugment(augment) {
  selectedAugment.value = augment
}

function resolvePreferredChampion() {
  const currentChampion = getChampionById(appStore.currentChampionId)
  if (currentChampion && (!augmentsData.value?.data || hasChampionData(currentChampion))) return currentChampion
  if (selectedChampion.value && (!augmentsData.value?.data || hasChampionData(selectedChampion.value))) return selectedChampion.value
  const hotChampion = hotChampions.value.find((champion) => !augmentsData.value?.data || hasChampionData(champion))
  if (hotChampion) return hotChampion
  const firstWithData = champions.find((champion) => !augmentsData.value?.data || hasChampionData(champion))
  return firstWithData || champions[0] || null
}

async function refreshStatus() {
  augmentsStatus.value = await getAugmentsStatus()
}

async function waitForRefreshCompletion() {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, attempt === 0 ? 400 : 900))
    await refreshStatus()
    if (!augmentsStatus.value?.is_updating) {
      await loadAugmentsData(true)
      return
    }
  }
  await loadAugmentsData(true)
}

async function refreshOnServer() {
  if (serverRefreshing.value) return
  serverRefreshing.value = true
  try {
    const result = await refreshAugmentsDataOnServer()
    if (!result?.success) {
      await refreshStatus()
      return
    }
    await waitForRefreshCompletion()
  } finally {
    serverRefreshing.value = false
  }
}

async function syncCurrentChampion() {
  if (appStore.gamePhase === 'ChampSelect') {
    await appStore.refreshCurrentChampion()
  }
}

onMounted(() => {
  selectedChampion.value = resolvePreferredChampion()
  void loadAugmentsData().finally(() => {
    selectedChampion.value = resolvePreferredChampion()
  })
  void refreshStatus()
  void syncCurrentChampion()
})

onUnmounted(() => {
  abortPendingLoad()
})

watch(() => augmentsData.value?.meta?.region, (region) => {
  if (!region) return
  selectedRegion.value = String(region).toUpperCase()
}, { immediate: true })

watch(() => augmentsData.value?.data, () => {
  if (!selectedChampion.value || !hasChampionData(selectedChampion.value)) {
    selectedChampion.value = resolvePreferredChampion()
  }
}, { immediate: true })

watch(() => appStore.currentChampionId, (championId) => {
  if (!championId || manualSelection.value) return
  const champion = getChampionById(championId)
  if (champion && champion.id !== selectedChampion.value?.id) {
    selectedChampion.value = champion
  }
}, { immediate: true })

watch(rankedAugments, (list) => {
  if (!list.length) {
    selectedAugment.value = null
    return
  }
  const currentKey = selectedAugment.value ? getAugmentKey(selectedAugment.value) : ''
  selectedAugment.value = list.find((item) => getAugmentKey(item) === currentKey) || list[0]
}, { immediate: true })

watch(isMayhemScrapedData, (enabled) => {
  if (enabled) {
    if (selectedTier.value === 'all') selectedTier.value = 'silver'
    if (!['default', 'popularity', 'strength'].includes(selectedSort.value)) selectedSort.value = 'default'
    return
  }
  if (!['default', 'pickRate', 'winRate', 'games'].includes(selectedSort.value)) selectedSort.value = 'default'
}, { immediate: true })

watch(() => appStore.gamePhase, (phase, previous) => {
  if (phase === 'ChampSelect') void syncCurrentChampion()
  if (previous === 'ChampSelect' && phase !== 'ChampSelect') manualSelection.value = false
})
</script>

<style scoped>
.augments-history-view {
  --aug-radius-lg: 16px;
  --aug-radius-md: 12px;
  --aug-surface: rgba(255, 255, 255, 0.03);
  --aug-border-soft: rgba(255, 255, 255, 0.06);
  --aug-shadow: 0 10px 28px rgba(0, 0, 0, 0.2);
  --aug-gap: 10px;
  height: 100%;
  overflow: auto;
  padding: 10px;
  color: var(--text-primary);
  background:
    radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 28%),
    radial-gradient(circle at top left, rgba(78, 204, 163, 0.08), transparent 24%),
    #0a0e1a;
}

.augments-shell {
  display: flex;
  flex-direction: column;
  gap: var(--aug-gap);
  min-height: 100%;
}

.surface-panel,
.status-banner,
.loading-panel {
  border-radius: var(--aug-radius-lg);
  border: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.02));
  box-shadow: var(--aug-shadow);
  backdrop-filter: blur(10px);
}

.status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  font-size: 12px;
}

.status-banner.info {
  color: var(--text-secondary);
}

.status-banner.warning {
  color: #ffb84d;
}

.status-banner.error {
  color: #ff8f8f;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.85;
}

.loading-panel {
  display: grid;
  place-items: center;
  min-height: 280px;
  padding: 24px;
  text-align: center;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 3px solid rgba(255, 255, 255, 0.12);
  border-top-color: rgba(91, 192, 255, 0.88);
  animation: spin 0.9s linear infinite;
}

.loading-title {
  margin-top: 14px;
  font-size: 16px;
  font-weight: 800;
}

.loading-subtitle {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: 288px minmax(0, 1fr);
  gap: var(--aug-gap);
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
  gap: var(--aug-gap);
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--aug-gap);
  min-width: 0;
}

.sidebar-panel,
.toolbar-panel,
.hero-overview-panel,
.augments-panel {
  padding: 12px;
}

.toolbar-panel {
  position: sticky;
  top: 0;
  z-index: 5;
}

.panel-head,
.toolbar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.panel-head--spaced {
  margin-bottom: 12px;
}

.panel-title,
.toolbar-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--text-primary);
}

.panel-subtitle,
.toolbar-subtitle {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.45;
}

.soft-badge {
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--aug-surface);
  border: 1px solid var(--aug-border-soft);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
}

.search-field,
.toolbar-search {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-field {
  margin-top: 12px;
}

.search-field span,
.toolbar-search span {
  color: var(--text-secondary);
  font-size: 11px;
}

.search-input,
.toolbar-search input {
  height: 40px;
  border-radius: var(--aug-radius-md);
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(9, 16, 30, 0.88);
  color: var(--text-primary);
  padding: 0 12px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.search-input:focus,
.toolbar-search input:focus {
  border-color: rgba(91, 192, 255, 0.6);
  box-shadow: 0 0 0 3px rgba(91, 192, 255, 0.1);
}

.hero-focus-card {
  margin-top: 12px;
  width: 100%;
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(135deg, rgba(52, 95, 168, 0.18), rgba(10, 16, 31, 0.64));
  text-align: left;
}

.hero-focus-avatar {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  object-fit: cover;
  border: 2px solid rgba(91, 192, 255, 0.44);
}

.hero-focus-main,
.hero-focus-title {
  min-width: 0;
}

.hero-focus-title strong {
  display: block;
  font-size: 16px;
  line-height: 1.15;
}

.hero-focus-title span,
.hero-focus-meta span {
  color: var(--text-secondary);
  font-size: 12px;
}

.hero-focus-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  flex-wrap: wrap;
}

.tier-pip {
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.champion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  max-height: 460px;
  overflow: auto;
  padding-right: 2px;
}

.champion-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 9px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  color: inherit;
  text-align: left;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.champion-row:hover,
.champion-row.active {
  background: rgba(91, 192, 255, 0.08);
  border-color: rgba(91, 192, 255, 0.28);
}

.champion-row.active {
  transform: translateY(-1px);
}

.champion-row__icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  object-fit: cover;
}

.champion-row__main,
.champion-row__meta {
  min-width: 0;
}

.champion-row__main strong {
  display: block;
  font-size: 13px;
  line-height: 1.2;
}

.champion-row__main span,
.champion-row__meta {
  color: var(--text-secondary);
  font-size: 11px;
}

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 34px;
  padding: 0 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.meta-row span {
  color: var(--text-secondary);
  font-size: 11px;
}

.meta-row strong {
  min-width: 0;
  text-align: right;
  font-size: 12px;
  color: var(--text-primary);
}

.meta-row strong.is-good {
  color: #7de3bf;
}

.meta-row strong.is-warn {
  color: #ffcc77;
}

.source-note {
  margin-top: 12px;
  padding: 10px 11px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.55;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.source-note--good {
  color: #92f0d3;
  background: rgba(78, 204, 163, 0.08);
}

.source-note--warn {
  color: #ffcf7e;
  background: rgba(255, 184, 77, 0.1);
}

.toolbar-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-stat {
  min-width: 96px;
  padding: 8px 10px;
  border-radius: var(--aug-radius-md);
  background: var(--aug-surface);
  border: 1px solid var(--aug-border-soft);
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
  font-size: 15px;
}

.toolbar-controls {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.toolbar-chip-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-chip {
  height: 30px;
  padding: 0 11px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.toolbar-chip--good {
  color: #7de3bf;
  border-color: rgba(78, 204, 163, 0.32);
}

.toolbar-chip--warn {
  color: #ffcf7e;
  border-color: rgba(255, 184, 77, 0.28);
}

.toolbar-actions {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-search {
  min-width: 280px;
}

.refresh-btn {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid rgba(91, 192, 255, 0.38);
  background: linear-gradient(135deg, rgba(91, 192, 255, 0.16), rgba(78, 204, 163, 0.12));
  color: #ecfcff;
  font-size: 13px;
  font-weight: 800;
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.refresh-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(91, 192, 255, 0.58);
}

.refresh-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hero-overview-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-overview-main {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
}

.hero-overview-avatar {
  width: 96px;
  height: 96px;
  border-radius: 24px;
  object-fit: cover;
  border: 2px solid rgba(91, 192, 255, 0.46);
  box-shadow: 0 16px 28px rgba(0, 0, 0, 0.26);
}

.hero-overview-copy,
.hero-overview-title-row {
  min-width: 0;
}

.hero-overview-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-overview-title-row h1 {
  font-size: 30px;
  font-weight: 900;
  line-height: 1.05;
  color: #f8fbff;
}

.hero-overview-title-row p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.hero-tier-badge {
  min-width: 90px;
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-tier-badge--t1,
.hero-tier-badge--t2,
.tier-pip.hero-tier-badge--t1,
.tier-pip.hero-tier-badge--t2 {
  color: #7de3bf;
  background: rgba(78, 204, 163, 0.12);
  border-color: rgba(78, 204, 163, 0.34);
}

.hero-tier-badge--t3,
.tier-pip.hero-tier-badge--t3 {
  color: #ffd582;
  background: rgba(255, 184, 77, 0.12);
  border-color: rgba(255, 184, 77, 0.34);
}

.hero-tier-badge--t4,
.tier-pip.hero-tier-badge--t4 {
  color: #9db6d2;
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
}

.hero-overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.hero-tag {
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.hero-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  min-height: 84px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.025);
}

.metric-card span {
  display: block;
  color: var(--text-secondary);
  font-size: 11px;
}

.metric-card strong {
  display: block;
  margin-top: 8px;
  color: var(--text-primary);
  font-size: 22px;
  line-height: 1.1;
}

.metric-card--highlight {
  background: linear-gradient(135deg, rgba(91, 192, 255, 0.11), rgba(78, 204, 163, 0.08));
  border-color: rgba(91, 192, 255, 0.2);
}

.tier-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tier-summary__item {
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.tier-summary__item--silver {
  color: #e6eef8;
  background: rgba(164, 180, 199, 0.1);
  border: 1px solid rgba(164, 180, 199, 0.22);
}

.tier-summary__item--gold {
  color: #fff1bb;
  background: rgba(255, 207, 66, 0.1);
  border: 1px solid rgba(255, 207, 66, 0.25);
}

.tier-summary__item--prismatic {
  color: #f2c7ff;
  background: rgba(195, 84, 255, 0.11);
  border: 1px solid rgba(195, 84, 255, 0.25);
}

.panel-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-tabs,
.sort-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tab,
.sort-tab {
  height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.025);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.filter-tab:hover,
.sort-tab:hover,
.filter-tab.active,
.sort-tab.active {
  color: var(--text-primary);
  border-color: rgba(91, 192, 255, 0.3);
  background: rgba(91, 192, 255, 0.08);
}

.filter-tab--silver.active {
  border-color: rgba(164, 180, 199, 0.36);
  background: rgba(164, 180, 199, 0.08);
}

.filter-tab--gold.active {
  border-color: rgba(255, 207, 66, 0.4);
  background: rgba(255, 207, 66, 0.1);
}

.filter-tab--prismatic.active {
  border-color: rgba(195, 84, 255, 0.42);
  background: rgba(195, 84, 255, 0.1);
}

.ranking-table {
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(5, 11, 22, 0.82);
}

.ranking-head,
.ranking-row {
  display: grid;
  grid-template-columns: 72px minmax(280px, 1fr) 112px 112px 112px 112px 112px;
  gap: 12px;
  align-items: center;
}

.ranking-head--mayhem,
.ranking-row--mayhem {
  grid-template-columns: 72px minmax(280px, 1fr) 112px 116px 116px;
}

.ranking-head {
  height: 44px;
  padding: 0 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 800;
  background: rgba(10, 18, 34, 0.92);
}

.ranking-head span:nth-child(n + 3) {
  text-align: center;
}

.ranking-body {
  display: flex;
  flex-direction: column;
}

.ranking-row {
  width: 100%;
  min-height: 80px;
  padding: 0 18px;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: transparent;
  color: inherit;
  text-align: left;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}

.ranking-row:last-child {
  border-bottom: none;
}

.ranking-row:hover,
.ranking-row.active {
  background: rgba(91, 192, 255, 0.07);
}

.ranking-row.active {
  box-shadow: inset 2px 0 0 rgba(91, 192, 255, 0.88);
}

.ranking-col {
  min-width: 0;
}

.ranking-col--index {
  color: #eff6ff;
  font-size: 14px;
  font-weight: 900;
}

.ranking-col--main {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.augment-icon-shell {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.augment-icon-shell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.augment-main-copy strong {
  display: block;
  color: #f8fbff;
  font-size: 15px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.augment-main-copy span {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranking-col--tier,
.ranking-col--metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.ranking-col--metric strong {
  color: #f7fbff;
  font-size: 15px;
  font-weight: 900;
}

.ranking-col--metric span {
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 11px;
}

.ranking-col--metric-highlight strong {
  color: #ffe38b;
}

.tier-pill {
  min-width: 76px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.tier-pill--silver {
  color: #e5edf8;
  border-color: rgba(164, 180, 199, 0.42);
  background: rgba(164, 180, 199, 0.08);
}

.tier-pill--gold {
  color: #fff4cf;
  border-color: rgba(255, 207, 66, 0.48);
  background: rgba(255, 207, 66, 0.08);
}

.tier-pill--prismatic {
  color: #f7dcff;
  border-color: rgba(195, 84, 255, 0.52);
  background: rgba(195, 84, 255, 0.09);
}

.tier-silver .ranking-col--index {
  color: #e4edf8;
}

.tier-gold .ranking-col--index {
  color: #ffe39b;
}

.tier-prismatic .ranking-col--index {
  color: #efb4ff;
}

.state-panel.empty {
  display: grid;
  place-items: center;
  min-height: 220px;
  padding: 24px;
  text-align: center;
}

.state-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 900;
}

.empty-title {
  margin-top: 14px;
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
}

.empty-subtitle {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1260px) {
  .content-grid {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  .hero-metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ranking-head,
  .ranking-row {
    grid-template-columns: 64px minmax(220px, 1fr) 100px 96px 96px 96px 96px;
  }

  .ranking-head--mayhem,
  .ranking-row--mayhem {
    grid-template-columns: 64px minmax(220px, 1fr) 100px 104px 104px;
  }
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .left-sticky,
  .toolbar-panel {
    position: static;
  }
}

@media (max-width: 820px) {
  .hero-overview-main {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .hero-overview-avatar {
    width: 72px;
    height: 72px;
    border-radius: 18px;
  }

  .hero-overview-title-row h1 {
    font-size: 24px;
  }

  .hero-metrics-grid {
    grid-template-columns: 1fr;
  }

  .ranking-head {
    display: none;
  }

  .ranking-row,
  .ranking-row--mayhem {
    grid-template-columns: 1fr;
    gap: 10px;
    min-height: auto;
    padding: 14px;
  }

  .ranking-col--index {
    display: none;
  }

  .ranking-col--tier,
  .ranking-col--metric {
    align-items: flex-start;
    text-align: left;
  }

  .toolbar-search {
    min-width: 100%;
  }
}
</style>
