# TASK-08: 英雄概览统计信息补全
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单修改
**Created**: 2026-05-05 19:10 GMT+8
**Focus**: 仅符文页面 — 补全左栏未显示的统计信息

---

## 目标

在 `RunesView.vue` 左栏的 stats-list 中补全缺失的英雄概览统计信息，并增加 counter 展示数量。

---

## 问题清单

### P0-1: Counter 数量不足
**文件**: `frontend/src/views/RunesView.vue` Line 114
**当前**: `countersPreview.slice(0, 3)` → 只显示 3 个
**修复**: 改为 `slice(0, 5)`，与 `buildCountersPreview` 的 `max=5` 参数对齐

### P1-1: 全位置 KDA 未显示
**文件**: `frontend/src/views/RunesView.vue`
**数据路径**: `overview.value.average_stats.kda`（已存在于后端返回数据）
**修复**: 在 stats-list 中新增一行显示全位置 KDA

```vue
<div class="stat-row"><span>KDA</span><strong>{{ revealChampionStats ? formatKda(overview.value.average_stats?.kda) : '—' }}</strong></div>
```

### P1-2: 全位置登场率未显示
**文件**: `frontend/src/views/RunesView.vue`
**数据路径**: `overview.value.average_stats.pick_rate`
**修复**: 在 stats-list 中新增一行显示全位置登场率

```vue
<div class="stat-row"><span>全位置登场率</span><strong>{{ revealChampionStats ? formatPercent(overview.value.average_stats?.pick_rate, 2) : '—' }}</strong></div>
```

### P1-3: 全位置禁用率未显示
**文件**: `frontend/src/views/RunesView.vue`
**数据路径**: `overview.value.average_stats.ban_rate`
**修复**: 在 stats-list 中新增一行显示全位置禁用率

```vue
<div class="stat-row"><span>全位置禁用率</span><strong>{{ revealChampionStats ? formatPercent(overview.value.average_stats?.ban_rate, 2) : '—' }}</strong></div>
```

---

## 需要新增的辅助函数

在 `frontend/src/utils/runesViewHelpers.js` 中新增 `formatKda` 函数：

```javascript
export function formatKda(kda) {
  if (kda === null || kda === undefined || Number.isNaN(Number(kda))) return '-'
  return Number(kda).toFixed(2)
}
```

---

## 执行步骤

1. 修改 `RunesView.vue` Line 114: `slice(0, 3)` → `slice(0, 5)`
2. 在 `RunesView.vue` stats-list 中新增 KDA / 全位置登场率 / 全位置禁用率 三行
3. 在 `runesViewHelpers.js` 中新增 `formatKda` 函数
4. 在 `RunesView.vue` script 中 import `formatKda`
5. 验证修改后构建通过

---

## 交付标准

- [ ] Counter 显示 5 个而非 3 个
- [ ] 左栏 stats-list 显示 KDA（如 2.85）
- [ ] 左栏 stats-list 显示全位置登场率
- [ ] 左栏 stats-list 显示全位置禁用率
- [ ] 构建无错误
