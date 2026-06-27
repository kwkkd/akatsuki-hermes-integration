<template>
  <div class="killchain-view">
    <header class="view-header">
      <h1>Kill Chain</h1>
      <button @click="runChain" class="btn btn-primary" :disabled="running">▶ {{ running ? 'Running...' : 'Execute' }}</button>
    </header>
    <div class="chain-phases">
      <div v-for="(phase, i) in phases" :key="i" class="phase-card" :class="phase.status">
        <div class="phase-number">{{ i + 1 }}</div>
        <div class="phase-content">
          <h3>{{ phase.name }}</h3>
          <p>{{ phase.description }}</p>
          <div v-if="phase.result" class="phase-result">
            <pre>{{ phase.result }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'KillChainView',
  setup() {
    const running = ref(false)
    const phases = ref([
      { name: 'Reconnaissance', description: 'Target information gathering', status: 'pending', result: '' },
      { name: 'Weaponization', description: 'Payload creation and obfuscation', status: 'pending', result: '' },
      { name: 'Delivery', description: 'Payload delivery to target', status: 'pending', result: '' },
      { name: 'Exploitation', description: 'Vulnerability exploitation', status: 'pending', result: '' },
      { name: 'Installation', description: 'Backdoor/persistence installation', status: 'pending', result: '' },
      { name: 'C2', description: 'Command & Control channel', status: 'pending', result: '' },
      { name: 'Actions', description: 'Mission objectives execution', status: 'pending', result: '' },
    ])

    async function runChain() {
      running.value = true
      for (let i = 0; i < phases.value.length; i++) {
        phases.value[i].status = 'running'
        await new Promise(r => setTimeout(r, 1000))
        try {
          const res = await fetch('/api/chain/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: 'target.local' }),
          })
          if (res.ok) {
            const data = await res.json()
            phases.value[i].result = JSON.stringify(data, null, 2)
          }
        } catch {}
        phases.value[i].status = i < phases.value.length - 1 ? 'completed' : 'completed'
      }
      running.value = false
    }

    return { running, phases, runChain }
  }
}
</script>
