# LOL 战绩助手 — 项目概述

## 基本信息

基于 pywebview + Vue 3 的英雄联盟桌面助手，仅 Windows 平台。核心功能：一键登录、符文/强化推荐、战绩查询、队伍分析、自动准备/选人、游戏内聊天、野怪监控。所有界面和代码注释使用中文。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.10+, pywebview 4.x, psutil, requests, websocket-client, ctypes(Win32), pyautogui, pytesseract, pygame, mss, opencv-python, pynput |
| 前端 | Vue 3.4 + Composition API(`<script setup>`), Vue Router 4(hash 模式), Pinia, ECharts 5, Vite 5 |
| 数据 | SQLite(战绩), JSON 文件(配置/账号/符文/强化缓存), 前端 IndexedDB(30 分钟缓存) |
| 外部 API | Riot LCU API(本地客户端), OP.GG Ranked API(符文/强化数据) |
| 打包 | PyInstaller → `dist/LOL战绩助手.exe` |

## 前后端通信

pywebview 将 `Bridge` 类注入为 `window.pywebview.api`。前端通过 `bridge.js` 的 `_call(method, ...args)` 统一调用。所有后端公共方法定义在 `backend/bridge.py`。

```
前端 bridge.js._call('method') → window.pywebview.api.method() → Bridge.method() → 返回 dict/list
```

后端通过 `window.evaluate_js()` 主动推送（线程安全）：
- `window.onRuntimeSnapshot(data)` — 运行时状态快照
- `window.onGameEnd(data)` — 游戏结束数据
- `window.onTeamAnalysis(data)` — 队伍分析结果

错误处理：bridge.js 的 `_makeErrorEnvelope()` 统一格式，前端调用永远不抛异常。

## 线程模型

- 主线程：pywebview UI 事件循环
- LCU WebSocket 线程：`LCUEvents` 接收客户端事件
- 连接守护线程：`_connection_guard_loop` 自动重连（指数退避）
- 登录工作线程：`LoginService._login_worker` Win32 自动化
- Snapshot 推送：`threading.Timer` 延迟合并（0.1-0.18s 去抖）
- 各 Service 独立工作线程

## 开发命令

```bash
# 启动应用
cd lol-assistant && python backend/main.py

# 前端构建（修改前端后必须执行）
cd lol-assistant/frontend && npm run build

# 打包
cd lol-assistant && pyinstaller build.spec
```

## 质量红线

所有代码变更必须遵守 `quality-gate.md` 定义的交付标准。两条铁律：
1. 绝不偷工减料 — 任务涉及的每个文件、每个调用链都要改完，不允许半成品交付
2. 交付前必须验证 — 对修改的文件运行 getDiagnostics，确认 bridge 前后端同步，清理调试代码，逐项通过检查清单后才能说"完成"

## 禁止事项

- 不要创建 `temp_*` 临时文件或调试用 `.md` 文档
- 不要修改 `jicheng/` 目录下的任何文件
- 不要在前端硬编码后端 URL，一律通过 bridge.js
- 不要在后端硬编码文件路径，使用 `os.path.join`
- 不要遗留 `.bak`、`.old`、`.tmp` 文件
- 新增后端 API 必须同时在 bridge.py 和 bridge.js 添加对应方法
- 回复和代码注释使用中文
