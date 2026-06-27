import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import KillChainView from './views/KillChainView.vue'
import NotesView from './views/NotesView.vue'
import SettingsView from './views/SettingsView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/killchain', name: 'killchain', component: KillChainView },
  { path: '/notes', name: 'notes', component: NotesView },
  { path: '/settings', name: 'settings', component: SettingsView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
