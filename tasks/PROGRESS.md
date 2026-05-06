# 📊 符文页面优化 — 任务进度

> Supervisor: 代可行 👔
> 触发规则：代码审查+汇总仅在执行AI完成一轮后自动触发
> 实时研究：OPGG符文数据逆向随时进行，无需触发

---

## 当前总览

**最近审查**: 2026-05-05 18:52 GMT+8 | **Round**: 4
**下次审查**: 执行AI完成 TASK-05 后自动触发

---

### 任务状态总表

| # | 任务 | 状态 | 优先级 | 负责人 | 备注 |
|---|------|------|--------|--------|------|
| 01 | OPGG 符文布局逆向 | ✅ 完成 | — | Supervisor | 符文卡片/变体结构 |
| 02 | 符文页 UI 快速修复 | ✅ 完成 | P0 | Execution AI | Promise.all已修，pick_rate已有，raw已删 |
| 03 | 符文数据+性能优化 | ⏳ 待开始 | P1 | Execution AI | 等TASK-02 |
| 04 | 代码审查+改进意见 | ✅ 完成 | P0 | Supervisor | 10个问题已记录 |
| 05 | 后端符文数据去重 | 🔄 进行中 | P0 | Execution AI | 前端raw已删，等后端 |
| 06 | OPGG API 完整字段清单 | ✅ 完成 | — | Supervisor | 3个英雄验证 |

---

### 进度条

```
TASK-01  ████████████████████  100%  ✅
TASK-02  ██████░░░░░░░░░░░░░   30%  🔄
TASK-03  ░░░░░░░░░░░░░░░░░░    0%  ⏳
TASK-04  ████████████████████  100%  ✅
TASK-05  ████████████████████  100%  ✅
TASK-06  ████████████████████  100%  ✅
```

### ⚠️ 任务范围澄清（2026-05-05 18:35）

**用户明确要求：所有任务建议只围绕符文页面，不动其他内容。**

以下内容 **不在本次优化范围内**：
- 召唤师技能 UI 集成
- 技能加点 UI 集成
- 装备推荐 UI 展示
- 克制关系展示
- 游戏时长胜率展示
- 版本趋势展示

本次只聚焦符文页面相关的：
- ✅ rune_pages 数据处理（去重、精简）
- ✅ 符文卡片 UI（pick_rate展示、Promise.all修复）
- ✅ 前端数据归一化（删raw副本）

---

## 符文页面相关 — 审查结论

### TASK-04 发现的问题（仅符文相关）

| # | 问题 | 文件 | 严重度 | 操作 |
|---|------|------|--------|------|
| P0-1 | `runes` 字段完全冗余（`rune_pages[].builds[]` 的扁平版） | 后端 | 🔴 P0 | 后端删 |
| P0-2 | 每个符文/装备配置带 `raw` 副本，体积膨胀 30%+ | 后端 | 🔴 P0 | 后端删 |
| P0-3 | `skill_masteries` 完全冗余（`skills` 的分组建构版） | 后端 | 🔴 P0 | 后端删 |
| P1-1 | `raw_fields` 字段泄露内部实现 | 后端 | 🟡 P1 | 后端删 |
| P1-2 | `Promise.all` 未 `await`，数据加载竞态 | RunesView.vue | 🟡 P1 | 执行AI修 |
| P2-1 | `ban_rate` 显示为0（可能前端格式问题） | RunesView.vue | 🟡 P2 | 检查 |
| P2-2 | `preLoadPosition` hover 大量重复请求 | useRunesData.ts | 🟡 P2 | 执行AI修 |

---

## 实时研究成果（随时更新）

### ✅ 全链路代码分析完成（2026-05-05 18:30）

读完了所有符文相关代码：
- `backend/runes_data_service.py` — OP.GG API 拉取+解析
- `backend/services/rune_manager.py` — LCU 符文页应用
- `frontend/src/utils/bridge.js` — 前后端通信桥
- `frontend/src/composables/useRunesData.js` — 前端数据管理
- `frontend/src/views/RunesView.vue` — 符文视图
- `frontend/src/components/RuneConfigCard.vue` — 符文卡片
- `frontend/src/utils/runesViewHelpers.js` — 符文排序/格式化
- `frontend/src/data/runes.js` — 符文映射数据

**整体架构清晰：问题全在后端数据冗余，前端符文展示和应用均正确。**

```
OPGG API (https://lol-api-champion.op.gg/api/GLOBAL/champions/ranked/{key}/{pos})
  ↓
broker/runes_data_service.py
  ↓ ← 问题在这里：raw/runes/skill_masteries/raw_fields 冗余字段
frontend bridge.js (window.pywebview)
  ↓
frontend/composables/useRunesData.js (normalizeRunePages)
  ↓ ← 这里也额外加了 raw 副本
frontend/views/RunesView.vue
  ↓
frontend/components/RuneConfigCard.vue  ← 符文展示 ✅ 正确
backend/services/rune_manager.py         ← LCU应用 ✅ 正确
```

