<template>
  <div class="select-view">
    <!-- 顶部标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <span class="header-icon">🎮</span>
        <h2>自动选人配置</h2>
      </div>
      <div class="header-right">
        <div class="toggle-card" :class="{ on: appStore.autoSelectEnabled }" @click="toggleAutoSelect">
          <span class="toggle-label">自动选人</span>
          <div class="toggle-switch">
            <div class="toggle-dot"></div>
          </div>
          <span class="toggle-status">{{ appStore.autoSelectEnabled ? 'ON' : 'OFF' }}</span>
        </div>
      </div>
    </div>
    
    <!-- 功能说明 -->
    <div class="feature-tips">
      <div class="tip-item">
        <span class="tip-icon">💡</span>
        <span>进入选人阶段后，将按列表顺序自动Ban/Pick英雄</span>
      </div>
      <div class="tip-item">
        <span class="tip-icon">🔄</span>
        <span>拖拽英雄可调整优先级顺序</span>
      </div>
    </div>
    
    <!-- 列表区域 -->
    <div class="lists-container">
      <!-- Ban 列表 -->
      <div class="list-card ban">
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">🚫</span>
            <span>Ban 列表</span>
          </div>
          <div class="header-badge">{{ configStore.banList.length }} 个英雄</div>
        </div>
        
        <div class="champion-list" :class="{ empty: !configStore.banList.length }">
          <TransitionGroup name="list">
            <div 
              v-for="(champId, idx) in configStore.banList" 
              :key="champId"
              class="champion-item"
              draggable="true"
              @dragstart="onDragStart($event, 'ban', idx)"
              @dragover.prevent
              @drop="onDrop($event, 'ban', idx)"
            >
              <div class="item-rank">{{ idx + 1 }}</div>
              <div class="item-avatar">
                <img v-if="getChampIcon(champId)" :src="getChampIcon(champId)" />
                <span v-else>{{ getChampionName(champId).charAt(0) }}</span>
              </div>
              <div class="item-info">
                <span class="item-name">{{ getChampionName(champId) }}</span>
              </div>
              <button class="item-remove" @click="removeChampion('ban', idx)">
                <span>×</span>
              </button>
            </div>
          </TransitionGroup>
          
          <div v-if="!configStore.banList.length" class="empty-state">
            <div class="empty-icon">🚫</div>
            <p>暂无Ban位英雄</p>
            <p class="empty-tip">添加你想禁用的英雄</p>
          </div>
        </div>
        
        <button class="add-button" @click="openSearch('ban')">
          <span class="add-icon">+</span>
          <span>添加英雄</span>
        </button>
      </div>
      
      <!-- Pick 列表 -->
      <div class="list-card pick">
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">✅</span>
            <span>Pick 列表</span>
          </div>
          <div class="header-badge">{{ configStore.pickList.length }} 个英雄</div>
        </div>
        
        <div class="champion-list" :class="{ empty: !configStore.pickList.length }">
          <TransitionGroup name="list">
            <div 
              v-for="(champId, idx) in configStore.pickList" 
              :key="champId"
              class="champion-item"
              draggable="true"
              @dragstart="onDragStart($event, 'pick', idx)"
              @dragover.prevent
              @drop="onDrop($event, 'pick', idx)"
            >
              <div class="item-rank">{{ idx + 1 }}</div>
              <div class="item-avatar">
                <img v-if="getChampIcon(champId)" :src="getChampIcon(champId)" />
                <span v-else>{{ getChampionName(champId).charAt(0) }}</span>
              </div>
              <div class="item-info">
                <span class="item-name">{{ getChampionName(champId) }}</span>
              </div>
              <button class="item-remove" @click="removeChampion('pick', idx)">
                <span>×</span>
              </button>
            </div>
          </TransitionGroup>
          
          <div v-if="!configStore.pickList.length" class="empty-state">
            <div class="empty-icon">🎯</div>
            <p>暂无Pick位英雄</p>
            <p class="empty-tip">添加你想选择的英雄</p>
          </div>
        </div>
        
        <button class="add-button" @click="openSearch('pick')">
          <span class="add-icon">+</span>
          <span>添加英雄</span>
        </button>
      </div>
    </div>
    
    <!-- 搜索弹窗 -->
    <Teleport to="body">
      <div class="search-modal" v-if="searchModal.show" @click.self="closeSearch">
        <div class="modal-content">
          <div class="modal-header">
            <h3>
              <span>{{ searchModal.type === 'ban' ? '🚫' : '✅' }}</span>
              添加到 {{ searchModal.type === 'ban' ? 'Ban' : 'Pick' }} 列表
            </h3>
            <button class="close-btn" @click="closeSearch">×</button>
          </div>
          
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input 
              ref="searchInput"
              v-model="searchKeyword" 
              placeholder="搜索英雄名称..."
            />
          </div>
          
          <div class="search-results">
            <div 
              v-for="champ in searchResults" 
              :key="champ.id"
              class="result-item"
              :class="{ disabled: isChampionInList(champ.id) }"
              @click="addChampion(champ.id)"
            >
              <div class="result-avatar">
                <img v-if="getChampIcon(champ.id)" :src="getChampIcon(champ.id)" />
                <span v-else>{{ champ.name.charAt(0) }}</span>
              </div>
              <div class="result-info">
                <span class="result-name">{{ champ.name }}</span>
                <span class="result-title">{{ champ.nameEn }}</span>
              </div>
              <span v-if="isChampionInList(champ.id)" class="result-tag">已添加</span>
              <span v-else class="result-add">+</span>
            </div>
            
            <div v-if="searchKeyword && !searchResults.length" class="no-results">
              未找到匹配的英雄
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useAppStore } from '@/stores/app'
import { useConfigStore } from '@/stores/config'
import { getChampionIcon } from '@/utils/ddragon'

