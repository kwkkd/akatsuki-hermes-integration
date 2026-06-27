import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref({
    notes_total: 0,
    tools_total: 0,
    operations_active: 0,
    peers_connected: 0,
  })
  const layout = ref({ widgets: [] })
  const alerts = ref([])

  async function fetchStats() {
    try {
      const res = await fetch('/api/dashboard/stats')
      if (res.ok) stats.value = await res.json()
    } catch {}
  }

  async function fetchLayout() {
    try {
      const res = await fetch('/api/dashboard/layout')
      if (res.ok) layout.value = await res.json()
    } catch {}
  }

  async function saveLayout(widgets) {
    try {
      await fetch('/api/dashboard/layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ widgets }),
      })
    } catch {}
  }

  function updateStats(data) {
    stats.value = { ...stats.value, ...data }
  }

  return { stats, layout, alerts, fetchStats, fetchLayout, saveLayout, updateStats }
})
