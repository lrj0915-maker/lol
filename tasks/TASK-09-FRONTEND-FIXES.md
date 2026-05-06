# TASK-09: 符文页面前端修复集
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单修改
**Created**: 2026-05-05 20:42 GMT+8
**Focus**: 仅符文页面 — 修复已知前端 bug 和展示问题

---

## 目标

修复符文页面前端已发现的展示 bug 和体验问题。

---

## 问题清单

### 🔴 P0-1: RuneConfigCard pick_rate 双百分号 bug
**文件**: `frontend/src/components/RuneConfigCard.vue` Line 10
**当前代码**:
```vue
<span class="pick-rate">{{ formatPercent(config.pick_rate, 2) }}% 登场</span>
```
**问题**: `formatPercent` 已返回带 `%` 的字符串（如 "67.00%"），模板又加一个 `%` → 显示 "67.00%% 登场"
**修复**:
```vue
<span class="pick-rate">{{ formatPercent(config.pick_rate, 2) }} 登场</span>
```

### 🟡 P1-1: 符文页数量硬编码为 5 个
**文件**: `frontend/src/views/RunesView.vue` Line 379
**当前代码**:
```javascript
const currentRuneConfigs = computed(() => {
  const configs = sortRuneConfigs(currentPositionData.value?.rune_pages || [], sortBy.value)
  return configs.slice(0, 5)
})
```
**问题**: 只展示 5 个符文页，OPGG 通常展示 7-10 个甚至全部。用户看不到更多符文组合。
**修复**: 改为展示 10 个，与 OPGG 对齐
```javascript
const currentRuneConfigs = computed(() => {
  const configs = sortRuneConfigs(currentPositionData.value?.rune_pages || [], sortBy.value)
  return configs.slice(0, 10)
})
```

### 🟡 P1-2: totalGames 基于已截断的 configs 计算
**文件**: `frontend/src/views/RunesView.vue` Line 380
**当前代码**:
```javascript
const totalGames = computed(() => currentRuneConfigs.value.reduce((sum, item) => sum + (item.play || 0), 0))
```
**问题**: `currentRuneConfigs` 已被 `slice(0, 5)` 截断，totalGames 只统计了前 5 个的 play 之和，不是全部符文页的总样本量。这导致 PopularityBadge 显示的比例偏低。
**修复**: 改为基于全部符文页计算
```javascript
const totalGames = computed(() => {
  const allConfigs = currentPositionData.value?.rune_pages || []
  return allConfigs.reduce((sum, item) => sum + (item.play || 0), 0)
})
```

### 🟡 P1-3: 装备推荐每组只展示第一个
**文件**: `frontend/src/views/RunesView.vue` Line 87-107
**当前代码**: 每组装备（starter_items/boots/core_items）只展示 `items[0]`
**问题**: OPGG 通常展示前 2-3 个备选装备。当前只展示一个，用户看不到其他选择。
**修复**: 每组展示前 2 个（如果有多于一个的话）
```vue
<!-- 出门装 -->
<div class="item-group" v-if="revealItemBlocks && currentPositionData?.starter_items?.length">
  <span class="item-label">出门</span>
  <div v-for="(item, idx) in currentPositionData.starter_items.slice(0, 2)" :key="idx" class="item-icons">
    <img v-for="id in item.ids" :key="id" :src="getItemIcon(id)" class="item-icon" loading="lazy" decoding="async" />
    <span class="item-wr">{{ formatWinRate(item) }}</span>
  </div>
</div>
```
鞋子和核心装同理。

---

## 执行步骤

1. 修复 P0-1: RuneConfigCard.vue Line 10 去掉多余的 `%`
2. 修复 P1-1: RunesView.vue Line 379 `slice(0, 5)` → `slice(0, 10)`
3. 修复 P1-2: RunesView.vue Line 380 totalGames 改为基于全部符文页计算
4. 修复 P1-3: RunesView.vue 装备推荐展示前 2 个
5. 验证修改后构建通过（项目当前无 lint 脚本）
6. 更新本任务文件状态为 ✅ DONE

---

## 交付标准

- [x] pick_rate 不再显示双百分号（如 "67.00% 登场"）
- [x] 符文页展示数量从 5 个改为 10 个
- [x] totalGames 计算基于全部符文页而非截断后的列表
- [x] 每组装备展示前 2 个备选（如果有多于一个）
- [x] 前端构建通过（项目当前无 lint 脚本，已执行 `npm run build`）
