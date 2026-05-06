/**
 * 符文系统数据映射
 * 包含所有符文树、符文、属性碎片的ID映射
 */

// ========== 符文树定义 ==========
export const RUNE_TREES = {
  8000: { id: 8000, name: '精密', nameEn: 'Precision', icon: 'perk-images/Styles/7201_Precision.png', color: '#FFD700', emoji: '⚔️' },
  8100: { id: 8100, name: '主宰', nameEn: 'Domination', icon: 'perk-images/Styles/7200_Domination.png', color: '#FF4655', emoji: '🗡️' },
  8200: { id: 8200, name: '巫术', nameEn: 'Sorcery', icon: 'perk-images/Styles/7202_Sorcery.png', color: '#9FAAFC', emoji: '🔮' },
  8300: { id: 8300, name: '坚决', nameEn: 'Resolve', icon: 'perk-images/Styles/7204_Resolve.png', color: '#00C48C', emoji: '🛡️' },
  8400: { id: 8400, name: '启迪', nameEn: 'Inspiration', icon: 'perk-images/Styles/7203_Whimsy.png', color: '#49AAC8', emoji: '💡' }
}

// ========== 符文映射 ==========
export const RUNE_MAP = {
  8005: { id: 8005, name: '强攻', nameEn: 'Press the Attack', icon: 'Styles/Precision/PressTheAttack/PressTheAttack.png', tree: 8000, slot: 'keystone' },
  8008: { id: 8008, name: '致命节奏', nameEn: 'Lethal Tempo', icon: 'Styles/Precision/LethalTempo/LethalTempoTemp.png', tree: 8000, slot: 'keystone' },
  8021: { id: 8021, name: '迅捷步法', nameEn: 'Fleet Footwork', icon: 'Styles/Precision/FleetFootwork/FleetFootwork.png', tree: 8000, slot: 'keystone' },
  8010: { id: 8010, name: '征服者', nameEn: 'Conqueror', icon: 'Styles/Precision/Conqueror/Conqueror.png', tree: 8000, slot: 'keystone' },
  9101: { id: 9101, name: '吸收生命', nameEn: 'Absorb Life', icon: 'Styles/Precision/AbsorbLife/AbsorbLife.png', tree: 8000, slot: 1 },
  9111: { id: 9111, name: '凯旋', nameEn: 'Triumph', icon: 'Styles/Precision/Triumph.png', tree: 8000, slot: 1 },
  8009: { id: 8009, name: '气定神闲', nameEn: 'Presence of Mind', icon: 'Styles/Precision/PresenceOfMind/PresenceOfMind.png', tree: 8000, slot: 1 },
  9104: { id: 9104, name: '传说：欢欣', nameEn: 'Legend: Alacrity', icon: 'Styles/Precision/LegendAlacrity/LegendAlacrity.png', tree: 8000, slot: 2 },
  9105: { id: 9105, name: '传说：急速', nameEn: 'Legend: Haste', icon: 'Styles/Precision/LegendHaste/LegendHaste.png', tree: 8000, slot: 2 },
  9103: { id: 9103, name: '传说：血统', nameEn: 'Legend: Bloodline', icon: 'Styles/Precision/LegendBloodline/LegendBloodline.png', tree: 8000, slot: 2 },
  8014: { id: 8014, name: '致命一击', nameEn: 'Coup de Grace', icon: 'Styles/Precision/CoupDeGrace/CoupDeGrace.png', tree: 8000, slot: 3 },
  8017: { id: 8017, name: '砍倒', nameEn: 'Cut Down', icon: 'Styles/Precision/CutDown/CutDown.png', tree: 8000, slot: 3 },
  8299: { id: 8299, name: '坚毅不倒', nameEn: 'Last Stand', icon: 'Styles/Sorcery/LastStand/LastStand.png', tree: 8000, slot: 3 },
  8112: { id: 8112, name: '电刑', nameEn: 'Electrocute', icon: 'Styles/Domination/Electrocute/Electrocute.png', tree: 8100, slot: 'keystone' },
  8124: { id: 8124, name: '掠食者', nameEn: 'Predator', icon: 'Styles/Domination/Predator/Predator.png', tree: 8100, slot: 'keystone' },
  8128: { id: 8128, name: '黑暗收割', nameEn: 'Dark Harvest', icon: 'Styles/Domination/DarkHarvest/DarkHarvest.png', tree: 8100, slot: 'keystone' },
  9923: { id: 9923, name: '丛刃', nameEn: 'Hail of Blades', icon: 'Styles/Domination/HailOfBlades/HailOfBlades.png', tree: 8100, slot: 'keystone' },
  8126: { id: 8126, name: '血之滋味', nameEn: 'Cheap Shot', icon: 'Styles/Domination/CheapShot/CheapShot.png', tree: 8100, slot: 1 },
  8139: { id: 8139, name: '恶意中伤', nameEn: 'Taste of Blood', icon: 'Styles/Domination/TasteOfBlood/GreenTerror_TasteOfBlood.png', tree: 8100, slot: 1 },
  8143: { id: 8143, name: '猛然冲击', nameEn: 'Sudden Impact', icon: 'Styles/Domination/SuddenImpact/SuddenImpact.png', tree: 8100, slot: 1 },
  8137: { id: 8137, name: '第六感', nameEn: 'Sixth Sense', icon: 'Styles/Domination/SixthSense/SixthSense.png', tree: 8100, slot: 2 },
  8140: { id: 8140, name: '阴森纪念品', nameEn: 'Grisly Mementos', icon: 'Styles/Domination/GrislyMementos/GrislyMementos.png', tree: 8100, slot: 2 },
  8141: { id: 8141, name: '深层守卫', nameEn: 'Deep Ward', icon: 'Styles/Domination/DeepWard/DeepWard.png', tree: 8100, slot: 2 },
  8135: { id: 8135, name: '寻宝猎人', nameEn: 'Treasure Hunter', icon: 'Styles/Domination/TreasureHunter/TreasureHunter.png', tree: 8100, slot: 3 },
  8105: { id: 8105, name: '无情猎手', nameEn: 'Relentless Hunter', icon: 'Styles/Domination/RelentlessHunter/RelentlessHunter.png', tree: 8100, slot: 3 },
  8106: { id: 8106, name: '终极猎人', nameEn: 'Ultimate Hunter', icon: 'Styles/Domination/UltimateHunter/UltimateHunter.png', tree: 8100, slot: 3 },
  8214: { id: 8214, name: '召唤：艾黎', nameEn: 'Summon Aery', icon: 'Styles/Sorcery/SummonAery/SummonAery.png', tree: 8200, slot: 'keystone' },
  8229: { id: 8229, name: '奥术彗星', nameEn: 'Arcane Comet', icon: 'Styles/Sorcery/ArcaneComet/ArcaneComet.png', tree: 8200, slot: 'keystone' },
  8230: { id: 8230, name: '相位猛冲', nameEn: 'Phase Rush', icon: 'Styles/Sorcery/PhaseRush/PhaseRush.png', tree: 8200, slot: 'keystone' },
  8224: { id: 8224, name: '公理奥术师', nameEn: 'Axiom Arcanist', icon: 'Styles/Sorcery/NullifyingOrb/Pokeshield.png', tree: 8200, slot: 1 },
  8226: { id: 8226, name: '法力流系带', nameEn: 'Manaflow Band', icon: 'Styles/Sorcery/ManaflowBand/ManaflowBand.png', tree: 8200, slot: 1 },
  8275: { id: 8275, name: '灵光披风', nameEn: 'Nimbus Cloak', icon: 'Styles/Sorcery/NimbusCloak/6361.png', tree: 8200, slot: 1 },
  8210: { id: 8210, name: '超然', nameEn: 'Transcendence', icon: 'Styles/Sorcery/Transcendence/Transcendence.png', tree: 8200, slot: 2 },
  8234: { id: 8234, name: '迅捷', nameEn: 'Celerity', icon: 'Styles/Sorcery/Celerity/CelerityTemp.png', tree: 8200, slot: 2 },
  8233: { id: 8233, name: '绝对专注', nameEn: 'Absolute Focus', icon: 'Styles/Sorcery/AbsoluteFocus/AbsoluteFocus.png', tree: 8200, slot: 2 },
  8237: { id: 8237, name: '焦灼', nameEn: 'Scorch', icon: 'Styles/Sorcery/Scorch/Scorch.png', tree: 8200, slot: 3 },
  8232: { id: 8232, name: '水上行走', nameEn: 'Waterwalking', icon: 'Styles/Sorcery/Waterwalking/Waterwalking.png', tree: 8200, slot: 3 },
  8236: { id: 8236, name: '风暴聚集', nameEn: 'Gathering Storm', icon: 'Styles/Sorcery/GatheringStorm/GatheringStorm.png', tree: 8200, slot: 3 },
  8437: { id: 8437, name: '不灭之握', nameEn: 'Grasp of the Undying', icon: 'Styles/Resolve/GraspOfTheUndying/GraspOfTheUndying.png', tree: 8300, slot: 'keystone' },
  8439: { id: 8439, name: '余震', nameEn: 'Aftershock', icon: 'Styles/Resolve/VeteranAftershock/VeteranAftershock.png', tree: 8300, slot: 'keystone' },
  8465: { id: 8465, name: '守护者', nameEn: 'Guardian', icon: 'Styles/Resolve/Guardian/Guardian.png', tree: 8300, slot: 'keystone' },
  8446: { id: 8446, name: '爆破', nameEn: 'Demolish', icon: 'Styles/Resolve/Demolish/Demolish.png', tree: 8300, slot: 1 },
  8463: { id: 8463, name: '生命源泉', nameEn: 'Font of Life', icon: 'Styles/Resolve/FontOfLife/FontOfLife.png', tree: 8300, slot: 1 },
  8401: { id: 8401, name: '护盾猛击', nameEn: 'Shield Bash', icon: 'Styles/Resolve/MirrorShell/MirrorShell.png', tree: 8300, slot: 1 },
  8429: { id: 8429, name: '调节', nameEn: 'Conditioning', icon: 'Styles/Resolve/Conditioning/Conditioning.png', tree: 8300, slot: 2 },
  8444: { id: 8444, name: '第二次呼吸', nameEn: 'Second Wind', icon: 'Styles/Resolve/SecondWind/SecondWind.png', tree: 8300, slot: 2 },
  8473: { id: 8473, name: '骸骨镀层', nameEn: 'Bone Plating', icon: 'Styles/Resolve/BonePlating/BonePlating.png', tree: 8300, slot: 2 },
  8451: { id: 8451, name: '过度生长', nameEn: 'Overgrowth', icon: 'Styles/Resolve/Overgrowth/Overgrowth.png', tree: 8300, slot: 3 },
  8453: { id: 8453, name: '复苏', nameEn: 'Revitalize', icon: 'Styles/Resolve/Revitalize/Revitalize.png', tree: 8300, slot: 3 },
  8242: { id: 8242, name: '不屈', nameEn: 'Unflinching', icon: 'Styles/Sorcery/Unflinching/Unflinching.png', tree: 8300, slot: 3 },
  8351: { id: 8351, name: '冰川增幅', nameEn: 'Glacial Augment', icon: 'Styles/Inspiration/GlacialAugment/GlacialAugment.png', tree: 8400, slot: 'keystone' },
  8360: { id: 8360, name: '启封的秘籍', nameEn: 'Unsealed Spellbook', icon: 'Styles/Inspiration/UnsealedSpellbook/UnsealedSpellbook.png', tree: 8400, slot: 'keystone' },
  8369: { id: 8369, name: '先攻', nameEn: 'First Strike', icon: 'Styles/Inspiration/FirstStrike/FirstStrike.png', tree: 8400, slot: 'keystone' },
  8306: { id: 8306, name: '海克斯科技闪现罗网', nameEn: 'Hextech Flashtraption', icon: 'Styles/Inspiration/HextechFlashtraption/HextechFlashtraption.png', tree: 8400, slot: 1 },
  8304: { id: 8304, name: '神奇之鞋', nameEn: 'Magical Footwear', icon: 'Styles/Inspiration/MagicalFootwear/MagicalFootwear.png', tree: 8400, slot: 1 },
  8321: { id: 8321, name: '现金返还', nameEn: 'Cash Back', icon: 'Styles/Inspiration/CashBack/CashBack.png', tree: 8400, slot: 1 },
  8313: { id: 8313, name: '三重补药', nameEn: 'Triple Tonic', icon: 'Styles/Inspiration/PerfectTiming/PerfectTiming.png', tree: 8400, slot: 1 },
  8352: { id: 8352, name: '时间扭曲补药', nameEn: 'Time Warp Tonic', icon: 'Styles/Inspiration/TimeWarpTonic/TimeWarpTonic.png', tree: 8400, slot: 2 },
  8345: { id: 8345, name: '饼干配送', nameEn: 'Biscuit Delivery', icon: 'Styles/Inspiration/BiscuitDelivery/BiscuitDelivery.png', tree: 8400, slot: 2 },
  8347: { id: 8347, name: '星界洞悉', nameEn: 'Cosmic Insight', icon: 'Styles/Inspiration/CosmicInsight/CosmicInsight.png', tree: 8400, slot: 3 },
  8410: { id: 8410, name: '疾跑', nameEn: 'Approach Velocity', icon: 'Styles/Resolve/ApproachVelocity/ApproachVelocity.png', tree: 8400, slot: 3 },
  8316: { id: 8316, name: '万事通', nameEn: 'Jack Of All Trades', icon: 'Styles/Inspiration/JackOfAllTrades/JackOfAllTrades.png', tree: 8400, slot: 3 }
}

