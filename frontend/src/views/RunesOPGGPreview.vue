<template>
  <div class="opgg-preview-page">
    <header class="hero">
      <div class="hero-left">
        <div class="breadcrumb">OP.GG / League of Legends / Champions / Darius / Build / Top</div>
        <h1>Darius Build</h1>
        <p class="subtitle">完整符文页前端设计稿预览：符文、技能、装备、对局、趋势、克制与协同一体化展示</p>
      </div>
      <div class="hero-right">
        <div class="hero-stats">
          <div v-for="stat in heroStats" :key="stat.label" class="stat-card">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
          </div>
        </div>
      </div>
    </header>

    <section class="toolbar">
      <div class="pill-group">
        <button v-for="mode in modes" :key="mode" class="pill" :class="{ active: mode === activeMode }" @click="activeMode = mode">{{ mode }}</button>
      </div>
      <div class="pill-group">
        <button v-for="tier in tiers" :key="tier" class="pill" :class="{ active: tier === activeTier }" @click="activeTier = tier">{{ tier }}</button>
      </div>
      <div class="pill-group">
        <button v-for="patch in patches" :key="patch" class="pill" :class="{ active: patch === activePatch }" @click="activePatch = patch">{{ patch }}</button>
      </div>
    </section>

    <section class="content-grid">
      <main class="main-column">
        <article class="panel accent">
          <div class="panel-head">
            <h2>Runes</h2>
            <span class="meta">Highest Win Rate / Pick Rate</span>
          </div>

          <div class="rune-summary">
            <div class="rune-ring">
              <div class="ring-value">40.84%</div>
              <div class="ring-label">8,619 Games</div>
            </div>
            <div class="rune-primary">
              <div class="tree-title">Precision</div>
              <div class="rune-list">
                <div v-for="r in primaryTree" :key="r" class="rune-chip">{{ r }}</div>
              </div>
            </div>
            <div class="rune-secondary">
              <div class="tree-title">Sorcery</div>
              <div class="rune-list">
                <div v-for="r in secondaryTree" :key="r" class="rune-chip soft">{{ r }}</div>
              </div>
            </div>
            <div class="rune-shards">
              <div class="tree-title">Shards</div>
              <div class="rune-list">
                <div v-for="r in shards" :key="r" class="rune-chip neutral">{{ r }}</div>
              </div>
            </div>
          </div>

          <div class="build-cards">
            <div v-for="build in runeBuilds" :key="build.id" class="build-card">
              <div class="build-top">
                <div class="build-rate">{{ build.winRate }}</div>
                <div class="build-pick">{{ build.pickRate }} · {{ build.games }} Games</div>
              </div>
              <div class="build-body">
                <div class="build-tree">
                  <div class="build-tree-title">{{ build.primary }}</div>
                  <div class="build-tree-runes">{{ build.primaryRunes.join(' · ') }}</div>
                </div>
                <div class="build-tree muted-block">
                  <div class="build-tree-title">{{ build.secondary }}</div>
                  <div class="build-tree-runes">{{ build.secondaryRunes.join(' · ') }}</div>
                </div>
                <div class="build-tree muted-block">
                  <div class="build-tree-title">Stat Modifiers</div>
                  <div class="build-tree-runes">{{ build.shards.join(' · ') }}</div>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <h2>Summoner Spells</h2>
            <span class="meta">Top combinations</span>
          </div>
          <div class="spell-list">
            <div v-for="spell in summonerSpells" :key="spell.label" class="spell-card">
              <div class="spell-icons">{{ spell.icons }}</div>
              <div>
                <div class="spell-label">{{ spell.label }}</div>
                <div class="spell-meta">{{ spell.games }} Games · {{ spell.winRate }}</div>
              </div>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <h2>Skill Order</h2>
            <span class="meta">Most popular skill path</span>
          </div>
          <div class="skill-order">
            <div v-for="item in skillOrders" :key="item.order" class="skill-card">
              <div class="skill-seq">{{ item.order }}</div>
              <div class="skill-meta">{{ item.games }} Games · {{ item.winRate }}</div>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <h2>Items</h2>
            <span class="meta">Starter / Boots / Core / Depth items</span>
          </div>
          <div class="item-sections">
            <section class="item-block">
              <h3>Starter Items</h3>
              <div class="item-row" v-for="item in itemSections.starter" :key="item.label">
                <span class="item-name">{{ item.label }}</span>
                <span class="item-games">{{ item.games }} Games</span>
                <span class="item-rate">{{ item.winRate }}</span>
              </div>
            </section>
            <section class="item-block">
              <h3>Boots</h3>
              <div class="item-row" v-for="item in itemSections.boots" :key="item.label">
                <span class="item-name">{{ item.label }}</span>
                <span class="item-games">{{ item.games }} Games</span>
                <span class="item-rate">{{ item.winRate }}</span>
              </div>
            </section>
            <section class="item-block wide">
              <h3>Core Builds</h3>
              <div class="core-builds">
                <div v-for="item in itemSections.core" :key="item.label" class="core-card">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.pickRate }}</span>
                  <small>{{ item.games }} Games · {{ item.winRate }}</small>
                </div>
              </div>
            </section>
            <section class="item-block wide">
              <h3>Depth Items</h3>
              <div class="depth-grid">
                <div v-for="item in itemSections.depth" :key="item.label" class="depth-card">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.games }} Games</span>
                  <small>{{ item.winRate }}</small>
                </div>
              </div>
            </section>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head">
            <h2>Counters & Synergies</h2>
            <span class="meta">Weak / Strong / Team synergy</span>
          </div>
          <div class="split-grid">
            <div class="split-card">
              <h3>Weak against</h3>
              <div v-for="counter in weakAgainst" :key="counter.name" class="counter-row">
                <span>{{ counter.name }}</span>
                <strong>{{ counter.rate }}</strong>
                <small>{{ counter.games }} Games</small>
              </div>
            </div>
            <div class="split-card">
              <h3>Strong against</h3>
              <div v-for="counter in strongAgainst" :key="counter.name" class="counter-row">
                <span>{{ counter.name }}</span>
                <strong>{{ counter.rate }}</strong>
                <small>{{ counter.games }} Games</small>
              </div>
            </div>
            <div class="split-card">
              <h3>Synergies</h3>
              <div class="synergy-tags">
                <span v-for="tag in synergies" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </article>
      </main>

      <aside class="side-column">
        <article class="panel side-panel">
          <div class="panel-head">
            <h2>Trend</h2>
            <span class="meta">Win / Pick / Ban</span>
          </div>
          <div class="trend-list">
            <div v-for="trend in trends" :key="trend.version" class="trend-row">
              <span class="trend-version">{{ trend.version }}</span>
              <div class="trend-bars">
                <div class="trend-bar win" :style="{ width: trend.win }"></div>
                <div class="trend-bar pick" :style="{ width: trend.pick }"></div>
                <div class="trend-bar ban" :style="{ width: trend.ban }"></div>
              </div>
            </div>
          </div>
        </article>

        <article class="panel side-panel">
          <div class="panel-head">
            <h2>Pages</h2>
            <span class="meta">OP.GG route groups</span>
          </div>
          <div class="route-cards">
            <div class="route-card active">Build</div>
            <div class="route-card">Runes</div>
            <div class="route-card">Items</div>
            <div class="route-card">Counters</div>
            <div class="route-card">Jungle paths</div>
            <div class="route-card">Skills</div>
            <div class="route-card">Trends</div>
            <div class="route-card">Masters Build</div>
          </div>
        </article>

        <article class="panel side-panel">
          <div class="panel-head">
            <h2>What to Crawl</h2>
            <span class="meta">Selected by page module</span>
          </div>
          <div class="checklist">
            <label v-for="task in crawlChecklist" :key="task.id" class="check-row">
              <input type="checkbox" v-model="task.checked" />
              <span>{{ task.label }}</span>
            </label>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeMode = ref('Ranked Solo/Duo')
