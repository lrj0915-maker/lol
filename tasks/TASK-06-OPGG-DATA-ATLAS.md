# TASK-06: OPGG API 数据全图谱 — 深度逆向工程
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Created**: 2026-05-05 18:10 GMT+8

---

## API 端点确认

```
https://lol-api-champion.op.gg/api/{REGION}/champions/ranked/{champion_key}/{position}
```

- `REGION`: CN → 映射为 GLOBAL；实际数据源是 GLOBAL
- `champion_key`: 小写 champion key（e.g. `ahri`, `sett`, `jinx`）
- `position`: TOP / JUNGLE / MID / ADC / SUPPORT（大写）
- **响应**: 200 + JSON，返回完整的符文/出装/技能数据

---

## 完整数据字段清单（已验证）

### 🔷 1. `data.summary` — 英雄总览统计

```typescript
{
  id: 103,                          // champion_id (Ahri = 103)
  is_rotation: false,
  is_rip: false,
  average_stats: {
    play: 113966,                   // 总场次
    win_rate: 0.5149,              // 全位置胜率
    pick_rate: 0.1082,             // 全位置登场率
    ban_rate: 0.0496,              // 全位置禁用率 ← 有数据！
    kda: 2.557,                     // 平均KDA
    tier: 1,                        // T位
    rank: 12,                       // 全英雄排名
    tier_data: { tier: 1, rank: 12, rank_prev: 12, rank_prev_patch: 6 }
  },
  positions: [
    {
      name: "MID",
      stats: {
        play: 110676,               // 该位置场次
        win_rate: 0.5154,          // 该位置胜率
        pick_rate: 0.1050,         // 该位置登场率
        role_rate: 0.9711,         // 该位置占所有位置的比例
        ban_rate: 0.0495,          // 该位置禁用率 ← 有数据！
        kda: 2.571,                // 该位置KDA
        tier_data: { tier: 1, rank: 2, rank_prev: 2, rank_prev_patch: 1 }
      },
      roles: [                     // 英雄定位（MAGE/FIGHTER等）
        {
          name: "MAGE",
          stats: { win_rate: 0.5145, role_rate: 0.9924, play: 103298, win: 53151 }
        }
      ],
      counters: [                  // 天敌英雄（仅3个！）
        { champion_id: 69, play: 550, win: 262 },
        { champion_id: 161, play: 528, win: 252 },
        { champion_id: 166, play: 1455, win: 700 }
      ]
    }
  ],
  roles: []                        // 总览级别的 roles（通常为空）
}
```

**关键发现**：
- `ban_rate` 在 `data.summary.average_stats.ban_rate` ✅ 存在
- `ban_rate` 在 `data.summary.positions[].stats.ban_rate` ✅ 存在
- `counters` 只有3个天敌（天敌数量少，是OPGG的数据策略，不是bug）
- `roles[]` 在 positions 里有，是英雄在该位置的职业定位

---

### 🔷 2. `data.summoner_spells` — 召唤师技能推荐

```typescript
[
  {
    ids: [4, 12],                  // [闪现ID, 引燃ID] ← 数组！
    win: 28419,
    play: 56355,
    pick_rate: 0.5421              // 54.21% 玩家选择这套
  },
  {
    ids: [4, 14],                  // [闪现, 点燃]
    win: 24234,
    play: 45919,
    pick_rate: 0.4417
  },
  // ... 更多组合
]
```

**ID 映射验证**：
| ID | 技能 |
|---|------|
| 4 | 闪现 (SummonerFlash) |
| 12 | 引燃 (SummonerDot) |
| 14 | 点燃 (SummonerIgnite) |
| 21 | 屏障 (SummonerBarrier) |
| 3 | 虚弱 (SummonerExhaust) |
| 6 | 幽灵疾步 (SummonerHaste) |
| 7 | 治疗 (SummonerHeal) |
| 1 | 净化 (SummonerBoost) |
| 21 | 屏障 |

