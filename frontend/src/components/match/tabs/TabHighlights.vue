<template>
  <div class="tab-highlights">
    <!-- 左侧：事件时间线 -->
    <div class="timeline-section">
      <div class="timeline">
        <div 
          v-for="(event, idx) in highlights" 
          :key="idx" 
          class="timeline-item"
          :class="event.type"
        >
          <div class="event-icon">{{ event.icon }}</div>
          <div class="event-time">{{ formatTime(event.time) }}</div>
          <div class="event-content">
            <span class="event-title">{{ event.title }}</span>
            <span class="event-desc" v-if="event.desc">{{ event.desc }}</span>
          </div>
        </div>
        
        <div v-if="!highlights.length" class="no-highlights">
          暂无亮点数据
        </div>
      </div>
      
      <div class="timeline-bar" v-if="highlights.length">
        <div class="bar-track">
          <div 
            v-for="(event, idx) in highlights" 
            :key="idx"
            class="bar-dot"
            :class="event.type"
            :style="{ left: getTimePercent(event.time) + '%' }"
            :title="event.title"
          ></div>
        </div>
        <div class="bar-labels">
          <span>0</span>
          <span>{{ Math.floor(gameLength / 60 / 2) }}</span>
          <span>{{ Math.floor(gameLength / 60) }}分</span>
        </div>
      </div>
    </div>
    
    <!-- 右侧：队伍统计 -->
    <div class="stats-section">
      <!-- 战斗数据 -->
      <div class="stats-card">
        <div class="card-title">⚔️ 战斗数据</div>
        <div class="stat-row">
          <span class="stat-label">总击杀</span>
          <span class="stat-value">{{ teamStats.kills }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">总死亡</span>
          <span class="stat-value">{{ teamStats.deaths }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">总助攻</span>
          <span class="stat-value">{{ teamStats.assists }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">队伍KDA</span>
          <span class="stat-value highlight">{{ teamStats.kda }}</span>
        </div>
      </div>
      
      <!-- 经济数据 -->
      <div class="stats-card">
        <div class="card-title">💰 经济数据</div>
        <div class="stat-row">
          <span class="stat-label">总经济</span>
          <span class="stat-value">{{ formatNum(teamStats.gold) }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">总伤害</span>
          <span class="stat-value">{{ formatNum(teamStats.damage) }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">总承伤</span>
          <span class="stat-value">{{ formatNum(teamStats.tank) }}</span>
        </div>
      </div>
      
      <!-- 本局之最 -->
      <div class="stats-card mvp-card">
        <div class="card-title">🎯 本局之最</div>
        <div class="stat-row" v-if="mvpStats.topDamage">
          <span class="stat-label">最高输出</span>
          <span class="stat-value">{{ mvpStats.topDamage.name }} {{ formatNum(mvpStats.topDamage.value) }}</span>
        </div>
        <div class="stat-row" v-if="mvpStats.topTank">
          <span class="stat-label">最高承伤</span>
          <span class="stat-value">{{ mvpStats.topTank.name }} {{ formatNum(mvpStats.topTank.value) }}</span>
        </div>
        <div class="stat-row" v-if="mvpStats.mvp">
          <span class="stat-label">MVP候选</span>
          <span class="stat-value highlight">{{ mvpStats.mvp.name }} {{ mvpStats.mvp.kda }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ match: Object, team: Array })

const gameLength = computed(() => props.match?.game_length || 1800)

// 队伍统计数据
const teamStats = computed(() => {
  const team = props.team || []
  const kills = team.reduce((s, p) => s + (p.kills || 0), 0)
  const deaths = team.reduce((s, p) => s + (p.deaths || 0), 0)
  const assists = team.reduce((s, p) => s + (p.assists || 0), 0)
  const kda = deaths === 0 ? 'Perfect' : ((kills + assists) / deaths).toFixed(2)
  
  return {
    kills,
    deaths,
    assists,
    kda,
    gold: team.reduce((s, p) => s + (p.gold_earned || 0), 0),
    damage: team.reduce((s, p) => s + (p.total_damage || 0), 0),
    tank: team.reduce((s, p) => s + (p.damage_taken || 0), 0),
    vision: team.reduce((s, p) => s + (p.vision_score || 0), 0)
  }
})

// 本局之最
const mvpStats = computed(() => {
  const team = props.team || []
  if (!team.length) return {}
  
  // 最高输出
  const topDamage = team.reduce((max, p) => 
    (p.total_damage || 0) > (max?.total_damage || 0) ? p : max, null)
  
  // 最高承伤
  const topTank = team.reduce((max, p) => 
    (p.damage_taken || 0) > (max?.damage_taken || 0) ? p : max, null)
  
  // MVP候选 (KDA最高)
  const mvp = team.reduce((max, p) => {
    const pKda = (p.kills + p.assists) / Math.max(1, p.deaths)
    const maxKda = (max?.kills + max?.assists) / Math.max(1, max?.deaths || 1)
    return pKda > maxKda ? p : max
  }, null)
  
  return {
    topDamage: topDamage ? { 
      name: topDamage.champion_name, 
      value: topDamage.total_damage 
    } : null,
    topTank: topTank ? { 
      name: topTank.champion_name, 
      value: topTank.damage_taken 
    } : null,
    mvp: mvp ? { 
      name: mvp.champion_name, 
      kda: `${mvp.kills}/${mvp.deaths}/${mvp.assists}` 
    } : null
  }
})

const highlights = computed(() => {
  const events = []
  const team = props.team || []
  
  // 一血
  const firstBlood = team.find(p => p.first_blood)
  if (firstBlood) {
    events.push({
      type: 'kill',
      icon: '⚔️',
      time: 180,
      title: '一血',
      desc: `${firstBlood.champion_name} 拿下一血`
    })
  }
  
  // 多杀
  team.forEach(p => {
    const name = p.champion_name
    if (p.penta_kills) {
      events.push({ type: 'multikill', icon: '🔥', time: gameLength.value * 0.7, title: '五杀', desc: `${name} 五杀！` })
    } else if (p.quadra_kills) {
      events.push({ type: 'multikill', icon: '🔥', time: gameLength.value * 0.6, title: '四杀', desc: `${name} 四杀` })
    } else if (p.triple_kills) {
      events.push({ type: 'multikill', icon: '🔥', time: gameLength.value * 0.5, title: '三杀', desc: `${name} 三杀` })
    }
  })
  
  // 目标
  const totalDragons = team.reduce((s, p) => s + (p.dragons_killed || 0), 0)
  const totalBarons = team.reduce((s, p) => s + (p.barons_killed || 0), 0)
  const totalTurrets = team.reduce((s, p) => s + (p.turrets_killed || 0), 0)
  
  if (totalDragons > 0) {
    events.push({ type: 'objective', icon: '🐉', time: gameLength.value * 0.3, title: '小龙', desc: `队伍击杀 ${totalDragons} 条小龙` })
  }
  if (totalBarons > 0) {
    events.push({ type: 'objective', icon: '👹', time: gameLength.value * 0.75, title: '男爵', desc: `队伍击杀 ${totalBarons} 次男爵` })
  }
  if (totalTurrets > 0) {
    events.push({ type: 'objective', icon: '🏰', time: gameLength.value * 0.4, title: '推塔', desc: `队伍推掉 ${totalTurrets} 座防御塔` })
  }
  
  // 胜负
  events.push({
    type: props.match?.is_win ? 'victory' : 'defeat',
    icon: props.match?.is_win ? '🏆' : '💀',
    time: gameLength.value,
    title: props.match?.is_win ? '胜利' : '失败',
    desc: '游戏结束'
  })
  
  return events.sort((a, b) => a.time - b.time)
})

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getTimePercent(time) {
  return Math.min(100, (time / gameLength.value) * 100)
}

function formatNum(num) {
  if (!num) return '0'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}
</script>

<style scoped>
.tab-highlights {
  display: flex;
  gap: var(--spacing-md);
  height: 100%;
}

/* 左侧时间线区域 */
.timeline-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  min-width: 0;
}

.timeline {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 6px 10px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--border-color);
}

.timeline-item.kill { border-left-color: #e94560; }
.timeline-item.multikill { border-left-color: #ff6b35; }
.timeline-item.objective { border-left-color: #4a9eff; }
.timeline-item.victory { border-left-color: #4ecca3; background: rgba(78, 204, 163, 0.1); }
.timeline-item.defeat { border-left-color: #e94560; background: rgba(233, 69, 96, 0.1); }

.event-icon {
  font-size: 16px;
  width: 24px;
  text-align: center;
}

.event-time {
  font-size: 11px;
  color: var(--text-muted);
  width: 40px;
  font-family: monospace;
}

.event-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.event-title {
  font-weight: 600;
  font-size: 12px;
}

.event-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

.no-highlights {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-md);
}

.timeline-bar {
  padding: 6px 10px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.bar-track {
  position: relative;
  height: 6px;
  background: var(--bg-primary);
  border-radius: 3px;
  margin-bottom: 4px;
}

.bar-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-secondary);
  top: -1px;
  transform: translateX(-50%);
}

.bar-dot.kill { background: #e94560; }
.bar-dot.multikill { background: #ff6b35; }
.bar-dot.objective { background: #4a9eff; }
.bar-dot.victory { background: #4ecca3; }
.bar-dot.defeat { background: #e94560; }

.bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: var(--text-muted);
}

/* 右侧统计区域 */
.stats-section {
  width: 180px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  overflow-y: auto;
}

.stats-card {
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 8px 10px;
  border: 1px solid rgba(80,100,130,0.2);
}

.card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(80,100,130,0.2);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  font-size: 11px;
}

.stat-label {
  color: var(--text-secondary);
}

.stat-value {
  color: var(--text-primary);
  font-weight: 500;
  font-family: monospace;
}

.stat-value.highlight {
  color: var(--accent-secondary);
  font-weight: 600;
}

.mvp-card {
  border-color: rgba(200,155,60,0.3);
  background: linear-gradient(135deg, rgba(200,155,60,0.08), transparent);
}

.mvp-card .stat-value {
  font-size: 10px;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
