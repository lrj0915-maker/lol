<template>
  <div class="rune-card" :class="{ expanded }">
    <!-- 折叠态：一行摘要 -->
    <div class="card-header" @click="expanded = !expanded">
      <span class="rank" :class="`r${rank}`">{{ rank <= 3 ? ['🥇','🥈','🥉'][rank-1] : `#${rank}` }}</span>

      <div class="header-info">
        <span class="tree-label">{{ primaryTreeName }} + {{ secondaryTreeName }}</span>
        <!-- 登场率 -->
        <span class="pick-rate">{{ formatRatePercent(config.pick_rate, 2) }} 登场</span>
        <PopularityBadge :games="config.play" :total-games="totalGames" />
      </div>

      <div class="header-wr">
        <WinRateBar :wins="config.win" :games="config.play" />
      </div>

      <button
        class="apply-btn"
        :disabled="isApplying"
        @click.stop="applyRunes"
      >
        {{ isApplying ? '⏳' : '⚡' }} 应用
      </button>

      <span class="caret">{{ expanded ? '▾' : '›' }}</span>
    </div>

    <!-- 展开态：横排符文 -->
    <div v-if="expanded" class="card-body">
      <!-- 核心数据行 -->
      <div class="body-stats">
        <span class="stat-item">
          <span class="stat-label">胜率</span>
          <span class="stat-val" :class="winRateClass(config.play ? config.win / config.play : 0)">{{ formatWinRate(config) }}</span>
        </span>
        <span class="stat-divider">|</span>
        <span class="stat-item">
          <span class="stat-label">场次</span>
          <span class="stat-val">{{ config.play || 0 }}</span>
        </span>
      </div>

      <div class="runes-row">
        <!-- 主系 -->
        <div class="rune-group primary-group">
          <div class="group-label" :style="{ color: primaryColor }">{{ primaryTreeName }}</div>
          <div class="rune-icons">
            <div class="rune-icon keystone" :style="{ borderColor: primaryColor }">
              <img :src="getRuneIconUrl(config.primary_rune_ids?.[0])" @error="imgErr" />
              <span class="rune-tip">{{ getRuneLabel(config.primary_rune_ids?.[0]) }}</span>
            </div>
            <span class="arrow">→</span>
            <div v-for="(id, i) in (config.primary_rune_ids || []).slice(1)" :key="i" class="rune-icon">
              <img :src="getRuneIconUrl(id)" @error="imgErr" />
              <span class="rune-tip">{{ getRuneLabel(id) }}</span>
            </div>
          </div>
        </div>

        <!-- 副系 -->
        <div class="rune-group secondary-group">
          <div class="group-label" :style="{ color: secondaryColor }">{{ secondaryTreeName }}</div>
          <div class="rune-icons">
            <div v-for="(id, i) in (config.secondary_rune_ids || [])" :key="i" class="rune-icon">
              <img :src="getRuneIconUrl(id)" @error="imgErr" />
              <span class="rune-tip">{{ getRuneLabel(id) }}</span>
            </div>
          </div>
        </div>

        <!-- 碎片 -->
        <div class="rune-group shard-group">
          <div class="group-label">碎片</div>
          <div class="rune-icons">
            <div v-for="(id, i) in (config.stat_mod_ids || [])" :key="i" class="rune-icon shard">
              <img :src="getShardIconUrl(id)" @error="imgErr" />
              <span class="rune-tip">{{ getShardLabel(id) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 次要操作 -->
      <div class="body-actions">
        <button class="small-btn" :class="{ active: isFavorited }" @click="toggleFavorite">
          {{ isFavorited ? '⭐ 已收藏' : '☆ 收藏' }}
        </button>
        <button class="small-btn" :class="{ active: showTrend }" @click="showTrend = !showTrend">
          📈 趋势
        </button>
      </div>

      <WinRateTrendChart
        v-if="showTrend"
        :configs="[{ rank, data: config }]"
        :champion-id="championId"
        :position="position"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, ref } from 'vue'
import WinRateBar from './WinRateBar.vue'
import PopularityBadge from './PopularityBadge.vue'
import { getTreeById, getRuneById, getRuneIconUrl, getStatShardById, getStatShardIconUrl } from '@/data/runes'
import { formatWinRate, winRateClass, formatRatePercent } from '@/utils/runesViewHelpers'
import { useFavorites } from '@/composables/useFavorites'
import bridge from '@/utils/bridge'

const WinRateTrendChart = defineAsyncComponent(() => import('./WinRateTrendChart.vue'))

const props = defineProps({
  config: { type: Object, required: true },
  rank: { type: Number, required: true },
  championId: { type: String, default: '' },
  championName: { type: String, default: '' },
  position: { type: String, default: '' },
  totalGames: { type: Number, default: 0 },
})

const emit = defineEmits(['applied'])
const expanded = ref(props.rank === 1)
const isApplying = ref(false)
const showTrend = ref(false)
const { isFavorite, addFavorite, removeFavorite } = useFavorites()

const isFavorited = computed(() => isFavorite(props.championId, props.position, props.rank))

const primaryTree = computed(() => getTreeById(props.config.primary_page_id))
const secondaryTree = computed(() => getTreeById(props.config.secondary_page_id))
const primaryTreeName = computed(() => primaryTree.value?.name || '未知')
const secondaryTreeName = computed(() => secondaryTree.value?.name || '未知')
const primaryColor = computed(() => primaryTree.value?.color || '#888')
const secondaryColor = computed(() => secondaryTree.value?.color || '#888')

function getRuneLabel(id) { return getRuneById(id)?.name || '未知' }
function getShardLabel(id) { return getStatShardById(id)?.name || '未知' }
function getShardIconUrl(id) { return getStatShardIconUrl(id) }
function imgErr(e) { e.target.style.opacity = '0.3' }

function toggleFavorite() {
  if (isFavorited.value) removeFavorite(`${props.championId}_${props.position}_${props.rank}`)
  else addFavorite(props.championId, props.position, props.config, props.rank)
}

function applyRunes() {
  if (isApplying.value) return
  isApplying.value = true
  bridge.applyRuneConfig(props.config, props.championName || '', props.position || '')
    .then(result => {
      emit('applied', { success: !!result?.success, message: result?.message, code: result?.code || (result?.success ? 'OK' : 'RUNE_APPLY_FAILED') })
    })
    .catch(error => {
      emit('applied', { success: false, message: error?.message || '应用失败', code: 'RUNE_APPLY_EXCEPTION' })
    })
    .finally(() => { isApplying.value = false })
}
</script>

<style scoped>
.rune-card {
  background: #111827;
  border: 1px solid #1e293b;
  border-radius: 8px;
  transition: border-color 0.15s;
  overflow: hidden;
}

.rune-card:hover { border-color: #334155; }
.rune-card.expanded { border-color: #4ECCB3; }

/* ===== Header ===== */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.1s;
}

.card-header:hover { background: #0f1525; }

.rank { font-size: 18px; min-width: 28px; text-align: center; }
.r1, .r2, .r3 { font-size: 20px; }

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  min-width: 0;
}

.tree-label {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
}

.header-wr {
  flex: 1 1 0;
  min-width: 120px;
  max-width: 260px;
}

.apply-btn {
  flex-shrink: 0;
  height: 28px;
  padding: 0 12px;
  border: none;
  border-radius: 5px;
  background: #4ECCB3;
  color: #0a0e1a;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}

.apply-btn:hover { background: #5dd4b4; }
.apply-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.caret {
  color: #475569;
  font-size: 14px;
  min-width: 14px;
  text-align: center;
}

/* ===== Body ===== */
.card-body {
  padding: 10px 12px;
  border-top: 1px solid #1e293b;
}

/* ===== 展开态数据行 ===== */
.body-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #141c2e;
}

.body-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.body-stats .stat-label {
  color: #64748b;
}

.body-stats .stat-val {
  color: #e2e8f0;
  font-weight: 600;
}

.body-stats .stat-divider {
  color: #1e293b;
}

.body-stats .wr-high { color: #4ECCB3 !important; }
.body-stats .wr-ok { color: #e2e8f0 !important; }
.body-stats .wr-low { color: #fb7185 !important; }

/* ===== 横排符文 ===== */
.runes-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.rune-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.group-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.rune-icons {
  display: flex;
  align-items: center;
  gap: 6px;
}

.arrow {
  color: #334155;
  font-size: 12px;
}

.rune-icon {
  position: relative;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px solid #1e293b;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s;
  background: #0a0e1a;
}

.rune-icon:hover {
  transform: scale(1.15);
  border-color: #4ECCB3;
}

.rune-icon.keystone {
  width: 42px;
  height: 42px;
  border-width: 2px;
}

.rune-icon.shard {
  width: 26px;
  height: 26px;
  border-radius: 5px;
}

.rune-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rune-icon.shard img {
  padding: 3px;
}

.rune-tip {
  position: absolute;
  bottom: -24px;
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #e2e8f0;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
  z-index: 10;
}

.rune-icon:hover .rune-tip { opacity: 1; }

/* ===== 次要操作 ===== */
.body-actions {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}

.small-btn {
  height: 26px;
  padding: 0 10px;
  border: 1px solid #1e293b;
  border-radius: 4px;
  background: #0f1525;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.small-btn:hover { border-color: #334155; color: #e2e8f0; }
.small-btn.active { border-color: #4ECCB3; color: #4ECCB3; }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .card-header { flex-wrap: wrap; gap: 6px; }
  .header-wr { flex: 1 1 100%; max-width: none; }
  .runes-row { gap: 10px; }
  .rune-icon { width: 30px; height: 30px; }
  .rune-icon.keystone { width: 36px; height: 36px; }
}

@media (prefers-reduced-motion: reduce) {
  .rune-card, .card-header, .apply-btn, .rune-icon, .small-btn {
    transition: none !important;
  }
}
</style>