const activeTier = ref('Emerald +')
const activePatch = ref('16.09')

const modes = ['Ranked Solo/Duo', 'Ranked Flex', 'ARAM', 'Arena']
const tiers = ['Challenger', 'Master +', 'Diamond +', 'Emerald +', 'Platinum +']
const patches = ['16.09', '16.08', '16.07']

const heroStats = [
  { label: 'Win rate', value: '49.44%' },
  { label: 'Pick rate', value: '6.55%' },
  { label: 'Ban rate', value: '13.33%' },
  { label: 'Tier', value: 'T3 #21' },
]

const primaryTree = ['Press the Attack', 'Triumph', 'Legend: Alacrity', 'Last Stand']
const secondaryTree = ['Nimbus Cloak', 'Celerity']
const shards = ['Attack Speed', 'Adaptive Force', 'Health']

const runeBuilds = [
  {
    id: 1,
    winRate: '53.79%',
    pickRate: '35.92%',
    games: '5,622',
    primary: 'Precision',
    primaryRunes: ['Press the Attack', 'Triumph', 'Legend: Alacrity', 'Last Stand'],
    secondary: 'Sorcery',
    secondaryRunes: ['Nimbus Cloak', 'Celerity'],
    shards: ['Attack Speed', 'Adaptive Force', 'Health'],
  },
  {
    id: 2,
    winRate: '48.91%',
    pickRate: '28.55%',
    games: '6,025',
    primary: 'Precision',
    primaryRunes: ['Conqueror', 'Triumph', 'Legend: Alacrity', 'Last Stand'],
    secondary: 'Resolve',
    secondaryRunes: ['Second Wind', 'Unflinching'],
    shards: ['Attack Speed', 'Adaptive Force', 'Health'],
  },
  {
    id: 3,
    winRate: '50.29%',
    pickRate: '24.66%',
    games: '5,204',
    primary: 'Resolve',
    primaryRunes: ['Grasp of the Undying', 'Shield Bash', 'Conditioning', 'Overgrowth'],
    secondary: 'Precision',
    secondaryRunes: ['Triumph', 'Last Stand'],
    shards: ['Attack Speed', 'Adaptive Force', 'Health'],
  },
]

