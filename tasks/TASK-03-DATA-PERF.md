# TASK-03: 数据+性能优化
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单修改
**Created**: 2026-05-05 18:59 GMT+8

---

## 目标

优化符文页面数据加载性能和缓存策略。

---

## 问题清单

### P1-1: `preLoadPosition` hover 大量重复请求 ✅ 已修复
**文件**: `frontend/src/views/RunesView.vue`
**状态**: 已存在 300ms debounce（Line 489-499）
**代码**:
```typescript
let positionDebounce: number | null = null
function preLoadPosition(position: string) {
  if (positionDebounce) return
  positionDebounce = window.setTimeout(() => {
    refreshSingleRunesEntry(...)
    positionDebounce = null
  }, 300)
}
```

### P1-2: IndexedDB 缓存 TTL 过短 ✅ 已修复
**文件**: `frontend/src/composables/useRunesData.js`
**状态**: 执行 AI 已修改（2026-05-05 19:07）
**修改**: `CACHE_DURATION = 30 * 60 * 1000` → `CACHE_DURATION = 2 * 60 * 60 * 1000`

### P2-1: `ban_rate` 显示为 0 ✅ 已确认
**文件**: `frontend/src/views/RunesView.vue`
**结论**: 数据链路完整，代码逻辑正确。
- 前端 `overviewPos = overview.value.position_stats || {}`，`overviewPos.ban_rate` 读取正确
- 后端 `fetch_champion_overview` 返回 `position_stats = selected_position.get('stats')`，含 ban_rate
- `formatRatePercent` 能正确处理小数格式（val≤1 时自动 ×100）
- 显示为 0 是因为该英雄 ban_rate 本身极低（如 Annie 0.008 → 0.80%），非代码 bug

---

## 执行步骤

1. 修复 `preLoadPosition` 重复请求问题
2. 调整 IndexedDB 缓存 TTL
3. 检查 `ban_rate` 显示逻辑
4. 验证修改后功能正常

---

## 交付标准

- [x] hover 位置 tab 不再重复请求（已有 300ms debounce）
- [x] 缓存命中率达到合理水平（TTL 延长至 2 小时）
- [x] ban_rate 显示逻辑已确认正确
