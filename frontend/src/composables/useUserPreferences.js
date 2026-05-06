/**
 * 用户偏好管理 Composable
 * 使用 localStorage 持久化用户设置
 */
import { ref, watch } from 'vue'

const STORAGE_KEY = 'lol-assistant-preferences'

// 默认偏好设置
const defaultPreferences = {
  // 符文相关
  runes: {
    lastPosition: 'MID',  // 上次选择的位置
    sortBy: 'winRate',    // 排序方式: 'winRate' | 'games'
    autoExpand: true,     // 是否自动展开第一个配置
    showTooltips: true,   // 是否显示符文提示
    activeRegion: 'CN',   // 默认区服
    selectedChampions: [] // 已选英雄历史
  },
  // 界面相关
  ui: {
    theme: 'dark',        // 主题: 'dark' | 'light'
    compactMode: false,   // 紧凑模式
    animationsEnabled: true  // 动画开关
  },
  // 其他偏好
  general: {
    language: 'zh-CN',    // 语言
    autoUpdate: true      // 自动更新数据
  }
}

class UserPreferences {
  constructor() {
    this.preferences = ref(this.load())
    this._saveTimer = null

    // 监听变化并自动保存（防抖 300ms）
    watch(
      () => this.preferences.value,
      (newPrefs) => {
        if (this._saveTimer) clearTimeout(this._saveTimer)
        this._saveTimer = setTimeout(() => {
          this._saveTimer = null
          this.save(newPrefs)
        }, 300)
      },
      { deep: true }
    )
  }
  
  /**
   * 从 localStorage 加载偏好设置
   */
  load() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          return this.mergeDeep(defaultPreferences, parsed)
        }
        console.warn('[useUserPreferences] localStorage 数据不是对象，使用默认配置')
      }
    } catch (error) {
      console.error('[useUserPreferences] 加载偏好设置失败:', error)
    }
    return JSON.parse(JSON.stringify(defaultPreferences))
  }
  
  /**
   * 保存偏好设置到 localStorage
   */
  save(preferences) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
    } catch (error) {
      // 保存失败，检查是否是存储空间不足
      if (error.name === 'QuotaExceededError') {
        this.cleanup()
      }
    }
  }
  
  /**
   * 深度合并对象
   */
  mergeDeep(target, source) {
    const output = Object.assign({}, target)
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] })
          } else {
            output[key] = this.mergeDeep(target[key], source[key])
          }
        } else {
          Object.assign(output, { [key]: source[key] })
        }
      })
    }
    return output
  }
  
  /**
   * 检查是否为对象
   */
  isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item)
  }
  
  /**
   * 获取符文偏好
   */
  getRunePreferences() {
    return this.preferences.value.runes
  }
  
  /**
   * 设置符文偏好
   */
  setRunePreferences(prefs) {
    this.preferences.value.runes = {
      ...this.preferences.value.runes,
      ...prefs
    }
  }
  
  /**
   * 获取上次选择的位置
   */
  getLastPosition() {
    return this.preferences.value.runes.lastPosition
  }
  
  /**
   * 设置上次选择的位置
   */
  setLastPosition(position) {
    this.preferences.value.runes.lastPosition = position
  }
  
  /**
   * 获取排序方式
   */
  getSortBy() {
    return this.preferences.value.runes.sortBy
  }
  
  /**
   * 设置排序方式
   */
  setSortBy(sortBy) {
    this.preferences.value.runes.sortBy = sortBy
  }

  /**
   * 获取当前区服
   */
  getActiveRegion() {
    return this.preferences.value.runes.activeRegion || 'CN'
  }

  /**
   * 设置当前区服
   */
  setActiveRegion(region) {
    const normalized = String(region || 'CN').toUpperCase().trim() || 'CN'
    this.preferences.value.runes.activeRegion = normalized
  }

  /**
   * 获取已选英雄历史
   */
  getSelectedChampions() {
    const history = this.preferences.value.runes.selectedChampions
    if (!Array.isArray(history)) return []
    return history
      .filter(item => item && Number(item.championId) > 0 && item.championKey)
      .slice(0, 30)
  }

  /**
   * 记录已选英雄（用于增量刷新）
   */
  rememberSelectedChampion(champion, position = 'MID') {
    if (!champion || !champion.id || !champion.key) return

    const championId = Number(champion.id)
    const championKey = String(champion.key || '').toLowerCase().trim()
    const normalizedPosition = String(position || 'MID').toUpperCase().trim() || 'MID'
    const now = Date.now()

    const previous = this.getSelectedChampions()
    const existing = previous.find(item => Number(item.championId) === championId)

    const mergedPositions = Array.from(new Set([...(existing?.positions || []), normalizedPosition]))

    const nextItem = {
      championId,
      championKey,
      championName: champion.name || existing?.championName || '',
      lastPosition: normalizedPosition,
      positions: mergedPositions,
      updatedAt: now,
    }

    const next = [
      nextItem,
      ...previous.filter(item => Number(item.championId) !== championId),
    ].slice(0, 30)

    this.preferences.value.runes.selectedChampions = next
  }

  /**
   * 清空已选英雄历史
   */
  clearSelectedChampions() {
    this.preferences.value.runes.selectedChampions = []
  }

  /**
   * 重置为默认设置
   */
  reset() {
    this.preferences.value = JSON.parse(JSON.stringify(defaultPreferences))
  }
  
  /**
   * 清理旧数据
   */
  cleanup() {
    try {
      // 清理其他可能的旧数据
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('lol-assistant-') && key !== STORAGE_KEY) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
    } catch (error) {
      // 清理失败，静默处理
    }
  }
  
  /**
   * 导出设置
   */
  export() {
    return JSON.stringify(this.preferences.value, null, 2)
  }
  
  /**
   * 导入设置
   */
  import(jsonString) {
    try {
      const imported = JSON.parse(jsonString)
      this.preferences.value = this.mergeDeep(defaultPreferences, imported)
      return true
    } catch (error) {
      // 导入失败
      return false
    }
  }
}

// 单例实例
let instance = null

/**
 * 使用用户偏好
 */
export function useUserPreferences() {
  if (!instance) {
    instance = new UserPreferences()
  }
  return instance
}

// 导出默认偏好设置（用于测试）
export { defaultPreferences }
