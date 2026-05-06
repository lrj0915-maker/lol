# TASK-05: 后端符文数据去重 + 精简
**Status**: ✅ DONE
**File**: `backend/services/runes_data_service.py`
**Lines**: 563-651
**Supervisor**: 代可行 👔
**Created**: 2026-05-05 18:25 GMT+8
**Focus**: 仅符文页面相关字段，其他不动

---

## 问题清单

### 🔴 P0 — 必须修复

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| P0-1 | `raw: page` 副本在每个符文页里 | backend/runes_data_service.py `_normalize_rune_pages` | 每个符文配置体积翻倍 |
| P0-2 | `raw: group` 副本在每个装备组里 | backend/runes_data_service.py `_normalize_item_group` | 装备数据体积膨胀 |
| P0-3 | `runes[]` 字段完全冗余（`rune_pages[].builds[]` 的扁平版） | backend `_parse_position_data` | ~30% 额外存储 |
| P0-4 | `skill_masteries[]` 字段完全冗余（`skills[]` 的分组版） | backend `_parse_position_data` | 额外存储 |

### 🟡 P1 — 建议修复

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| P1-1 | `raw_fields` 字段泄露内部实现信息 | backend `_parse_position_data` | 安全/信息泄露 |
| P1-2 | 前端 `normalizeRunePages` 也加了 `raw: page` | frontend useRunesData.js | 内存浪费 |

---

## 具体修改点

### 后端 runes_data_service.py

#### 1. 删除 `_normalize_rune_pages` 中的 `raw: page`

```python
# 修改前（当前）：
def _normalize_rune_pages(self, data):
    for page in pages:
        normalized.append({
            **page,
            'raw': page,   # ← 删掉
        })

# 修改后：
def _normalize_rune_pages(self, data):
    for page in pages:
        builds = page.get('builds') if isinstance(page.get('builds'), list) else []
        normalized.append({
            'id': page.get('id'),
            'primary_page_id': page.get('primary_page_id'),
            'secondary_page_id': page.get('secondary_page_id'),
            'play': page.get('play', 0),
            'win': page.get('win', 0),
            'pick_rate': page.get('pick_rate', 0),
            'builds': builds,
            # 不要再加 'raw': page
        })
```

#### 2. 删除 `_normalize_item_group` 中的 `raw: group`

```python
# 修改前（当前）：
def _normalize_item_group(self, data, *keys):
    for group in groups:
        normalized.append({
            **group,
            'raw': group,  # ← 删掉
        })

# 修改后：
def _normalize_item_group(self, data, *keys):
    for group in groups:
        normalized.append({
            'ids': group.get('ids', []),
            'play': group.get('play', 0),
            'win': group.get('win', 0),
            'pick_rate': group.get('pick_rate', 0),
            # 不要再加 'raw': group
        })
```

#### 3. 删除 `_parse_position_data` 中的冗余字段

```python
# 删除这些行：
'runes': flat_runes or rune_pages,           # ← 删掉
'skill_masteries': self._first_list(data, 'skill_masteries'),  # ← 删掉
'raw_fields': sorted(list(data.keys())),     # ← 删掉
```

保留：
```python
return {
    'schema_version': 'opgg-ranked-v2',
    'source': 'opgg-ranked-api',
    'source_version': api_meta.get('version'),
    'source_cached_at': api_meta.get('cached_at'),
    'rune_pages': rune_pages,         # ← 保留（唯一符文数据来源）
    'summoner_spells': self._first_list(data, 'summoner_spells'),
    'core_items': core_items,
    'items': core_items,
    'boots': boots,
    'starter_items': starter_items,
    'last_items': last_items,
    'skills': self._first_list(data, 'skills'),
    'counters': self._first_list(data, 'counters'),
    'game_lengths': self._first_list(data, 'game_lengths'),
    'trends': data.get('trends', {}),
    # 不再返回 runes / skill_masteries / raw_fields
}
```

---

### 前端 useRunesData.js

#### 删除 `normalizeRunePages` 和 `normalizeItemGroup` 中的 `raw`

```javascript
// 修改前：
function normalizeRunePages(source) {
    return candidates.map((page) => {
        const builds = Array.isArray(page.builds) && page.builds.length ? page.builds : [page]
        return {
            ...page,
            builds,
            raw: page.raw || page,  // ← 删掉
        }
    })
}

function normalizeItemGroup(source) {
    return candidates.map((item) => {
        return {
            ids: Array.isArray(item.ids) ? item.ids : ...,
            play: Number(item.play || 0),
            win: Number(item.win || 0),
            pick_rate: Number(item.pick_rate || 0),
            raw: item,  // ← 删掉
        }
    })
}

// 修改后：去掉 raw 字段即可
```

---

## 收益估算

| 操作 | 节省空间 |
|------|---------|
| 删 `raw`（符文页） | ~50% rune_pages 体积 |
| 删 `raw`（装备） | ~30% 装备数据体积 |
| 删 `runes[]` | ~20% 总数据体积 |
| 删 `skill_masteries[]` | ~5% 总数据体积 |
| 删 `raw_fields` | ~1KB/英雄 |

**总计**：数据文件体积预计减少 **40-50%**

---

## 注意事项

1. **删字段不影响前端**：前端只用 `rune_pages`，`runes` 从未被直接使用
2. **需要重建数据**：修改后要重新运行 `scripts/fetch_runes.py` 或触发全量刷新
3. **前端也同步删**：useRunesData.js 的 `normalizeRunePages` 也要同步删 raw，否则前端缓存里还有
4. **不需要改 rune_manager.py**：LCU API 只用符文ID，不依赖这些字段

---

**Status Log**:
- [2026-05-05 19:16] [TASK-05] Status: ✅ DONE — 后端去重验证完成。_parse_position_data 已删除 runes、skill_masteries、raw_fields 字段；_normalize_rune_pages 和 _normalize_item_group 不再添加 raw 副本；flat_runes 仅作为 fallback 保留在 _normalize_rune_pages 中（当 rune_pages 为空时使用）。
- [2026-05-05 18:25] [TASK-05] Created — 后端符文数据去重任务清单
- [2026-05-05 18:25] 确认前端符文展示逻辑正确（runes.js/RuneConfigCard 无问题）
- [2026-05-05 18:25] 发现前端 useRunesData.js 也有 raw 冗余，需同步修复