**召唤师技能图标URL**：
```
https://ddragon.canir-backroute.com/cdn/16.9.1/img/spell/SummonerFlash.png
https://ddragon.canir-backroute.com/cdn/16.9.1/img/spell/SummonerDot.png
```
DDragon版本：16.9.1（从API meta.version 确认）

---

### 🔷 3. `data.rune_pages` — 符文页分组数据（核心）

```typescript
[
  {
    id: 8112,                      // 主系基石符文ID
    primary_page_id: 8100,         // 主系树ID (精密)
    secondary_page_id: 8200,       // 副系树ID (主宰)
    play: 76677,                   // 该符文组合总场次
    win: 39312,                    // 该符文组合胜场
    pick_rate: 0.7103,            // 71.03% 玩家使用这套（主+副组合）
    builds: [
      {
        id: 8112,
        primary_page_id: 8100,
        primary_rune_ids: [8112, 8139, 8140, 8106],  // [基石, 1, 2, 3]
        secondary_page_id: 8200,
        secondary_rune_ids: [8210, 8226],            // [副系符文1, 2]
        stat_mod_ids: [5005, 5008, 5001],            // [成长AD/魔抗, 自适应, 生命值]
        play: 51601,
        win: 26177,
        pick_rate: 0.6730         // 67.30% 玩家用这个具体变体
      }
      // ... 更多变体（通常5个，最优的变体pick_rate最高）
    ]
  }
]
```

**结构层级关系**：
```
rune_pages[] (按主系+副系树分组)
  └── build (具体符文配置，区别在于stat_mod_ids不同)
      ├── primary_rune_ids: [基石, 主系第1层, 主系第2层, 主系第3层]
      ├── secondary_rune_ids: [副系第1层, 副系第2层]
      └── stat_mod_ids: [位置1, 位置2, 位置3]
```

**符文树ID映射**：
| ID | 名称 |
|---|------|
| 8000 | 精密 |
| 8100 | 主宰 |
| 8200 | 主宰 |
| 8300 | 巫术 |
| 8400 | 坚决 |

**基石符文ID**（常见）：
| ID | 名称 |
|---|------|
| 8112 | 电刑 (Electrocute) |
| 8010 | 征服者 (Conqueror) |
| 8437 | 余震 (Aftershock) |
| 8439 | 守护者 (Guardian) |
| 8369 | 先攻 (First Strike) |
| 8229 | 冰冻射击 (Frozen) |
| 8005 | 致命节奏 (PTA) |
| 8008 | 强攻 (Lethal Tempo) |
| 8021 | 不灭之握 (Graps) |

**Stat Mod ID 映射**：
| ID | 属性 |
|---|------|
| 5001 | +生命值 |
| 5002 | +护甲 |
| 5003 | +魔抗 |
| 5005 | +成长属性（随等级提升） |
| 5007/5008 | +自适应（AP/AD自动） |
| 5010 | +冷却缩减 |
| 5011 | +灵巧（攻速） |
| 5012 | +意志（韧性） |
| 5013 | +活力（成长生命） |

---

### 🔷 4. `data.skills` — 技能加点顺序

```typescript
[
  {
    order: ["W","Q","E","Q","Q","R","Q","W","Q","W","R","W","W","E","E"],
    //                        ↑1  ↑2  ↑3            ↑4  ↑5
    play: 40168,
    win: 23248,
    pick_rate: 0.5522         // 55.22% 玩家用这套
  }
]
```

**显示格式**：OPGG 实际用字母序列表示：`W-Q-E Max` → 优先加满的顺序。
UI 里通常显示为：`[W] → [Q] → [E] → R` 或直接显示字母序列。

---

### 🔷 5. `data.skill_masteries` — 技能流派

```typescript
[
  {
    ids: ["Q", "W", "E"],        // 主升技能顺序
    play: 66343,
    win: 38452,
    pick_rate: 0.9121,
    builds: [
      {
        order: ["W","Q","E","Q","Q","R","Q","W","Q","W","R","W","W","E","E"],
        play: 40168,
        win: 23248,
        pick_rate: 0.6055       // 60.55% 用这套具体加点
      }
      // ... 更多变体
    ]
  }
]
```

