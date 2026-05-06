---
inclusion: fileMatch
fileMatchPattern: "frontend/**"
---

# 前端开发规范

## 关键提醒

任何前端文件修改后，必须执行 `cd frontend && npm run build`，否则 pywebview 加载的是旧的 `frontend/dist/`。

## 编码规范

- 组件使用 Vue 3 `<script setup>` + scoped CSS
- 状态管理使用 Pinia（stores/app.js, match.js, config.js）
- 组合式函数放 `composables/`（useRunesData, useAugmentsData, useFavorites, useUserPreferences）
- 后端调用统一通过 `utils/bridge.js`，不要直接访问 `window.pywebview`
- 资源 URL 通过 `utils/ddragon.js` 获取
- 格式化工具在 `utils/format.js`

## UI/UX 规范

- 暗色主题，背景 `#0d1117`，卡片 `#21262d`
- 主色：绿 `#4ecca3`、红 `#e94560`、蓝 `#58a6ff`、金 `#ffd700`
- 字体：Microsoft YaHei，字号 11-32px
- CSS 变量定义在 `styles/variables.css`
- 布局：左侧 Sidebar 图标导航 + 底部 StatusBar + 中间内容区
- 所有文案使用中文

## 目录结构

```
frontend/src/
├── views/           # 页面：Login, Match, Runes, Augments, Select, Analysis, Jungle, History, Settings, Enhancements
├── components/      # 可复用组件
│   ├── layout/      # 布局组件（Sidebar, StatusBar）
│   └── match/       # 战绩相关组件（PlayerCard, LiveGamePanel, OverviewBar, RadarChart, DetailTabs）
│       └── tabs/    # 详情 Tab 页（TabHighlights, TabDataOverview, TabMyPerformance 等）
├── composables/     # 组合式函数（useRunesData, useAugmentsData, useFavorites, useUserPreferences）
├── stores/          # Pinia 状态（app, match, config）
├── utils/           # bridge.js, ddragon.js, format.js
├── data/            # 静态数据（champions.js, runes.js, augments.js, summonerSpells.js）
├── directives/      # 自定义指令（lazyLoad.js）
├── router/          # 路由定义（hash 模式）
└── styles/          # variables.css, global.css
```
