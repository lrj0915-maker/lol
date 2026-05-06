# TASK-10: 登录界面修复集
**Status**: ✅ DONE
**Supervisor**: 代可行 👔
**Execution AI**: 按以下清单排查和修复
**Created**: 2026-05-05 20:55 GMT+8
**Focus**: 登录界面 — 账号列表为空 + 按钮点击后窗口空白

---

## 用户描述的问题

1. **账号列表显示"没有匹配的账号"**，但 `data/accounts.json` 实际有 28 个账号
2. **工具按钮（好友管理/清理好友/分解精粹/关闭游戏）点击后窗口变空白**，过一会才恢复
3. **原本没有上述问题** — 说明是最近引入的 regression

---

## 已发现的线索

### 线索A：`accounts.json` 存在且有数据
- 文件路径：`lol-assistant/data/accounts.json`
- 内容：28 个账号，包含 qq、password、server_index、summoner_name、ban_info 等字段
- 后端 `account_manager.list_accounts()` 直接读取此文件，无过滤逻辑
- `bridge.py` 的 `get_accounts()` 直接返回 `list_accounts()` 结果

### 线索B：前端 `loadAccounts()` 防御性不足
```javascript
// LoginView.vue Line 626-631
async function loadAccounts() {
  try {
    accounts.value = await bridge.getAccounts() || []
  } catch (error) {
    console.error('[LoginView] loadAccounts error:', error)
  }
}
```
**问题**：如果 `bridge.getAccounts()` 返回错误信封（如 `{code, message}` 对象）而非数组，
`accounts.value` 会被赋值为对象。后续 `filteredAccounts` 中调用 `result.filter(...)` 会抛
`TypeError: result.filter is not a function`，导致 computed 异常、渲染中断。

### 线索C：`patch_login_css.py` 替换逻辑存在严重 bug
```python
idx_start = content.find(old_css_start)
idx_end = content.find(old_css_end) + len(old_css_end)
if idx_start > 0 and idx_end > idx_start:
    content = content[:idx_start] + new_css + content[idx_end:]
```
**问题**：如果 `old_css_end` 不存在，`find()` 返回 -1，`idx_end = -1 + len(old_css_end)` 可能为正数。
若此时 `idx_start` 较小，条件 `idx_end > idx_start` 可能成立，导致从 `idx_start` 到 `idx_end` 之间的
内容被错误替换（可能截断大量 CSS）。

### 线索D：`patch_login_css3.py` 硬编码行号
```python
lines[752:766] = [new_css_lines + '\n']
```
**问题**：直接硬编码行号 752-766。如果 LoginView.vue 行数变化（如添加/删除代码），
替换会命中错误位置，导致 CSS 被截断或重复。

### 线索E：后端登录异常
多个账号的 `last_login_message` 显示：
```
'LoginService' object has no attribute '_find_launcher_window'
```
说明 `_kill_launcher_processes` 中调用的 `self._find_launcher_window()` 在某些路径上不可见。

---

## 问题清单

### 🔴 P0-1: 账号列表显示"没有匹配的账号"
**文件**: `frontend/src/views/LoginView.vue`
**位置**: `loadAccounts()` 函数 + `filteredAccounts` computed
**根因**: `bridge.getAccounts()` 返回值格式不保险 — 可能返回错误信封（对象）而非数组。

**修复方案**:
```javascript
async function loadAccounts() {
  try {
    const result = await bridge.getAccounts()
    // 防御性检查：确保返回的是数组
    if (Array.isArray(result)) {
      accounts.value = result
    } else if (result && Array.isArray(result.data)) {
      accounts.value = result.data
    } else {
      accounts.value = []
      console.warn('[LoginView] getAccounts 返回非数组:', result)
    }
  } catch (error) {
    console.error('[LoginView] loadAccounts error:', error)
    accounts.value = []
  }
}
```

同时在 `filteredAccounts` 中增加防御：
```javascript
const filteredAccounts = computed(() => {
  let result = Array.isArray(accounts.value) ? accounts.value : []
  // ... 其余过滤逻辑不变
})
```

### 🔴 P0-2: 按钮点击后窗口变空白
**可能原因**（多因素叠加）：

1. **CSS 被 patch 脚本破坏**：`patch_login_css.py` 或 `patch_login_css3.py` 可能截断了 LoginView.vue 的 CSS，
   导致 `.content` 或 `.main` 的 flex 布局在某些状态下高度计算为 0。
2. **Vue computed 异常级联**：如果 `accounts.value` 不是数组，`filteredAccounts` 和 `sortedAccounts`
   的 computed 会抛异常，Vue 3 会阻止部分渲染，可能导致区域空白。
3. **PyWebView 渲染闪烁**：大量 DOM 更新 + CSS 变化可能触发 WebView 重绘延迟。

**修复方案**:
1. 先修复 P0-1（确保 `accounts.value` 始终是数组）
2. 检查 LoginView.vue 的 CSS 是否完整（特别是 `.content`、`.main`、`.login-view` 的 flex 布局）
3. 在 `.content` 上增加 `min-height` 兜底，防止 flex 收缩导致内容不可见：
   ```css
   .content {
     min-height: 200px; /* 兜底，防止 flex 收缩到 0 */
   }
   ```

### 🟡 P1-1: `_find_launcher_window` 不可见异常
**文件**: `backend/services/login_service.py`
**位置**: `_kill_launcher_processes` 方法内调用 `self._find_launcher_window()`
**根因**: 多个账号的 `last_login_message` 显示 `'LoginService' object has no attribute '_find_launcher_window'`。

**修复方案**: 检查 `_find_launcher_window` 方法的定义位置。如果它是在类外部定义的（因 patch 脚本
插入到了错误位置），需要将其移回类内部。

### 🟡 P1-2: patch 脚本清理
**文件**: 根目录 `patch_login_*.py`、`patch_kill*.py`
**问题**: 这些 patch 脚本逻辑脆弱，可能再次破坏代码。应在修复完成后清理或归档。

---

## 执行步骤

1. **修复 P0-1**：在 `LoginView.vue` 中增强 `loadAccounts()` 和 `filteredAccounts` 的防御性检查
2. **验证 CSS 完整性**：读取 `LoginView.vue` 的 CSS 部分，确认没有被截断（特别是 `.content`、`.main`、`.tool-row`）
3. **修复 P0-2**：如果 CSS 完整但问题仍在，给 `.content` 增加 `min-height` 兜底
4. **修复 P1-1**：检查 `login_service.py` 中 `_find_launcher_window` 的定义位置
5. **验证修复**：构建前端并校验后端语法
6. **更新本任务文件状态为 ✅ DONE**

---

## 交付标准

- [x] 账号列表正确显示 `accounts.json` 中的账号（28 个）
- [x] 工具按钮点击后窗口不再变空白
- [x] `_find_launcher_window` 异常不再出现
- [x] 前端构建通过且后端语法校验通过
