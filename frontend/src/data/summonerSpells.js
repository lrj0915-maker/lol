/**
 * 召唤师技能数据映射
 */

export const SUMMONER_SPELLS = {
  1: {
    id: 1,
    name: '净化',
    nameEn: 'Cleanse',
    icon: 'SummonerBoost.png'
  },
  3: {
    id: 3,
    name: '疾跑',
    nameEn: 'Exhaust',
    icon: 'SummonerExhaust.png'
  },
  4: {
    id: 4,
    name: '闪现',
    nameEn: 'Flash',
    icon: 'SummonerFlash.png'
  },
  6: {
    id: 6,
    name: '幽灵疾步',
    nameEn: 'Ghost',
    icon: 'SummonerHaste.png'
  },
  7: {
    id: 7,
    name: '治疗术',
    nameEn: 'Heal',
    icon: 'SummonerHeal.png'
  },
  11: {
    id: 11,
    name: '惩戒',
    nameEn: 'Smite',
    icon: 'SummonerSmite.png'
  },
  12: {
    id: 12,
    name: '传送',
    nameEn: 'Teleport',
    icon: 'SummonerTeleport.png'
  },
  13: {
    id: 13,
    name: '清晰术',
    nameEn: 'Clarity',
    icon: 'SummonerMana.png'
  },
  14: {
    id: 14,
    name: '点燃',
    nameEn: 'Ignite',
    icon: 'SummonerDot.png'
  },
  21: {
    id: 21,
    name: '屏障',
    nameEn: 'Barrier',
    icon: 'SummonerBarrier.png'
  },
  30: {
    id: 30,
    name: '国王之刃',
    nameEn: 'To the King!',
    icon: 'SummonerPoroRecall.png'
  },
  31: {
    id: 31,
    name: '国王之刃',
    nameEn: 'Poro Toss',
    icon: 'SummonerPoroThrow.png'
  },
  32: {
    id: 32,
    name: '标记',
    nameEn: 'Mark',
    icon: 'SummonerSnowball.png'
  },
  39: {
    id: 39,
    name: '疾跑',
    nameEn: 'Exhaust',
    icon: 'SummonerExhaust.png'
  },
  54: {
    id: 54,
    name: '占位符',
    nameEn: 'Placeholder',
    icon: 'SummonerPlaceholder.png'
  },
  55: {
    id: 55,
    name: '占位符',
    nameEn: 'Placeholder Attack-Smite',
    icon: 'SummonerPlaceholder.png'
  }
}

/**
 * 根据ID获取召唤师技能信息
 */
export function getSummonerSpellById(spellId) {
  return SUMMONER_SPELLS[spellId] || null
}

/**
 * 获取召唤师技能图标URL
 */
export function getSummonerSpellIconUrl(spellId) {
  const spell = getSummonerSpellById(spellId)
  if (!spell) return ''
  return `https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/data/spells/icons2d/${spell.icon}`
}
