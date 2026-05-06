/**
 * 与 Python 后端通信的桥接工具
 */

class Bridge {
  constructor() {
    this._pywebview = null
    this._errorSeq = 0
  }

  _nextTraceId(method = 'bridge') {
    this._errorSeq += 1
    return `${method}-${Date.now()}-${this._errorSeq}`
  }

  _makeErrorEnvelope(method, error, fallbackCode = 'BRIDGE_CALL_FAILED') {
    const code = error?.code || fallbackCode
    const message = error?.message || '调用失败'
    return {
      success: false,
      error: true,
      code,
      message,
      retryable: true,
      traceId: this._nextTraceId(method),
      details: error instanceof Error ? error.stack || error.message : String(error || ''),
    }
  }

  _makeSuccessEnvelope(data) {
    return {
      success: true,
      error: false,
      ...data,
    }
  }

  _isErrorEnvelope(result) {
    return !!result && (result.error === true || result.success === false)
  }

  _normalizeResult(method, result) {
    if (this._isErrorEnvelope(result)) return result
    if (result && typeof result === 'object' && !Array.isArray(result)) {
      return this._makeSuccessEnvelope(result)
    }
    return this._makeSuccessEnvelope({ value: result, method })
  }

  get api() {
    if (!this._pywebview && window.pywebview) {
      this._pywebview = window.pywebview.api
    }
    return this._pywebview
  }

