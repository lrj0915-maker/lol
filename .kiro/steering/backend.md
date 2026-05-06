---
inclusion: fileMatch
fileMatchPattern: "backend/**"
---

# 后端开发规范

## 关键提醒

新增后端 API 方法时，必须同时在 `bridge.py` 和 `frontend/src/utils/bridge.js` 添加对应方法。

## 架构

```
backend/
├── main.py              # 入口，pywebview 窗口创建
├── bridge.py            # 前后端桥接，所有 API 方法
├── config.py            # 配置管理（原子写、深合并、版本迁移）
├── logger.py            # 统一日志模块（get_logger）
├── lcu/                 # LCU 客户端通信层
│   ├── connection.py    # 连接管理（lockfile 解析、端口/token）
│   ├── api.py           # REST API 封装
│   └── events.py        # WebSocket 事件订阅
├── services/            # 业务服务层
│   ├── login_service.py         # Win32 自动化登录
│   ├── account_manager.py       # 多账号 CRUD
│   ├── auto_accept.py           # 自动准备
│   ├── auto_select.py           # 自动选人/禁用
│   ├── match_history.py         # 战绩追踪
│   ├── team_analyzer.py         # 队伍分析
│   ├── scoring.py               # 共享评分模块（player_score/rank/match_stats）
│   ├── chat_sender.py           # 选人阶段聊天
│   ├── ingame_chat.py           # 游戏内 AHK 聊天
│   ├── runes_data_service.py    # 符文数据（OP.GG）
│   ├── rune_manager.py          # 符文应用到客户端
│   ├── augments_updater.py      # 强化数据（OP.GG）
│   ├── jungle_monitor.py        # 野怪 OCR 监控（主用，RapidOCR + AudioManager）
│   ├── jungle_monitor_tesseract.py  # 野怪监控（Tesseract 备用）
│   ├── jungle_monitor_rapidocr_backup.py  # 野怪监控（RapidOCR 备用方案）
│   ├── jungle_alert.py          # 野怪提醒逻辑
│   ├── audio_manager.py         # 语音提醒（pygame.mixer）
│   └── audio/                   # 音频资源
├── scripts/             # 辅助脚本
│   ├── region_select.py     # 大区选择
│   ├── send_chat.ahk        # AHK 聊天脚本
│   └── send_team_chat.ahk   # AHK 队伍聊天脚本
├── storage/             # 数据持久化
│   ├── database.py      # SQLite 操作
│   └── models.py        # 数据模型
└── data/                # 运行时数据
    ├── config.json      # 后端配置副本
    └── jungle_cache.txt # 野怪识别缓存
```

## 编码规范

- 使用 `os.path.join` 拼接路径，不要硬编码
- 配置读写通过 `config.py` 的 `config.get()` / `config.set()`
- 配置使用原子写（tempfile + os.replace）
- Bridge 方法返回 dict（含 success 字段）或 list
- 线程安全：`window.evaluate_js()` 可从任意线程调用
- Snapshot 推送使用 `_schedule_runtime_snapshot_push()` 去抖

## 已知坑

1. Win32 64 位签名：SendMessageW 必须声明 `argtypes = [c_void_p, c_uint, c_ulonglong, c_void_p]`，`restype = c_longlong`
2. 登录器隐藏窗口：SendMessage 在 SW_HIDE 后仍有效，但需先 SW_RESTORE 让控件初始化
3. LCU 重连：客户端重启后必须 `init_services(force=True)`
4. Snapshot 去抖：Timer 合并高频事件，避免前端被淹没
5. 配置原子写：`tempfile + os.replace` 防写入中断损坏

## 外部依赖

### jicheng 登录器
- 路径：`../jicheng/`（Bridge 计算：`os.path.join(os.path.dirname(project_root), 'jicheng')`）
- 登录器.exe 必须以 jicheng 目录为 CWD 启动
- 28 个大区，0 索引（皮城警备 = 18）
- 不要修改 jicheng 目录下的任何文件

### OP.GG API
- 符文：`https://lol-api-champion.op.gg/api/KR/champions/ranked`
- 有频率限制，需控制请求间隔

### LCU API
- 通过 lockfile 获取端口和 token
- 客户端重启后端口/token 会变，需重连