const summonerSpells = [
  { label: 'Flash + Ghost', icons: 'F + G', games: '16,590', winRate: '49.45%' },
  { label: 'Flash + Teleport', icons: 'F + T', games: '3,479', winRate: '49.58%' },
]

const skillOrders = [
  { order: 'W Q E Q Q R ...', games: '5,622', winRate: '53.79%' },
  { order: 'W E Q Q Q R ...', games: '2,976', winRate: '54.44%' },
  { order: 'Q W E Q Q R ...', games: '2,809', winRate: '52.43%' },
]

const itemSections = {
  starter: [
    { label: 'Doran + Potion', games: '13,519', winRate: '50.29%' },
    { label: 'Shield + Potion', games: '7,281', winRate: '47.66%' },
  ],
  boots: [
    { label: 'Plated Steelcaps', games: '11,845', winRate: '49.51%' },
    { label: 'Mercury Treads', games: '5,908', winRate: '48.80%' },
  ],
  core: [
    { label: 'Stridebreaker / Black Cleaver', pickRate: '7.90%', games: '1,026', winRate: '60.33%' },
    { label: 'Trinity / Sterak', pickRate: '6.41%', games: '832', winRate: '63.46%' },
    { label: 'Triforce / Hullbreaker', pickRate: '5.64%', games: '732', winRate: '56.28%' },
    { label: 'Stridebreaker / Hullbreaker', pickRate: '4.68%', games: '608', winRate: '57.40%' },
  ],
  depth: [
    { label: 'Fourth item', games: '1,150', winRate: '57.83%' },
    { label: 'Fifth item', games: '237', winRate: '59.49%' },
    { label: 'Sixth item', games: '7', winRate: '71.43%' },
  ],
}

const weakAgainst = [
  { name: 'Cassiopeia', rate: '34.09%', games: '44' },
  { name: 'Malzahar', rate: '36.00%', games: '50' },
  { name: 'Heimerdinger', rate: '37.70%', games: '122' },
]

const strongAgainst = [
  { name: 'Poppy', rate: '58.43%', games: '89' },
  { name: 'Shen', rate: '56.42%', games: '358' },
  { name: 'Xin Zhao', rate: '55.48%', games: '146' },
]

const synergies = ['Jungle', 'Mid', 'ADC', 'Support']

const trends = [
  { version: '16.09', win: '49.4%', pick: '6.5%', ban: '13.3%' },
  { version: '16.08', win: '50.2%', pick: '7.0%', ban: '14.6%' },
  { version: '16.07', win: '50.1%', pick: '7.1%', ban: '14.7%' },
]

const crawlChecklist = [
  { id: 'runePages', label: '符文主组合与 builds', checked: true },
  { id: 'summonerSpells', label: '召唤师技能', checked: true },
  { id: 'skillOrder', label: '技能加点', checked: true },
  { id: 'items', label: '装备区（出门 / 鞋子 / 核心 / 深度）', checked: true },
  { id: 'counters', label: '克制关系', checked: true },
  { id: 'synergies', label: '英雄协同', checked: true },
  { id: 'trends', label: '版本趋势', checked: true },
  { id: 'masters', label: '大师排行 / Pro builds', checked: false },
]
</script>

<style scoped>
.opgg-preview-page {
  min-height: 100%;
  padding: 24px;
  background: linear-gradient(180deg, #08111f 0%, #0a0e1a 100%);
  color: #e2e8f0;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 24px;
  border: 1px solid #1e293b;
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.9);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
}

.hero h1 {
  margin: 8px 0 10px;
  font-size: 34px;
}

