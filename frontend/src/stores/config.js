import { defineStore } from 'pinia'
import { ref } from 'vue'
import { bridge } from '@/utils/bridge'
import { champions as builtInChampions, searchChampions as searchBuiltIn, getChampionById as getBuiltIn } from '@/data/champions'

export const useConfigStore = defineStore('config', () => {
  // 简化：只保留全局 ban/pick 列表
  const banList = ref([])
  const pickList = ref([])
  
  // 使用内置英雄数据
  const champions = ref(builtInChampions)
  const loading = ref(false)

  // 获取配置
  async function fetchConfig() {
    loading.value = true
    try {
      const data = await bridge.getSelectConfig()
      if (data) {
        banList.value = data.ban || []
        pickList.value = data.pick || []
      }
    } catch (e) {
      // 获取配置失败，使用默认配置
    } finally {
      loading.value = false
    }
  }

  // 保存配置
  async function saveConfig() {
    try {
      await bridge.setSelectConfig(banList.value, pickList.value)
    } catch (e) {
      // 保存配置失败，静默处理
    }
  }

  // 添加英雄
  function addChampion(type, champId) {
    const list = type === 'ban' ? banList : pickList
    if (!list.value.includes(champId)) {
      list.value.push(champId)
      saveConfig()
    }
  }

  // 移除英雄
  function removeChampion(type, idx) {
    const list = type === 'ban' ? banList : pickList
    list.value.splice(idx, 1)
    saveConfig()
  }

  // 重新排序
  function reorderChampion(type, fromIdx, toIdx) {
    const list = type === 'ban' ? banList : pickList
    const [item] = list.value.splice(fromIdx, 1)
    list.value.splice(toIdx, 0, item)
    saveConfig()
  }

  function getChampionById(id) {
    return getBuiltIn(id)
  }

  function searchChampions(keyword) {
    return searchBuiltIn(keyword)
  }

  return {
    banList,
    pickList,
    champions,
    loading,
    fetchConfig,
    saveConfig,
    addChampion,
    removeChampion,
    reorderChampion,
    getChampionById,
    searchChampions
  }
})
