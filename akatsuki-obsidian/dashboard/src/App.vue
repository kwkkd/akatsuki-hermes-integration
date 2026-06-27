<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo">AKATSUKI</div>
      <nav>
        <router-link to="/" class="nav-item" :class="{ active: $route.name === 'dashboard' }">
          📊 Dashboard
        </router-link>
        <router-link to="/killchain" class="nav-item" :class="{ active: $route.name === 'killchain' }">
          ⚔️ Kill Chain
        </router-link>
        <router-link to="/notes" class="nav-item" :class="{ active: $route.name === 'notes' }">
          📝 Notes
        </router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: $route.name === 'settings' }">
          ⚙️ Settings
        </router-link>
      </nav>
      <div class="sidebar-status">
        <span class="status-indicator" :class="connected ? 'online' : 'offline'"></span>
        {{ connected ? 'Connected' : 'Disconnected' }}
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from './stores/dashboard.js'

export default {
  name: 'App',
  setup() {
    const store = useDashboardStore()
    const connected = ref(false)
    let ws = null

    function connect() {
      ws = new WebSocket(`ws://${location.hostname}:8000/ws`)
      ws.onopen = () => { connected.value = true }
      ws.onclose = () => { connected.value = false; setTimeout(connect, 5000) }
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.event === 'stats') store.updateStats(msg.data)
        } catch {}
      }
    }

    onMounted(connect)
    onUnmounted(() => { if (ws) ws.close() })

    return { connected }
  }
}
</script>