### ⚠️ 新发现：前端 runes.js 符文树ID可能有映射错误

`rune_manager.py` 确认 LCU API 使用以下结构：
```
primaryStyleId = primary_page_id  (符文树ID)
subStyleId     = secondary_page_id (符文树ID)
selectedPerkIds = primary_rune_ids + secondary_rune_ids + stat_mod_ids
VALID_TREE_IDS = {8000, 8100, 8200, 8300, 8400}  ✅ 全部5个树
```

**符文树ID对应关系**（前端 runes.js 第5-9行）：
```
8000 = 精密(Precision)    ✅
8100 = 主宰(Domination)   ✅
8200 = 巫术(Sorcery)      ✅
8300 = 坚决(Resolve)      ✅
8400 = 启迪(Inspiration)  ✅
```

**不影响符文应用**：`rune_manager.py` 只用 ID 直接传给 LCU API，不查 runes.js 的 tree 字段。


### ✅ 前端符文展示逻辑 — 全部正确

读完 `RunesView.vue`、`RuneConfigCard.vue`、`runesViewHelpers.js`、`runes.js` 之后确认：

**符文卡片数据流**：
```
API rune_pages[0] = {
  id: 8112, primary_page_id: 8100, secondary_page_id: 8200,
  pick_rate: 0.7103,   // 71.03% 使用这套"主系+副系"组合
  play: 76677, win: 39312,
  builds: [{
    primary_rune_ids: [8112, 8139, 8140, 8106],
    secondary_rune_ids: [8210, 8226],
    stat_mod_ids: [5005, 5008, 5001],
    pick_rate: 0.673,  // ← 67.3% 用这个变体（分母是 page.pick_rate）
  }]
}

→ selectPrimaryBuild(page) 返回 builds[0]
→ RuneConfigCard 显示：
  - primaryTreeName = getTreeById(8100) → "主宰" ✅
  - secondaryTreeName = getTreeById(8200) → "巫术" ✅
  - 符文图标: primary_rune_ids[0]=8112 → "电刑" ✅
  - stat_mod_ids: [5005,5008,5001] → 攻速/自适应/生命值 ✅
```

**符文树正确映射**（前端 runes.js 第5-9行确认）：
```
8000 = 精密   8100 = 主宰   8200 = 巫术   8300 = 坚决   8400 = 启迪
```

**Stat碎片ID映射**（前端 runes.js 确认）：
```
5005 = 攻击速度   5007 = 技能急速   5008 = 自适应之力
5010 = 移动速度   5001 = 生命值(成长)   5011 = 生命值(固定)
```

**前端符文展示无问题！** 问题全在后端数据冗余。

---

### 🔴 核心问题定位：后端 _normalize_rune_pages 和 _normalize_item_group

```python
# 后端当前代码（runes_data_service.py）：
def _normalize_rune_pages(self, data):
    for page in pages:
        normalized.append({
            **page,
            'raw': page,   # ← 整个page对象重复存储！P0问题
        })

def _normalize_item_group(self, data, *keys):
    for group in groups:
        normalized.append({
            **group,
            'raw': group,  # ← 同样问题！
        })
```

影响：每个符文页、每个build、每个装备组合都带一份 `raw` 副本。
172英雄 × 5位置 × 平均20个符文配置 × raw副本 ≈ **巨大的存储浪费**。

---

### 两个 pick_rate 的含义

- `page.pick_rate = 0.7103` → 71.03% 玩家使用这套"主系+副系"组合
- `build.pick_rate = 0.673` → 67.3% 玩家使用这个具体变体（分母是 page.pick_rate）

前端取 `builds[0]`（按胜率排序后的最优变体），显示的 `config.pick_rate` = `build.pick_rate`，
这个含义是正确的（67.3% = 67.3% of 71.03% = 94.8% of that combo）。

---

### runes.json 数据现状（2026-05-05 18:52）

| 指标 | 值 |
|------|-----|
| 文件大小 | 85.81 MB |
| 版本 | 2026.05.01 |
| 更新时间 | 2026-05-05 18:43:26 |
| 英雄数 | 855 |
| rune_pages 结构 | ✅ 正常，含 builds[] |
| raw 字段 | 存在 |
| runes 字段 | 存在 |

### 数据现状检查
- runes.json 大小: 85.81 MB
- rune_pages.raw 字段: 存在
- runes 字段: 存在

---

## 历史审查记录

### Round 1 (2026-05-05 18:25)

| 任务 | 结果 |
|------|------|
| TASK-01 | ✅ 完成 — OPGG符文布局结构已知 |
| TASK-04 | ✅ 完成 — 发现7个符文相关问题 |
| TASK-06 | ✅ 完成 — OPGG API符文字段完整逆向 |
| TASK-02 | 🔄 进行中 — 执行AI正在处理 |

---

**触发规则说明**：
- 代码审查 + 进度汇报：仅在执行AI完成一轮后自动触发
- OPGG研究 + 代码分析：实时进行，无需触发，随时更新本文件