.breadcrumb,
.subtitle,
.meta,
.item-games,
.item-rate,
.skill-meta,
.spell-meta,
.trend-version,
.check-row,
.route-card,
.counter-row small {
  color: #94a3b8;
  font-size: 12px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
}

.stat-card,
.panel,
.route-card,
.spell-card,
.skill-card,
.item-block,
.split-card,
.core-card,
.depth-card {
  border: 1px solid #1e293b;
  background: #0f172a;
  border-radius: 16px;
}

.stat-card {
  padding: 14px;
  min-width: 120px;
}

.stat-card span,
.stat-card strong {
  display: block;
}

.stat-card strong {
  margin-top: 6px;
  font-size: 20px;
  color: #f8fafc;
}

.toolbar,
.panel-head,
.pill-group,
.build-top,
.build-body,
.spell-card,
.skill-card,
.counter-row,
.item-row,
.route-card,
.check-row {
  display: flex;
  align-items: center;
}

.toolbar {
  justify-content: space-between;
  gap: 12px;
  margin: 18px 0;
  flex-wrap: wrap;
}

.pill {
  border: 1px solid #243244;
  background: #0f172a;
  color: #cbd5e1;
  padding: 10px 14px;
  border-radius: 999px;
  cursor: pointer;
}

.pill.active {
  background: #4eccb3;
  color: #06111b;
  border-color: #4eccb3;
  font-weight: 700;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
}

.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel {
  padding: 18px;
}

.panel-head {
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel h2,
.item-block h3,
.split-card h3 {
  margin: 0;
}

.accent {
  background: linear-gradient(180deg, rgba(78, 204, 179, 0.08), rgba(15, 23, 42, 0.96));
}

.rune-summary {
  display: grid;
  grid-template-columns: 200px 1fr 1fr 1fr;
  gap: 16px;
}

.rune-ring {
  display: grid;
  place-items: center;
  min-height: 180px;
  border-radius: 18px;
  border: 1px solid rgba(78, 204, 179, 0.35);
  background: radial-gradient(circle at center, rgba(78, 204, 179, 0.12), rgba(15, 23, 42, 0.95));
}

.ring-value {
  font-size: 30px;
  font-weight: 800;
}

.tree-title {
  margin-bottom: 10px;
  font-size: 14px;
  color: #f8fafc;
  font-weight: 700;
}

.rune-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.rune-chip {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(78, 204, 179, 0.14);
  border: 1px solid rgba(78, 204, 179, 0.3);
  color: #d1fae5;
}

.rune-chip.soft {
  background: rgba(96, 165, 250, 0.12);
  border-color: rgba(96, 165, 250, 0.25);
}

.rune-chip.neutral {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.24);
}

.build-cards,
.spell-list,
.skill-order,
.item-sections,
.split-grid,
.route-cards,
.checklist,
.depth-grid,
.core-builds {
  display: grid;
  gap: 12px;
}

.build-cards {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 18px;
}

.build-card,
.spell-card,
.skill-card,
.core-card,
.depth-card {
  padding: 14px;
}

.build-rate {
  font-size: 20px;
  font-weight: 800;
  color: #4eccb3;
}

.build-pick {
  color: #94a3b8;
  font-size: 12px;
}

.build-body {
  margin-top: 10px;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}

.muted-block {
  opacity: 0.85;
}

.spell-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.skill-order {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.item-sections {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.item-block.wide {
  grid-column: span 2;
}

.item-row,
.counter-row {
  justify-content: space-between;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(30, 41, 59, 0.75);
}

.item-row:last-child,
.counter-row:last-child {
  border-bottom: none;
}

.core-builds {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.depth-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.split-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(78, 204, 179, 0.12);
  border: 1px solid rgba(78, 204, 179, 0.24);
}

.side-panel .route-cards {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.route-card {
  justify-content: center;
  min-height: 44px;
}

.route-card.active {
  background: rgba(78, 204, 179, 0.16);
  color: #d1fae5;
  border-color: rgba(78, 204, 179, 0.4);
}

.checklist {
  grid-template-columns: 1fr;
}

.check-row {
  gap: 10px;
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trend-bars {
  display: flex;
  gap: 6px;
}

.trend-bar {
  height: 8px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.trend-bar.win { background: #4eccb3; }
.trend-bar.pick { background: #60a5fa; }
.trend-bar.ban { background: #fb7185; }

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero,
  .rune-summary,
  .build-cards,
  .spell-list,
  .skill-order,
  .item-sections,
  .split-grid,
  .core-builds,
  .depth-grid,
  .side-column {
    grid-template-columns: 1fr;
    display: grid;
  }

  .item-block.wide {
    grid-column: auto;
  }

  .hero {
    flex-direction: column;
  }
}
</style>
