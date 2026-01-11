import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { bridge } from '@/utils/bridge'

export const useAppStore = defineStore('app', () => {
  // 状态
  const connected = ref(false)
  const gamePhase = ref('None')
  const autoAcceptEnabled = ref(false)
  const autoSelectEnabled = ref(false)
  const summoner = ref(null)

  // 计算属性
  const gamePhaseText = computed(() => {
    const phaseMap = {
      'None': '未连接',
      'Lobby': '大厅',
      'Matchmaking': '匹配中',
      'ReadyCheck': '准备检查',
      'ChampSelect': '选人中',
      'InProgress': '游戏中',
      'EndOfGame': '游戏结束',
      'WaitingForStats': '等待结算'
    }
    return phaseMap[gamePhase.value] || gamePhase.value
  })

  // 方法
  async function connect() {
    const result = await bridge.connect()
    connected.value = result?.success || false
    if (connected.value) {
      await refreshStatus()
    }
    return connected.value
  }

  async function refreshStatus() {
    const [connStatus, acceptStatus, selectStatus, phase, summonerInfo] = await Promise.all([
      bridge.getConnectionStatus(),
      bridge.getAutoAcceptStatus(),
      bridge.getAutoSelectStatus(),
      bridge.getGameflowPhase(),
      bridge.getCurrentSummoner()
    ])

    connected.value = connStatus?.connected || false
    autoAcceptEnabled.value = acceptStatus?.enabled || false
    autoSelectEnabled.value = selectStatus?.enabled || false
    gamePhase.value = phase?.phase || 'None'
    summoner.value = summonerInfo
  }

  async function setAutoAccept(enabled) {
    await bridge.setAutoAccept(enabled)
    autoAcceptEnabled.value = enabled
  }

  async function setAutoSelect(enabled) {
    await bridge.setAutoSelect(enabled)
    autoSelectEnabled.value = enabled
  }

  return {
    connected,
    gamePhase,
    gamePhaseText,
    autoAcceptEnabled,
    autoSelectEnabled,
    summoner,
    connect,
    refreshStatus,
    setAutoAccept,
    setAutoSelect
  }
})
