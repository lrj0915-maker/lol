// @vitest-environment jsdom
import { ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import RunesView from './RunesView.vue'

let bridgeApplyRuneConfigMock
let appStoreMock
let userPrefsMock
let useRunesDataReturn

vi.mock('@/utils/bridge', () => ({
  default: {
    applyRuneConfig: (...args) => bridgeApplyRuneConfigMock(...args),
  },
}))

vi.mock('@/stores/app', () => ({
  useAppStore: () => appStoreMock,
}))

vi.mock('@/composables/useFavorites', () => ({
  useFavorites: () => ({}),
}))

vi.mock('@/composables/useUserPreferences', () => ({
  useUserPreferences: () => userPrefsMock,
}))

vi.mock('@/utils/ddragon', () => ({
  getChampionIcon: (id) => `champ-${id}.png`,
  getItemIcon: (id) => `item-${id}.png`,
}))

vi.mock('@/data/champions', () => {
  const champions = [{ id: 1, key: 'Ahri', name: '阿狸', nameEn: 'Ahri' }]
  return {
    champions,
    getChampionById: (id) => champions.find((item) => Number(item.id) === Number(id)) || null,
    searchChampions: () => champions,
  }
})

vi.mock('@/composables/useRunesData', () => ({
  useRunesData: () => useRunesDataReturn,
}))

function createRunesData() {
  return {
    data: {
      1: {
        key: 'Ahri',
        positions: {
          MID: {
            rune_pages: [
              { id: 'A', play: 100, win: 50 },
              { id: 'B', play: 50, win: 30 },
            ],
            starter_items: [],
            boots: [],
            core_items: [],
          },
        },
      },
    },
    version: '16.1',
    updateTime: '2026-03-03 10:00:00',
    meta: { region: 'CN', source_region: 'CN' },
  }
}

function mountView() {
  return mount(RunesView, {
    global: {
      stubs: {
        EmptyStateCard: true,
        RuneConfigCard: {
          props: ['config', 'rank'],
          template: `
            <div class="rune-card-stub" :data-id="config.id" :data-rank="rank">
              <button class="emit-fail" @click="$emit('applied', { success: false, code: 'RUNE_PAGE_FULL' })">emit</button>
            </div>
          `,
        },
      },
    },
  })
}

describe('RunesView interactions', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    bridgeApplyRuneConfigMock = vi.fn()
    appStoreMock = { currentChampionId: 1, gamePhase: 'None' }
    userPrefsMock = {
      getSortBy: vi.fn(() => 'winRate'),
      getLastPosition: vi.fn(() => 'MID'),
      getActiveRegion: vi.fn(() => 'CN'),
      setLastPosition: vi.fn(),
      setSortBy: vi.fn(),
      setActiveRegion: vi.fn(),
      rememberSelectedChampion: vi.fn(),
    }

    const runesData = ref(createRunesData())
    useRunesDataReturn = {
      runesData,
      isLoading: ref(false),
      loadError: ref(null),
      loadProgress: ref(100),
      loadRunesData: vi.fn(async () => runesData.value),
      clearCache: vi.fn(async () => {}),
      getRunesStatus: vi.fn(async () => ({ exists: false })),
      refreshRunesDataOnServer: vi.fn(async () => ({ success: true })),
      refreshSingleRunesEntry: vi.fn(async () => ({ success: true })),
      getChampionOverview: vi.fn(async () => ({ success: false })),
    }
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
  })

  it('默认按胜率排序，切换后按场次排序', async () => {
    wrapper = mountView()
    await flushPromises()

    let cards = wrapper.findAll('.rune-card-stub')
    expect(cards[0].attributes('data-id')).toBe('B')
    expect(cards[1].attributes('data-id')).toBe('A')

    const sortButtons = wrapper.findAll('.sort-group .sort-btn')
    await sortButtons[1].trigger('click')
    await flushPromises()

    cards = wrapper.findAll('.rune-card-stub')
    expect(cards[0].attributes('data-id')).toBe('A')
    expect(cards[1].attributes('data-id')).toBe('B')
  })

  it('一键应用使用顶部推荐，并显示错误提示', async () => {
    bridgeApplyRuneConfigMock.mockResolvedValue({ success: false, code: 'RUNE_PAGE_FULL' })
    wrapper = mountView()
    await flushPromises()

    await wrapper.get('.act-btn.primary').trigger('click')
    await flushPromises()

    expect(bridgeApplyRuneConfigMock).toHaveBeenCalledTimes(1)
    expect(bridgeApplyRuneConfigMock.mock.calls[0][0]).toMatchObject({ id: 'B' })
    expect(wrapper.text()).toContain('符文页已满，请先删除一个自定义页。')
  })

  it('卡片 applied 事件会触发错误映射文案', async () => {
    wrapper = mountView()
    await flushPromises()

    await wrapper.get('.emit-fail').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('符文页已满，请先删除一个自定义页。')
  })
})
