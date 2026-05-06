---
inclusion: manual
---

# 功能模块数据流

手动引用此文件了解各功能的完整数据流。

## 登录流程

```
LoginView 输入账号密码 → bridge.start_login()
  → Bridge.start_login() → AccountManager 自动保存
  → LoginService._do_login() [后台线程]
    → 杀残留进程 → 启动登录器.exe（CWD=jicheng/）
    → Win32 SendMessage 填写控件 → 点击登录
    → 监控：检测验证码窗口 / RiotClient / LeagueClient
  → 成功 → Bridge.connect() → LCU 连接
  → 前端轮询 get_login_status → 成功后跳转 /match
```

## 符文推荐

```
ChampSelect → runtime snapshot → App.vue 跳转 /runes
  → RunesView → useRunesData composable
    → IndexedDB 缓存(30min) → 命中直接用
    → 未命中 → bridge.getRunesEntry(championId, position)
      → RunesDataService → data/runes.json → 返回配置列表
  → 用户点击"应用" → bridge.apply_rune_config() → RuneManager → LCU API
```

## 队伍分析

```
ChampSelect → TeamAnalyzerService 自动触发
  → LCU API 获取双方玩家 → 批量查战绩 → 计算评分
  → evaluate_js('window.onTeamAnalysis(...)') → AnalysisView
  → 可选：ChatSenderService 自动发送到聊天
```

## 自动准备/选人

```
LCU WebSocket /lol-matchmaking/v1/ready-check → AutoAcceptService → 自动接受
LCU WebSocket /lol-champ-select/v1/session → AutoSelectService → 自动选人/禁用
```

## 野怪监控

```
JungleView 启动 → JungleMonitor 截屏 + OCR
  → 检测到野怪文字 → AudioManager 语音提醒 / AHK 发送聊天
```

## 数据存储

| 存储 | 位置 | 用途 |
|------|------|------|
| config.json | data/ | 应用配置（原子写、深合并、版本迁移） |
| accounts.json | data/ | 登录账号（密码 base64 编码） |
| runes.json | data/ | OP.GG 符文数据缓存 |
| augments.json | data/ | OP.GG 强化数据缓存 |
| history.db | data/ | SQLite 战绩记录 |
| config.json | backend/data/ | 后端运行时配置副本 |
| jungle_cache.txt | backend/data/ | 野怪 OCR 识别缓存 |
| IndexedDB | 浏览器 | 前端符文/强化 30 分钟缓存 |