export const STAT_SHARD_MAP = {
  5008: { id: 5008, name: '自适应之力', nameEn: 'Adaptive Force', icon: 'StatMods/StatModsAdaptiveForceIcon.png', description: '+9自适应之力', row: 0 },
  5005: { id: 5005, name: '攻击速度', nameEn: 'Attack Speed', icon: 'StatMods/StatModsAttackSpeedIcon.png', description: '+10%攻击速度', row: 0 },
  5007: { id: 5007, name: '技能急速', nameEn: 'Ability Haste', icon: 'StatMods/StatModsCDRScalingIcon.png', description: '+8技能急速', row: 0 },
  5010: { id: 5010, name: '移动速度', nameEn: 'Move Speed', icon: 'StatMods/StatModsMoveSpeedIcon.png', description: '+2%移动速度', row: 1 },
  5001: { id: 5001, name: '生命值', nameEn: 'Health Scaling', icon: 'StatMods/StatModsHealthScalingIcon.png', description: '+15-140生命值（基于等级）', row: 1 },
  5011: { id: 5011, name: '生命值', nameEn: 'Health', icon: 'StatMods/StatModsHealthScalingIcon.png', description: '+65生命值', row: 2 },
  5013: { id: 5013, name: '韧性和减速抗性', nameEn: 'Tenacity and Slow Resist', icon: 'StatMods/StatModsTenacityIcon.png', description: '+10%韧性和减速抗性', row: 2 }
}

