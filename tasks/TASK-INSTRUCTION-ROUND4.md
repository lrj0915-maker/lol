# Round 4 任务指令
**Supervisor**: 代可行 👔
**Created**: 2026-05-05 18:40 GMT+8
**范围**: 仅符文页面相关改动

---

## 为什么停下来了

上一轮你的 `edit` 工具报错："Could not find the exact text"。原因是文件内容在你读取之后被其他操作修改过，`oldText` 匹配不上了。

**解决方案**：edit 之前先用 `read` 确认文件当前内容，找到精确的 oldText 再 edit。

---

## 你现在要做的（Round 4）

**本轮范围：仅符文页面相关改动。召唤师技能、技能加点 UI 不做。**

### 任务 A: 修 `Promise.all` 缺少 await（P0-2）

**文件**: `frontend/src/views/RunesView.vue`

1. 先 `read` 这个文件，搜索 `Promise.all`
2. 找到没有 `await` 的那一行，改成 `await Promise.all([...])`

当前已知的模式：
```typescript
// 找到这一行（没有 await）：
Promise.all([
  refreshRunesStatus(),
  ensureCurrentPositionData(),
  loadChampionOverview(),
])

// 改成：
await Promise.all([
  refreshRunesStatus(),
  ensureCurrentPositionData(),
  loadChampionOverview(),
])
```

**注意**：可能有多个 Promise.all，确认是在 `loadData` 函数内的是要改的那一个。

---

### 任务 B: 加符文登场率 pick_rate 显示（P0-5）

**文件**: `frontend/src/components/RuneConfigCard.vue`

1. 先 `read` 这个文件
2. 在卡片的 header 区域（PopularityBadge 附近）加一行显示 pick_rate

具体位置：在模板里找 `<PopularityBadge` 或 `:games=` 那一行，在附近加：
```vue
<span class="pick-rate" v-if="config.pick_rate">
  {{ (config.pick_rate * 100).toFixed(1) }}% 登场
</span>
```

3. 在 `<style scoped>` 里加：
```css
.pick-rate {
  font-size: 11px;
  color: #94a3b8;
  margin-left: 4px;
}
```

**注意**：如果文件中已经有 pick-rate 相关代码，先确认是否已实现，再决定是否需要加。

---

### 任务 C: 删前端数据里的 raw 副本（P1-3）

**文件**: `frontend/src/composables/useRunesData.js`

1. 先 `read` 这个文件
2. 找 `normalizeRunePages` 函数，看有没有在每个 item 上加 `raw` 字段
3. 如果有，删掉 `raw` 相关代码

模式大概是：
```javascript
// 删掉这样的代码：
normalized.push({
  ...item,
  raw: item,  // ← 删除这行
})
```

同时检查 `normalizeItemGroup` 函数，有同样问题也删。

---

### 任务 D: 确认 runes.json 存储结构（不修改后端）

读取 `data/runes.json` 的前 50 行，确认：
- `rune_pages` 里的每个 page 有没有 `raw` 字段
- `runes` 字段是否存在（如果存在，说明后端还没清理）

把这部分信息记录到 PROGRESS.md：
```
### 数据现状检查
- runes.json 大小: X MB
- rune_pages.raw 字段: 存在/不存在
- runes 字段: 存在/不存在
```

---

## 执行顺序

1. 先做 **任务 A**（Promise.all await）
2. 做 **任务 B**（pick_rate 显示）
3. 做 **任务 C**（删前端 raw）
4. 做 **任务 D**（确认数据现状）
5. 写汇报

---

## 注意事项

- 每个 edit 之前必须先 read 文件
- 不要修改召唤师技能或技能加点相关内容
- 做完不要停，等下一轮指令
- 报告格式照旧

---

## 完成后汇报

```
✅ Round 4 完成

[修改的文件]
- frontend/src/views/RunesView.vue (Promise.all await)
- frontend/src/components/RuneConfigCard.vue (pick_rate 显示)
- frontend/src/composables/useRunesData.js (删 raw)
- tasks/PROGRESS.md (数据现状)

[验证]
- [x] Promise.all 已有 await
- [x] pick_rate 已在卡片显示
- [x] 前端已删 raw 副本
- [x] runes.json 数据现状已记录

[下一轮任务]
- TASK-05 后端去重（删除 runes/skill_masteries/raw_fields 字段）
```
