// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RuneConfigCard from './RuneConfigCard.vue'

const { applyRuneConfigMock, addFavoriteMock, removeFavoriteMock, isFavoriteMock } = vi.hoisted(() => ({
  applyRuneConfigMock: vi.fn(),
  addFavoriteMock: vi.fn(),
  removeFavoriteMock: vi.fn(),
  isFavoriteMock: vi.fn(() => false),
}))

vi.mock('@/utils/bridge', () => ({
  default: {
    applyRuneConfig: applyRuneConfigMock,
  },
}))

vi.mock('@/composables/useFavorites', () => ({
  useFavorites: () => ({
    isFavorite: isFavoriteMock,
    addFavorite: addFavoriteMock,
    removeFavorite: removeFavoriteMock,
  }),
}))

vi.mock('@/data/runes', () => ({
  getTreeById: (id) => ({ id, name: `Tree-${id}`, color: '#123456' }),
  getRuneById: (id) => ({ id, name: `Rune-${id}` }),
  getRuneIconUrl: (id) => `rune-${id}.png`,
  getStatShardById: (id) => ({ id, name: `Shard-${id}` }),
  getStatShardIconUrl: (id) => `shard-${id}.png`,
}))

function createProps() {
  return {
    config: {
      primary_page_id: 8000,
      secondary_page_id: 8100,
      primary_rune_ids: [8005, 9101, 9104, 8014],
      secondary_rune_ids: [8139, 8135],
      stat_mod_ids: [5008, 5008, 5002],
      play: 120,
      win: 70,
    },
    rank: 1,
    championId: '1',
    championName: 'Ahri',
    position: 'MID',
    totalGames: 200,
  }
}

function mountCard(props = createProps()) {
  return mount(RuneConfigCard, {
    props,
    global: {
      stubs: {
        WinRateBar: true,
        PopularityBadge: true,
        WinRateTrendChart: true,
      },
    },
  })
}

describe('RuneConfigCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    isFavoriteMock.mockReturnValue(false)
  })

  it('应用按钮触发成功事件，并在处理中禁用按钮', async () => {
    let resolveApply
    applyRuneConfigMock.mockReturnValue(
      new Promise((resolve) => {
        resolveApply = resolve
      }),
    )

    const wrapper = mountCard()
    const applyBtn = wrapper.get('.apply-btn')

    await applyBtn.trigger('click')
    expect(applyRuneConfigMock).toHaveBeenCalledTimes(1)
    expect(applyRuneConfigMock).toHaveBeenCalledWith(
      expect.objectContaining({ play: 120, win: 70 }),
      'Ahri',
      'MID',
    )
    expect(applyBtn.attributes('disabled')).toBeDefined()

    resolveApply({ success: true, message: 'ok' })
    await flushPromises()

    const payload = wrapper.emitted('applied')?.[0]?.[0]
    expect(payload).toMatchObject({ success: true, message: 'ok', code: 'OK' })
  })

  it('应用失败时发出异常事件', async () => {
    applyRuneConfigMock.mockRejectedValue(new Error('network down'))
    const wrapper = mountCard()

    await wrapper.get('.apply-btn').trigger('click')
    await flushPromises()

    const payload = wrapper.emitted('applied')?.[0]?.[0]
    expect(payload).toMatchObject({
      success: false,
      message: 'network down',
      code: 'RUNE_APPLY_EXCEPTION',
    })
  })

  it('收藏按钮在未收藏时调用 addFavorite', async () => {
    const wrapper = mountCard()
    const favoriteBtn = wrapper.findAll('.small-btn')[0]

    await favoriteBtn.trigger('click')

    expect(addFavoriteMock).toHaveBeenCalledTimes(1)
    expect(addFavoriteMock).toHaveBeenCalledWith(
      '1',
      'MID',
      expect.objectContaining({ play: 120, win: 70 }),
      1,
    )
    expect(removeFavoriteMock).not.toHaveBeenCalled()
  })
})
