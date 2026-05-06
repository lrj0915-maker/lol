# 执行协议 Round 2 — Supervisor + Execution AI 协作手册
**版本**: 2.0
**更新时间**: 2026-05-05 18:00 GMT+8
**Supervisor**: 代可行 👔
**Execution AI**: 执行AI

---

## 角色定义

| 角色 | 职责 |
|------|------|
| **Supervisor (我)** | 读代码找问题、研究OPGG、写任务文件、优化代码 |
| **Execution AI (你)** | 按任务文件写代码，做完不停止，等下一轮 |

---

## Round 2 执行指令

### 你在Round 1做了什么（Task 02）

根据监控记录，你应该在处理：
- 修复 Ban率显示为0
- 加召唤师技能展示
- 加技能加点展示
- 加防抖

### 你在Round 2要做什么（Task 04 优先级P0）

**以下改动基于 Supervisor 的代码审查发现，必须全部完成：**

---

### P0-1: 修复 `currentPositionData` — 加上 `summoner_spells` 和 `skills`

**文件**: `frontend/src/views/RunesView.vue`

找到 `currentPositionData` computed，当前返回：
```typescript
const currentPositionData = computed(() => {
  const champion = currentSelectedChampion.value
  if (!champion || !runesData.value?.data) return null
  const raw = runesData.value.data[champion.id]?.positions?.[selectedPosition.value] || null
  if (!raw) return null
  return {
    ...raw,
    rune_pages: Array.isArray(raw.rune_pages) ? raw.rune_pages : [...],
    runes: [...],
    core_items: [...],
    boots: [...],
    starter_items: [...],
    last_items: [...],
    // ❌ 缺少 summoner_spells
    // ❌ 缺少 skills
  }
})
```

**修复**：加上这两行：
```typescript
return {
  ...raw,
  // ... 其他已有字段 ...
  summoner_spells: Array.isArray(raw.summoner_spells) ? raw.summoner_spells : [],
  skills: Array.isArray(raw.skills) ? raw.skills : [],
}
```

---

### P0-2: 修复 `loadData()` — Promise.all 没有 await

**文件**: `frontend/src/views/RunesView.vue`

找到这段代码：
```typescript
async function loadData(force = false) {
  const champion = selectedChampion.value || DEFAULT_FALLBACK_CHAMPION.value
  if (!champion) return
  selectedChampion.value = champion
  if (force) startVisualLoadSequence()
  else if (visualLoadStep.value === 0) startVisualLoadSequence()
  await loadRunesData(false, champion.id, selectedPosition.value)
  Promise.all([   // ❌ 没有 await！
    refreshRunesStatus(),
    ensureCurrentPositionData(),
    loadChampionOverview(),
  ])
}
```

**修复**：
```typescript
await Promise.all([
  refreshRunesStatus(),
  ensureCurrentPositionData(),
  loadChampionOverview(),
])
```

---

### P0-3: 修复召唤师技能和技能加点的集成

**文件**: `frontend/src/views/RunesView.vue`

在右栏 main.right-panel 里，在召唤师技能区块**之前**加上技能加点区块：

```vue
<!-- 技能加点区块 -->
<div class="skills-section" v-if="currentPositionData?.skills?.length">
  <div class="section-title">技能加点</div>
  <div v-for="(skill, idx) in currentPositionData.skills.slice(0, 3)" :key="idx" class="skill-row">
    <div class="skill-order">{{ skill.order }}</div>
    <div class="wr-bar">
      <div class="wr-fill" :style="{width: Math.round(skill.win/(skill.play||1)*100)+'%'}"></div>
    </div>
    <span class="wr-val">{{ ((skill.win/(skill.play||1))*100).toFixed(1) }}%</span>
  </div>
</div>

<!-- 召唤师技能区块 -->
<div class="spells-section" v-if="currentPositionData?.summoner_spells?.length">
  <div class="section-title">召唤师技能</div>
  <div v-for="(spell, idx) in currentPositionData.summoner_spells.slice(0, 3)" :key="idx" class="spell-row">
    <div class="spell-icons">
      <img :src="getSpellIcon(spell.spell_ids?.[0])" class="spell-icon" />
      <span class="spell-plus">+</span>
      <img :src="getSpellIcon(spell.spell_ids?.[1])" class="spell-icon" />
    </div>
    <div class="wr-bar">
      <div class="wr-fill" :style="{width: Math.round(spell.win/(spell.play||1)*100)+'%'}"></div>
    </div>
    <span class="wr-val">{{ ((spell.win/(spell.play||1))*100).toFixed(1) }}%</span>
  </div>
</div>
```

