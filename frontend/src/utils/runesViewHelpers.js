export function sortRuneConfigs(configs, sortBy = 'winRate') {
  const source = Array.isArray(configs) ? configs : []
  if (sortBy === 'winRate') {
    return [...source].sort((a, b) => {
      const aRate = a?.play ? (a.win / a.play) * 100 : 0
      const bRate = b?.play ? (b.win / b.play) * 100 : 0
      return bRate - aRate
    })
  }
  return [...source].sort((a, b) => (b?.play || 0) - (a?.play || 0))
}

export function winRateClass(val) {
  if (val === null || val === undefined) return ''
  const v = Number(val)
  const pct = v <= 1 ? v * 100 : v
  if (pct >= 53) return 'wr-high'
  if (pct >= 50) return 'wr-ok'
  return 'wr-low'
}

export function getBuilds(config) {
  if (Array.isArray(config?.builds) && config.builds.length > 0) return config.builds
  return [config]
}

export function selectPrimaryBuild(config, sortBy = 'winRate') {
  const builds = getBuilds(config)
  if (!builds.length) return config
  if (sortBy === 'winRate') {
    const sorted = [...builds].sort((a, b) => {
      const aRate = a?.play ? a.win / a.play : 0
      const bRate = b?.play ? b.win / b.play : 0
      return bRate - aRate
    })
    return sorted[0] || builds[0] || config
  }
  const sorted = [...builds].sort((a, b) => (b?.play || 0) - (a?.play || 0))
  return sorted[0] || builds[0] || config
}

export function formatWinRate(build) {
  const play = build?.play || 0
  const win = build?.win || 0
  if (!play) return '-'
  return `${((win / play) * 100).toFixed(1)}%`
}

export function formatRatePercent(value, precision = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  const val = Number(value)
  if (val <= 1) return `${(val * 100).toFixed(precision)}%`
  return `${val.toFixed(precision)}%`
}

export function formatCompactNumber(num) {
  const value = Number(num || 0)
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
  return `${value}`
}

export function formatKda(kda) {
  if (kda === null || kda === undefined || Number.isNaN(Number(kda))) return '-'
  return Number(kda).toFixed(2)
}

export function buildCountersPreview(overviewCounters, positionCounters, limit = 5) {
  const source = (Array.isArray(overviewCounters) && overviewCounters.length ? overviewCounters : positionCounters) || []
  if (!Array.isArray(source)) return []
  return source
    .map(item => ({
      ...item,
      champion_id: Number(item?.champion_id || 0),
      play: Number(item?.play || 0),
      win: Number(item?.win || 0),
    }))
    .filter(item => item.champion_id > 0 && item.play > 0)
    .sort((a, b) => b.play - a.play)
    .slice(0, limit)
}

const GAME_LENGTH_LABELS = {
  0: '前期',
  25: '中期',
  30: '中后',
  35: '后期',
  40: '超后',
}

export function buildGameLengths(raw) {
  if (!Array.isArray(raw) || !raw.length) return []
  return raw
    .map(item => ({
      label: GAME_LENGTH_LABELS[item.game_length] || `${item.game_length}m`,
      minutes: item.game_length === 0 ? '≤25' : `${item.game_length}+`,
      rate: item.rate,
      avg: item.average || 0.5,
    }))
    .filter(item => item.rate !== null && item.rate !== undefined)
}

export function buildVersionTrends(trends, limit = 4) {
  if (!trends || typeof trends !== 'object') return []
  const winArr = trends.win
  if (!Array.isArray(winArr) || !winArr.length) return []
  return winArr
    .slice(0, limit)
    .map(item => ({
      version: item.version || '?',
      rate: item.rate,
      rank: item.rank,
    }))
    .filter(item => item.rate !== null && item.rate !== undefined && item.rate > 0)
}
