<template>
  <div class="battle-pagination">
    <div class="page-summary">
      <span>共 {{ total }} 场</span>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
    </div>

    <div class="page-actions">
      <button :disabled="page <= 1" @click="$emit('page-change', page - 1)">上一页</button>
      <button :disabled="page >= totalPages" @click="$emit('page-change', page + 1)">下一页</button>
      <select :value="pageSize" @change="$emit('page-size-change', Number($event.target.value))">
        <option :value="10">10 / 页</option>
        <option :value="20">20 / 页</option>
        <option :value="50">50 / 页</option>
      </select>
    </div>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
})

defineEmits(['page-change', 'page-size-change'])
</script>

<style scoped>
.battle-pagination { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.page-summary { display: flex; gap: 8px; flex-wrap: wrap; color: var(--text-secondary); font-size: 12px; }
.page-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
button,select { height: 36px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--border-color); background: rgba(255, 255, 255, 0.04); color: var(--text-primary); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