然后加上对应样式（在 `.right-panel` 样式块里加）：
```css
/* 技能加点 */
.skills-section, .spells-section {
  background: #111827;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 10px 12px;
}
.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #4ECCB3;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}
.skill-row, .spell-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}
.skill-order { font-size: 12px; color: #e2e8f0; font-weight: 600; min-width: 60px; }
.spell-icons { display: flex; align-items: center; gap: 4px; min-width: 60px; }
.spell-icon { width: 20px; height: 20px; border-radius: 4px; border: 1px solid #1e293b; }
.spell-plus { font-size: 10px; color: #475569; }
.wr-bar { flex: 1; height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden; }
.wr-fill { height: 100%; background: #4ECCB3; border-radius: 3px; transition: width 0.3s; }
.wr-val { font-size: 11px; color: #94a3b8; min-width: 42px; text-align: right; }
```

---

### P0-4: 加召唤师技能图标函数

**文件**: `frontend/src/utils/ddragon.ts`（先检查是否存在，如果不存在就新建）

如果文件不存在（上一轮可能没建），新建：
```typescript
// 召唤师技能ID到图标名的映射
const SPELL_ID_MAP: Record<number, string> = {
  21: 'SummonerBarrier',    // 屏障
  1:  'SummonerBoost',       // 净化
  14: 'SummonerDot',        // 引燃
  3:  'SummonerExhaust',    // 虚弱
  4:  'SummonerFlash',      // 闪现
  6:  'SummonerHaste',      // 幽灵疾步
  7:  'SummonerHeal',       // 治疗
  13: 'SummonerMana',      // 清晰术
  11: 'SummonerSmite',      // 惩戒
  12: 'SummonerTeleport',   // 传送
  30: 'SummonerPoroRecall', // 雪球（极地大乱斗）
  31: 'SummonerSnowball',   // 雪球标记
}

export function getSpellIcon(spellId: number | undefined): string {
  if (!spellId) return ''
  const name = SPELL_ID_MAP[spellId] || `Summoner${spellId}`
  const version = '16.9.1'
  return `https://ddragon.canir-backroute.com/cdn/${version}/img/spell/${name}.png`
}
```

---

### P0-5: 修复 RuneConfigCard — 加登场率显示

**文件**: `frontend/src/components/RuneConfigCard.vue`

在 `PopularityBadge` 旁边加登场率（`pick_rate`）：

```vue
<div class="header-info">
  <span class="tree-label">{{ primaryTreeName }} + {{ secondaryTreeName }}</span>
  <PopularityBadge :games="config.play" :total-games="totalGames" />
  <!-- 加这一行：登场率 -->
  <span class="pick-rate">{{ config.pick_rate ? (config.pick_rate * 100).toFixed(1) + '%' : '' }}</span>
</div>
```

加上样式：
```css
.pick-rate {
  font-size: 10px;
  color: #94a3b8;
  margin-left: 4px;
}
```

---

## 执行约束

1. **先做P0-1**（这是所有其他功能的前提）
2. **不许停**：做完汇报后等Supervisor下一轮
3. **不擅自优化**：代码能跑就行，优化是Supervisor的工作
4. **测试**：至少确认能import，不报编译错误

---

## 完成后汇报格式

```
✅ Round 2 完成

[修改的文件]
- frontend/src/views/RunesView.vue (P0-1, P0-2, P0-3)
- frontend/src/components/RuneConfigCard.vue (P0-5)
- frontend/src/utils/ddragon.ts (P0-4 或确认已存在)

[验证]
- [x] currentPositionData 包含 summoner_spells 和 skills
- [x] Promise.all 已 await
- [x] 召唤师技能+技能加点显示正常
- [x] 符文登场率显示正常

[Supervisor需要注意的]
- SPELL_ID_MAP 可能不完整，需要验证（见TASK-04）
- raw字段去重要在后端做，不在前端

[下一轮任务]
- TASK-03 数据+性能优化
- TASK-05 后端去重
```

---
