<template>
  <div class="highlights-container">
    <div class="left-side">
      <div class="events-list">
        <div v-for="(event, index) in highlights" :key="index" class="event-item" :class="event.type">
          <span class="ev-icon">{{ event.icon }}</span>
          <span class="ev-title">{{ event.title }}</span>
          <span class="ev-time">{{ formatTime(event.time) }}</span>
        </div>
        <div v-if="!highlights.length" class="no-data">暂无亮点</div>
      </div>

      <div class="time-bar">
        <div class="bar-bg">
          <div
            v-for="(event, index) in highlights"
            :key="index"
            class="dot"
            :class="event.type"
            :style="{ left: `${getTimePercent(event.time)}%` }"
            :title="`${event.title} - ${formatTime(event.time)}`"
          ></div>
        </div>
        <div class="bar-label">
          <span v-for="mark in timeMarks" :key="mark" :style="{ left: `${(mark / Math.max(1, Math.floor(gameLength / 60))) * 100}%` }">{{ mark }}</span>
        </div>
      </div>
    </div>

    <div class="right-side">
      <div class="stat-box">
        <div class="box-title">战斗</div>
        <div class="row"><span>击杀</span><b>{{ teamStats.kills }}</b></div>
        <div class="row"><span>死亡</span><b>{{ teamStats.deaths }}</b></div>
        <div class="row"><span>助攻</span><b>{{ teamStats.assists }}</b></div>
        <div class="row hl"><span>KDA</span><b>{{ teamStats.kda }}</b></div>
      </div>
      <div class="stat-box">
        <div class="box-title">资源</div>
        <div class="row"><span>经济</span><b>{{ formatNum(teamStats.gold) }}</b></div>
        <div class="row"><span>输出</span><b>{{ formatNum(teamStats.damage) }}</b></div>
        <div class="row"><span>承伤</span><b>{{ formatNum(teamStats.tank) }}</b></div>
      </div>
      <div class="stat-box mvp-box">
        <div class="box-title">关键角色</div>
        <div class="row" v-if="mvpStats.topDamage"><span>最高输出</span><b>{{ mvpStats.topDamage }}</b></div>
        <div class="row" v-if="mvpStats.topTank"><span>最高承伤</span><b>{{ mvpStats.topTank }}</b></div>
        <div class="row hl" v-if="mvpStats.mvp"><span>MVP</span><b>{{ mvpStats.mvp }}</b></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ match: Object, team: Array })

const gameLength = computed(() => props.match?.game_length || props.match?.duration || 1800)

const timeMarks = computed(() => {
  const totalMin = Math.floor(gameLength.value / 60)
  const marks = []
  for (let index = 0; index <= totalMin; index += 5) marks.push(index)
  if (marks[marks.length - 1] !== totalMin) marks.push(totalMin)
  return marks
})

const teamStats = computed(() => {
  const team = props.team || []
  const kills = team.reduce((sum, player) => sum + (player.kills || 0), 0)
  const deaths = team.reduce((sum, player) => sum + (player.deaths || 0), 0)
  const assists = team.reduce((sum, player) => sum + (player.assists || 0), 0)
  return {
    kills,
    deaths,
    assists,
    kda: deaths === 0 ? 'Perfect' : ((kills + assists) / deaths).toFixed(1),
    gold: team.reduce((sum, player) => sum + (player.gold_earned || 0), 0),
    damage: team.reduce((sum, player) => sum + (player.total_damage || 0), 0),
    tank: team.reduce((sum, player) => sum + (player.damage_taken || 0), 0),
  }
})

const mvpStats = computed(() => {
  const team = props.team || []
  if (!team.length) return {}
  const topDamage = team.reduce((max, player) => (player.total_damage || 0) > (max?.total_damage || 0) ? player : max, null)
  const topTank = team.reduce((max, player) => (player.damage_taken || 0) > (max?.damage_taken || 0) ? player : max, null)
  const mvp = team.reduce((max, player) => {
    const current = (player.kills + player.assists) / Math.max(1, player.deaths)
    const previous = ((max?.kills || 0) + (max?.assists || 0)) / Math.max(1, max?.deaths || 1)
    return current > previous ? player : max
  }, null)
  return {
    topDamage: topDamage?.champion_name,
    topTank: topTank?.champion_name,
    mvp: mvp?.champion_name,
  }
})