export function getTreeById(treeId) {
  return RUNE_TREES[treeId] || null
}

export function getRuneById(runeId) {
  return RUNE_MAP[runeId] || null
}

export function getStatShardById(shardId) {
  return STAT_SHARD_MAP[shardId] || null
}

export function getRunesByTree(treeId) {
  const runes = Object.values(RUNE_MAP).filter(r => r.tree === treeId)
  return {
    keystones: runes.filter(r => r.slot === 'keystone'),
    slot1: runes.filter(r => r.slot === 1),
    slot2: runes.filter(r => r.slot === 2),
    slot3: runes.filter(r => r.slot === 3)
  }
}

export function getRuneIconUrl(runeId) {
  const rune = getRuneById(runeId)
  if (!rune) return ''
  // 使用Data Dragon CDN，路径格式：perk-images/Styles/...
  return `https://ddragon.leagueoflegends.com/cdn/img/perk-images/${rune.icon}`
}

export function getTreeIconUrl(treeId) {
  const tree = getTreeById(treeId)
  if (!tree) return ''
  // 使用Data Dragon CDN
  return `https://ddragon.leagueoflegends.com/cdn/img/${tree.icon}`
}

export function getStatShardIconUrl(shardId) {
  const shard = getStatShardById(shardId)
  if (!shard) return ''
  // 使用Data Dragon CDN
  return `https://ddragon.leagueoflegends.com/cdn/img/${shard.icon}`
}

/**
 * 预加载所有符文图标到浏览器缓存
 * 调用后在显示符文时图标会直接使用缓存中的图片
 */
export function preloadRuneIcons() {
  const urls = new Set()

  // 收集主系符文图标
  Object.values(RUNE_MAP).forEach(rune => {
    if (rune.icon) {
      urls.add(`https://ddragon.leagueoflegends.com/cdn/img/perk-images/${rune.icon}`)
    }
  })

  // 收集符文树图标
  Object.values(RUNE_TREES).forEach(tree => {
    if (tree.icon) {
      urls.add(`https://ddragon.leagueoflegends.com/cdn/img/${tree.icon}`)
    }
  })

  // 收集属性碎片图标
  Object.values(STAT_SHARD_MAP).forEach(shard => {
    if (shard.icon) {
      urls.add(`https://ddragon.leagueoflegends.com/cdn/img/${shard.icon}`)
    }
  })

  // 静默预加载，不阻塞
  urls.forEach(url => {
    const img = new Image()
    img.src = url
  })
}
