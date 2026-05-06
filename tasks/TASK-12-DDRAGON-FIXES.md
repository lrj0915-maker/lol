# TASK-12: DDragon 资源与召唤师技能图标修复
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单执行
**Created**: 2026-05-05 22:05 GMT+8
**Focus**: 前端资源链接版本过旧 + 召唤师技能图标缺失

---

## 背景

经代码扫描发现，前端存在**资源版本不一致**和**召唤师技能图标缺失**问题，可能导致部分英雄/技能图标 404 或不显示。

---

## 问题清单

### 🔴 P0-1: DDragon 版本 `14.24.1` 过旧
**文件**: `frontend/src/utils/ddragon.js` Line 6
**问题**: 硬编码 `const DDRAGON_VERSION = '14.24.1'`，但 INDEX.md/TASK-06 记录当前 DDragon 版本应为 `16.9.1`。版本过旧会导致：
- 新英雄（如 2025 年后发布的）图标 404
- 新物品图标 404
- 部分重做过英雄/物品的图标不匹配

**修复方案**:
```javascript
const DDRAGON_VERSION = '16.9.1'
```

**验证**: 检查 `https://ddragon.leagueoflegends.com/cdn/16.9.1/img/champion/Ahri.png` 是否可访问。

---

### 🔴 P0-2: `getSpellIcon()` 缺少召唤师技能 13/30/31
**文件**: `frontend/src/utils/ddragon.js` Line 47-58
**问题**: spellMap 缺少以下 ID：
- `13` = 清晰术 (SummonerMana) — 在 `summonerSpells.js` 中有定义
- `30` = 国王之刃/雪球召回 (SummonerPoroRecall) — 大乱斗模式
- `31` = 国王之刃/雪球投掷 (SummonerPoroThrow) — 大乱斗模式

当后端返回的 `summoner_spells` 包含这些 ID 时，`getSpellIcon()` 返回 `null`，`SummonerSpellCard.vue` 中 `v-if` 条件不通过，图标完全不显示。

**对比**: `frontend/src/data/summonerSpells.js` 有完整映射（1,3,4,6,7,11,12,13,14,21,30,31,32,39,54,55），但使用 `raw.communitydragon.org` 作为图标源。而 `ddragon.js` 的 `getSpellIcon()` 使用 `ddragon.leagueoflegends.com`，两者不一致。

**修复方案**:
```javascript
const spellMap = {
  1: 'SummonerBoost',      // 净化
  3: 'SummonerExhaust',    // 虚弱
  4: 'SummonerFlash',      // 闪现
  6: 'SummonerHaste',      // 幽灵疾步
  7: 'SummonerHeal',       // 治疗
  11: 'SummonerSmite',     // 惩戒
  12: 'SummonerTeleport',  // 传送
  13: 'SummonerMana',      // 清晰术 ← 新增
  14: 'SummonerDot',       // 点燃
  21: 'SummonerBarrier',   // 屏障
  30: 'SummonerPoroRecall', // 雪球召回 ← 新增
  31: 'SummonerPoroThrow',  // 雪球投掷 ← 新增
  32: 'SummonerSnowball',  // 标记/雪球
}
```

---

### 🟡 P1-1: `BattleProfileHeader.vue` 也硬编码了旧版本
**文件**: `frontend/src/components/battle/BattleProfileHeader.vue` Line 66
**问题**: 硬编码 `https://ddragon.leagueoflegends.com/cdn/14.24.1/img/profileicon/...`

**修复方案**: 统一使用 `ddragon.js` 导出的 `DDRAGON_BASE` 或独立常量。

---

### 🟡 P1-2: `SkillOrderCard.vue` 技能加点顺序显示格式
**文件**: `frontend/src/components/SkillOrderCard.vue` Line 16
**问题**: TASK-06 发现后端 `skills[].order` 是**字符串数组** `["W","Q","E","Q"...]`，但 `SkillOrderCard.vue` 直接显示 `{{ skill.order }}`。Vue 会自动将数组转为逗号分隔的字符串（如 `"W,Q,E,Q,Q,R,Q,W,W"`），而不是 OPGG 风格的 `W > Q > E > Q > Q > R ...`。

**RunesOPGGPreview.vue 的 mock 数据**使用的是字符串 `'W Q E Q Q R ...'`，说明前端期望的是**空格分隔的字符串**。

**当前显示效果**: `W,Q,E,Q,Q,R,Q,W,W`（逗号分隔，不美观）
**期望效果**: `W > Q > E > Q > Q > R > Q > W > W`（箭头分隔，OPGG 风格）

**修复方案**（在 `SkillOrderCard.vue` 中处理）：
```javascript
// 如果 order 是数组，转为箭头分隔的字符串
const displayOrder = computed(() => {
  if (Array.isArray(props.skill?.order)) {
    return props.skill.order.join(' > ')
  }
  return props.skill?.order || ''
})
```

或在 `RunesView.vue` 的 `currentPositionData` computed 中统一转换：
```javascript
skills: Array.isArray(raw.skills) ? raw.skills.map(s => ({
  ...s,
  order: Array.isArray(s.order) ? s.order.join(' > ') : s.order
})) : [],
```

---

## 执行步骤

1. **修复 P0-1**: 更新 `ddragon.js` 中 `DDRAGON_VERSION` 为 `16.9.1`
2. **修复 P0-2**: 在 `ddragon.js` `getSpellIcon()` 的 spellMap 中补充 13/30/31
3. **修复 P1-1**: 更新 `BattleProfileHeader.vue` 中的硬编码版本号
4. **修复 P1-2**: 在 `SkillOrderCard.vue` 或 `RunesView.vue` 中处理 `order` 数组格式
5. **构建检查**: 确认前端构建无错误
6. **更新本任务文件状态为 ✅ DONE**

---

## 交付标准

- [x] `ddragon.js` 版本更新为 `16.9.1`
- [x] `getSpellIcon()` 支持 13/30/31
- [x] `BattleProfileHeader.vue` 不再硬编码版本号
- [x] 技能加点顺序显示为箭头分隔格式（如 `W > Q > E > Q`）
- [x] 前端构建通过
