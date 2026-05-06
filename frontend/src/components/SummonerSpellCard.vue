<script setup>
// 召唤师技能卡片组件
// 展示召唤师技能图标、胜率和登场率
import { getSpellIcon } from '@/utils/ddragon'

defineProps({
  spell: {
    type: Object,
    required: true,
    // spell 结构: { spell_ids: number[], play: number, win: number, pick_rate: number }
  },
})
</script>

<template>
  <div class="spell-card">
    <!-- 召唤师技能图标 -->
    <div class="spell-icons">
      <img
        v-if="spell.spell_ids?.[0]"
        :src="getSpellIcon(spell.spell_ids[0])"
        :alt="`召唤师技能 ${spell.spell_ids[0]}`"
        class="spell-icon"
        loading="lazy"
        decoding="async"
        @error="(e) => (e.target.style.display = 'none')"
      />
      <span class="spell-plus">+</span>
      <img
        v-if="spell.spell_ids?.[1]"
        :src="getSpellIcon(spell.spell_ids[1])"
        :alt="`召唤师技能 ${spell.spell_ids[1]}`"
        class="spell-icon"
        loading="lazy"
        decoding="async"
        @error="(e) => (e.target.style.display = 'none')"
      />
    </div>
    <!-- 统计数据 -->
    <div class="spell-meta">
      <div class="wr-bar">
        <div
          class="wr-fill"
          :style="{ width: spell.play ? (spell.win / spell.play * 100) + '%' : '0%' }"
        />
      </div>
      <span class="spell-stats">
        {{ spell.play ? (spell.win / spell.play * 100).toFixed(1) : '0.0' }}%
        <span class="spell-games">({{ spell.play || 0 }}场)</span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.spell-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.spell-icons {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.spell-icon {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid #1e293b;
  object-fit: cover;
}

.spell-plus {
  color: #334155;
  font-size: 12px;
}

.spell-meta {
  flex: 1;
  min-width: 0;
}

.wr-bar {
  height: 4px;
  background: #1e293b;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 2px;
}

.wr-fill {
  height: 100%;
  background: #4ECCB3;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.spell-stats {
  font-size: 11px;
  color: #94a3b8;
}

.spell-games {
  color: #475569;
}
</style>
