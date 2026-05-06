import { describe, expect, it, vi } from 'vitest'

function createEntryPayload(overrides = {}) {
  return {
    success: true,
    champion_id: 1,
    champion_key: 'Ahri',
    position: 'MID',
    version: '16.1',
    updateTime: '2026-03-03 10:00:00',
    meta: { region: 'CN', source_region: 'CN' },
    position_data: { rune_pages: [{ id: 'A', play: 100, win: 50 }] },
    ...overrides,
  }
}

async function setupUseRunesData({ cacheReadResult = null, bridgeEntryResult = null } = {}) {
  vi.resetModules()

  const cacheStore = {
    read: vi.fn(async () => cacheReadResult),
    write: vi.fn(async () => true),
    remove: vi.fn(async () => true),
    clear: vi.fn(async () => true),
  }

  const bridge = {
    getRunesEntry: vi.fn(async () => bridgeEntryResult),
    getRunesDataStatus: vi.fn(async () => ({ exists: true })),
    refreshRunesData: vi.fn(async () => ({ success: true })),
    refreshRunesSingle: vi.fn(async () => ({ success: true })),
    refreshRunesSelected: vi.fn(async () => ({ success: true })),
    getChampionOverview: vi.fn(async () => ({ success: true })),
  }

  vi.doMock('@/utils/indexedDbStore', () => ({
    createIndexedDbStore: () => cacheStore,
  }))

  vi.doMock('@/utils/bridge', () => ({
    bridge,
    default: bridge,
  }))

  const { useRunesData } = await import('./useRunesData')
  const api = useRunesData()
  return { api, bridge, cacheStore }
}

describe('useRunesData', () => {
  it('命中有效缓存时直接返回缓存并跳过 API', async () => {
    const payload = createEntryPayload()
    const { api, bridge } = await setupUseRunesData({
      cacheReadResult: { data: payload, cacheTime: Date.now() },
      bridgeEntryResult: createEntryPayload({ position_data: { rune_pages: [{ id: 'B' }] } }),
    })

    await api.loadRunesData(false, 1, 'MID')

    expect(bridge.getRunesEntry).not.toHaveBeenCalled()
    expect(api.getChampionPositionRunes(1, 'MID')).toEqual(payload.position_data)
  })

  it('缓存未命中时回退 API 并写入缓存', async () => {
    const payload = createEntryPayload()
    const { api, bridge, cacheStore } = await setupUseRunesData({
      cacheReadResult: null,
      bridgeEntryResult: payload,
    })

    await api.loadRunesData(false, 1, 'MID')

    expect(bridge.getRunesEntry).toHaveBeenCalledWith(1, 'MID')
    expect(cacheStore.write).toHaveBeenCalledTimes(1)
    expect(cacheStore.write.mock.calls[0][0]).toBe('entry:1:MID')
    expect(api.getChampionPositionRunes(1, 'MID')).toEqual(payload.position_data)
  })

  it('POSITION_NOT_FOUND 属于可恢复错误，不抛异常', async () => {
    const { api } = await setupUseRunesData({
      cacheReadResult: null,
      bridgeEntryResult: { error: 'POSITION_NOT_FOUND', message: 'not found' },
    })

    await expect(api.loadRunesData(false, 1, 'MID')).resolves.toBeDefined()
    expect(api.loadError.value).toBeNull()
  })

  it('非可恢复错误会抛异常并写入 loadError', async () => {
    const { api } = await setupUseRunesData({
      cacheReadResult: null,
      bridgeEntryResult: { error: 'SERVER_ERROR', message: 'server down' },
    })

    await expect(api.loadRunesData(false, 1, 'MID')).rejects.toThrow('server down')
    expect(api.loadError.value).toBe('server down')
  })
})