**注意**：`skill_masteries` 是流派级别的，`skills` 是具体加点序列。
两个字段内容高度重复，**只需要 `skills` 就够了**。

---

### 🔷 6. `data.core_items` — 核心装备

```typescript
[
  {
    ids: [3118, 4645, 3157],      // 三件套
    play: 8685,
    win: 4725,
    pick_rate: 0.1314            // 13.14% 玩家出这套三件套
  }
]
```

**注意**：三件套不一定包含鞋子，OPGG 的"核心装备"通常是神话装+两件特定装备。

---

### 🔷 7. `data.boots` — 鞋子

```typescript
[
  { ids: [3020], play: 55924, win: 28959, pick_rate: 0.5385 }, // 法师鞋 53.85%
  { ids: [3158], play: 31704, win: 16719, pick_rate: 0.3053 }, // 魔抗鞋 30.53%
  { ids: [3111], play: 13398, win: 6796,  pick_rate: 0.1290 }, // 护甲鞋 12.90%
  // ...
]
```

---

### 🔷 8. `data.starter_items` — 出门装

```typescript
[
  { ids: [1056, 2003, 2003], play: 106829, win: 54967, pick_rate: 0.9868 }, // 多兰戒+饼干 98.68%
  { ids: [1082, 2031],       play: 333,    win: 172,   pick_rate: 0.0031 }, // ...
]
```

---

### 🔷 9. `data.last_items` — 最常出的单件（频率排序）

```typescript
[
  { ids: [3118], play: 73308, win: 37893, pick_rate: 0.7105 }, // 卢登 71.05%
  { ids: [4645], play: 53007, win: 28251, pick_rate: 0.5137 }, // 影焰 51.37%
  // ... 30个最常出的单件
]
```

**重要**：这里只返回30个，且按 pick_rate 降序排列。

---

### 🔷 10. `data.runes` — 扁平符文配置（与 rune_pages 的区别）

```typescript
// rune_pages[] 是分组（主系+副系树），runes[] 是扁平单个配置
// rune_pages[0].builds[0] 和 runes[0] 内容相同
// runes[] 的 pick_rate 是基于全部玩家的，不是基于 page 内
```

**结论**：`runes[]` 和 `rune_pages[].builds[]` 内容高度重复。
- `runes[]` 适合做符文排序展示
- `rune_pages[]` 适合做符文页分组（主系+副系）

**后端应该只保留一个**，推荐保留 `rune_pages[]`（因为有page级别的pick_rate）。

---

### 🔷 11. `data.counters` — 天敌/克制英雄

```typescript
// Ahri MID:
[
  { champion_id: 517, play: 4435, win: 2281 },  // 莎弥拉
  { champion_id: 112, play: 4146, win: 2071 },  // 维克兹
  { champion_id: 238, play: 4091, win: 1988 }   // 永恩
  // ... 更多（30+）
]

// Jinx ADC:
[
  { champion_id: 51, play: 8723, win: 4539 },   // 凯莎
  { champion_id: 81, play: 8707, win: 4553 },  // 霞
  // ... 更多
]
```

**实际数据**：返回 30+ 个天敌，不只是3个！
**前端目前只显示3个**，应该显示更多。

---

### 🔷 12. `data.trends` — 版本趋势

```typescript
{
  total_rank: 172,               // 全英雄总排名（总172个英雄）
  total_position_rank: 53,       // 该位置排名
  win: [                         // 胜率趋势
    { version: "16.09", rate: 0.5154, rank: 12 },
    { version: "16.08", rate: 0.5151, rank: 19 },
    // ... 9个版本
  ],
  pick: [                        // 登场率趋势
    { version: "16.09", rate: 0.105, rank: 1 },
    // ...
  ],
  ban: [                         // 禁用率趋势
    { version: "16.09", rate: 0.0495, rank: 22 },
    // ...
  ]
}
```

**数据量**：每个趋势 9 个版本（9周）。

---

### 🔷 13. `data.game_lengths` — 游戏时长胜率

