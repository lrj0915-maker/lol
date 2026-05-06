// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAppStore } from '@/stores/app'

const { bridgeMock } = vi.hoisted(() => ({
  bridgeMock: {
    getServerList: vi.fn(),
    getAccounts: vi.fn(),
    getAutoFriends: vi.fn(),
    detectGamePath: vi.fn(),
    updateAccount: vi.fn(),
    addAccount: vi.fn(),
    startLogin: vi.fn(),
    getLoginStatus: vi.fn(),
    focusLoginCaptcha: vi.fn(),
    setDefaultAccount: vi.fn(),
    fetchSummonerName: vi.fn(),
    addAutoFriend: vi.fn(),
    removeAutoFriend: vi.fn(),
    triggerAddFriends: vi.fn(),
    deleteAllFriends: vi.fn(),
    disenchantAllShards: vi.fn(),
  },
}))

vi.mock('@/utils/bridge', () => ({
  default: bridgeMock,
}))

import LoginView from './LoginView.vue'

function buildAccounts() {
  return [
    {
      id: 'acct-1',
      qq: '10001',
      password: 'pw1',
      nickname: '主号',
      server_index: 0,
      summoner_name: '召唤师一号',
      last_login_status: 'success',
      is_default: true,
      ban_info: '检测到违规软件加载，游戏环境异常',
      ban_type: '封号',
      ban_end: '2026-04-02 01:09:36',
      ban_days: '30',
    },
    {
      id: 'acct-2',
      qq: '20002',
      password: 'pw2',
      nickname: '小号',
      server_index: 1,
      summoner_name: '测试召唤师',
      last_login_status: 'failed',
      is_default: false,
    },
  ]
}

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(LoginView, {
    global: {
      plugins: [pinia],
    },
  })
  return { wrapper, appStore: useAppStore() }
}

