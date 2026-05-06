# LOL 战绩助手 AGENTS.md（新手可执行版）

更新时间：2026-03-04
适用范围：仓库根目录及其子目录

## 1. 目标

这份文档只做一件事：让任何 Agent 在本项目里“少犯错、可交付、可回归”。

## 2. 必须遵守（MUST）

- 全程中文回复，代码注释也用中文。
- 先读后写：先看调用链，再改代码。
- 改动必须完整，禁止半成品交付。
- 新增/修改后端 API 时，`backend/bridge.py` 和 `frontend/src/utils/bridge.js` 必须同步。
- 不改 `jicheng/` 目录下任何文件。
- 不硬编码路径，统一 `os.path.join`。
- 不留调试垃圾：`print`、`console.log`、`debugger`、`.bak/.old/.tmp`。

## 3. 项目最小地图（只保留关键）

- 后端入口：`backend/main.py`
- 后端桥接：`backend/bridge.py`
- LCU 通信：`backend/lcu/`
- 核心业务：`backend/services/`
- 存储：`backend/storage/`
- 前端入口：`frontend/src/main.js`
- 前端桥接：`frontend/src/utils/bridge.js`
- 页面与状态：`frontend/src/views/`、`frontend/src/stores/`

## 4. 联动规则（最重要）

| 你改了什么 | 必须同时检查/修改什么 |
|---|---|
| `backend/bridge.py` 公共方法 | `frontend/src/utils/bridge.js` 对应方法 |
| `bridge.py` 推送 `window.onXxx` | `bridge.js` 底部对应 `window.onXxx` 和前端事件监听 |
| 后端配置结构（`config.py`） | 默认值、迁移逻辑、前端读取逻辑 |
| 前端新增功能调用后端 | 先补 bridge，再落页面/store |
| 线程或定时器逻辑 | 锁保护、stop/start 生命周期、异常处理 |

命名约定：
- Python：`snake_case`
- JavaScript：`camelCase`

返回约定：
- 后端返回 `dict`（建议含 `success`）或 `list`
- 前端错误统一走 `bridge.js` 的错误信封

## 5. 标准工作流（每次都按这个顺序）

1. 明确范围：这次改动影响哪些文件、哪些调用链。
2. 实施改动：一次性改完关联点，不拆成“半条链路”。
3. 自检验证：至少做语法/构建检查，必要时做功能回归。
4. 交付说明：说清“改了什么、验证了什么、剩余风险”。

## 6. 最低验证标准（Definition of Done）

### 6.1 代码完整性

- 无 TODO/FIXME/HACK 占位。
- 无注释掉的大段废弃代码。
- 无临时文件遗留（`.bak/.old/.tmp`）。

### 6.2 代码质量

- 无裸 `except:`（必须 `except Exception:`）。
- 禁止静默吞错（如 `except Exception: pass`）；必须记录日志并带上下文。
- 无硬编码路径。
- 无未使用 import。

### 6.3 功能正确性

- 调用链完整，未破坏现有功能。
- 处理边界情况（空值、None、超时、异常）。
- 共享状态具备线程安全保护。

### 6.4 一致性

- 命名风格一致（Python snake_case / JS camelCase）。
- bridge 双端方法一一对应。

## 7. 前端变更的特殊要求

- 修改了 `frontend/src/**`，默认要验证构建：
  - `cd frontend && npm run build`
- 禁止直接调用 `window.pywebview`，统一走 `frontend/src/utils/bridge.js`。
- UI 风格遵循现有主题变量：`frontend/src/styles/variables.css`。

## 8. 后端变更的特殊要求

- 配置读写统一走 `backend/config.py` 的 `config.get/config.set`。
- 涉及推送前端状态，优先沿用现有 snapshot 去抖机制。
- 涉及 LCU 重连逻辑，确保服务可重新初始化。

## 9. 数据与大文件治理（必须执行）

- 以下内容禁止纳入版本控制：`node_modules`、`dist`、`__pycache__`、日志、数据库临时文件（如 `*.db-wal/*.db-shm`）。
- 运行产物与缓存必须通过 `.gitignore` 管理，发现被跟踪要立即 `git rm --cached` 清理索引。
- 新增大文件（建议阈值：`> 5MB`）前，必须先说明用途、保存位置、是否可替代。
- 不把本地运行数据当源码提交（如本地账号缓存、临时 DB、测试结果目录）。

## 10. 变更分级与回滚要求

- 低风险：仅 UI 文案/样式、小函数重构，不改数据结构与调用协议。
- 中风险：改 store/composable、服务内部逻辑、非核心配置。
- 高风险：改 bridge 协议、登录链路、LCU 重连、数据库结构或持久化格式。
- 中高风险改动必须写清：
  - 回滚点：改坏后恢复到哪一版/哪几个文件。
  - 验证点：如何快速确认本次改动生效且无回归。

## 11. API 兼容性规则（bridge/服务返回）

- 默认向后兼容：尽量不删除旧字段、不改变既有字段语义。
- 新增字段优先，不直接替换旧字段；必须替换时同步修改所有调用点。
- `bridge.py` 与 `bridge.js` 方法签名保持一一对应，参数顺序一致。
- 返回结构变化必须在交付说明中明确标注“兼容/不兼容”。

