# Spec: In-Game Auto Start + Auto Taunt Reliability

- Date: 2026-03-03
- Scope: `lol-assistant` backend in-game phase handling
- Target files:
  - `backend/services/ingame_chat.py`
  - `backend/bridge.py` (if phase reconciliation entrypoint is needed)
  - `backend/lcu/events.py` (only if event loss handling needs enhancement)

## 1) 什么是 Spec

Spec (Specification) 是“可执行技术规格说明”。  
它定义目标行为、触发条件、状态机、异常处理、日志与验收标准，确保实现可复现、可测试、可回归。

## 2) 背景与问题

用户反馈：
- 出游戏自动关闭正常。
- 进游戏未自动打开打野检测。
- 进游戏未自动发送嘲讽。

当前代码/日志已观察到的风险点：
- `ingame_chat.py` 的 `GameStart` 未被当作“游戏内阶段”处理，存在在 `GameStart` 误停监控的行为。
- 日志中出现 `phase=GameStart` 后立即“检测到离开游戏阶段(GameStart)，自动停止野怪监控”，与预期冲突。
- 游戏启动窗口期存在 LCU 连接短暂失败（`WinError 10061`），会导致仅靠单次事件触发不稳定。

## 3) 文档依据（联网检索）

- Riot 官方文档：League Client API / Game Client API 说明（LCU 非官方支持、可通过客户端 swagger 探索）
  - https://developer.riotgames.com/docs/lol#game-client-api
- LCU OpenAPI（镜像，含 `gameflow-phase` 枚举、`/Subscribe`、`/Unsubscribe`、聊天接口）
  - https://raw.githubusercontent.com/nomi-san/lcu-api/main/openapi.json
- LCU WebSocket 注册与事件类型示例（`OnJsonApiEvent`）
  - https://lcu-driver.readthedocs.io/en/latest/quickstart.html
- 社区文档：LCU 连接与 lockfile 基础、WebSocket 事件命名示例
  - https://hextechdocs.dev/getting-started-with-the-lcu-api/
  - https://github.com/riftrun/hexgate

说明：事件名模式与实战连接流程由社区资料补充；`gameflow-phase` 枚举与核心接口来自 OpenAPI 一手解析。

## 4) 目标与非目标

### 4.1 目标

- 修复“进游戏自动打开打野检测”触发失败。
- 修复“进游戏自动发嘲讽”触发失败。
- 保持“出游戏自动关闭”行为不回归。
- 在 LCU 短暂断连场景下保持可恢复。

### 4.2 非目标

- 不重构打野检测 OCR 核心算法。
- 不新增 UI 功能，仅保证现有开关行为正确。

## 5) 状态模型（必须落实）

以 `/lol-gameflow/v1/gameflow-phase` 为主状态源，枚举基线：
`None, Lobby, Matchmaking, CheckedIntoTournament, ReadyCheck, ChampSelect, GameStart, FailedToLaunch, InProgress, Reconnect, WaitingForStats, PreEndOfGame, EndOfGame, TerminatedInError`

定义：
- `IN_GAME_PHASES = { GameStart, InProgress, Reconnect }`
- `OUT_GAME_PHASES =` 其余阶段

关键规则：
- 进入 `IN_GAME_PHASES`：允许自动启动打野检测（幂等），并触发自动嘲讽判定。
- 保持在 `IN_GAME_PHASES`：绝不执行自动停止。
- 从 `IN_GAME_PHASES` 转到 `OUT_GAME_PHASES`：执行自动停止（幂等）。

## 6) 触发链路规范

### 6.1 自动打开打野检测

触发条件：
- `jungle_monitor.auto_start == true`
- phase 进入 `IN_GAME_PHASES`
- `jungle_monitor.is_running() == false`

执行：
- 调用 `jungle_monitor.start()`
- 记录结构化日志：`phase`, `auto_start`, `pre_running`, `start_result`

