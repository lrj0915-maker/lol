import { describe, expect, it } from 'vitest'
import {
  buildCountersPreview,
  buildGameLengths,
  buildVersionTrends,
  formatCompactNumber,
  formatRatePercent,
  formatWinRate,
  selectPrimaryBuild,
  sortRuneConfigs,
  winRateClass,
} from './runesViewHelpers'

describe('runesViewHelpers', () => {
  it('sortRuneConfigs sorts by win rate', () => {
    const list = [
      { id: 1, play: 100, win: 49 },
      { id: 2, play: 50, win: 30 },
      { id: 3, play: 200, win: 100 },
    ]
    const sorted = sortRuneConfigs(list, 'winRate')
    expect(sorted.map(item => item.id)).toEqual([2, 3, 1])
  })

  it('sortRuneConfigs sorts by games', () => {
    const list = [
      { id: 1, play: 20, win: 10 },
      { id: 2, play: 200, win: 100 },
      { id: 3, play: 50, win: 20 },
    ]
    const sorted = sortRuneConfigs(list, 'games')
    expect(sorted.map(item => item.id)).toEqual([2, 3, 1])
  })

  it('selectPrimaryBuild returns primary build by strategy', () => {
    const config = {
      builds: [
        { id: 'a', play: 100, win: 52 },
        { id: 'b', play: 40, win: 30 },
        { id: 'c', play: 200, win: 98 },
      ],
    }

    expect(selectPrimaryBuild(config, 'winRate').id).toBe('b')
    expect(selectPrimaryBuild(config, 'games').id).toBe('c')
  })

  it('winRateClass maps win rate threshold to class', () => {
    expect(winRateClass(null)).toBe('')
    expect(winRateClass(0.54)).toBe('wr-high')
    expect(winRateClass(52)).toBe('wr-ok')
    expect(winRateClass(0.49)).toBe('wr-low')
  })

  it('formatters return expected text', () => {
    expect(formatWinRate({ play: 0, win: 0 })).toBe('-')
    expect(formatWinRate({ play: 200, win: 103 })).toBe('51.5%')
    expect(formatRatePercent(0.518, 2)).toBe('51.80%')
    expect(formatRatePercent(51.8, 1)).toBe('51.8%')
    expect(formatCompactNumber(999)).toBe('999')
    expect(formatCompactNumber(1200)).toBe('1.2K')
    expect(formatCompactNumber(3200000)).toBe('3.2M')
  })

  it('buildCountersPreview picks overview first and normalizes', () => {
    const overview = [
      { champion_id: '100', play: '15', win: '8' },
      { champion_id: '0', play: '10', win: '5' },
    ]
    const position = [
      { champion_id: '200', play: '99', win: '50' },
    ]
    const result = buildCountersPreview(overview, position, 5)
    expect(result).toHaveLength(1)
    expect(result[0]).toMatchObject({ champion_id: 100, play: 15, win: 8 })
  })

  it('buildGameLengths maps labels and filters invalid rate', () => {
    const input = [
      { game_length: 0, rate: 0.51, average: 0.48 },
      { game_length: 30, rate: 0.49, average: 0.5 },
      { game_length: 35, rate: null, average: 0.5 },
    ]
    const result = buildGameLengths(input)
    expect(result).toHaveLength(2)
    expect(result[0]).toMatchObject({ label: '前期', minutes: '≤25', rate: 0.51 })
    expect(result[1]).toMatchObject({ label: '中后', minutes: '30+', rate: 0.49 })
  })

  it('buildVersionTrends keeps top N and positive rate only', () => {
    const trends = {
      win: [
        { version: '14.10', rate: 0.51, rank: 1 },
        { version: '14.9', rate: 0, rank: 2 },
        { version: '14.8', rate: 0.49, rank: 3 },
      ],
    }
    const result = buildVersionTrends(trends, 4)
    expect(result).toHaveLength(2)
    expect(result.map(item => item.version)).toEqual(['14.10', '14.8'])
  })
})