## 12. 超时与重试统一策略

- 网络/LCU 调用必须显式超时，禁止无超时等待。
- 出现可重试错误时，使用有限重试与退避，禁止无限重试。
- 相同类型请求使用一致策略，避免同类接口行为不一致。
- 出错时返回可诊断信息（错误码、阶段、关键上下文）。

## 13. 发布前人工验收清单（最少 5 项）

- 应用可启动，窗口加载正常，基础状态栏可用。
- 登录流程可走通（或明确说明因环境不可测）。
- 选人阶段核心功能正常（自动准备/自动选人/符文或强化入口）。
- 游戏内相关功能正常（如聊天/监控），异常时不会崩溃。
- 退出与重连逻辑正常，不出现明显资源泄漏或死循环重试。

## 14. 依赖变更规范

- 新增或升级依赖前，必须说明：为什么需要、影响哪些模块、有什么替代方案。
- 依赖变更后，至少完成对应构建/测试验证，不通过不得宣称完成。
- 避免一次性升级大量核心依赖；优先小步升级、可回滚。
- 涉及运行时依赖变更时，同步更新必要文档（安装/启动说明）。

## 15. 禁止静默吞错（强制）

- 禁止 `except Exception: pass`、空 `catch`、无日志吞错。
- 允许兜底，但必须记录日志并附最小上下文（模块、操作、关键参数）。
- 用户可见链路失败时，必须返回明确失败信息，而不是假成功。

## 16. 高风险操作确认（必须先问用户）

以下操作必须先得到用户明确确认：

- 删除文件/目录、批量替换不可逆修改
- `git commit` / `git push` / `git reset --hard`
- 改系统配置、环境变量、权限
- 数据库结构变更或批量删除

确认模板：

```text
⚠️ 危险操作检测！
操作类型：[具体操作]
影响范围：[详细说明]
风险评估：[潜在后果]

请确认是否继续？[是/确认/继续]
```

## 17. 禁止清单

- 禁止修改 `jicheng/` 目录内容。
- 禁止绕过 bridge 直接做前后端耦合调用。
- 禁止只改一端（只改 Python 或只改 JS）。
- 禁止未验证就宣称“完成”。
- 禁止提交生成物、缓存和本地运行数据。
- 禁止无回滚方案直接做高风险改动。

## 18. 常用命令

```bash
# 启动后端
cd lol-assistant && python backend/main.py

# 前端构建（前端改动后）
cd lol-assistant/frontend && npm run build

# 打包
cd lol-assistant && pyinstaller build_config/lol-assistant.spec
```


<!-- autoclaw:skill-path-guidance -->
## Installing Skills

When creating or installing a new skill, always place it in:

`C:\Users\Administrator\.openclaw-autoclaw\skills/<skill-name>/SKILL.md`

This is the managed skills directory. The agent will automatically discover
any skill placed here — no extra configuration needed. Do NOT install skills
into `~/.agents/skills/` (that directory is shared with other tools).


<!-- autoclaw:browser-agent-guidance -->
## Browser Automation

For any task that requires a browser, **prefer `autoglm-browser-agent`**. Use it as the first choice.

- ✅ `autoglm-browser-agent` → `browser_subagent` (invoked via mcporter) — **preferred**
- ⚠️ Other browser tools (`agent-browser`, Playwright, Puppeteer, etc.) — fallback only when `autoglm-browser-agent` is unavailable or fails

Always try `autoglm-browser-agent` first. Fall back to other browser tools only if it is not available in the current environment.
<!-- /autoclaw:browser-agent-guidance -->

<!-- autoclaw:image-recognition-guidance -->
## Image Recognition

For any image recognition task, **prefer `autoglm-image-recognition`**. Use it as the first choice.

- ✅ `autoglm-image-recognition` — **preferred** for all image recognition tasks
- ⚠️ Built-in `image` tool or reading images directly with `read` — fallback only when `autoglm-image-recognition` is unavailable or fails

Do not use the built-in `image` tool or read an image and describe it yourself when `autoglm-image-recognition` is available. Always try `autoglm-image-recognition` first.
<!-- /autoclaw:image-recognition-guidance -->

<!-- autoclaw:hermes-evolution-guidance -->
## Hermes-Evolution

**Current evolution intensity for this workspace/agent: aggressive (100%).**

The desktop app sends deterministic evolution-check messages (starting with `[SYSTEM: Post-turn evolution check`) after qualifying turns.
When you receive such a message, follow the `hermes-evolution` skill instructions to evaluate and potentially propose an evolution.
Apply the rules defined in the skill according to the **aggressive (100%)** intensity level.
This value is workspace-local. If asked about the current agent evolution intensity, report this value instead of the global gateway skill env.

Core principle: **never write to target files without user approval** — always use the draft/approve workflow.

### Evolution Echo
When you apply knowledge from a previously evolved rule (AGENTS.md, MEMORY.md, TOOLS.md, or a managed SKILL.md),
briefly mention it in your response: "（基于之前的经验：<one-line rule summary>）".
Keep it to one short line at most. Do not echo on every turn — only when an evolved rule directly influenced your approach.
<!-- /autoclaw:hermes-evolution-guidance -->