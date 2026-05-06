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

async function toggleAutoSelect() {
  const next = !appStore.autoSelectEnabled
  await appStore.setAutoSelect(next)
  if (next && !appStore.autoSelectOneShot) {
    await appStore.setAutoSelectOneShot(true)
  }
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
  animation: pageEnter 0.5s ease;
  position: relative;
}

.select-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 250px;
  background: radial-gradient(ellipse at top center, rgba(78, 204, 163, 0.06) 0%, transparent 60%);
  pointer-events: none;
  z-index: 0;
}

@keyframes pageEnter {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

/* 顶部标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.header-icon {
  font-size: 36px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.page-header h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 开关卡片 */
.toggle-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 14px 24px;
  background: var(--gradient-card);
  border-radius: 28px;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.toggle-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%);
  transition: left 0.5s ease;
}

.toggle-card:hover {
  background: var(--bg-hover);
  border-color: var(--border-color-light);
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.toggle-card:hover::before {
  left: 100%;
}

.toggle-card.on {
  border-color: var(--color-win);
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.25) 0%, rgba(78, 204, 163, 0.1) 100%);
  box-shadow: 0 0 40px rgba(78, 204, 163, 0.3), var(--shadow-lg);
  animation: toggleGlow 2s ease-in-out infinite;
}

@keyframes toggleGlow {
  0%, 100% { box-shadow: 0 0 30px rgba(78, 204, 163, 0.25), var(--shadow-lg); }
  50% { box-shadow: 0 0 45px rgba(78, 204, 163, 0.4), var(--shadow-lg); }
}

.toggle-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.toggle-switch {
  width: 48px;
  height: 26px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-radius: 13px;
  position: relative;
  transition: all 0.3s;
  border: 1px solid var(--border-color);
}

.toggle-card.on .toggle-switch {
  background: linear-gradient(135deg, #4ecca3 0%, #3db892 100%);
  border-color: transparent;
  box-shadow: 0 0 15px rgba(78, 204, 163, 0.4);
}

.toggle-dot {
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, #fff 0%, #e0e0e0 100%);
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.toggle-card.on .toggle-dot {
  left: 24px;
}

.toggle-status {
  font-weight: 700;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  min-width: 32px;
  transition: all var(--transition-fast);
}

.toggle-card.on .toggle-status {
  color: #4ecca3;
  text-shadow: 0 0 10px rgba(78, 204, 163, 0.5);
}

/* 功能提示 */
.feature-tips {
  display: flex;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(90deg, rgba(78, 204, 163, 0.12) 0%, rgba(88, 166, 255, 0.08) 100%);
  border-radius: var(--border-radius-lg);
  border-left: 4px solid var(--accent-secondary);
  box-shadow: var(--shadow-md), 0 0 30px rgba(78, 204, 163, 0.1);
  position: relative;
  z-index: 1;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tip-item:hover {
  color: var(--text-primary);
  transform: translateX(4px);
}

.tip-icon {
  font-size: 18px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

/* 列表容器 */
.lists-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  position: relative;
  z-index: 1;
}

/* 列表卡片 */
.list-card {
  background: var(--gradient-card);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-normal);
  position: relative;
  animation: cardEnter 0.5s ease backwards;
}

.list-card:first-child { animation-delay: 0.1s; }
.list-card:last-child { animation-delay: 0.2s; }

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.list-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
}

.list-card:hover {
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-xl), 0 0 50px rgba(0, 0, 0, 0.25);
  transform: translateY(-4px);
}

.list-card.ban::before {
  background: var(--gradient-lose);
  box-shadow: 0 0 20px rgba(233, 69, 96, 0.4);
}

.list-card.ban .card-header {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.25) 0%, transparent 100%);
  border-bottom: 1px solid rgba(233, 69, 96, 0.3);
}

.list-card.pick::before {
  background: var(--gradient-win);
  box-shadow: 0 0 20px rgba(78, 204, 163, 0.4);
}

.list-card.pick .card-header {
  background: linear-gradient(135deg, rgba(78, 204, 163, 0.25) 0%, transparent 100%);
  border-bottom: 1px solid rgba(78, 204, 163, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: 600;
  font-size: var(--font-size-md);
}

.title-icon {
  font-size: 20px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.header-badge {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 5px 12px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-radius: 14px;
  border: 1px solid var(--border-color);
}

/* 英雄列表 */
.champion-list {
  flex: 1;
  min-height: 280px;
  max-height: 400px;
  overflow-y: auto;
  padding: var(--spacing-md);
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
  padding: 14px 16px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(22, 27, 34, 0.8) 100%);
  border-radius: var(--border-radius);
  margin-bottom: 10px;
  cursor: grab;
  transition: all var(--transition-normal);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
  animation: itemEnter 0.3s ease backwards;
}

.champion-item:nth-child(1) { animation-delay: 0.05s; }
.champion-item:nth-child(2) { animation-delay: 0.1s; }
.champion-item:nth-child(3) { animation-delay: 0.15s; }
.champion-item:nth-child(4) { animation-delay: 0.2s; }
.champion-item:nth-child(5) { animation-delay: 0.25s; }

@keyframes itemEnter {
  from {
    opacity: 0;
    transform: translateX(-15px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.champion-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(255,255,255,0.02) 0%, transparent 50%);
  pointer-events: none;
}

.champion-item:hover {
  background: var(--bg-hover);
  border-color: var(--border-color);
  transform: translateX(8px);
  box-shadow: var(--shadow-lg);
}

.champion-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.item-rank {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: var(--bg-primary);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(78, 204, 163, 0.3);
}

.item-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-color);
  transition: all var(--transition-fast);
}