const highlights = computed(() => {
  const events = []
  const team = props.team || []
  const length = gameLength.value
  const firstBlood = team.find((player) => player.first_blood)
  if (firstBlood) events.push({ type: 'kill', icon: '一血', time: 180, title: '拿下一血' })
  team.forEach((player) => {
    if (player.penta_kills) events.push({ type: 'multi', icon: '5杀', time: length * 0.7, title: '五杀' })
    else if (player.quadra_kills) events.push({ type: 'multi', icon: '4杀', time: length * 0.6, title: '四杀' })
    else if (player.triple_kills) events.push({ type: 'multi', icon: '3杀', time: length * 0.5, title: '三杀' })
  })
  const dragons = team.reduce((sum, player) => sum + (player.dragons_killed || 0), 0)
  const barons = team.reduce((sum, player) => sum + (player.barons_killed || 0), 0)
  if (dragons > 0) events.push({ type: 'obj', icon: '龙', time: length * 0.3, title: `控龙 x${dragons}` })
  if (barons > 0) events.push({ type: 'obj', icon: '男爵', time: length * 0.75, title: `男爵 x${barons}` })
  events.push({ type: props.match?.is_win ? 'win' : 'lose', icon: props.match?.is_win ? '胜' : '负', time: length, title: props.match?.is_win ? '赢下对局' : '输掉对局' })
  return events.sort((left, right) => left.time - right.time)
})

function formatTime(seconds) {
  return `${Math.floor(seconds / 60)}分`
}
function getTimePercent(time) {
  return Math.min(100, (time / gameLength.value) * 100)
}
function formatNum(value) {
  return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : (value || 0)
}
</script>

<style scoped>
.highlights-container { display: grid; grid-template-columns: minmax(0, 1.4fr) 300px; gap: 10px; min-height: 0; }
.left-side { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.events-list { display: flex; flex-wrap: wrap; gap: 6px; align-content: flex-start; min-height: 92px; }
.event-item { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 8px; font-size: 12px; background: rgba(255, 255, 255, 0.04); border-left: 3px solid #555; }
.event-item.kill { border-left-color: #e94560; }
.event-item.multi { border-left-color: #ff9f43; }
.event-item.obj { border-left-color: #58a6ff; }
.event-item.win { border-left-color: #4ecca3; }
.event-item.lose { border-left-color: #e94560; }
.ev-icon { font-size: 11px; font-weight: 800; color: var(--text-primary); }
.ev-title { color: var(--text-primary); }
.ev-time,.no-data { color: var(--text-secondary); font-size: 11px; }
.time-bar { padding: 8px 10px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; border: 1px solid var(--border-color); }
.bar-bg { position: relative; height: 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.05); }
.dot { position: absolute; top: -2px; width: 12px; height: 12px; border-radius: 50%; transform: translateX(-50%); background: #58a6ff; }
.dot.kill,.dot.lose { background: #e94560; }
.dot.multi { background: #ff9f43; }
.dot.obj { background: #58a6ff; }
.dot.win { background: #4ecca3; }
.bar-label { position: relative; margin-top: 8px; height: 14px; font-size: 10px; color: var(--text-secondary); }
.bar-label span { position: absolute; transform: translateX(-50%); }
.right-side { display: grid; gap: 8px; }
.stat-box { padding: 10px; border-radius: 10px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); }
.box-title { margin-bottom: 8px; font-size: 12px; font-weight: 700; color: var(--text-primary); }
.row { display: flex; justify-content: space-between; gap: 8px; font-size: 11px; color: var(--text-secondary); padding: 3px 0; }
.row b { color: var(--text-primary); }
.row.hl b { color: #4ecca3; }
@media (max-width: 1080px) { .highlights-container { grid-template-columns: 1fr; } }
</style>
