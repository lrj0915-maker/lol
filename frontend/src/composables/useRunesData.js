/**
 * 符文数据管理 Composable
 * 优化点：支持按英雄+分路加载，避免前端首次全量拉取 runes.json。
 */

import { ref, computed } from 'vue'
import { bridge } from '@/utils/bridge'
import { createIndexedDbStore } from '@/utils/indexedDbStore'

const runesData = ref({ data: {}, version: '', updateTime: '', meta: {} })
const isLoading = ref(false)
const loadError = ref(null)
const loadProgress = ref(0)
const lastLoadTime = ref(null)
const inflightLoadMap = new Map()
const requestTokenMap = new Map()
const ABORTED_TOKEN = '__ABORTED__'

const CACHE_DURATION = 2 * 60 * 60 * 1000
const CACHE_SCHEMA_VERSION = 'v2'

const DB_NAME = 'lol-assistant-cache'
const DB_VERSION = 3
const STORE_NAME = 'runes'
const cacheStore = createIndexedDbStore({
  dbName: DB_NAME,
  dbVersion: DB_VERSION,
  storeName: STORE_NAME,
})

function entryKey(championId, position = 'MID') {
  return `entry:${CACHE_SCHEMA_VERSION}:${Number(championId)}:${String(position || 'MID').toUpperCase()}`
}

function normalizeItemGroup(source) {
  const candidates = Array.isArray(source?.items)
    ? source.items
    : Array.isArray(source?.core_items)
      ? source.core_items
      : Array.isArray(source?.build_items)
        ? source.build_items
        : []

  return candidates
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      return {
        ids: Array.isArray(item.ids) ? item.ids : Array.isArray(item.item_ids) ? item.item_ids : [],
        play: Number(item.play || 0),
        win: Number(item.win || 0),
        pick_rate: Number(item.pick_rate || 0),
      }
    })
    .filter(Boolean)
}

function normalizeRunePages(source) {
  const candidates = Array.isArray(source?.rune_pages)
    ? source.rune_pages
    : Array.isArray(source?.perk_pages)
      ? source.perk_pages
      : []

  return candidates
    .map((page) => {
      if (!page || typeof page !== 'object') return null
      const builds = Array.isArray(page.builds) && page.builds.length ? page.builds : [page]
      // 将主 build 的符文ID提升到顶层，供 RuneConfigCard 直接使用
      const primaryBuild = builds[0] || {}
      return {
        ...page,
        play: Number(page.play || 0),
        win: Number(page.win || 0),
        pick_rate: Number(page.pick_rate || 0),
        builds,
        primary_rune_ids: Array.isArray(page.primary_rune_ids) ? page.primary_rune_ids : (Array.isArray(primaryBuild.primary_rune_ids) ? primaryBuild.primary_rune_ids : []),
        secondary_rune_ids: Array.isArray(page.secondary_rune_ids) ? page.secondary_rune_ids : (Array.isArray(primaryBuild.secondary_rune_ids) ? primaryBuild.secondary_rune_ids : []),
        stat_mod_ids: Array.isArray(page.stat_mod_ids) ? page.stat_mod_ids : (Array.isArray(primaryBuild.stat_mod_ids) ? primaryBuild.stat_mod_ids : []),
      }
    })
    .filter(Boolean)
}

function normalizePositionPayload(payload) {
  if (!payload || typeof payload !== 'object') return null
  return {
    ...payload,
    rune_pages: normalizeRunePages(payload),
    runes: normalizeRunePages(payload),
    core_items: normalizeItemGroup(payload),
    items: normalizeItemGroup(payload),
    boots: normalizeItemGroup({ items: payload.boots || payload.boot_items || [] }),
    starter_items: normalizeItemGroup({ items: payload.starter_items || payload.start_items || [] }),
    last_items: normalizeItemGroup({ items: payload.last_items || payload.final_items || [] }),
  }
}

