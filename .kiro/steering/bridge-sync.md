---
inclusion: fileMatch
fileMatchPattern: "{backend/bridge.py,frontend/src/utils/bridge.js}"
---

# Bridge 同步规范

修改 `bridge.py` 或 `bridge.js` 时，必须保持两端方法一一对应。

## 同步检查清单

1. 在 `bridge.py` 的 `Bridge` 类中新增/修改公共方法
2. 在 `bridge.js` 的 `Bridge` 类中新增/修改对应的 JS 方法
3. JS 方法名使用 camelCase，Python 方法名使用 snake_case
4. JS 方法通过 `this._call('python_method_name', ...args)` 调用
5. Python 方法返回 dict（含 success 字段）或 list

## 数据推送（后端 → 前端）

后端通过 `window.evaluate_js()` 推送，前端通过 CustomEvent 分发：
- `onRuntimeSnapshot` → `runtime-snapshot` 事件 → appStore
- `onGameEnd` → `game-end` 事件
- `onTeamAnalysis` → `team-analysis` 事件

新增推送回调时，需在 bridge.js 底部注册对应的 `window.onXxx` 处理函数。
