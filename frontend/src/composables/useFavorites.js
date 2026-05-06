/**
 * 收藏管理 Composable
 * 管理用户收藏的符文配置
 */

import { ref, computed } from 'vue'

const FAVORITES_KEY = 'lol_rune_favorites'

// 全局状态
const favorites = ref([])

// 加载收藏
function loadFavorites() {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        favorites.value = parsed
      } else {
        console.warn('[useFavorites] localStorage 数据不是数组，重置为空')
        favorites.value = []
      }
      return
    }
  } catch (e) {
    console.error('[useFavorites] 加载收藏失败:', e)
  }
  favorites.value = []
}

// 保存收藏
function saveFavorites() {
  try {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites.value))
  } catch (e) {
    // 保存收藏失败，静默处理
  }
}

export function useFavorites() {
  /**
   * 添加收藏
   */
  function addFavorite(championId, position, config, rank) {
    const favorite = {
      id: `${championId}_${position}_${rank}`,
      championId,
      position,
      config,
      rank,
      addedAt: Date.now()
    }
    
    // 检查是否已存在
    const exists = favorites.value.some(f => f.id === favorite.id)
    if (exists) {
      return false
    }
    
    favorites.value.push(favorite)
    saveFavorites()
    return true
  }

  /**
   * 移除收藏
   */
  function removeFavorite(favoriteId) {
    const index = favorites.value.findIndex(f => f.id === favoriteId)
    if (index !== -1) {
      favorites.value.splice(index, 1)
      saveFavorites()
      return true
    }
    return false
  }

  /**
   * 检查是否已收藏
   */
  function isFavorite(championId, position, rank) {
    const id = `${championId}_${position}_${rank}`
    return favorites.value.some(f => f.id === id)
  }

  /**
   * 获取指定英雄的收藏
   */
  function getChampionFavorites(championId) {
    return favorites.value.filter(f => f.championId === championId)
  }

  /**
   * 获取指定位置的收藏
   */
  function getPositionFavorites(position) {
    return favorites.value.filter(f => f.position === position)
  }

  /**
   * 清空所有收藏
   */
  function clearFavorites() {
    favorites.value = []
    saveFavorites()
  }

  /**
   * 收藏数量
   */
  const favoritesCount = computed(() => favorites.value.length)

  /**
   * 按时间排序的收藏列表
   */
  const sortedFavorites = computed(() => {
    return [...favorites.value].sort((a, b) => b.addedAt - a.addedAt)
  })

  // 初始化时加载收藏
  if (favorites.value.length === 0) {
    loadFavorites()
  }

  return {
    favorites,
    favoritesCount,
    sortedFavorites,
    addFavorite,
    removeFavorite,
    isFavorite,
    getChampionFavorites,
    getPositionFavorites,
    clearFavorites
  }
}
