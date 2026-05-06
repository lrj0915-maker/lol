/**
 * 格式化工具函数
 */

/**
 * 格式化游戏时长
 */
export function formatGameLength(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * 格式化 KDA
 */
export function formatKDA(kills, deaths, assists) {
  if (deaths === 0) {
    return 'Perfect'
  }
  return ((kills + assists) / deaths).toFixed(2)
}

/**
 * 格式化数字（带单位）
 */
export function formatNumber(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

/**
 * 格式化百分比
 */
export function formatPercent(value, total) {
  if (total === 0) return '0%'
  return Math.round(value / total * 100) + '%'
}

/**
 * 格式化时间戳
 */
export function formatTimestamp(timestamp) {
  const date = new Date(timestamp * 1000)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hour = date.getHours().toString().padStart(2, '0')
  const minute = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

/**
 * 格式化相对时间（如 "3分钟前"、"2小时前"、"1天前"）
 * @param {number} timestamp - Unix 时间戳（秒）或毫秒时间戳
 * @param {object} opts - 可选项
 * @param {boolean} opts.seconds - 是否使用秒级精度（默认 false，分钟级）
 * @returns {string}
 */
export function formatRelativeTime(timestamp, opts = {}) {
  if (!timestamp) return ''
  const ts = timestamp > 1e12 ? timestamp : timestamp * 1000
  const diff = Date.now() - ts
  if (diff < 0) return '刚刚'
  const seconds = Math.floor(diff / 1000)
  if (opts.seconds && seconds < 60) return '刚刚'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  const date = new Date(ts)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

/**
 * 获取评分颜色
 */
export function getScoreColor(score) {
  if (typeof score === 'number') {
    if (score >= 80) return '#ff6b35'
    if (score >= 60) return '#ffd700'
    if (score >= 40) return '#8b949e'
    if (score >= 20) return '#58a6ff'
    return '#e94560'
  }
  const scoreStr = String(score).toUpperCase()
  if (scoreStr.startsWith('S')) return '#ff6b35'
  if (scoreStr.startsWith('A')) return '#ffd700'
  if (scoreStr.startsWith('B')) return '#8b949e'
  if (scoreStr.startsWith('C')) return '#58a6ff'
  return '#e94560'
}

/**
 * 位置名称映射（小写 key）
 */
export const positionNames = {
  top: '上单',
  jungle: '打野',
  mid: '中单',
  adc: 'ADC',
  support: '辅助'
}

/**
 * 位置名称映射（大写 key，兼容 LCU API 返回值）
 */
export const POSITION_NAMES = {
  TOP: '上单',
  JUNGLE: '打野',
  MID: '中单',
  ADC: '下路',
  SUPPORT: '辅助'
}

/**
 * 游戏模式名称映射
 */
export const gameModeNames = {
  'CLASSIC': '匹配/排位',
  'ARAM': '大乱斗',
  'URF': '无限火力',
  'ONEFORALL': '克隆模式'
}
