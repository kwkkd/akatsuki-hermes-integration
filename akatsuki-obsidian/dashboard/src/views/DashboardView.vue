<template>
  <div class="dashboard-view">
    <header class="view-header">
      <h1>Dashboard</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn btn-sm">🔄 Refresh</button>
      </div>
    </header>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ store.stats.notes_total }}</div>
        <div class="stat-label">Total Notes</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ store.stats.tools_total }}</div>
        <div class="stat-label">Tools</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ store.stats.operations_active }}</div>
        <div class="stat-label">Active Operations</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ store.stats.peers_connected }}</div>
        <div class="stat-label">Peers</div>
      </div>
    </div>
    <div class="widget-grid">
      <div v-for="w in store.layout.widgets" :key="w.id" class="widget-slot">
        <div class="widget-header">
          <span>{{ w.title || w.type }}</span>
          <button @click="removeWidget(w.id)" class="btn-icon">✕</button>
        </div>
        <div class="widget-body" v-html="widgetHtml(w.id)"></div>
      </div>
    </div>
    <div class="add-widget">
      <select v-model="newWidgetType">
        <option value="">Add widget...</option>
        <option v-for="aw in availableWidgets" :key="aw.id" :value="aw.id">{{ aw.name }}</option>
      </select>
      <button @click="addWidget" class="btn btn-sm">+ Add</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard.js'

export default {
  name: 'DashboardView',
  setup() {
    const store = useDashboardStore()
    const newWidgetType = ref('')
    const availableWidgets = ref([])
    const renderedHtml = ref({})

    async function refresh() {
      await store.fetchStats()
      await store.fetchLayout()
    }

    async function addWidget() {
      if (!newWidgetType.value) return
      const id = `w-${Date.now()}`
      store.layout.widgets.push({ id, type: newWidgetType.value, title: newWidgetType.value, config: {} })
      await store.saveLayout(store.layout.widgets)
      newWidgetType.value = ''
    }

    async function removeWidget(id) {
      store.layout.widgets = store.layout.widgets.filter(w => w.id !== id)
      await store.saveLayout(store.layout.widgets)
    }

    function widgetHtml(id) {
      return renderedHtml.value[id] || `<div class="widget-placeholder">Loading...</div>`
    }

    onMounted(async () => {
      await refresh()
      const res = await fetch('/api/dashboard/widgets/available')
      if (res.ok) {
        const data = await res.json()
        availableWidgets.value = data.widgets
      }
    })

    return { store, newWidgetType, availableWidgets, renderedHtml, refresh, addWidget, removeWidget, widgetHtml }
  }
}
</script>
