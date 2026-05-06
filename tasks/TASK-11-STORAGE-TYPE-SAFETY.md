# TASK-11: localStorage 解析类型安全检查
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单执行
**Created**: 2026-05-05 22:03 GMT+8
**Focus**: 前端 localStorage JSON.parse 缺少类型检查，可能导致运行时异常

---

## 背景

TASK-10 修复了 `LoginView.vue` 的 `loadAccounts()` — `bridge.getAccounts()` 返回非数组时导致 `.filter()` 崩溃。

经代码扫描，发现**同样的类型安全漏洞**存在于 localStorage 解析逻辑中：`JSON.parse()` 不会抛出异常当 JSON 本身是合法的，但类型不对（如数组变对象、对象变数组）。

---

## 问题清单

### 🔴 P1-1: `useFavorites.js` 收藏列表类型不安全
**文件**: `frontend/src/composables/useFavorites.js`
**位置**: Line 14-22

```javascript
function loadFavorites() {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY)
    if (stored) {
      favorites.value = JSON.parse(stored)  // ← 如果存的是对象而非数组，不会抛错
    }
  } catch (e) {
    favorites.value = []
  }
}
```

**风险**: 如果 localStorage 被外部篡改（如用户手动编辑、其他脚本写入），`stored` 可能是合法 JSON 但不是数组（如 `{"foo": "bar"}`）。此时 `favorites.value` 变成对象，后续所有 `.filter()` / `.some()` / `.push()` 调用都会抛出 `TypeError`，导致收藏功能完全不可用。

**修复方案**:
```javascript
function loadFavorites() {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        favorites.value = parsed
      } else {
        console.warn('[useFavorites] localStorage 数据不是数组，重置为空')
        favorites.value = []
      }
    }
  } catch (e) {
    console.error('[useFavorites] 加载收藏失败:', e)
    favorites.value = []
  }
}
```

---

### 🔴 P1-2: `useUserPreferences.js` 偏好设置类型不安全
**文件**: `frontend/src/composables/useUserPreferences.js`
**位置**: Line 50-62

```javascript
load() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return this.mergeDeep(defaultPreferences, parsed)  // ← 如果 parsed 不是对象，mergeDeep 行为不可预期
    }
  } catch (error) {
    // 加载失败，使用默认配置
  }
  return JSON.parse(JSON.stringify(defaultPreferences))
}
```

**风险**: 如果 `parsed` 是数组或其他非对象类型，`mergeDeep` 可能返回不可预期的结果，甚至导致后续代码访问不存在的属性时出错。

**修复方案**:
```javascript
load() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return this.mergeDeep(defaultPreferences, parsed)
      } else {
        console.warn('[useUserPreferences] localStorage 数据不是对象，使用默认配置')
      }
    }
  } catch (error) {
    console.error('[useUserPreferences] 加载偏好设置失败:', error)
  }
  return JSON.parse(JSON.stringify(defaultPreferences))
}
```

---

## 执行步骤

1. **修复 P1-1**: 修改 `useFavorites.js` 的 `loadFavorites()`，增加 `Array.isArray(parsed)` 检查
2. **修复 P1-2**: 修改 `useUserPreferences.js` 的 `load()`，增加对象类型检查
3. **构建检查**: 确认前端构建无错误
4. **更新本任务文件状态为 ✅ DONE**

---

## 交付标准

- [x] `useFavorites.js` `loadFavorites()` 在 JSON.parse 后验证结果为数组
- [x] `useUserPreferences.js` `load()` 在 JSON.parse 后验证结果为对象
- [x] 前端构建通过
- [x] console.warn/console.error 在类型不匹配时正确输出日志