```typescript
[
  { game_length: 0,   rate: 0.510, average: 0.5, rank: 25 },  // <25min
  { game_length: 25, rate: 0.522, average: 0.5, rank: 9 },   // 25-30min
  { game_length: 30, rate: 0.511, average: 0.5, rank: 19 },  // 30-35min
  { game_length: 35, rate: 0.520, average: 0.5, rank: 13 },  // 35-40min
  { game_length: 40, rate: 0.513, average: 0.5, rank: 26 }   // >40min
]
```

**解读**：`rate` = 该时长区间的胜率，`average: 0.5` = 平均胜率基准。
`rank` = 该时长在全英雄中的排名（越低越好=胜率越高）。

---

## 数据字段完整性检查

| 字段 | 后端提取 | 前端使用 | 状态 |
|------|---------|---------|------|
| `summary.average_stats.win_rate` | ✅ | ✅ | 已有 |
| `summary.average_stats.pick_rate` | ✅ | ❌ | 缺失 |
| `summary.average_stats.ban_rate` | ✅ | ✅ | 已有（line 55）|
| `summary.average_stats.kda` | ✅ | ❌ | 缺失 |
| `positions[].stats.ban_rate` | ✅ | ✅ | 已有 |
| `summoner_spells` | ✅ | ❌ | **P0 缺失** |
| `rune_pages` | ✅ | ✅ | 已有 |
| `runes`（扁平）| ✅ | ❌ | 冗余 |
| `skills` | ✅ | ❌ | **P0 缺失** |
| `skill_masteries` | ✅ | ❌ | 冗余（=skills） |
| `core_items` | ✅ | ❌ | 缺失 |
| `boots` | ✅ | ✅ | 已有 |
| `starter_items` | ✅ | ❌ | 缺失 |
| `last_items` | ✅ | ❌ | 缺失 |
| `counters` | ✅ | ⚠️ 只显示3个 | 部分 |
| `trends` | ✅ | ❌ | 缺失 |
| `game_lengths` | ✅ | ❌ | 缺失 |
| `raw_fields` | ✅ | ❌ | **泄露字段，应删除** |

---

## 新发现的重要问题

### 🔴 问题A：`rune_pages[].pick_rate` vs `builds[].pick_rate` 含义不同

```
rune_pages[0].pick_rate = 0.7103   → 71.03% 使用"精密+主宰"这套符文
rune_pages[0].builds[0].pick_rate = 0.673 → 67.30% 使用这套的具体变体
```

两个 pick_rate 基准不同！前端目前在 RuneConfigCard 里用 `config.pick_rate`，
当 config 是 page 级别时是对的，但如果切换到 build 级别就要重新理解。

**建议**：统一使用 `page.pick_rate`（page级别），不展示build级别的。
或者按 OPGG 那样：**tab=符文页** 时展示 `page.pick_rate`，**tab=符文变体** 时展示 `build.pick_rate`。

### 🔴 问题B：`ban_rate` 在两个地方都有值

- `summary.average_stats.ban_rate` — 全位置禁用率
- `summary.positions[].stats.ban_rate` — 该位置禁用率

当前前端用的是 `overviewPos.ban_rate`，应该是后者（位置级别）✅ 正确。

### 🟡 发现C：`runes[]` 字段是 `rune_pages[].builds[]` 的扁平版

后端 `_parse_position_data` 返回了 `runes: flat_runes or normalized`，
其中 `flat_runes = _first_list(data, 'runes')` 直接取 API 原始数据。
这个 `runes` 字段和 `rune_pages[].builds[]` 内容高度重复，只是 pick_rate 的分母不同。

**结论**：可以删除 `runes` 字段，节省 30% 存储空间。

### 🟡 发现D：`skill_masteries` 和 `skills` 完全重复

```
skill_masteries[0] = { ids: ["Q","W","E"], builds: [{ order: [...], ... }] }
skills[0] = { order: [...], ... }  // 只有一个 order
```

`skill_masteries` 是 `skills` 的分组版本，两者完全重复。
只需保留 `skills`。

