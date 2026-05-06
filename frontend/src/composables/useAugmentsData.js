import { computed, ref } from 'vue'
import { bridge } from '@/utils/bridge'
import { createIndexedDbStore } from '@/utils/indexedDbStore'

const augmentsData = ref(null)
const isLoading = ref(false)
const loadError = ref(null)
const loadProgress = ref(0)
const lastLoadTime = ref(null)
let inflightPromise = null
let requestToken = null
const ABORTED_TOKEN = '__ABORTED__'

const CACHE_DURATION = 30 * 60 * 1000
const DB_NAME = 'lol-assistant-augments-cache'
const DB_VERSION = 1
const STORE_NAME = 'augments'
const AUGMENTS_CACHE_KEY = 'augments_data'
const cacheStore = createIndexedDbStore({
  dbName: DB_NAME,
  dbVersion: DB_VERSION,
  storeName: STORE_NAME,
})

export function useAugmentsData() {
  function isCacheValid(cacheTime) {
    if (!cacheTime) return false
    const age = Date.now() - Number(cacheTime)
    return age < CACHE_DURATION
  }

  async function loadFromCache({ allowStale = false } = {}) {
    try {
      const cached = await cacheStore.read(AUGMENTS_CACHE_KEY)
      if (!cached || !cached.data) return null

      const isValid = isCacheValid(cached.cacheTime)
      if (!allowStale && !isValid) return null

      return {
        ...cached.data,
        _cached: true,
        _cacheTime: cached.cacheTime,
        _stale: !isValid,
      }
    } catch {
      return null
    }
  }

  async function saveToCache(data) {
    try {
      const { _cached, _cacheTime, ...cleanData } = data
      await cacheStore.write(AUGMENTS_CACHE_KEY, {
        data: cleanData,
        cacheTime: Date.now(),
      })
      return true
    } catch {
      return false
    }
  }

  async function clearCache() {
    try {
      await cacheStore.remove(AUGMENTS_CACHE_KEY)
    } catch {
    }
  }

  async function getAugmentsStatus() {
    try {
      return await bridge.getAugmentsDataStatus()
    } catch {
      return null
    }
  }

  async function refreshAugmentsDataOnServer() {
    const result = await bridge.refreshAugmentsData()
    if (!result) throw new Error('刷新强化数据失败')
    return result
  }

  async function loadFromAPI() {
    loadProgress.value = 20
    const data = await bridge.getAugmentsData()
    loadProgress.value = 75

    if (!data || data.error) {
      throw new Error(data?.error || '获取强化数据失败')
    }

    if (!data.data || typeof data.data !== 'object') {
      throw new Error('强化数据格式异常：缺少 data 字段')
    }

    loadProgress.value = 100
    return data
  }

  async function loadAugmentsData(forceRefresh = false) {
    if (inflightPromise) {
      return inflightPromise
    }

    if (augmentsData.value && !forceRefresh) {
      return augmentsData.value
    }

    isLoading.value = true
    loadError.value = null
    loadProgress.value = 0
    requestToken = `${Date.now()}-${Math.random()}`

    inflightPromise = (async () => {
      let staleCache = null

      try {
        let data = null

        if (!forceRefresh) {
          data = await loadFromCache()
          if (data) {
            augmentsData.value = data
            lastLoadTime.value = Date.now()
            loadProgress.value = 100
            return data
          }

          staleCache = await loadFromCache({ allowStale: true })
          if (staleCache) {
            augmentsData.value = staleCache
            lastLoadTime.value = Date.now()
            loadProgress.value = 35
          }
        }

        data = await loadFromAPI()

        if (!requestToken || requestToken === ABORTED_TOKEN) {
          return augmentsData.value
        }

        await saveToCache(data)
        augmentsData.value = data
        lastLoadTime.value = Date.now()
        return data
      } catch (error) {
        loadError.value = error?.message || '加载强化数据失败'
        if (staleCache) {
          return staleCache
        }
        throw error
      } finally {
        isLoading.value = false
        inflightPromise = null
        if (requestToken !== ABORTED_TOKEN) {
          requestToken = null
        }
      }
    })()

    return inflightPromise
  }

  function abortPendingLoad() {
    requestToken = ABORTED_TOKEN
  }

  const dataStats = computed(() => {
    if (!augmentsData.value?.data) {
      return null
    }

    return {
      champions: Object.keys(augmentsData.value.data).length,
      updateTime: augmentsData.value.updateTime || '',
      cached: augmentsData.value._cached || false,
      stale: augmentsData.value._stale || false,
      cacheTime: augmentsData.value._cacheTime || null,
    }
  })

  return {
    augmentsData,
    isLoading,
    loadError,
    loadProgress,
    lastLoadTime,
    dataStats,
    loadAugmentsData,
    clearCache,
    isCacheValid,
    getAugmentsStatus,
    refreshAugmentsDataOnServer,
    abortPendingLoad,
  }
}
