import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { bridge } from '@/utils/bridge'

const DEV = import.meta.env.DEV

function defaultBattleFilters() {
  return {
    game_mode: '',
    champion_id: null,
    result: '',
    time_range: '',
    teammate: '',
  }
}

export const useMatchStore = defineStore('match', () => {
  const currentMatch = ref(null)
  const historyList = ref([])
  const loading = ref(false)
  const liveGameData = ref(null)
  const liveLoading = ref(false)
  const _fromHistory = ref(false)
  const _liveTimer = ref(null)

  const battleProfile = ref({})
  const battleSummary = ref({})
  const battleHeroUsage = ref([])
  const battleRecentTeammates = ref([])
  const battleHistoryPage = ref({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 1,
    filters_applied: {},
  })
  const battleFilters = reactive(defaultBattleFilters())
  const battleExpandedMatchId = ref(null)
  const battleMatchDetailsCache = ref({})
  const battleLoadingStates = reactive({
    profile: false,
    history: false,
    refreshing: false,
    detailIds: {},
  })
  const battleDetailErrors = ref({})
  const battleStatus = ref({ type: '', message: '' })

  function applyBattleProfilePayload(payload) {
    battleProfile.value = payload?.profile || {}
    battleSummary.value = payload?.summary || {}
    battleHeroUsage.value = payload?.hero_usage || []
    battleRecentTeammates.value = payload?.recent_teammates || []
    return payload
  }

  function setBattleStatus(type = '', message = '') {
    battleStatus.value = { type, message }
  }

  function clearBattleStatus() {
    setBattleStatus('', '')
  }

  async function fetchCurrentMatch() {
    loading.value = true
    try {
      const data = await bridge.getCurrentMatchStats()
      currentMatch.value = data
    } catch (error) {
      console.error('fetchCurrentMatch failed', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchHistoryList(options = {}) {
    loading.value = true
    try {
      const { limit = 50, offset = 0, gameMode, championId } = options
      const data = await bridge.getMatchHistoryList(limit, offset, gameMode, championId)
      historyList.value = data || []
    } finally {
      loading.value = false
    }
  }

  async function fetchMatchDetail(gameId) {
    return await bridge.getMatchDetail(gameId)
  }

  function setCurrentMatch(data) {
    currentMatch.value = data
  }

  function setFromHistory(val = true) {
    _fromHistory.value = val
  }

  function consumeFromHistory() {
    if (_fromHistory.value) {
      _fromHistory.value = false
      return true
    }
    return false
  }

  async function fetchBattleProfileSummary(options = {}) {
    const { refresh = false } = options
    if (refresh) {
      battleLoadingStates.refreshing = true
    } else {
      battleLoadingStates.profile = true
    }
    try {
      const result = refresh
        ? await bridge.refreshBattleProfileSummary()
        : await bridge.getBattleProfileSummary()
      const payload = result?.data || result || {}
      applyBattleProfilePayload(payload)

      if (refresh) {
        if (result?.success === false) {
          setBattleStatus('warning', result?.message || '刷新失败，已保留当前缓存数据')
        } else {
          setBattleStatus('success', '战绩中心已刷新为最新缓存')
        }
      } else if (payload?.profile?.is_online === false) {
        setBattleStatus('info', '当前为离线缓存模式，展示数据可能不是最新')
      } else {
        clearBattleStatus()
      }

      return payload
    } catch (error) {
      if (refresh) {
        setBattleStatus('warning', error?.message || '刷新失败，已保留当前缓存数据')
      }
      throw error
    } finally {
      battleLoadingStates.profile = false
      battleLoadingStates.refreshing = false
    }
  }

  async function fetchBattleHistoryPage(options = {}) {
    battleLoadingStates.history = true
    try {
      const page = options.page || battleHistoryPage.value.page || 1
      const pageSize = options.pageSize || battleHistoryPage.value.page_size || 20
      const filters = {
        ...battleFilters,
        ...(options.filters || {}),
      }
      const result = await bridge.getBattleHistoryPage(page, pageSize, filters)
      battleHistoryPage.value = result || {
        items: [],
        page,
        page_size: pageSize,
        total: 0,
        total_pages: 1,
        filters_applied: filters,
      }
      return battleHistoryPage.value
    } finally {
      battleLoadingStates.history = false
    }
  }

  function setBattleFilter(patch, resetPage = true) {
    Object.assign(battleFilters, patch || {})
    if (resetPage) {
      battleHistoryPage.value.page = 1
    }
  }

  function resetBattleFilters() {
    Object.assign(battleFilters, defaultBattleFilters())
    battleHistoryPage.value.page = 1
  }

  async function setBattlePage(page) {
    battleHistoryPage.value.page = page
    return await fetchBattleHistoryPage({ page })
  }

  async function setBattlePageSize(pageSize) {
    battleHistoryPage.value.page_size = pageSize
    battleHistoryPage.value.page = 1
    return await fetchBattleHistoryPage({ page: 1, pageSize })
  }

  async function toggleBattleMatchDetail(gameId) {
    if (battleExpandedMatchId.value === gameId) {
      battleExpandedMatchId.value = null
      return null
    }
    battleExpandedMatchId.value = gameId
    if (battleMatchDetailsCache.value[gameId]) {
      return battleMatchDetailsCache.value[gameId]
    }
    delete battleDetailErrors.value[gameId]
    battleLoadingStates.detailIds[gameId] = true
    try {
      const detail = await bridge.getBattleMatchDetail(gameId)
      if (detail && detail.game_id) {
        battleMatchDetailsCache.value = {
          ...battleMatchDetailsCache.value,
          [gameId]: detail,
        }
        return detail
      }
      battleDetailErrors.value = {
        ...battleDetailErrors.value,
        [gameId]: '详情加载失败，请稍后重试',
      }
      return null
    } catch (error) {
      battleDetailErrors.value = {
        ...battleDetailErrors.value,
        [gameId]: error?.message || '详情加载失败，请稍后重试',
      }
      return null
    } finally {
      delete battleLoadingStates.detailIds[gameId]
    }
  }

  async function retryBattleMatchDetail(gameId) {
    const nextCache = { ...battleMatchDetailsCache.value }
    delete nextCache[gameId]
    battleMatchDetailsCache.value = nextCache

    const nextErrors = { ...battleDetailErrors.value }
    delete nextErrors[gameId]
    battleDetailErrors.value = nextErrors

    battleExpandedMatchId.value = null
    return await toggleBattleMatchDetail(gameId)
  }

  function getBattleMatchDetailFromCache(gameId) {
    return battleMatchDetailsCache.value[gameId] || null
  }

  function clearBattleDetailCache() {
    battleMatchDetailsCache.value = {}
    battleDetailErrors.value = {}
    battleExpandedMatchId.value = null
  }

  async function fetchLiveGameData() {
    liveLoading.value = true
    try {
      const data = await bridge.getLiveGameData()
      if (data && data.success) {
        liveGameData.value = data
      }
      return data
    } catch (error) {
      console.error('fetchLiveGameData failed', error)
      return null
    } finally {
      liveLoading.value = false
    }
  }

  function startLivePolling() {
    stopLivePolling()
    fetchLiveGameData()
    _liveTimer.value = setInterval(fetchLiveGameData, 5000)
  }

  function stopLivePolling() {
    if (_liveTimer.value) {
      clearInterval(_liveTimer.value)
      _liveTimer.value = null
    }
  }

  function clearLiveData() {
    liveGameData.value = null
  }

  function loadMockData() {
    const myTeam = [
      {
        summoner_name: 'Demo Jungler',
        champion_name: '李青',
        champion_id: 64,
        is_me: true,
        kills: 9,
        deaths: 3,
        assists: 14,
        total_damage: 28600,
        physical_damage: 22100,
        magic_damage: 4200,
        true_damage: 2300,
        damage_taken: 25400,
        gold_earned: 14800,
        gold_spent: 14300,
        minions_killed: 41,
        neutral_minions_killed: 132,
        vision_score: 29,
        wards_placed: 10,
        wards_killed: 6,
        control_wards: 3,
        first_blood: true,
        triple_kills: 0,
        double_kills: 1,
        quadra_kills: 0,
        penta_kills: 0,
        turrets_killed: 2,
        dragons_killed: 2,
        barons_killed: 1,
        cc_time: 18,
        heal: 2500,
        damage_to_buildings: 4200,
        damage_self_mitigated: 16800,
        largest_critical_strike: 0,
        largest_killing_spree: 5,
        longest_time_living: 540,
        time_spent_dead: 96,
        spell1_casts: 12,
        spell2_casts: 18,
        items_purchased: 17,
        game_score: 'S',
        spell1: 4,
        spell2: 11,
        items: [6692, 3071, 3142, 3111, 3026, 0],
      },
      {
        summoner_name: 'Demo Top',
        champion_name: '德莱厄斯',
        champion_id: 122,
        is_me: false,
        kills: 6,
        deaths: 5,
        assists: 8,
        total_damage: 24100,
        physical_damage: 21000,
        magic_damage: 900,
        true_damage: 2200,
        damage_taken: 31800,
        gold_earned: 13100,
        gold_spent: 12800,
        minions_killed: 186,
        neutral_minions_killed: 8,
        vision_score: 19,
        wards_placed: 9,
        wards_killed: 3,
        control_wards: 2,
        first_blood: false,
        triple_kills: 0,
        double_kills: 1,
        quadra_kills: 0,
        penta_kills: 0,
        turrets_killed: 1,
        dragons_killed: 0,
        barons_killed: 0,
        cc_time: 21,
        heal: 1100,
        damage_to_buildings: 3100,
        damage_self_mitigated: 22400,
        largest_critical_strike: 0,
        largest_killing_spree: 3,
        longest_time_living: 420,
        time_spent_dead: 165,
        spell1_casts: 7,
        spell2_casts: 5,
        items_purchased: 15,
        game_score: 'A',
        spell1: 4,
        spell2: 12,
        items: [6631, 3053, 3065, 3047, 3075, 0],
      },
      {
        summoner_name: 'Demo Mid',
        champion_name: '阿狸',
        champion_id: 103,
        is_me: false,
        kills: 12,
        deaths: 4,
        assists: 9,
        total_damage: 33200,
        physical_damage: 1800,
        magic_damage: 29800,
        true_damage: 1600,
        damage_taken: 17300,
        gold_earned: 15200,
        gold_spent: 14900,
        minions_killed: 201,
        neutral_minions_killed: 18,
        vision_score: 21,
        wards_placed: 11,
        wards_killed: 4,
        control_wards: 2,
        first_blood: false,
        triple_kills: 1,
        double_kills: 1,
        quadra_kills: 0,
        penta_kills: 0,
        turrets_killed: 2,
        dragons_killed: 0,
        barons_killed: 0,
        cc_time: 14,
        heal: 900,
        damage_to_buildings: 3700,
        damage_self_mitigated: 9800,
        largest_critical_strike: 0,
        largest_killing_spree: 6,
        longest_time_living: 501,
        time_spent_dead: 110,
        spell1_casts: 9,
        spell2_casts: 8,
        items_purchased: 16,
        game_score: 'S+',
        spell1: 4,
        spell2: 14,
        items: [6655, 3157, 3089, 3020, 4645, 0],
      },
      {
        summoner_name: 'Demo ADC',
        champion_name: '金克丝',
        champion_id: 222,
        is_me: false,
        kills: 11,
        deaths: 4,
        assists: 10,
        total_damage: 35100,
        physical_damage: 33400,
        magic_damage: 700,
        true_damage: 1000,
        damage_taken: 14800,
        gold_earned: 15800,
        gold_spent: 15400,
        minions_killed: 248,
        neutral_minions_killed: 20,
        vision_score: 18,
        wards_placed: 8,
        wards_killed: 3,
        control_wards: 1,
        first_blood: false,
        triple_kills: 0,
        double_kills: 2,
        quadra_kills: 0,
        penta_kills: 0,
        turrets_killed: 4,
        dragons_killed: 0,
        barons_killed: 0,
        cc_time: 9,
        heal: 700,
        damage_to_buildings: 8400,
        damage_self_mitigated: 7600,
        largest_critical_strike: 1280,
        largest_killing_spree: 5,
        longest_time_living: 568,
        time_spent_dead: 103,
        spell1_casts: 4,
        spell2_casts: 7,
        items_purchased: 17,
        game_score: 'S',
        spell1: 4,
        spell2: 7,
        items: [6671, 3031, 3094, 3036, 3006, 0],
      },
      {
        summoner_name: 'Demo Support',
        champion_name: '蕾欧娜',
        champion_id: 89,
        is_me: false,
        kills: 2,
        deaths: 6,
        assists: 21,
        total_damage: 9400,
        physical_damage: 2600,
        magic_damage: 6100,
        true_damage: 700,
        damage_taken: 38200,
        gold_earned: 9400,
        gold_spent: 8900,
        minions_killed: 31,
        neutral_minions_killed: 3,
        vision_score: 67,
        wards_placed: 33,
        wards_killed: 11,
        control_wards: 7,
        first_blood: false,
        triple_kills: 0,
        double_kills: 0,
        quadra_kills: 0,
        penta_kills: 0,
        turrets_killed: 0,
        dragons_killed: 0,
        barons_killed: 0,
        cc_time: 37,
        heal: 500,
        damage_to_buildings: 1100,
        damage_self_mitigated: 34100,
        largest_critical_strike: 0,
        largest_killing_spree: 0,
        longest_time_living: 310,
        time_spent_dead: 286,
        spell1_casts: 6,
        spell2_casts: 4,
        items_purchased: 13,
        game_score: 'A',
        spell1: 4,
        spell2: 3,
        items: [3190, 3109, 3050, 3117, 0, 0],
      },
    ]

    const enemyTeam = [
      { summoner_name: 'Enemy Top', champion_name: '亚托克斯', champion_id: 266, is_me: false, kills: 4, deaths: 7, assists: 5, total_damage: 22800, damage_taken: 30100, gold_earned: 12100, vision_score: 16, minions_killed: 194, neutral_minions_killed: 9, spell1: 4, spell2: 12, items: [6630, 3053, 3047, 3071, 3065, 0], game_score: 'B' },
      { summoner_name: 'Enemy Jungle', champion_name: '嘉文四世', champion_id: 59, is_me: false, kills: 3, deaths: 8, assists: 9, total_damage: 18700, damage_taken: 27900, gold_earned: 11300, vision_score: 24, minions_killed: 36, neutral_minions_killed: 118, spell1: 4, spell2: 11, items: [6692, 3071, 3111, 0, 0, 0], game_score: 'C' },
      { summoner_name: 'Enemy Mid', champion_name: '维克托', champion_id: 112, is_me: false, kills: 8, deaths: 7, assists: 4, total_damage: 28900, damage_taken: 16100, gold_earned: 13900, vision_score: 17, minions_killed: 212, neutral_minions_killed: 12, spell1: 4, spell2: 14, items: [6655, 3157, 3020, 3089, 0, 0], game_score: 'A' },
      { summoner_name: 'Enemy ADC', champion_name: '霞', champion_id: 498, is_me: false, kills: 7, deaths: 6, assists: 6, total_damage: 27600, damage_taken: 14200, gold_earned: 13600, vision_score: 15, minions_killed: 231, neutral_minions_killed: 11, spell1: 4, spell2: 7, items: [6672, 3094, 3036, 3006, 0, 0], game_score: 'A' },
      { summoner_name: 'Enemy Support', champion_name: '锤石', champion_id: 412, is_me: false, kills: 1, deaths: 8, assists: 14, total_damage: 8200, damage_taken: 24700, gold_earned: 8900, vision_score: 59, minions_killed: 24, neutral_minions_killed: 2, spell1: 4, spell2: 3, items: [3190, 3109, 3117, 0, 0, 0], game_score: 'B' },
    ]

    const damageMax = Math.max(...myTeam.map((player) => player.total_damage || 0), 1)
    const tankMax = Math.max(...myTeam.map((player) => player.damage_taken || 0), 1)
    const goldMax = Math.max(...myTeam.map((player) => player.gold_earned || 0), 1)
    const visionMax = Math.max(...myTeam.map((player) => player.vision_score || 0), 1)
    const teamfightMax = Math.max(...myTeam.map((player) => (player.kills || 0) + (player.assists || 0)), 1)
    const objectiveMax = Math.max(...myTeam.map((player) => (player.turrets_killed || 0) + (player.dragons_killed || 0) + (player.barons_killed || 0)), 1)

    const radarData = myTeam.map((player) => ({
      summoner_name: player.summoner_name,
      champion_name: player.champion_name,
      is_me: player.is_me,
      dimensions: {
        output: Math.round((player.total_damage || 0) / damageMax * 100),
        survival: Math.round((player.damage_taken || 0) / tankMax * 100),
        development: Math.round((player.gold_earned || 0) / goldMax * 100),
        teamfight: Math.round(((player.kills || 0) + (player.assists || 0)) / teamfightMax * 100),
        vision: Math.round((player.vision_score || 0) / visionMax * 100),
        objective: Math.round((((player.turrets_killed || 0) + (player.dragons_killed || 0) + (player.barons_killed || 0)) / objectiveMax) * 100),
      },
    }))

    currentMatch.value = {
      game_id: 'MOCK_001',
      game_mode: 'RANKED_SOLO_5x5',
      game_length: 1845,
      timestamp: Math.floor(Date.now() / 1000) - 3600,
      is_win: true,
      my_team: myTeam,
      enemy_team: enemyTeam,
      radar_data: radarData,
    }
  }

  return {
    currentMatch,
    historyList,
    loading,
    liveGameData,
    liveLoading,
    battleProfile,
    battleSummary,
    battleHeroUsage,
    battleRecentTeammates,
    battleHistoryPage,
    battleFilters,
    battleExpandedMatchId,
    battleMatchDetailsCache,
    battleLoadingStates,
    battleDetailErrors,
    battleStatus,
    fetchCurrentMatch,
    fetchHistoryList,
    fetchMatchDetail,
    setCurrentMatch,
    setFromHistory,
    consumeFromHistory,
    fetchBattleProfileSummary,
    fetchBattleHistoryPage,
    setBattleFilter,
    resetBattleFilters,
    setBattlePage,
    setBattlePageSize,
    toggleBattleMatchDetail,
    retryBattleMatchDetail,
    getBattleMatchDetailFromCache,
    clearBattleDetailCache,
    clearBattleStatus,
    fetchLiveGameData,
    startLivePolling,
    stopLivePolling,
    clearLiveData,
    loadMockData,
    canUseMockData: DEV,
  }
})
