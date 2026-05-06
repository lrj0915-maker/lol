import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/match',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
  },
  {
    path: '/cache',
    name: 'Cache',
    component: () => import('@/views/CacheView.vue'),
  },
  {
    path: '/match',
    name: 'Match',
    component: () => import('@/views/MatchView.vue'),
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/AnalysisView.vue'),
  },
  {
    path: '/select',
    name: 'Select',
    component: () => import('@/views/SelectView.vue'),
  },
  {
    path: '/runes',
    name: 'Runes',
    component: () => import('@/views/RunesView.vue'),
  },
  {
    path: '/runes-preview',
    name: 'RunesOPGGPreview',
    component: () => import('@/views/RunesOPGGPreview.vue'),
  },
  {
    path: '/augments',
    name: 'Augments',
    component: () => import('@/views/AugmentsView.vue'),
  },
  {
    path: '/jungle',
    name: 'Jungle',
    component: () => import('@/views/JungleView.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
  },
  {
    path: '/enhancements',
    redirect: '/augments',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