describe('LoginView', () => {
  let wrapper
  let appStore

  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    setActivePinia(createPinia())
    bridgeMock.getServerList.mockResolvedValue([
      { index: 0, name: '艾欧尼亚' },
      { index: 1, name: '祖安' },
      { index: 18, name: '皮城警备' },
    ])
    bridgeMock.getAccounts.mockResolvedValue(buildAccounts())
    bridgeMock.getAutoFriends.mockResolvedValue([{ name: '好友一', tag: 'CN1' }])
    bridgeMock.detectGamePath.mockResolvedValue({ success: true, path: 'D:/Game' })
    bridgeMock.updateAccount.mockResolvedValue({ success: true })
    bridgeMock.addAccount.mockResolvedValue({ success: true, id: 'acct-1' })
    bridgeMock.startLogin.mockResolvedValue({ success: true })
    bridgeMock.getLoginStatus.mockResolvedValue({ status: 'idle', phase: 'idle', message: '', progress: 0 })
    bridgeMock.focusLoginCaptcha.mockResolvedValue({ success: true, message: '已尝试将验证码窗口置前' })
    bridgeMock.setDefaultAccount.mockResolvedValue({ success: true })
    bridgeMock.fetchSummonerName.mockResolvedValue({ success: true })
    bridgeMock.addAutoFriend.mockResolvedValue({ success: true })
    bridgeMock.removeAutoFriend.mockResolvedValue({ success: true })
    bridgeMock.triggerAddFriends.mockResolvedValue({ success: true, message: '指定好友添加完成' })
    bridgeMock.deleteAllFriends.mockResolvedValue({ success: true, message: '非白名单好友删除完成' })
    bridgeMock.disenchantAllShards.mockResolvedValue({ success: true, count: 2, total_value: 420 })
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('选中已保存封号账号时直接展示封号信息块', async () => {
    ;({ wrapper } = mountView())
    await flushPromises()

    expect(wrapper.text()).toContain('账号风险')
    expect(wrapper.text()).toContain('封禁类型')
    expect(wrapper.text()).toContain('2026-04-02 01:09:36')
    expect(wrapper.text()).toContain('检测到违规软件加载，游戏环境异常')
  })

  it('登录过程中收到封号状态时显示顶部风险信息', async () => {
    bridgeMock.getLoginStatus.mockResolvedValue({
      status: 'banned',
      phase: 'banned',
      message: '账号封号',
      progress: 0,
      ban_info: '账号已被封停',
      ban_type: '封停',
      ban_end: '2026-04-08 01:09:27',
    })

    ;({ wrapper } = mountView())
    await flushPromises()

    await wrapper.get('.cred-input').setValue('10001----pw1')
    await wrapper.findAll('button').find((button) => button.text() === '登录').trigger('click')
    await vi.advanceTimersByTimeAsync(800)
    await flushPromises()

    expect(wrapper.find('.status-banner.danger').exists()).toBe(true)
    expect(wrapper.text()).toContain('账号已封禁')
    expect(wrapper.text()).toContain('2026-04-08 01:09:27')
    expect(wrapper.text()).toContain('账号已被封停')
  })

  it('验证码阶段可以聚焦验证码窗口', async () => {
    bridgeMock.getLoginStatus.mockResolvedValue({
      status: 'logging_in',
      phase: 'waiting_captcha',
      message: '请完成验证码',
      progress: 55,
    })

    ;({ wrapper } = mountView())
    await flushPromises()

    await wrapper.get('.cred-input').setValue('10001----pw1')
    await wrapper.findAll('button').find((button) => button.text() === '登录').trigger('click')
    await vi.advanceTimersByTimeAsync(800)
    await flushPromises()

    expect(wrapper.find('.helper-box').exists()).toBe(true)

    const focusButton = wrapper.findAll('button').find((button) => button.text().includes('验证码'))
    await focusButton.trigger('click')
    await flushPromises()

    expect(bridgeMock.focusLoginCaptcha).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('已尝试将验证码窗口置前')
  })

  it('好友工具可以增删并执行批量操作', async () => {
    const accounts = buildAccounts()
    bridgeMock.getAccounts.mockResolvedValue(accounts)

    ;({ wrapper, appStore } = mountView())
    appStore.connected = true
    await flushPromises()

    const inputs = wrapper.findAll('.friend-form input')
    await inputs[0].setValue('好友二')
    await inputs[1].setValue('CN2')
    await wrapper.findAll('.friend-form .primary-btn')[0].trigger('click')
    await flushPromises()

    expect(bridgeMock.addAutoFriend).toHaveBeenCalledWith('好友二', 'CN2')

    await wrapper.find('.friend-row .ghost-btn').trigger('click')
    await flushPromises()
    expect(bridgeMock.removeAutoFriend).toHaveBeenCalledWith('好友一', 'CN1')

    const addFriendsButton = wrapper.findAll('button').find((button) => button.text() === '添加指定好友')
    await addFriendsButton.trigger('click')
    await flushPromises()
    expect(bridgeMock.triggerAddFriends).toHaveBeenCalledTimes(1)

    const deleteFriendsButton = wrapper.findAll('button').find((button) => button.text() === '删除非白名单好友')
    await deleteFriendsButton.trigger('click')
    await flushPromises()
    expect(bridgeMock.deleteAllFriends).toHaveBeenCalledTimes(1)
  })

  it('分解精粹按钮执行后展示结果', async () => {
    ;({ wrapper, appStore } = mountView())
    appStore.connected = true
    await flushPromises()

    await wrapper.findAll('.primary-btn').find((button) => button.text().includes('分解精粹')).trigger('click')
    await flushPromises()

    expect(bridgeMock.disenchantAllShards).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('分解 2 个，获得 420')
  })

  it('可以切换账号并设为默认账号', async () => {
    ;({ wrapper } = mountView())
    await flushPromises()

    await wrapper.findAll('.account-row')[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('小号')
    expect(wrapper.text()).toContain('测试召唤师')

    const defaultButton = wrapper.findAll('button').find((button) => button.text() === '设为默认')
    await defaultButton.trigger('click')
    await flushPromises()
    expect(bridgeMock.setDefaultAccount).toHaveBeenCalledWith('acct-2')
  })
})
