# LOL 设置锁定功能设计

## 1. 功能概述

让用户在不同账号之间切换时，自动保持相同的键位、鼠标、界面等设置。

## 2. 目标文件

用户当前游戏设置已保存在：

```
E:\WeGameApps\英雄联盟\.settings_template\
  ├─ PersistedSettings.json  (键位、鼠标、操作习惯)
  ├─ input.ini               (键位绑定)
  └─ game.cfg               (画面、声音、性能)
```

## 3. 功能设计

### 3.1 配置项（config.py）

```python
DEFAULT_CONFIG = {
    # ...现有配置...
    "settings_lock": {
        "enabled": False,
        "auto_restore": True,
        "target_path": "",  # 用户可自定义，默认为 LOL 安装目录
    },
}
```

### 3.2 触发时机

| 时机 | 动作 |
|------|------|
| 登录成功（`_on_login_success`） | 自动恢复设置 |
| 选人阶段开始（`ChampSelect`） | 兜底检查恢复 |
| 游戏阶段（`InProgress`） | 可选兜底 |

### 3.3 后端实现

#### 3.3.1 设置文件操作

- `save_current_settings()`: 从游戏目录复制当前设置到 `.settings_template`
- `restore_settings()`: 从 `.settings_template` 恢复到游戏目录
- `get_settings_template_info()`: 获取模板文件信息

#### 3.3.2 触发逻辑

在 `_on_login_success` 和 `on_runtime_state_event` 中添加检测：

1. 检查 `config.get('settings_lock.enabled')`
2. 如果开启，检查当前账号是否与上次不同
3. 执行 `restore_settings()`

#### 3.3.3 路径检测

- 检测 LOL 游戏路径：`detect_game_path()`
- 设置模板目录：游戏目录下的 `.settings_template`

### 3.4 前端实现

#### 3.4.1 设置界面

在 `SettingsView.vue` 新增设置区块：

```
设置锁定
  ├─ [开关] 启用设置锁定
  ├─ [路径显示] 游戏目录（自动检测）
  ├─ [按钮] 立即保存当前设置
  ├─ [按钮] 立即恢复设置
  └─ [状态] 上次保存时间
```

#### 3.4.2 bridge.js 扩展

```javascript
// 设置锁定
getSettingsLockConfig()
setSettingsLockConfig(enabled, autoRestore)
saveCurrentSettings()
restoreSettings()
getSettingsTemplateInfo()
```

## 4. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/config.py` | 修改 | 新增 `settings_lock` 配置项 |
| `backend/bridge.py` | 修改 | 新增设置保存/恢复方法 + 触发逻辑 |
| `frontend/src/utils/bridge.js` | 修改 | 新增 bridge 方法 |
| `frontend/src/views/SettingsView.vue` | 修改 | 新增设置界面区块 |
| `docs/plans/YYYY-MM-DD-settings-lock-design.md` | 新增 | 本设计文档 |

## 5. 触发流程图

```
用户登录 → _on_login_success
       ↓
检查 settings_lock.enabled == True?
       ↓ 是 → 检查账号是否变化
              ↓ 变化 → restore_settings()
              ↓ 相间 → 跳过
       ↓ 否 → 不处理
```

## 6. 兼容性

- 默认关闭，不影响现有功能
- 自动检测游戏路径
- 恢复失败时记录日志，不阻塞登录流程