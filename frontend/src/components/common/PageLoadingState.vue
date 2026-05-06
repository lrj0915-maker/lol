<template>
  <div class="page-loading-state">
    <div class="loading-spinner"></div>
    <div class="loading-title">{{ title }}</div>
    <div v-if="description" class="loading-description">{{ description }}</div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '加载中',
  },
  description: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.page-loading-state {
  min-height: 240px;
  display: grid;
  place-items: center;
  padding: 24px;
  text-align: center;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 3px solid rgba(255,255,255,0.12);
  border-top-color: rgba(88,166,255,0.9);
  animation: spin 0.9s linear infinite;
}

.loading-title {
  margin-top: 14px;
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
}

.loading-description {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
