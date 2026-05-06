import { describe, expect, it, vi } from 'vitest'

function deferred() {
  let resolve
  const promise = new Promise((res) => {
    resolve = res
  })
  return { promise, resolve }
}

async function setupUseAugmentsData({ cacheReadResult = null, bridgeDataResult = null } = {}) {
  vi.resetModules()

  const cacheStore = {
    read: vi.fn(async () => cacheReadResult),
    write: vi.fn(async () => true),
    remove: vi.fn(async () => true),
    clear: vi.fn(async () => true),
  }

  const bridge = {
    getAugmentsData: vi.fn(async () => bridgeDataResult),
    getAugmentsDataStatus: vi.fn(async () => ({ exists: true })),
    refreshAugmentsData: vi.fn(async () => ({ success: true })),
  }

  vi.doMock('@/utils/indexedDbStore', () => ({
    createIndexedDbStore: () => cacheStore,
  }))

  vi.doMock('@/utils/bridge', () => ({
    bridge,
    default: bridge,
  }))

  const { useAugmentsData } = await import('./useAugmentsData')
  const api = useAugmentsData()
  return { api, bridge, cacheStore }
}

describe('useAugmentsData', () => {
  it('命中有效缓存时直接返回缓存数据并跳过 API', async () => {
    const cachedPayload = { data: { 1: { name: 'A' } }, updateTime: '2026-03-03 10:00:00' }
    const { api, bridge } = await setupUseAugmentsData({
      cacheReadResult: { data: cachedPayload, cacheTime: Date.now() },
      bridgeDataResult: { data: { 2: { name: 'B' } }, updateTime: '2026-03-03 11:00:00' },
    })

    const result = await api.loadAugmentsData(false)

    expect(bridge.getAugmentsData).not.toHaveBeenCalled()
    expect(result._cached).toBe(true)
    expect(result.data).toEqual(cachedPayload.data)
  })

  it('缓存过期时回退 API，并写入新缓存', async () => {
    const { api, bridge, cacheStore } = await setupUseAugmentsData({
      cacheReadResult: {
        data: { data: { stale: true } },
        cacheTime: Date.now() - 31 * 60 * 1000,
      },
      bridgeDataResult: {
        data: { 2: { name: 'B' } },
        updateTime: '2026-03-03 11:00:00',
      },
    })

    const result = await api.loadAugmentsData(false)

    expect(bridge.getAugmentsData).toHaveBeenCalledTimes(1)
    expect(cacheStore.write).toHaveBeenCalledTimes(1)
    expect(result.data).toEqual({ 2: { name: 'B' } })
  })

  it('API 返回缺失 data 字段时抛出格式异常', async () => {
    const { api } = await setupUseAugmentsData({
      cacheReadResult: null,
      bridgeDataResult: { updateTime: '2026-03-03 11:00:00' },
    })

    await expect(api.loadAugmentsData(true)).rejects.toThrow(/data/)
    expect(api.loadError.value).toContain('data')
  })

  it('中止加载后不会覆盖现有状态', async () => {
    const asyncRequest = deferred()
    const { api, bridge, cacheStore } = await setupUseAugmentsData({
      cacheReadResult: null,
      bridgeDataResult: null,
    })

    bridge.getAugmentsData.mockReturnValue(asyncRequest.promise)

    const loadPromise = api.loadAugmentsData(true)
    api.abortPendingLoad()
    asyncRequest.resolve({
      data: { 3: { name: 'C' } },
      updateTime: '2026-03-03 12:00:00',
    })

    const result = await loadPromise

    expect(result).toBeNull()
    expect(api.augmentsData.value).toBeNull()
    expect(cacheStore.write).not.toHaveBeenCalled()
  })
})