.champion-item:hover .item-avatar {
  border-color: var(--accent-secondary);
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
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--text-muted);
  border-radius: 8px;
  font-size: 20px;
  opacity: 0;
  transition: all var(--transition-fast);
}

.champion-item:hover .item-remove {
  opacity: 1;
}

.item-remove:hover {
  background: rgba(233, 69, 96, 0.2);
  color: #e94560;
  transform: scale(1.1);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
}

.empty-icon {
  font-size: 56px;
  margin-bottom: var(--spacing-md);
  opacity: 0.4;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.empty-state p {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.empty-tip {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  margin-top: 6px;
}

/* 添加按钮 */
.add-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: 18px;
  background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  border-top: 1px solid var(--border-color);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.add-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(78, 204, 163, 0.1) 50%, transparent 100%);
  transition: left 0.5s ease;
}

.add-button:hover {
  background: var(--bg-hover);
  color: var(--accent-secondary);
}

.add-button:hover::before {
  left: 100%;
}

.add-button:active {
  background: var(--bg-primary);
}

.add-icon {
  font-size: 22px;
  font-weight: 300;
  transition: transform var(--transition-fast);
}

.add-button:hover .add-icon {
  transform: rotate(90deg);
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.35s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-25px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(25px);
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
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
  border-radius: 20px;
  width: 500px;
  max-height: 620px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 60px rgba(78, 204, 163, 0.1);
  border: 1px solid var(--border-color);
  animation: modalSlideIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

@keyframes modalSlideIn {
  from { 
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-primary);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 100%);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.modal-header h3 span {
  font-size: 24px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.close-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  color: var(--text-muted);
  font-size: 22px;
  border-radius: 10px;
  transition: all var(--transition-normal);
  border: 1px solid var(--border-color);
}

.close-btn:hover {
  background: rgba(233, 69, 96, 0.2);
  color: var(--color-lose);
  border-color: rgba(233, 69, 96, 0.3);
  transform: rotate(90deg);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin: var(--spacing-lg) var(--spacing-xl);
  padding: 14px 18px;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  border-radius: 12px;
  border: 2px solid var(--border-color);
  transition: all var(--transition-normal);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.3);
}

.search-box:focus-within {
  border-color: var(--accent-secondary);
  box-shadow: 0 0 0 4px rgba(78, 204, 163, 0.15), inset 0 2px 6px rgba(0, 0, 0, 0.3);
}

.search-icon {
  font-size: 18px;
  opacity: 0.6;
  transition: all var(--transition-fast);
}

.search-box:focus-within .search-icon {
  opacity: 1;
  transform: scale(1.1);
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
  padding: 0 var(--spacing-lg) var(--spacing-lg);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-bottom: 6px;
  border: 1px solid transparent;
  position: relative;
}

.result-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--gradient-primary);
  border-radius: 0 2px 2px 0;
  transition: height var(--transition-fast);
}

.result-item:hover:not(.disabled) {
  background: linear-gradient(90deg, rgba(78, 204, 163, 0.1) 0%, transparent 50%);
  border-color: var(--border-color);
  transform: translateX(4px);
}

.result-item:hover:not(.disabled)::before {
  height: 60%;
}

.result-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.result-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-color);
  transition: all var(--transition-fast);
}

.result-item:hover:not(.disabled) .result-avatar {
  border-color: var(--accent-secondary);
  box-shadow: 0 0 15px rgba(78, 204, 163, 0.3);
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
  gap: 2px;
}

.result-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.result-title {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.result-tag {
  font-size: 11px;
  color: var(--text-muted);
  padding: 5px 10px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.result-add {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: var(--bg-primary);
  border-radius: 8px;
  font-size: 20px;
  font-weight: 300;
  opacity: 0;
  transform: scale(0.8);
  transition: all var(--transition-normal);
  box-shadow: 0 2px 10px rgba(78, 204, 163, 0.3);
}

.result-item:hover:not(.disabled) .result-add {
  opacity: 1;
  transform: scale(1);
}

.result-add:hover {
  transform: scale(1.1) !important;
  box-shadow: 0 4px 15px rgba(78, 204, 163, 0.5);
}

.no-results {
  text-align: center;
  padding: var(--spacing-xl) * 2;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.no-results::before {
  content: '🔍';
  display: block;
  font-size: 48px;
  margin-bottom: var(--spacing-md);
  opacity: 0.3;
}
</style>
