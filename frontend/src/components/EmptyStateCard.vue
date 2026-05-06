<template>
  <div class="empty-state-card" :class="type">
    <div class="empty-icon">{{ icon }}</div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-description">{{ description }}</p>

    <div v-if="actions.length" class="empty-actions">
      <button
        v-for="(action, index) in actions"
        :key="index"
        class="action-btn"
        :class="action.type || 'default'"
        @click="action.handler"
      >
        <span v-if="action.icon" class="action-icon">{{ action.icon }}</span>
        <span>{{ action.text }}</span>
      </button>
    </div>

    <div v-if="hints.length" class="empty-hints">
      <div v-for="(hint, index) in hints" :key="index" class="hint-item">
        <span class="hint-dot"></span>
        <span class="hint-text">{{ hint }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'empty',
  },
  icon: {
    type: String,
    default: '?',
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  actions: {
    type: Array,
    default: () => [],
  },
  hints: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.empty-state-card {
  min-height: 260px;
  padding: 32px 24px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,0.05);
  color: var(--text-secondary);
  font-size: 18px;
  font-weight: 900;
}

.empty-title {
  margin-top: 14px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}

.empty-description {
  margin-top: 8px;
  max-width: 520px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-secondary);
}

.empty-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.action-btn {
  height: 38px;
  padding: 0 14px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: var(--text-primary);
}

.action-btn.primary {
  color: #07131b;
  background: linear-gradient(135deg, #4ecca3 0%, #58a6ff 100%);
  border-color: transparent;
}

.empty-hints {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: min(100%, 520px);
}

.hint-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.05);
  text-align: left;
}

.hint-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  margin-top: 6px;
  background: rgba(78,204,163,0.8);
  flex-shrink: 0;
}

.hint-text {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.empty-state-card.error .empty-icon {
  color: #ff9aa8;
  background: rgba(233,69,96,0.12);
}
</style>