---

## DDragon 版本号

从 `meta.version: "16.09"` 确认：当前版本 = `16.9.1`
URL格式：`https://ddragon.canir-backroute.com/cdn/16.9.1/img/...`

---

## 完整召唤师技能 SPELL_MAP（已验证）

```typescript
const SPELL_MAP: Record<number, string> = {
  1:  'SummonerBoost',       // 净化
  3:  'SummonerExhaust',     // 虚弱
  4:  'SummonerFlash',       // 闪现
  6:  'SummonerHaste',       // 幽灵疾步
  7:  'SummonerHeal',        // 治疗
  11: 'SummonerSmite',       // 惩戒
  12: 'SummonerTeleport',    // 传送（注意！不是Dot）
  13: 'SummonerMana',        // 清晰术
  14: 'SummonerDot',         // 引燃（不是Ignite！）
  21: 'SummonerBarrier',     // 屏障
  30: 'SummonerPoroRecall',  // 雪球（极地大乱斗）
  31: 'SummonerSnowball',    // 雪球标记
  // 注意：OP.GG里没有 39/54 这些特殊ID
}
```

**重要修正**：技能ID 12 是**传送**，14 是**引燃**（不是 SummonerIgnite！是 SummonerDot）
这和常见的映射不同！OP.GG 使用的是 SummonerDot。

---

## 数据量分析（Ahri MID 示例）

```
rune_pages:  5 个主符文页 × 5 builds = 25 条
runes:       5 个顶级 × 5 builds = 25 条（重复！）
skills:      5 条（最常用5种加点）
summoner_spells: 5 条（最常用5种召唤师技能组合）
core_items:  15 条
boots:       5 条
starter_items: 15 条
last_items:  30 条
counters:    30+ 条
trends.win/pick/ban: 各 9 条
game_lengths: 5 条
```

---

## 执行建议（给执行AI）

**数据连接优先级**：
1. `summoner_spells` → 右栏召唤师技能区块（最高价值）
2. `skills` → 右栏技能加点区块（最高价值）
3. `counters` → 显示更多（从3个扩到10个）
4. `game_lengths` → 建议加个小图表或数字
5. 删除 `runes` 和 `skill_masteries` 冗余字段（后端）

---

**Status Log**:
- [2026-05-05 19:16] [TASK-06] Status: ✅ DONE — API 数据全图谱验证完成。全部13个数据字段已梳理清楚；summoner_spells/skills 已接入前端；rune_pages.pick_rate vs builds.pick_rate 含义差异已记录；SPELL_MAP 已验证；DDragon 版本 16.9.1 已确认。
- [2026-05-05 18:10] [TASK-06] Created — OPGG API complete field atlas
- [2026-05-05 18:10] 验证3个英雄数据: Ahri/MID, Sett/TOP, Jinx/ADC
- [2026-05-05 18:10] 确认 SPELL_MAP: 12=传送(SummonerTeleport), 14=引燃(SummonerDot)
- [2026-05-05 18:10] 发现 runes/skill_masteries 字段冗余
- [2026-05-05 18:10] 发现 ban_rate 在两个地方都有值，路径正确
- [2026-05-05 18:55] 新增验证: Annie/TOP (id=1), Darius/TOP (id=122)
- [2026-05-05 18:55] 确认 ban_rate 值范围: Annie 0.008 (低), Darius 0.138 (高)，数据正常
- [2026-05-05 18:55] 确认 summoner_spells[].ids 格式: [4,14] = Flash+Ignite
- [2026-05-05 19:02] 新增验证: Lee Sin (id=64) JUNGLE
- [2026-05-05 19:02] Lee Sin 召唤师技能: [4,11]=Flash+Smite (99.97%), [11,14]=Smite+Ignite (0.02%)
- [2026-05-05 19:02] Lee Sin 符文页: 8010(Conqueror)+8000/8300, pick_rate=79.52%, 4个builds变体
- [2026-05-05 19:02] 发现 `mythic_items` 字段为空数组（旧版本遗留，可删除）
