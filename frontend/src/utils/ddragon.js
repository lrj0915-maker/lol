/**
 * Data Dragon 资源工具
 * 用于获取英雄头像、技能图标等
 */

const DDRAGON_VERSION = '14.24.1'
const DDRAGON_BASE = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}`

// 英雄 key 映射（id -> key）
import { champions } from '@/data/champions'

const championKeyMap = {}
champions.forEach(c => {
  championKeyMap[c.id] = c.key
})

/**
 * 获取英雄头像 URL
 */
export function getChampionIcon(championId) {
  const key = championKeyMap[championId]
  if (!key) return null
  return `${DDRAGON_BASE}/img/champion/${key}.png`
}

/**
 * 获取英雄加载图 URL
 */
export function getChampionSplash(championId, skinNum = 0) {
  const key = championKeyMap[championId]
  if (!key) return null
  return `${DDRAGON_BASE}/img/champion/splash/${key}_${skinNum}.jpg`
}

/**
 * 获取物品图标 URL
 */
export function getItemIcon(itemId) {
  if (!itemId) return null
  return `${DDRAGON_BASE}/img/item/${itemId}.png`
}

/**
 * 获取召唤师技能图标 URL
 */
export function getSpellIcon(spellId) {
  const spellMap = {
    1: 'SummonerBoost',      // 净化
    3: 'SummonerExhaust',    // 虚弱
    4: 'SummonerFlash',      // 闪现
    6: 'SummonerHaste',      // 幽灵疾步
    7: 'SummonerHeal',       // 治疗
    11: 'SummonerSmite',     // 惩戒
    12: 'SummonerTeleport',  // 传送
    14: 'SummonerDot',       // 点燃
    21: 'SummonerBarrier',   // 屏障
    32: 'SummonerSnowball',  // 雪球（大乱斗）
  }
  const name = spellMap[spellId]
  if (!name) return null
  return `${DDRAGON_BASE}/img/spell/${name}.png`
}

export default {
  getChampionIcon,
  getChampionSplash,
  getItemIcon,
  getSpellIcon
}
