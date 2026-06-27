<template>
  <div class="settings-view">
    <header class="view-header">
      <h1>Settings</h1>
    </header>
    <section class="settings-section">
      <h2>Connection</h2>
      <div class="setting-row">
        <label>Bridge URL</label>
        <input v-model="settings.bridge_url" placeholder="ws://localhost:18749" />
      </div>
      <div class="setting-row">
        <label>API URL</label>
        <input v-model="settings.api_url" placeholder="http://localhost:8000" />
      </div>
    </section>
    <section class="settings-section">
      <h2>Authentication</h2>
      <div class="setting-row">
        <label>Username</label>
        <input v-model="settings.username" />
      </div>
      <div class="setting-row">
        <label>Token</label>
        <input v-model="settings.token" type="password" />
      </div>
      <button @click="saveSettings" class="btn btn-primary">Save</button>
      <span v-if="saved" class="saved-msg">✓ Saved</span>
    </section>
    <section class="settings-section">
      <h2>Notifications</h2>
      <div class="setting-row">
        <label>Telegram Bot Token</label>
        <input v-model="settings.telegram_token" type="password" />
      </div>
      <div class="setting-row">
        <label>Telegram Chat ID</label>
        <input v-model="settings.telegram_chat_id" />
      </div>
    </section>
    <section class="settings-section">
      <h2>About</h2>
      <p>AKATSUKI Framework v1.0</p>
      <p>Hermes Agent Bridge + Obsidian Integration</p>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'SettingsView',
  setup() {
    const settings = ref({
      bridge_url: 'ws://localhost:18749',
      api_url: 'http://localhost:8000',
      username: '',
      token: '',
      telegram_token: '',
      telegram_chat_id: '',
    })
    const saved = ref(false)

    function loadSettings() {
      try {
        const stored = localStorage.getItem('akatsuki_settings')
        if (stored) settings.value = { ...settings.value, ...JSON.parse(stored) }
      } catch {}
    }

    function saveSettings() {
      localStorage.setItem('akatsuki_settings', JSON.stringify(settings.value))
      saved.value = true
      setTimeout(() => { saved.value = false }, 2000)
    }

    onMounted(loadSettings)

    return { settings, saved, saveSettings }
  }
}
</script>
