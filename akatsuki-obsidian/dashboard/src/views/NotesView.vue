<template>
  <div class="notes-view">
    <header class="view-header">
      <h1>Notes</h1>
      <button @click="refresh" class="btn btn-sm">🔄 Refresh</button>
    </header>
    <div class="notes-list">
      <div v-for="note in notes" :key="note.path" class="note-card" @click="viewNote(note.path)">
        <div class="note-title">{{ note.title }}</div>
        <div class="note-path">{{ note.path }}</div>
        <div class="note-tags">
          <span v-for="tag in (note.tags || [])" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'NotesView',
  setup() {
    const notes = ref([])

    async function refresh() {
      try {
        const res = await fetch('/api/notes')
        if (res.ok) notes.value = await res.json()
      } catch {}
    }

    function viewNote(path) {
      window.open(`/api/notes/${encodeURIComponent(path)}`, '_blank')
    }

    onMounted(refresh)

    return { notes, refresh, viewNote }
  }
}
</script>