禁止行为：
- 在 `GameStart` 执行 stop（当前风险点）。

### 6.2 自动发送嘲讽

触发条件：
- `ingame_chat.enabled == true`
- 当前对局未发送过（按 `gameId` 去重）
- phase 进入 `IN_GAME_PHASES` 后满足发送窗口

发送窗口策略：
- 首选在 `InProgress` 触发。
- 若仅收到 `GameStart`，允许进入等待队列并在 `InProgress` 或超时后尝试。
- 发送前再次确认 phase 仍在 `IN_GAME_PHASES`。

去重策略：
- 使用 `gameflow session.gameData.gameId` 作为一局唯一键。
- 同一 `gameId` 最多自动发送一次。
- 离开对局后清理发送标记。

## 7) 可靠性与容错

- 事件主驱动：`OnJsonApiEvent` + `/lol-gameflow/v1/gameflow-phase`
- 轮询兜底：每 1-2 秒读取 `/lol-gameflow/v1/session` 对齐状态（仅在连接可用时）
- 启动窗口容错：当 LCU 连接短暂失败（如 `10061`）时，不立即判定“离开游戏”，保留上次 in-game 状态一个短暂宽限窗口（建议 10-15 秒）
- 所有 start/stop/send 操作必须幂等，避免重复线程或重复发送

## 8) 实现改动清单（最小化）

1. `backend/services/ingame_chat.py`
- 抽取 phase 分类函数（in-game / out-game），避免硬编码分散。
- 修正 `_sync_jungle_monitor_state`：将 `GameStart`/`Reconnect` 纳入 in-game，禁止误 stop。
- 将“自动嘲讽已发送”从布尔提升为“按 `gameId` 去重”逻辑。
- 增加发送前二次校验与重试日志。

2. `backend/bridge.py`（如需）
- 在连接重建后立即推送一次当前 `session/phase` 到 in-game service，缩短漏事件窗口。

3. `backend/lcu/events.py`（仅必要时）
- 保持现有订阅模型；若发现抖动，补充订阅重放或健康日志，不改协议。

## 9) 日志与可观测性（验收必须）

新增/统一日志字段：
- `phase_prev`, `phase_curr`, `in_game`, `game_id`
- `auto_start_enabled`, `monitor_running_before`, `monitor_running_after`
- `taunt_enabled`, `taunt_sent`, `taunt_skip_reason`
- `lcu_connected`, `reconnect_count`

必须可检索到以下关键日志：
- `ENTER_IN_GAME` / `LEAVE_IN_GAME`
- `JUNGLE_AUTO_START_TRIGGERED` / `JUNGLE_AUTO_STOP_TRIGGERED`
- `TAUNT_AUTO_TRIGGERED` / `TAUNT_AUTO_SENT` / `TAUNT_AUTO_SKIPPED`

## 10) 验收标准

通过标准：
- 进入对局后（`GameStart` 或 `InProgress`）打野检测自动开启，不需手动操作。
- 每局自动嘲讽最多一次，且在游戏内实际发送。
- 出游戏后自动关闭保持正常。
- 客户端重连/短暂断连后，下一次 phase 同步可恢复正确状态。
- 连续 5 局回归无“进游戏不启动/不发送”的复现。

失败判定：
- 任意一局出现 `GameStart` 导致自动 stop。
- 同一局重复自动嘲讽多次。
- 出游戏后监控未关闭。

## 11) 测试计划

单元测试：
- phase 分类函数覆盖全部枚举。
- `GameStart -> InProgress -> EndOfGame` 转移链路断言 start/stop/send 次数。
- `Reconnect` 场景下不误 stop。

集成测试（模拟事件）：
- 仅 `GameStart` 先到、`InProgress` 延迟到。
- `InProgress` 事件丢失但 session 轮询存在。
- LCU 短暂断连（连接拒绝）后恢复。

手工回归：
- 实机 5 局：排队、重开、重连、正常结束各场景至少覆盖一次。

