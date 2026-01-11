/**
 * 与 Python 后端通信的桥接工具
 */

class Bridge {
  constructor() {
    this._pywebview = null
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
      return null
    }
    try {
      return await this.api[method](...args)
    } catch (e) {
      console.error(`Bridge call failed: ${method}`, e)
      return null
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

  // 游戏状态
  getGameflowPhase() {
    return this._call('get_gameflow_phase')
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
    return this._call('set_chat_config', config.auto_send, config.send_my_team, config.send_enemy, config.hotkey)
  }

  sendAnalysisToChat() {
    return this._call('send_analysis_to_chat')
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
}

export const bridge = new Bridge()

// 全局游戏结束回调
window.onGameEnd = (data) => {
  const event = new CustomEvent('game-end', { detail: data })
  window.dispatchEvent(event)
}

// 全局队伍分析回调
window.onTeamAnalysis = (data) => {
  const event = new CustomEvent('team-analysis', { detail: data })
  window.dispatchEvent(event)
}