  async _call(method, ...args) {
    if (!this.api) {
      console.warn('PyWebView API not available')
      return this._makeErrorEnvelope(method, { message: 'PyWebView API 不可用', code: 'PYWEBVIEW_API_UNAVAILABLE' })
    }
    const maxRetries = 1
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const timeoutMs = 15000
        const result = await Promise.race([
          this.api[method](...args),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Bridge 调用超时')), timeoutMs)
          ),
        ])
        return this._normalizeResult(method, result)
      } catch (e) {
        const msg = String(e?.message || e || '')
        const isRetryable = msg.includes('超时') || msg.includes('timeout')
        if (attempt < maxRetries && isRetryable) {
          await new Promise((r) => setTimeout(r, 200 * (attempt + 1)))
          continue
        }
        console.error(`Bridge call failed: ${method}`, e)
        return this._makeErrorEnvelope(method, e, isRetryable ? 'TRANSIENT_ERROR' : 'BRIDGE_CALL_FAILED')
      }
    }
  }

  // 连接相关
  connect() {
    return this._call('connect')
  }

  disconnect() {
    return this._call('disconnect')
  }

  getConnectionStatus() {
    return this._call('get_connection_status')
  }

  getRuntimeSnapshot() {
    return this._call('get_runtime_snapshot')
  }

  // 自动准备
  getAutoAcceptStatus() {
    return this._call('get_auto_accept_status')
  }

  setAutoAccept(enabled) {
    return this._call('set_auto_accept', enabled)
  }

  // 自动选人
  getAutoSelectStatus() {
    return this._call('get_auto_select_status')
  }

  setAutoSelect(enabled) {
    return this._call('set_auto_select', enabled)
  }

  setAutoSelectOneShot(oneshot) {
    return this._call('set_auto_select_oneshot', oneshot)
  }

  getSelectConfig() {
    return this._call('get_select_config')
  }

  setSelectConfig(banList, pickList) {
    return this._call('set_select_config', banList, pickList)
  }

  // 英雄数据
  getChampions() {
    return this._call('get_champions')
  }

  // 战绩相关
  getCurrentMatchStats() {
    return this._call('get_current_match_stats')
  }

  getMatchHistoryList(limit, offset, gameMode, championId) {
    return this._call('get_match_history_list', limit, offset, gameMode, championId)
  }

  getMatchDetail(gameId) {
    return this._call('get_match_detail', gameId)
  }

  getStats() {
    return this._call('get_stats')
  }

  getBattleProfileSummary() {
    return this._call('get_battle_profile_summary')
  }

  refreshBattleProfileSummary() {
    return this._call('refresh_battle_profile_summary')
  }

  getBattleHistoryPage(page, pageSize, filters) {
    return this._call('get_battle_history_page', page, pageSize, filters)
  }

  getBattleMatchDetail(gameId) {
    return this._call('get_battle_match_detail', gameId)
  }

  // 游戏状态
  getGameflowPhase() {
    return this._call('get_gameflow_phase')
  }

  getGameModeRouteHint() {
    return this._call('get_game_mode_route_hint')
  }

  getCurrentSummoner() {
    return this._call('get_current_summoner')
  }

  // 队伍分析
  getTeamAnalysis() {
    return this._call('get_team_analysis')
  }

  refreshTeamAnalysis() {
    return this._call('refresh_team_analysis')
  }

  // 聊天发送
  getChatConfig() {
    return this._call('get_chat_config')
  }

  setChatConfig(config) {
    return this._call(
      'set_chat_config',
      config?.auto_send,
      config?.send_my_team,
      config?.send_enemy,
      config?.hotkey,
    )
  }

  sendAnalysisToChat() {
    return this._call('send_analysis_to_chat')
  }

  // 当前选择的英雄
  getCurrentChampion() {
    return this._call('get_current_champion')
  }

  getRunesData() {
    return this._call('get_runes_data')
  }

  getRunesEntry(championId, position) {
    return this._call('get_runes_entry', championId, position)
  }

  getRunesDataStatus() {
    return this._call('get_runes_data_status')
  }

  refreshRunesData() {
    return this._call('refresh_runes_data')
  }

  refreshRunesSingle(championId, championKey, position, region) {
    return this._call('refresh_runes_single', championId, championKey, position, region)
  }

  refreshRunesSelected(targets, region, positions) {
    return this._call('refresh_runes_selected', targets, region, positions)
  }

  getChampionOverview(championKey, position, region) {
    return this._call('get_champion_overview', championKey, position, region)
  }

  getAugmentsData() {
    return this._call('get_augments_data')
  }

  getAugmentsDataStatus() {
    return this._call('get_augments_data_status')
  }

  refreshAugmentsData() {
    return this._call('refresh_augments_data')
  }

  // 实时对局数据
  getLiveGameData() {
    return this._call('get_live_game_data')
  }

  // 游戏内聊天
  getIngameChatStatus() {
    return this._call('get_ingame_chat_status')
  }

  setIngameChat(enabled) {
    return this._call('set_ingame_chat', enabled)
  }

  sendIngameTaunt() {
    return this._call('send_ingame_taunt')
  }

  // 符文应用
  applyRuneConfig(runeConfig, championName, position) {
    return this._call('apply_rune_config', runeConfig, championName, position)
  }

  // 登录相关
  getServerList() {
    return this._call('get_server_list')
  }

  detectGamePath() {
    return this._call('detect_game_path')
  }

  getLoginStatus() {
    return this._call('get_login_status')
  }

  startLogin(qq, password, serverIndex, gamePath, accountId) {
    return this._call('start_login', qq, password, serverIndex, gamePath, accountId)
  }

  forceCloseGame() {
    return this._call('force_close_game')
  }

  // 账号管理
  getAccounts() {
    return this._call('get_accounts')
  }

  addAccount(qq, password, nickname, serverIndex, gamePath) {
    return this._call('add_account', qq, password, nickname, serverIndex, gamePath)
  }

  updateAccount(accountId, qq, password, nickname, serverIndex, gamePath) {
    return this._call('update_account', accountId, qq, password, nickname, serverIndex, gamePath)
  }

  deleteAccount(accountId) {
    return this._call('delete_account', accountId)
  }

  setDefaultAccount(accountId) {
    return this._call('set_default_account', accountId)
  }

  focusLoginCaptcha() {
    return this._call('focus_login_captcha')
  }

  fetchSummonerName(accountId) {
    return this._call('fetch_summoner_name', accountId)
  }

  // 自动加好友
  getAutoFriends() {
    return this._call('get_auto_friends')
  }

  addAutoFriend(name, tag) {
    return this._call('add_auto_friend', name, tag)
  }

  removeAutoFriend(name, tag) {
    return this._call('remove_auto_friend', name, tag)
  }

  triggerAddFriends() {
    return this._call('trigger_add_friends')
  }

  deleteAllFriends() {
    return this._call('delete_all_friends')
  }

  // 自动分解精粹
  getAutoDisenchant() {
    return this._call('get_auto_disenchant')
  }

  setAutoDisenchant(enabled) {
    return this._call('set_auto_disenchant', enabled)
  }

  disenchantAllShards() {
    return this._call('disenchant_all_shards')
  }

  getLootShards() {
    return this._call('get_loot_shards')
  }

  // 野怪监控
  getJungleMonitorStatus() {
    return this._call('get_jungle_monitor_status')
  }

  setJungleMonitorConfig(configData) {
    return this._call('set_jungle_monitor_config', configData)
  }

  startJungleMonitor() {
    return this._call('start_jungle_monitor')
  }

  stopJungleMonitor() {
    return this._call('stop_jungle_monitor')
  }

  setJungleMonitorAutoStart(enabled) {
    return this._call('set_jungle_monitor_auto_start', enabled)
  }

  getJungleMonitorLogs() {
    return this._call('get_jungle_monitor_logs')
  }

  clearJungleMonitorLogs() {
    return this._call('clear_jungle_monitor_logs')
  }

  getCachedJungleMessage() {
    return this._call('get_cached_jungle_message')
  }

  sendCachedJungleMessage() {
    return this._call('send_cached_jungle_message')
  }

  testJungleOcr() {
    return this._call('test_jungle_ocr')
  }

  startRegionSelect() {
    return this._call('start_region_select')
  }

  // 缓存置换
  replaceCacheFiles() {
    return this._call('replace_cache_files')
  }

  listCacheBackups() {
    return this._call('list_cache_backups')
  }

  rollbackCache(backupName) {
    return this._call('rollback_cache', backupName)
  }

  exportCacheLogs(logs) {
    return this._call('export_cache_logs', logs)
  }

  getCacheTemplateInfo() {
    return this._call('get_cache_template_info')
  }

  checkTargetSafety(targetPath) {
    return this._call('check_target_safety', targetPath)
  }

  getRecommendedPaths() {
    return this._call('get_recommended_paths')
  }

  quickRestoreLatestBackup() {
    return this._call('quick_restore_latest_backup')
  }

  getOperationStatistics() {
    return this._call('get_operation_statistics')
  }

  cleanupAllTempFiles(targetPath) {
    return this._call('cleanup_all_temp_files', targetPath)
  }

  // 设置锁定
  getSettingsLockConfig() {
    return this._call('get_settings_lock_config')
  }

  setSettingsLockConfig(enabled, autoRestore, gamePath) {
    return this._call('set_settings_lock_config', enabled, autoRestore, gamePath)
  }

  saveCurrentSettings() {
    return this._call('save_current_settings')
  }

  restoreSettings() {
    return this._call('restore_settings')
  }

  getSettingsTemplateInfo() {
    return this._call('get_settings_template_info')
  }
}

export const bridge = new Bridge()
export default bridge

const bridgeEvents = {
  onGameEnd: 'game-end',
  onTeamAnalysis: 'team-analysis',
  onRuntimeSnapshot: 'runtime-snapshot',
  onBanDetected: 'ban-detected',
  onPostLoginTools: 'post-login-tools',
}

function dispatchBridgeEvent(type, data) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(type, { detail: data }))
}

Object.entries(bridgeEvents).forEach(([handlerName, eventType]) => {
  if (typeof window === 'undefined') return
  window[handlerName] = (data) => dispatchBridgeEvent(eventType, data)
})