const appStore = useAppStore()
const configStore = useConfigStore()

const searchModal = ref({ show: false, type: '' })
const searchKeyword = ref('')
const searchInput = ref(null)
let dragData = null

const searchResults = computed(() => {
  return configStore.searchChampions(searchKeyword.value).slice(0, 50)
})

function toggleAutoSelect() {
  appStore.setAutoSelect(!appStore.autoSelectEnabled)
}

function getChampionName(id) {
  return configStore.getChampionById(id)?.name || `ID:${id}`
}

function getChampIcon(id) {
  return getChampionIcon(id)
}

function isChampionInList(champId) {
  return configStore.banList.includes(champId) || configStore.pickList.includes(champId)
}

function openSearch(type) {
  searchModal.value = { show: true, type }
  searchKeyword.value = ''
  nextTick(() => searchInput.value?.focus())
}

function closeSearch() {
  searchModal.value.show = false
}

function addChampion(champId) {
  if (isChampionInList(champId)) return
  configStore.addChampion(searchModal.value.type, champId)
}

function removeChampion(type, idx) {
  configStore.removeChampion(type, idx)
}

function onDragStart(e, type, idx) {
  dragData = { type, idx }
  e.target.classList.add('dragging')
}

function onDrop(e, type, targetIdx) {
  if (!dragData || dragData.type !== type) return
  configStore.reorderChampion(type, dragData.idx, targetIdx)
  dragData = null
}
</script>

<style scoped>
.select-view {
  padding: var(--spacing-lg);
  height: 100%;
  overflow-y: auto;
}

/* 顶部标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.header-icon {
  font-size: 28px;
}

.page-header h2 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

/* 开关卡片 */
.toggle-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 16px;
  background: var(--bg-card);
  border-radius: 25px;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
}

.toggle-card:hover {
  background: var(--bg-hover);
  border-color: var(--border-color-light);
}

.toggle-card.on {
  border-color: var(--color-win);
  background: rgba(78, 204, 163, 0.1);
  box-shadow: var(--glow-win);
}

.toggle-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: var(--bg-secondary);
  border-radius: 12px;
  position: relative;
  transition: all 0.3s;
}

.toggle-card.on .toggle-switch {
  background: #4ecca3;
}

.toggle-dot {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: all 0.3s;
}

.toggle-card.on .toggle-dot {
  left: 22px;
}

.toggle-status {
  font-weight: 700;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  min-width: 30px;
}

.toggle-card.on .toggle-status {
  color: #4ecca3;
}

/* 功能提示 */
.feature-tips {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: rgba(200, 155, 60, 0.08);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--accent-secondary);
}

.tip-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.tip-icon {
  font-size: 14px;
}

/* 列表容器 */
.lists-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

/* 列表卡片 */
.list-card {
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.list-card.ban .card-header {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.15), transparent);
  border-bottom: 1px solid rgba(233, 69, 96, 0.2);
}

.list-card.pick .card-header {
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.15), transparent);
  border-bottom: 1px solid rgba(78, 204, 163, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-weight: 600;
  font-size: var(--font-size-md);
}

.title-icon {
  font-size: 18px;
}

.header-badge {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: 12px;
}

/* 英雄列表 */
.champion-list {
  flex: 1;
  min-height: 280px;
  max-height: 400px;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.champion-list.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.champion-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: grab;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.champion-item:hover {
  background: var(--bg-hover);
  border-color: var(--border-color);
}

.champion-item.dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.item-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-secondary);
  color: var(--bg-primary);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

.item-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-avatar span {
  font-weight: 600;
  color: var(--text-secondary);
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.item-remove {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--text-muted);
  border-radius: 6px;
  font-size: 18px;
  opacity: 0;
  transition: all 0.2s;
}

.champion-item:hover .item-remove {
  opacity: 1;
}

.item-remove:hover {
  background: rgba(233, 69, 96, 0.15);
  color: #e94560;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-sm);
  opacity: 0.3;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.empty-tip {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  margin-top: 4px;
}

/* 添加按钮 */
.add-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: 14px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  border-top: 1px solid var(--border-color);
  transition: all 0.2s;
}

.add-button:hover {
  background: var(--bg-hover);
  color: var(--accent-secondary);
}

.add-icon {
  font-size: 18px;
  font-weight: 300;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>

<style>
/* 搜索弹窗 */
.search-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-card);
  border-radius: 16px;
  width: 480px;
  max-height: 600px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--border-color);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 20px;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin: var(--spacing-md) var(--spacing-lg);
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--border-color);
}

.search-box:focus-within {
  border-color: var(--accent-secondary);
}

.search-icon {
  font-size: 16px;
  opacity: 0.5;
}

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.search-results {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--spacing-md) var(--spacing-md);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 4px;
}

.result-item:hover:not(.disabled) {
  background: var(--bg-hover);
}

.result-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.result-title {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.result-tag {
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.result-add {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-secondary);
  color: var(--bg-primary);
  border-radius: 6px;
  font-size: 18px;
  font-weight: 300;
  opacity: 0;
  transition: all 0.2s;
}

.result-item:hover:not(.disabled) .result-add {
  opacity: 1;
}

.no-results {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-muted);
}
</style>
