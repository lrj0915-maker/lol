<template>
  <section class="battle-panel battle-panel-hero">
    <div class="panel-head">
      <div>
        <div class="panel-title">英雄使用</div>
        <div class="panel-subtitle">最近 20 场英雄分布与效率</div>
      </div>
      <div class="panel-tip">最近 20 场</div>
    </div>

    <div v-if="heroes.length" class="hero-list">
      <button
        v-for="hero in heroes"
        :key="hero.champion_id"
        class="hero-item"
        :class="{ active: activeChampionId === hero.champion_id }"
        @click="$emit('select', hero)"
      >
        <img v-if="getChampionIcon(hero.champion_id)" :src="getChampionIcon(hero.champion_id)" class="hero-icon" :alt="hero.champion_name" />
        <div v-else class="hero-icon placeholder">无</div>

        <div class="hero-meta">
          <div class="hero-top-row">
            <div class="hero-name">{{ hero.champion_name }}</div>
            <div class="hero-kda numeric">{{ hero.avg_kda }} KDA</div>
          </div>
          <div class="hero-bottom-row">
            <span class="hero-stat numeric">{{ hero.games }} 场</span>
            <span class="hero-stat numeric">{{ hero.wins }} 胜</span>
            <span class="hero-stat hero-winrate numeric">{{ hero.win_rate }}%</span>
          </div>
          <div class="hero-bar">
            <div class="hero-bar-fill" :style="{ width: `${Math.min(Number(hero.win_rate || 0), 100)}%` }"></div>
          </div>
        </div>
      </button>
    </div>

    <div v-else class="empty-tip empty-block">暂无可展示的英雄统计</div>
  </section>
</template>

<script setup>
import { getChampionIcon } from '@/utils/ddragon'
defineProps({ heroes: { type: Array, default: () => [] }, activeChampionId: { type: Number, default: null } })
defineEmits(['select'])
</script>

<style scoped>
.battle-panel { position: relative; padding: 14px; border-radius: 16px; background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.02)); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 12px 28px rgba(0,0,0,.18); overflow: hidden; }
.battle-panel::before { content: ''; position: absolute; inset: 0 0 auto 0; height: 2px; background: linear-gradient(90deg, rgba(255,184,77,.78), rgba(78,204,163,.58)); opacity: .92; }
.battle-panel::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at top right, rgba(78,204,163,.08), transparent 34%); pointer-events: none; }
.panel-head,.hero-list,.empty-block { position: relative; z-index: 1; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.panel-title { font-size: 16px; font-weight: 800; color: var(--text-primary); }
.panel-subtitle { margin-top: 2px; font-size: 11px; color: var(--text-secondary); }
.panel-tip,.empty-tip { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 999px; font-size: 12px; color: var(--text-secondary); background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.06); }
.hero-list { display: flex; flex-direction: column; gap: 8px; }
.hero-item { display: grid; grid-template-columns: 42px 1fr; gap: 10px; align-items: center; width: 100%; min-height: 68px; padding: 10px; border: 1px solid transparent; border-radius: 12px; background: rgba(255,255,255,.03); color: inherit; cursor: pointer; text-align: left; transition: all .18s ease; }
.hero-item:hover { transform: translateY(-1px); border-color: rgba(255,255,255,.12); background: rgba(255,255,255,.05); }
.hero-item.active { border-color: rgba(78,204,163,.42); background: linear-gradient(90deg, rgba(78,204,163,.14), rgba(88,166,255,.08)); box-shadow: inset 3px 0 0 rgba(78,204,163,.9), 0 10px 24px rgba(78,204,163,.08); }
.hero-icon { width: 42px; height: 42px; border-radius: 12px; object-fit: cover; }
.hero-icon.placeholder { display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.04); color: var(--text-secondary); font-weight: 700; }
.hero-meta { min-width: 0; display: grid; gap: 5px; }
.hero-top-row,.hero-bottom-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.hero-name { font-weight: 700; color: var(--text-primary); }
.hero-kda { font-size: 12px; color: var(--accent-secondary); font-weight: 700; }
.hero-stat { font-size: 11px; color: var(--text-secondary); }
.hero-winrate { color: var(--text-primary); font-weight: 700; }
.hero-bar { height: 6px; border-radius: 999px; background: rgba(255,255,255,.06); overflow: hidden; }
.hero-bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #4ecca3, #58a6ff); }
.numeric { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
</style>