export function useRunesData() {
  function isCacheValid(cacheTime) {
    if (!cacheTime) return false
    const age = Date.now() - Number(cacheTime)
    return age < CACHE_DURATION
  }

  function ensureDataShape() {
    if (!runesData.value || typeof runesData.value !== 'object') {
      runesData.value = { data: {}, version: '', updateTime: '', meta: {} }
      return
    }
    if (!runesData.value.data || typeof runesData.value.data !== 'object') {
      runesData.value.data = {}
    }
    if (!runesData.value.meta || typeof runesData.value.meta !== 'object') {
      runesData.value.meta = {}
    }
  }

  function normalizePositionData(positionData) {
    if (!positionData || typeof positionData !== 'object') return null
    return normalizePositionPayload(positionData)
  }

  function mergeEntryPayload(payload) {
    if (!payload?.success) return null
    ensureDataShape()

    const championId = String(payload.champion_id)
    const position = String(payload.position || 'MID').toUpperCase()
    const normalizedPositionData = normalizePositionData(payload.position_data) || {}

    const championBucket = runesData.value.data[championId] || { key: payload.champion_key || '', positions: {} }
    championBucket.key = payload.champion_key || championBucket.key || ''
    championBucket.positions = championBucket.positions || {}
    championBucket.positions[position] = normalizedPositionData

    runesData.value.data[championId] = championBucket
    if (payload.version) runesData.value.version = payload.version
    if (payload.updateTime) runesData.value.updateTime = payload.updateTime
    if (payload.meta) runesData.value.meta = payload.meta

    return championBucket.positions[position]
  }

  async function loadEntryFromCache(championId, position = 'MID') {
    try {
      const cached = await cacheStore.read(entryKey(championId, position))
      if (!cached || !cached.data || !isCacheValid(cached.cacheTime)) return null
      return cached.data
    } catch (error) {
      // 缓存加载失败，静默处理
      return null
    }
  }

  async function saveEntryToCache(championId, position = 'MID', payload = null) {
    if (!payload) return false
    try {
      await cacheStore.write(entryKey(championId, position), {
        data: payload,
        cacheTime: Date.now(),
      })
      return true
    } catch (error) {
      // 缓存保存失败，静默处理
      return false
    }
  }

  async function clearCache() {
    try {
      await cacheStore.clear()
      runesData.value = { data: {}, version: '', updateTime: '', meta: {} }
      lastLoadTime.value = null
    } catch (error) {
      // 缓存清理失败，静默处理
    }
  }

  async function getRunesStatus() {
    try {
      return await bridge.getRunesDataStatus()
    } catch {
      return null
    }
  }

  async function refreshRunesDataOnServer() {
    const result = await bridge.refreshRunesData()
    if (!result) throw new Error('无法触发符文全量更新')
    return result
  }

  async function refreshSingleRunesEntry(championId, championKey, position = 'MID', region = 'CN') {
    const result = await bridge.refreshRunesSingle(championId, championKey, position, region)
    if (result?.success) {
      const fresh = await bridge.getRunesEntry(championId, position)
      if (fresh?.success) {
        mergeEntryPayload(fresh)
        await saveEntryToCache(championId, position, fresh)
      }
    }
    return result
  }

  async function refreshSelectedRunesEntries(targets, region = 'CN', positions = null) {
    return bridge.refreshRunesSelected(targets, region, positions)
  }

  async function getChampionOverview(championKey, position = 'MID', region = 'CN') {
    try {
      return await bridge.getChampionOverview(championKey, position, region)
    } catch {
      return null
    }
  }

  async function loadRunesData(forceRefresh = false, championId = null, position = 'MID') {
    if (!championId) {
      ensureDataShape()
      return runesData.value
    }

    const normalizedPosition = String(position || 'MID').toUpperCase()
    const key = entryKey(championId, normalizedPosition)

    if (!forceRefresh && inflightLoadMap.has(key)) {
      return inflightLoadMap.get(key)
    }

    isLoading.value = true
    loadError.value = null
    loadProgress.value = 0

    const token = `${Date.now()}-${Math.random()}`
    requestTokenMap.set(key, token)

    const work = (async () => {
      try {
        let payload = null

        if (!forceRefresh) {
          loadProgress.value = 20
          payload = await loadEntryFromCache(championId, normalizedPosition)
        }

        if (!payload) {
          loadProgress.value = 55
          payload = await bridge.getRunesEntry(championId, normalizedPosition)
          // CHAMPION_NOT_FOUND / POSITION_NOT_FOUND / RUNE_DATA_NOT_FOUND 属于可恢复状态，
          // 不抛异常，让 ensureCurrentPositionData 自动从服务器拉取
          const recoverable = ['CHAMPION_NOT_FOUND', 'POSITION_NOT_FOUND', 'RUNE_DATA_NOT_FOUND']
          if (!payload || (payload.error && !recoverable.includes(payload.error))) {
            throw new Error(payload?.message || payload?.error || '符文数据获取失败')
          }
          if (payload.success) {
            await saveEntryToCache(championId, normalizedPosition, payload)
          }
        }

        if (requestTokenMap.get(key) !== token || requestTokenMap.get(key) === ABORTED_TOKEN) {
          return runesData.value
        }

        if (payload?.success) {
          mergeEntryPayload(payload)
        }

        loadProgress.value = 100
        lastLoadTime.value = Date.now()
        return runesData.value
      } catch (error) {
        loadError.value = error?.message || '未知错误'
        throw error
      } finally {
        inflightLoadMap.delete(key)
        if (requestTokenMap.get(key) === token || requestTokenMap.get(key) === ABORTED_TOKEN) {
          requestTokenMap.delete(key)
        }
        isLoading.value = false
      }
    })()

    inflightLoadMap.set(key, work)
    return work
  }

  function abortPendingLoad(championId = null, position = 'MID') {
    if (!championId) {
      for (const currentKey of requestTokenMap.keys()) {
        requestTokenMap.set(currentKey, ABORTED_TOKEN)
      }
      return
    }
    const normalizedPosition = String(position || 'MID').toUpperCase()
    const key = entryKey(championId, normalizedPosition)
    if (requestTokenMap.has(key)) {
      requestTokenMap.set(key, ABORTED_TOKEN)
    }
  }

  function getChampionRunes(championId) {
    ensureDataShape()
    return runesData.value.data[String(championId)] || null
  }

  function getChampionPositionRunes(championId, position) {
    const championData = getChampionRunes(championId)
    if (!championData?.positions) return null
    return championData.positions[String(position || 'MID').toUpperCase()] || null
  }

  /**
   * 后台静默刷新：不触发 isLoading，不抛异常，不影响当前展示的缓存数据。
   * 成功后自动写入 IndexedDB，下次启动秒开。
   */
  async function silentRefresh(championId, position = 'MID') {
    if (!championId) return
    const normalizedPosition = String(position || 'MID').toUpperCase()
    try {
      let payload = await bridge.getRunesEntry(championId, normalizedPosition)
      const recoverable = ['CHAMPION_NOT_FOUND', 'POSITION_NOT_FOUND', 'RUNE_DATA_NOT_FOUND']
      if (!payload || (payload.error && !recoverable.includes(payload.error))) return
      if (payload.success) {
        mergeEntryPayload(payload)
        await saveEntryToCache(championId, normalizedPosition, payload)
      }
    } catch {
      // 静默刷新失败不打扰用户
    }
  }

  /**
   * 秒开预填：直接从 IndexedDB 加载缓存，不设 isLoading，不阻塞 UI。
   * 返回 true 表示有可用缓存并已回填，false 表示需要正常加载。
   */
  async function preloadFromCache(championId, position = 'MID') {
    if (!championId) return false
    const normalizedPosition = String(position || 'MID').toUpperCase()
    const cached = await loadEntryFromCache(championId, normalizedPosition)
    if (!cached || !cached.success) return false
    mergeEntryPayload(cached)
    lastLoadTime.value = Date.now()
    return true
  }

  const dataStats = computed(() => {
    ensureDataShape()
    const champions = Object.keys(runesData.value.data || {})
    let totalConfigs = 0
    let totalPositions = 0

    champions.forEach((championId) => {
      const championData = runesData.value.data[championId]
      if (championData?.positions) {
        const positions = Object.keys(championData.positions)
        totalPositions += positions.length
        positions.forEach((currentPosition) => {
          const positionData = championData.positions[currentPosition]
          if (positionData?.rune_pages) {
            totalConfigs += positionData.rune_pages.length
          }
        })
      }
    })

    return {
      champions: champions.length,
      positions: totalPositions,
      configs: totalConfigs,
      version: runesData.value.version,
      updateTime: runesData.value.updateTime,
      cached: false,
      cacheTime: null,
    }
  })

  return {
    runesData,
    isLoading,
    loadError,
    loadProgress,
    lastLoadTime,
    dataStats,

    loadRunesData,
    getChampionRunes,
    getChampionPositionRunes,
    clearCache,
    isCacheValid,
    getRunesStatus,
    refreshRunesDataOnServer,
    refreshSingleRunesEntry,
    refreshSelectedRunesEntries,
    getChampionOverview,
    mergeEntryPayload,
    abortPendingLoad,
    preloadFromCache,
    silentRefresh,
  }
}
