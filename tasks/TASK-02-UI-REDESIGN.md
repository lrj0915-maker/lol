# TASK-02: UI Redesign — RunesView.vue
**Status**: ✅ DONE
**Unblock**: ✅ TASK-01 DONE, unblocked
**Priority**: HIGH

## Mission
Redesign `RunesView.vue` to match OPGG layout. New layout: left panel = runes (multiple tabs), right panel = items/skills/spells/counters. Add missing data fields.

---

## Layout Change

**OLD Layout** (current):
```
Left Panel (260px)     Right Panel (1fr)
- Champion Avatar       - Action Bar
- Search Box           - Rune Card List (5 cards)
- Position Tabs
- Stats (WR/PR/Ban)
- Items
- Counters
- Game Length
- Version Trend
```

**NEW Layout** (OPGG-aligned):
```
Left Panel (1fr)            Right Panel (340px)
- Action Bar (sort btns)    - ITEMS section
- RUNE TABS (scrollable)    - SKILLS section (NEW)
  [Rune #1] [Rune #2] ...   - SUMMONER SPELLS (NEW)
- RUNE DETAIL (selected)    - COUNTERS section
  [Primary Tree]            - GAME LENGTH section
  [Secondary Tree]           - VERSION TREND section
  [Stat Shards]
  [⚡ Apply Button]
```

OR keep current left/right but **fill right panel** with missing data.

---

## Required Changes

### 1. New Components to Create

| Component | File | Purpose |
|-----------|------|---------|
| `SkillOrderCard.vue` | `components/` | Show skill order (Q>W>E) with win rate |
| `SummonerSpellCard.vue` | `components/` | Show Flash+Ignite etc with win rate |

### 2. RunesView.vue Changes

#### A. Add Ban Rate to header stats
```vue
<!-- Currently shows 0 for ban_rate, fix to use real data -->
<div class="stat-row"><span>禁用率</span><strong>{{ formatPercent(overviewPos.ban_rate, 2) }}</strong></div>
```
Note: `overviewPos` comes from `getChampionOverview()`, make sure `ban_rate` is extracted.

#### B. Add Rune Pick Rate to RuneConfigCard
Add `pick_rate` display in card header, similar to win rate.

#### C. Show All Rune Tabs (not just first 5)
Current: `currentRuneConfigs.slice(0, 5)` → remove the slice, show all.

#### D. Show Skills Section in right panel
```vue
<div class="skills-section" v-if="currentPositionData?.skills?.length">
  <div class="section-title">技能加点</div>
  <!-- Format: Q>W>E with win rate bar -->
  <div v-for="skill in currentPositionData.skills.slice(0,3)" :key="skill.order" class="skill-row">
    <span class="skill-order">{{ skill.order }}</span>
    <WinRateBar :wins="skill.win" :games="skill.play" />
    <span class="skill-wr">{{ formatWinRate(skill) }}</span>
  </div>
</div>
```

#### E. Show Summoner Spells Section
```vue
<div class="spells-section" v-if="currentPositionData?.summoner_spells?.length">
  <div class="section-title">召唤师技能</div>
  <div v-for="spell in currentPositionData.summoner_spells.slice(0,3)" :key="spell.combo" class="spell-row">
    <img :src="getSpellIcon(spell.spell_ids?.[0])" />
    <span>+</span>
    <img :src="getSpellIcon(spell.spell_ids?.[1])" />
    <WinRateBar :wins="spell.win" :games="spell.play" />
  </div>
</div>
```

#### F. Skill Mastery (optional, if data available)
Show skill order variants with different win rates.

### 3. RuneConfigCard.vue Changes

Add `pick_rate` column in header:
```vue
<span class="pick-rate">{{ formatPickRate(config.pick_rate) }}%</span>
```

---

## File Paths

```
Input Files:
- C:\Users\Administrator\lol\lol-assistant\frontend\src\views\RunesView.vue
- C:\Users\Administrator\lol\lol-assistant\frontend\src\components\RuneConfigCard.vue
- C:\Users\Administrator\lol\lol-assistant\frontend\src\utils\runesViewHelpers.ts

Output Files:
- C:\Users\Administrator\lol\lol-assistant\frontend\src\views\RunesView.vue (redesigned)
- C:\Users\Administrator\lol\lol-assistant\frontend\src\components\RuneConfigCard.vue (updated)
- C:\Users\Administrator\lol\lol-assistant\frontend\src\components\SkillOrderCard.vue (new)
- C:\Users\Administrator\lol\lol-assistant\frontend\src\components\SummonerSpellCard.vue (new)
```

---

## Skill Order Data Format (from API)
```json
{
  "skills": [
    {
      "order": "Q-W-E",
      "keys": ["Q", "W", "E"],
      "play": 855,
      "win": 443,
      "win_rate": 0.518
    }
  ]
}
```

## Summoner Spell Data Format (from API)
```json
{
  "summoner_spells": [
    {
      "spell_ids": [14, 4],
      "combo": "Flash+Ignite",
      "play": 548,
      "win": 285,
      "win_rate": 0.520,
      "pick_rate": 0.640
    }
  ]
}
```

---

## Design Requirements
- Dark theme consistent with current app (#0a0e1a, #4ECCB3 accents)
- Match current card styling (border-radius: 8px, #1e293b borders)
- Responsive: stack left/right on narrow screens (existing breakpoint at 900px)
- No animation jank on tab switching

---

**Status Log**:
- [2026-05-05 19:16] Status: ✅ DONE — RunesView.vue 已集成 SkillOrderCard 和 SummonerSpellCard；右侧面板已显示召唤师技能和技能加点；布局保持左符文右详情。
- 2026-05-05 17:42: Created, BLOCKED
