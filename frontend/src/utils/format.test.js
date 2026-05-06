import { describe, expect, it } from 'vitest'
import {
  formatGameLength,
  formatKDA,
  formatNumber,
  formatPercent,
  getScoreColor,
} from './format'

describe('format utils', () => {
  it('formats game length as mm:ss', () => {
    expect(formatGameLength(0)).toBe('0:00')
    expect(formatGameLength(65)).toBe('1:05')
    expect(formatGameLength(3599)).toBe('59:59')
  })

  it('formats KDA with perfect fallback', () => {
    expect(formatKDA(8, 0, 3)).toBe('Perfect')
    expect(formatKDA(8, 2, 6)).toBe('7.00')
  })

  it('formats number with k/w unit', () => {
    expect(formatNumber(999)).toBe('999')
    expect(formatNumber(1500)).toBe('1.5k')
    expect(formatNumber(30000)).toBe('3.0w')
  })

  it('formats percentage safely', () => {
    expect(formatPercent(2, 8)).toBe('25%')
    expect(formatPercent(0, 0)).toBe('0%')
  })

  it('resolves score color by numeric and grade value', () => {
    expect(getScoreColor(85)).toBe('#ff6b35')
    expect(getScoreColor('A+')).toBe('#ffd700')
    expect(getScoreColor('C')).toBe('#58a6ff')
  })
})
