<template>
  <div class="live-panel">
    <!-- 等待加载 -->
    <div class="live-loading" v-if="!data">
      <div class="spinner"></div>
      <p>等待游戏加载...</p>
    </div>

    <template v-else>
      <!-- 团队总览 -->
      <div class="team-overview">
        <div class="overview-title">团队总览</div>
        <div class="compare-row">
          <span class="compare-label ally-label">我方</span>
          <span class="compare-val ally-val">{{ data.my_kills }}</span>
          <div class="compare-bar-wrap">
            <div class="compare-bar ally-bar" :style="{ width: killPct.ally + '%' }"></div>
            <div class="compare-bar enemy-bar" :style="{ width: killPct.enemy + '%' }"></div>
          </div>
          <span class="compare-val enemy-val">{{ data.enemy_kills }}</span>
          <span class="compare-label enemy-label">对方</span>
        </div>
      </div>

      <!-- 双方玩家表格 -->
      <div class="teams-section">
        <div class="team-block">
          <div class="team-header ally-header">我方</div>
          <table class="player-table">
            <thead>
              <tr>
                <th class="col-champ">英雄</th>
                <th class="col-lvl">等级</th>
                <th class="col-kda">KDA</th>
                <th class="col-cs">补刀</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in data.my_team" :key="p.name" :class="{ 'is-me': p.is_me }">
                <td class="col-champ">{{ p.champion }}</td>
                <td class="col-lvl">{{ p.level }}</td>
                <td class="col-kda">
                  <span class="k">{{ p.kills }}</span>/<span class="d">{{ p.deaths }}</span>/<span class="a">{{ p.assists }}</span>
                </td>
                <td class="col-cs">{{ p.cs }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="team-block">
          <div class="team-header enemy-header">对方</div>
          <table class="player-table">
            <thead>
              <tr>
                <th class="col-champ">英雄</th>
                <th class="col-lvl">等级</th>
                <th class="col-kda">KDA</th>
                <th class="col-cs">补刀</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in data.enemy_team" :key="p.name">
                <td class="col-champ">{{ p.champion }}</td>
                <td class="col-lvl">{{ p.level }}</td>
                <td class="col-kda">
                  <span class="k">{{ p.kills }}</span>/<span class="d">{{ p.deaths }}</span>/<span class="a">{{ p.assists }}</span>
                </td>
                <td class="col-cs">{{ p.cs }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 重要事件 -->
      <div class="events-section" v-if="data.events && data.events.length">
        <div class="events-title">重要事件</div>
        <div class="events-list">
          <div
            v-for="(ev, i) in data.events"
            :key="i"
            class="event-item"
            :class="ev.side"
          >
            <span class="event-time">{{ formatTime(ev.time) }}</span>
            <span class="event-side-icon">{{ ev.side === 'ally' ? '🟦' : '🟥' }}</span>
            <span class="event-label">{{ ev.side === 'ally' ? '我方' : '对方' }} {{ ev.label }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: null }
})

const killPct = computed(() => {
  if (!props.data) return { ally: 50, enemy: 50 }
  const total = (props.data.my_kills || 0) + (props.data.enemy_kills || 0)
  if (total === 0) return { ally: 50, enemy: 50 }
  return {
    ally: Math.round(props.data.my_kills / total * 100),
    enemy: Math.round(props.data.enemy_kills / total * 100),
  }
})

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.live-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  height: 100%;
  overflow-y: auto;
  animation: panelEnter var(--duration-slow) var(--ease-smooth);
}

@keyframes panelEnter {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.live-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.live-loading .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-secondary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.live-loading p {
  animation: loadPulse 2s ease-in-out infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes loadPulse { 0%,100% { opacity: 0.6; } 50% { opacity: 1; } }

/* 团队总览 */
.team-overview {
  background: var(--gradient-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  position: relative;
  overflow: hidden;
}

/* 顶部发光线 */
.team-overview::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
  opacity: 0.5;
}

.overview-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.compare-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compare-label { font-size: 12px; min-width: 28px; }
.ally-label { color: var(--color-info); text-align: right; }
.enemy-label { color: var(--color-lose); }

.compare-val { font-size: 16px; font-weight: 700; font-family: 'Consolas', monospace; min-width: 28px; text-align: center; }
.ally-val { color: var(--color-info); }
.enemy-val { color: var(--color-lose); }

.compare-bar-wrap {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  display: flex;
  overflow: hidden;
  background: var(--bg-primary);
}

.compare-bar {
  height: 100%;
  transition: width 0.5s ease;
}

.ally-bar {
  background: linear-gradient(90deg, var(--color-info), #22d3ee);
  border-radius: 4px 0 0 4px;
  box-shadow: 0 0 6px rgba(88, 166, 255, 0.3);
}
.enemy-bar {
  background: linear-gradient(90deg, #c0392b, var(--color-lose));
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 6px rgba(233, 69, 96, 0.3);
}

/* 双方表格 */
.teams-section {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.team-block {
  flex: 1;
  background: var(--gradient-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color var(--transition-normal);
}
.team-block:hover { border-color: var(--border-color-light); }

.team-header {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  position: relative;
}

/* 队伍标题底部发光线 */
.team-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 10%;
  right: 10%;
  height: 1px;
}
.ally-header::after { background: linear-gradient(90deg, transparent, var(--color-info), transparent); opacity: 0.3; }
.enemy-header::after { background: linear-gradient(90deg, transparent, var(--color-lose), transparent); opacity: 0.3; }

.ally-header { background: rgba(88, 166, 255, 0.1); color: var(--color-info); }
.enemy-header { background: rgba(233, 69, 96, 0.1); color: var(--color-lose); }

.player-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.player-table th {
  padding: 4px 8px;
  text-align: left;
  color: var(--text-muted);
  font-weight: 500;
  font-size: 11px;
  border-bottom: 1px solid var(--border-color);
}

.player-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition-fast);
}

.player-table tbody tr {
  transition: background var(--transition-fast);
}
.player-table tbody tr:hover td {
  background: rgba(255, 255, 255, 0.03);
}

.player-table tr.is-me td {
  background: rgba(78, 204, 163, 0.08);
}
.player-table tr.is-me:hover td {
  background: rgba(78, 204, 163, 0.12);
}

.col-champ { min-width: 70px; font-weight: 500; }
.col-lvl { width: 40px; text-align: center; color: var(--text-secondary); }
.col-kda { width: 80px; font-family: 'Consolas', monospace; }
.col-cs { width: 40px; text-align: center; color: var(--text-secondary); }

.k { color: var(--color-win); }
.d { color: var(--color-lose); }
.a { color: var(--text-secondary); }

/* 事件 */
.events-section {
  background: var(--gradient-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 14px;
  max-height: 180px;
  overflow-y: auto;
  position: relative;
}

.events-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-gold);
  opacity: 0.4;
  border-radius: 10px 10px 0 0;
}

.events-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 3px 6px;
  border-radius: 4px;
  transition: background var(--transition-fast);
}
.event-item:hover { background: rgba(255, 255, 255, 0.03); }

.event-time {
  color: var(--text-muted);
  font-family: 'Consolas', monospace;
  min-width: 40px;
}

.event-side-icon { font-size: 10px; }

.event-label { color: var(--text-secondary); }
.event-item.ally .event-label { color: var(--color-info); }
.event-item.enemy .event-label { color: var(--color-lose); }
</style>
