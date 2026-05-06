# TASK-07: 符文变体(Builds)展示逻辑分析
**Status**: 🔄 RESEARCH IN PROGRESS
**Supervisor**: 代可行 👔
**Created**: 2026-05-05 18:38 GMT+8
**Focus**: 仅符文页面 — 符文变体(bulds)如何展示

---

## 现状：变体只展示第一层

当前前端只展示5个符文页（rune_pages），每个页取 `builds[0]`（最优变体）展示：

```typescript
// runesViewHelpers.js
export function selectPrimaryBuild(config, sortBy) {
  const builds = getBuilds(config)  // builds[0] 或 [config]
  if (!builds.length) return config
  if (sortBy === 'winRate') {
    return [...builds].sort((a, b) => b.win/b.play - a.win/b.play)[0]
  }
  return [...builds].sort((a, b) => b.play - a.play)[0]
}
```

**问题**：用户看不到同一个主+副符文组合下的5种不同变体（stat_mod_ids不同）。

---

## OP.GG 实际展示方式

从数据来看，OP.GG 的符文页变体展示逻辑：

1. **顶部**：5个主符文页标签（按 pick_rate 排序）
2. **选中页内**：显示具体符文配置 + 5个变体切换器
3. **变体区别**：只在于 stat_mod_ids（属性碎片）不同

```
符文页 #1: 电刑+奥术彗星
  ├─ 变体A: [攻速/自适应/生命值] ← 最常用 (67.3%)
  ├─ 变体B: [攻速/自适应/攻速]    (5.4%)
  ├─ 变体C: [攻速/自适应/生命值] + 不同副系 (4.8%)
  └─ ...

符文页 #2: 电刑+主宰（不同副系）
符文页 #3: ...
```

---

## 前端目前的问题

1. **不展示变体选择器**：用户只能看到 `builds[0]`，看不到其他变体
2. **所有5个页都展示了 builds[0]**，但同一个主系+副系组合下的不同 stat_mod_ids 变体被折叠了

---

## 可能的优化方向

### 方向A：符文页内嵌变体选择器（推荐）
在每个 `RuneConfigCard` 展开态底部加变体选择器：

```
RuneConfigCard (主系+副系 = 电刑+奥术彗星)
  ├─ 符文展示 (主系4个 + 副系2个 + 碎片)
  ├─ 当前变体: [攻速/自适应/生命值]
  └─ 变体选择:
      [●] A: 攻速/自适应/生命值  67.3%  ⭐
      [ ] B: 攻速/自适应/攻速     5.4%
      [ ] C: ...                  4.8%
```

**实现方式**：展开态底部加一个变体列表，点击切换 `selectedBuild`。

### 方向B：折叠变体数量
如果变体 pick_rate < 1%，直接折叠不展示，减少噪音。

---

## 数据结构参考

```typescript
// 一个符文页包含5个变体
rune_pages[0] = {
  id: 8112,
  primary_page_id: 8100,
  secondary_page_id: 8200,
  pick_rate: 0.7103,  // 71.03% 使用这套组合
  play: 76677,
  builds: [
    { stat_mod_ids: [5005,5008,5001], pick_rate: 0.673, win: 26177, play: 51601 },
    { stat_mod_ids: [5005,5008,5011], pick_rate: 0.0539, ... },
    { stat_mod_ids: [5005,5008,5011], pick_rate: 0.0482, ... },  // 副系不同
    ...
  ]
}
```

---

## 状态：待讨论

这个功能是否值得做取决于用户意图。目前用户只要求符文页面相关的修复，不要求新功能。等 TASK-02/05 完成后评估。

**Status Log**:
- [2026-05-05 18:38] [TASK-07] Created — 符文变体展示逻辑分析
- [2026-05-05 18:38] 确认：前端只展示 builds[0]，不展示其他变体
- [2026-05-05 18:38] 确认：stat_mod_ids 是变体之间唯一区别
