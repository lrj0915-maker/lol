import { defineStore } from 'pinia'
import { ref } from 'vue'
import { bridge } from '@/utils/bridge'

export const useMatchStore = defineStore('match', () => {
  // 状态
  const currentMatch = ref(null)
  const historyList = ref([])
  const loading = ref(false)

  // 方法
  async function fetchCurrentMatch() {
    loading.value = true
    try {
      const data = await bridge.getCurrentMatchStats()
      currentMatch.value = data
    } catch (e) {
      console.log('获取战绩失败')
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
    const data = await bridge.getMatchDetail(gameId)
    return data
  }

  function setCurrentMatch(data) {
    currentMatch.value = data
  }

  // 生成模拟数据
  function loadMockData() {
    const mockPlayers = [
      { champion_name: '亚索', champion_id: 157, is_me: true, kills: 8, deaths: 3, assists: 12, total_damage: 28500, physical_damage: 22800, magic_damage: 4200, true_damage: 1500, damage_taken: 22000, gold_earned: 14200, gold_spent: 13800, minions_killed: 180, neutral_minions_killed: 35, vision_score: 28, wards_placed: 12, wards_killed: 5, control_wards: 2, first_blood: true, triple_kills: 1, turrets_killed: 2, dragons_killed: 1, barons_killed: 1, cc_time: 45, heal: 2100, damage_to_buildings: 4200, damage_self_mitigated: 18500, largest_critical_strike: 1234, largest_killing_spree: 5, longest_time_living: 512, time_spent_dead: 135, spell1_casts: 3, spell2_casts: 8, items_purchased: 18, game_score: 'S', spell1: 4, spell2: 14, items: [3153, 6672, 3031, 3036, 3006, 0] },
      { champion_name: '盲僧', champion_id: 64, is_me: false, kills: 5, deaths: 4, assists: 15, total_damage: 18200, physical_damage: 16500, magic_damage: 1200, true_damage: 500, damage_taken: 28500, gold_earned: 12800, gold_spent: 12200, minions_killed: 45, neutral_minions_killed: 111, vision_score: 35, wards_placed: 18, wards_killed: 8, control_wards: 4, first_blood: false, turrets_killed: 1, dragons_killed: 2, barons_killed: 0, cc_time: 52, heal: 3200, damage_to_buildings: 2100, damage_self_mitigated: 25600, largest_critical_strike: 0, largest_killing_spree: 3, longest_time_living: 445, time_spent_dead: 180, spell1_casts: 5, spell2_casts: 12, items_purchased: 15, game_score: 'A', spell1: 4, spell2: 11, items: [6693, 3071, 3053, 3111, 0, 0] },
      { champion_name: '卡特琳娜', champion_id: 55, is_me: false, kills: 12, deaths: 5, assists: 8, total_damage: 35200, physical_damage: 2100, magic_damage: 31500, true_damage: 1600, damage_taken: 18700, gold_earned: 15600, gold_spent: 15100, minions_killed: 165, neutral_minions_killed: 33, vision_score: 18, wards_placed: 8, wards_killed: 3, control_wards: 1, first_blood: false, triple_kills: 2, double_kills: 2, turrets_killed: 1, dragons_killed: 0, barons_killed: 0, cc_time: 12, heal: 1800, damage_to_buildings: 1500, damage_self_mitigated: 12300, largest_critical_strike: 0, largest_killing_spree: 6, longest_time_living: 380, time_spent_dead: 210, spell1_casts: 4, spell2_casts: 6, items_purchased: 16, game_score: 'S+', spell1: 4, spell2: 14, items: [4645, 3157, 3089, 3020, 4628, 0] },
      { champion_name: '寒冰射手', champion_id: 22, is_me: false, kills: 10, deaths: 3, assists: 14, total_damage: 32100, physical_damage: 30500, magic_damage: 800, true_damage: 800, damage_taken: 15200, gold_earned: 14800, gold_spent: 14300, minions_killed: 220, neutral_minions_killed: 25, vision_score: 22, wards_placed: 10, wards_killed: 4, control_wards: 2, first_blood: false, double_kills: 1, turrets_killed: 3, dragons_killed: 1, barons_killed: 1, cc_time: 28, heal: 1500, damage_to_buildings: 6800, damage_self_mitigated: 8900, largest_critical_strike: 1456, largest_killing_spree: 4, longest_time_living: 520, time_spent_dead: 95, spell1_casts: 2, spell2_casts: 5, items_purchased: 17, game_score: 'S', spell1: 4, spell2: 7, items: [6672, 3031, 3094, 3036, 3006, 0] },
      { champion_name: '曙光女神', champion_id: 89, is_me: false, kills: 2, deaths: 6, assists: 22, total_damage: 8500, physical_damage: 3200, magic_damage: 4800, true_damage: 500, damage_taken: 42500, gold_earned: 9200, gold_spent: 8800, minions_killed: 28, neutral_minions_killed: 4, vision_score: 72, wards_placed: 35, wards_killed: 12, control_wards: 8, first_blood: false, turrets_killed: 0, dragons_killed: 0, barons_killed: 0, cc_time: 38, heal: 800, damage_to_buildings: 1200, damage_self_mitigated: 35200, largest_critical_strike: 0, largest_killing_spree: 0, longest_time_living: 320, time_spent_dead: 280, spell1_casts: 6, spell2_casts: 4, items_purchased: 12, game_score: 'A', spell1: 4, spell2: 3, items: [3190, 3109, 3050, 3117, 0, 0] }
    ]

    // 计算雷达数据 - 使用相对最大值归一化，让数据分布更均匀
    const maxValues = {
      damage: Math.max(...mockPlayers.map(p => p.total_damage)),
      tank: Math.max(...mockPlayers.map(p => p.damage_taken)),
      gold: Math.max(...mockPlayers.map(p => p.gold_earned)),
      vision: Math.max(...mockPlayers.map(p => p.vision_score)),
      objectives: Math.max(...mockPlayers.map(p => p.turrets_killed + (p.dragons_killed || 0) + (p.barons_killed || 0))),
      teamfight: Math.max(...mockPlayers.map(p => p.kills + p.assists))
    }

    const radarData = mockPlayers.map(p => {
      const objectives = p.turrets_killed + (p.dragons_killed || 0) + (p.barons_killed || 0)
      const teamfight = p.kills + p.assists
      
      return {
        summoner_name: p.champion_name,
        champion_name: p.champion_name,
        is_me: p.is_me,
        dimensions: {
          output: Math.round(p.total_damage / maxValues.damage * 100),
          survival: Math.round(p.damage_taken / maxValues.tank * 100),
          development: Math.round(p.gold_earned / maxValues.gold * 100),
          teamfight: Math.round(teamfight / maxValues.teamfight * 100),
          vision: Math.round(p.vision_score / maxValues.vision * 100),
          objective: maxValues.objectives > 0 ? Math.round(objectives / maxValues.objectives * 100) : 0
        }
      }
    })

    currentMatch.value = {
      game_id: 'MOCK_001',
      game_mode: '排位赛',
      game_length: 1845,
      is_win: true,
      my_team: mockPlayers,
      enemy_team: [],
      radar_data: radarData
    }
  }

  return {
    currentMatch,
    historyList,
    loading,
    fetchCurrentMatch,
    fetchHistoryList,
    fetchMatchDetail,
    setCurrentMatch,
    loadMockData
  }
})
