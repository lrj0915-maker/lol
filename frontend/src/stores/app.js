import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { bridge } from '@/utils/bridge'

const phaseMap = {
  None: '未连接',
  Lobby: '大厅',
  Matchmaking: '匹配中',
  ReadyCheck: '准备检查',
  ChampSelect: '选人中',
  InProgress: '游戏中',
  EndOfGame: '游戏结束',
  WaitingForStats: '等待结算',
}

export const useAppStore = defineStore('app', () => {
  const connected = ref(false)
  const gamePhase = ref('None')
  const autoAcceptEnabled = ref(false)
  const autoSelectEnabled = ref(false)
  const autoSelectOneShot = ref(true)
  const summoner = ref(null)
  const currentChampionId = ref(null)
  const recommendedRoute = ref('/runes')
  const gameModeType = ref('CLASSIC')
  const lastError = ref(null)
  const _statusInflight = ref(null)
  const _lastStatusAt = ref(0)

  const gamePhaseText = computed(() => phaseMap[gamePhase.value] || gamePhase.value)

  function setError(result) {
    lastError.value = result?.error ? result : null
  }

  function updateCurrentChampion(championId) {
    currentChampionId.value = championId || null
  }

  function applySnapshot(snapshot) {
    if (!snapshot || snapshot.error) return

    connected.value = !!snapshot.connected
    gamePhase.value = snapshot.game_phase || 'None'
    autoAcceptEnabled.value = !!snapshot.auto_accept?.enabled
    autoSelectEnabled.value = !!snapshot.auto_select?.enabled
    autoSelectOneShot.value = snapshot.auto_select?.oneshot ?? true
    summoner.value = snapshot.summoner || null
    recommendedRoute.value = snapshot.recommended_route || '/runes'
    gameModeType.value = snapshot.game_mode_type || 'CLASSIC'

    if (gamePhase.value === 'ChampSelect' && snapshot.current_champion?.champion_id) {
      updateCurrentChampion(snapshot.current_champion.champion_id)
    }
  }

  async function connect() {
    const result = await bridge.connect()
    connected.value = !!result?.success
    setError(result)
    if (connected.value) {
      await refreshStatus()
    }
    return connected.value
  }

  async function refreshStatus() {
    const now = Date.now()
    if (_statusInflight.value) return _statusInflight.value

    if (now - _lastStatusAt.value < 800) {
      return {
        connected: connected.value,
        game_phase: gamePhase.value,
        recommended_route: recommendedRoute.value,
        game_mode_type: gameModeType.value,
      }
    }

    _statusInflight.value = (async () => {
      const snapshot = await bridge.getRuntimeSnapshot()
      if (snapshot?.success) {
        applySnapshot(snapshot)
        _lastStatusAt.value = Date.now()
        setError(null)
        return snapshot
      }

      const [connStatus, acceptStatus, selectStatus, phase, summonerInfo, modeHint] = await Promise.all([
        bridge.getConnectionStatus(),
        bridge.getAutoAcceptStatus(),
        bridge.getAutoSelectStatus(),
        bridge.getGameflowPhase(),
        bridge.getCurrentSummoner(),
        bridge.getGameModeRouteHint(),
      ])

      connected.value = !!connStatus?.connected
      autoAcceptEnabled.value = !!acceptStatus?.enabled
      autoSelectEnabled.value = !!selectStatus?.enabled
      autoSelectOneShot.value = selectStatus?.oneshot ?? true
      gamePhase.value = phase?.phase || 'None'
      summoner.value = summonerInfo?.success === false ? null : (summonerInfo || null)
      recommendedRoute.value = modeHint?.route || '/runes'
      gameModeType.value = modeHint?.mode || 'CLASSIC'
      _lastStatusAt.value = Date.now()
      setError(snapshot)

      if (gamePhase.value === 'ChampSelect') {
        await refreshCurrentChampion()
      }

      return {
        connected: connected.value,
        game_phase: gamePhase.value,
        recommended_route: recommendedRoute.value,
        game_mode_type: gameModeType.value,
      }
    })()

    try {
      return await _statusInflight.value
    } finally {
      _statusInflight.value = null
    }
  }

  async function refreshCurrentChampion() {
    const result = await bridge.getCurrentChampion()
    updateCurrentChampion(result?.success ? result?.champion_id : null)
    setError(result)
  }

  async function setAutoAccept(enabled) {
    const result = await bridge.setAutoAccept(enabled)
    autoAcceptEnabled.value = !!result?.success ? enabled : autoAcceptEnabled.value
    setError(result)
  }

  async function setAutoSelect(enabled) {
    const result = await bridge.setAutoSelect(enabled)
    autoSelectEnabled.value = !!result?.success ? enabled : autoSelectEnabled.value
    setError(result)
  }

  async function setAutoSelectOneShot(oneshot) {
    const result = await bridge.setAutoSelectOneShot(oneshot)
    autoSelectOneShot.value = !!result?.success ? !!oneshot : autoSelectOneShot.value
    setError(result)
  }

  return {
    connected,
    gamePhase,
    gamePhaseText,
    autoAcceptEnabled,
    autoSelectEnabled,
    autoSelectOneShot,
    summoner,
    currentChampionId,
    recommendedRoute,
    gameModeType,
    lastError,
    connect,
    refreshStatus,
    refreshCurrentChampion,
    setAutoAccept,
    setAutoSelect,
    setAutoSelectOneShot,
    updateCurrentChampion,
  }
})
