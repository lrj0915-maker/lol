<template>
  <div v-if="message" class="page-status-banner" :class="tone">
    <span class="banner-dot"></span>
    <span>{{ message }}</span>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: '',
  },
  tone: {
    type: String,
    default: 'info',
  },
})
</script>

<style scoped>
.page-status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
  font-size: 12px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.2);
}

.banner-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.9;
}

.page-status-banner.info {
  color: var(--text-secondary);
}

.page-status-banner.success {
  color: #7de3bf;
}

.page-status-banner.warning {
  color: #ffcc77;
}

.page-status-banner.error {
  color: #ff9aa8;
}
</style>
