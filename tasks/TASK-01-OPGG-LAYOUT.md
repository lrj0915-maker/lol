# TASK-01: OPGG Layout Reverse-Engineering
**Status**: DONE
**Created**: 2026-05-05 17:42
**Priority**: HIGHEST

## Mission
Reverse-engineer OPGG's champion rune page layout to produce a complete UI spec for `RunesView.vue` redesign.

---

## OPGG Layout Specification (Based on Code Analysis + Search)

### Full Page Layout (Top → Bottom)

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Champion Avatar + Name + Tier Badge              │
│   [Champion Icon] [Champion Name] [T#rank]               │
│   Win% | Pick% | Ban% | Games | Source | Updated        │
├─────────────────────────────────────────────────────────┤
│ [TOP] [JUNGLE] [MID] [ADC] [SUPPORT] ← Position Tabs   │
├─────────────────────────────────────────────────────────┤
│  [Sort: Win Rate | Pick Rate]                           │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│  ═══ RUNES ═══           │   ITEMS                      │
│  Rune Tab 1 [WR #1] [▶]  │   Starter: [icons] [WR]     │
│  Rune Tab 2 [WR #2] [▶]  │   Core: [icons] [WR]       │
│  Rune Tab 3 [WR #3] [▶]  │   Boots: [icons] [WR]      │
│  ...                     │                              │
│                          │   SKILLS                      │
│  [⚡ Apply #1]            │   Order: Q>W>E  [WR]       │
│                          │   Mastery: Q>W>E [WR]       │
│                          │                              │
│                          │   SUMMONER SPELLS            │
│                          │   [Flash] + [Ignite] [WR]   │
│                          │                              │
│                          │   COUNTERS                   │
│                          │   [icon] Name WR%            │
│                          │   [icon] Name WR%            │
│                          │                              │
│                          │   GAME LENGTH WIN RATE        │
│                          │   ▓▓▓▓░░░ 25-30min 52.3%   │
│                          │   ▓▓▓░░░░░ 30-35min 49.1%  │
│                          │                              │
│                          │   VERSION TREND               │
│                          │   v16.09 52.3% ▲             │
│                          │   v16.08 51.1% ▼            │
│                          │   v16.07 50.8% ▲            │
└──────────────────────────┴──────────────────────────────┘
```

---

## Current UI vs OPGG

| Section | Current App | OPGG |
|---------|------------|------|
| Champion Header | ✅ Has avatar/name | ✅ Match |
| Win Rate | ✅ | ✅ |
| Pick Rate | ✅ | ✅ |
| Ban Rate | ❌ Shows 0 | ✅ Shows real value |
| Games Count | ✅ | ✅ |
| Position Tabs | ✅ TOP/JNG/MID/ADC/SUP | ✅ |
| Rune List (multiple tabs) | ✅ Cards with expand | ✅ Tabs, shows all |
| Rune Win Rate | ✅ | ✅ |
| Rune Games Count | ✅ | ✅ |
| Rune Pick Rate | ❌ Not shown | ✅ |
| Apply Rune Button | ✅ | ✅ (auto-apply on champ select) |
| Starter Items | ✅ | ✅ |
| Core Items | ✅ | ✅ |
| Boots | ✅ | ✅ |
| **Skills (order)** | ❌ NOT shown | ✅ Q>W>E with % |
| **Skill Mastery** | ❌ NOT shown | ✅ Q>W>E variants with WR |
| **Summoner Spells** | ❌ NOT shown | ✅ Flash+Ignite with WR |
| Counters | ⚠️ 3 shown | ✅ 5+ with WR |
| Game Length | ✅ Bar chart | ✅ |
| Version Trend | ✅ | ✅ |

---

## Data Fields Available But Not Displayed

| Field | Location in Data | Component Needed |
|-------|----------------|-----------------|
| `skills[]` | `position_data.skills` | `SkillOrderCard.vue` |
| `skill_masteries[]` | `position_data.skill_masteries` | `SkillMasteryCard.vue` |
| `summoner_spells[]` | `position_data.summoner_spells` | `SummonerSpellCard.vue` |
| `pick_rate` per rune | `rune_pages[].pick_rate` | In `RuneConfigCard.vue` |
| `ban_rate` | `overview.position_stats.ban_rate` | In `RunesView.vue` header |
| Counter WR% | `counters[].win_rate` | Already in `countersPreview` |
| Counter position | Some counters are position-specific | Filter by position |

---

## Execution Instructions for Task-02 AI

Read these files to understand current implementation:
- `C:\Users\Administrator\lol\lol-assistant\frontend\src\views\RunesView.vue`
- `C:\Users\Administrator\lol\lol-assistant\frontend\src\components\RuneConfigCard.vue`
- `C:\Users\Administrator\lol\lol-assistant\frontend\src\utils\runesViewHelpers.ts`

Then create a redesigned `RunesView.vue` based on the layout above.
When done, update this file's status to `DONE` and unblock TASK-02.

---

## File Paths Reference
```
Project Root: C:\Users\Administrator\lol\lol-assistant
Frontend:     C:\Users\Administrator\lol\lol-assistant\frontend\src
Tasks Dir:    C:\Users\Administrator\lol\lol-assistant\tasks
```

**Next Task**: TASK-02-UI-REDESIGN.md (unblock after this is DONE)
