import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { bridge } from '@/utils/bridge'

export function useRuntimeSync(appStore, matchStore) {
  const router = useRouter()
  const route = useRoute()

  let chatHotkey = 'F1'
  let lastAutoRouteAt = 0
  let stopAutoRouteWatch = null

  function applyRuntimeSnapshot(snapshot) {
    if (!snapshot || snapshot.error) return false

    appStore.connected = !!snapshot.connected
    appStore.gamePhase = snapshot.game_phase || 'None'
    appStore.autoAcceptEnabled = !!snapshot.auto_accept?.enabled
    appStore.autoSelectEnabled = !!snapshot.auto_select?.enabled
    appStore.autoSelectOneShot = snapshot.auto_select?.oneshot ?? true
    appStore.recommendedRoute = snapshot.recommended_route || '/runes'
    appStore.gameModeType = snapshot.game_mode_type || 'CLASSIC'
    appStore.updateCurrentChampion(
      snapshot.game_phase === 'ChampSelect' ? snapshot.current_champion?.champion_id : null,
    )
    return true
  }

  function onGameEnd(event) {
    matchStore.setCurrentMatch(event?.detail || null)
  }

  function onRuntimeSnapshot(event) {
    applyRuntimeSnapshot(event?.detail)
  }

  async function loadChatConfig() {
    const cfg = await bridge.getChatConfig()
    if (cfg?.success && cfg?.hotkey) {
      chatHotkey = cfg.hotkey
    }
  }

  function shouldAutoRoute() {
    return appStore.connected && appStore.gamePhase === 'ChampSelect'
  }

  async function autoRouteByMode() {
    if (!shouldAutoRoute()) return
    const targetRoute = appStore.recommendedRoute || '/runes'
    if (!['/runes', '/augments'].includes(targetRoute)) return
    if (targetRoute === route.path) return

    const now = Date.now()
    if (now - lastAutoRouteAt < 1200) return
    lastAutoRouteAt = now

    await router.replace(targetRoute)
  }

  function onGlobalKeydown(event) {
    const active = document.activeElement
    if (!active) return
    const tag = active.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || active.isContentEditable) return

    const key = String(event.key || '').toUpperCase()
    if (key === chatHotkey) {
      event.preventDefault()
      bridge.sendAnalysisToChat()
    }
  }

  onMounted(async () => {
    await loadChatConfig()

    window.addEventListener('keydown', onGlobalKeydown)
    window.addEventListener('game-end', onGameEnd)
    window.addEventListener('runtime-snapshot', onRuntimeSnapshot)

    stopAutoRouteWatch = watch(
      () => [appStore.connected, appStore.gamePhase, appStore.recommendedRoute],
      () => {
        autoRouteByMode()
      },
      { immediate: true },
    )
  })

  onUnmounted(() => {
    if (stopAutoRouteWatch) {
      stopAutoRouteWatch()
      stopAutoRouteWatch = null
    }
    window.removeEventListener('game-end', onGameEnd)
    window.removeEventListener('runtime-snapshot', onRuntimeSnapshot)
    window.removeEventListener('keydown', onGlobalKeydown)
  })
}
