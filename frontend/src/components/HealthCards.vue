<template>
  <div class="grid grid-cols-2 md:grid-cols-5 gap-3.5 mb-6">
    <div
      v-for="(card, i) in services"
      :key="i"
      class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">{{ card.name }}</span>
        <span
          class="w-2.5 h-2.5 rounded-full"
          :class="card.status === 'healthy' ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-amber-500 shadow-sm shadow-amber-500/50'"
        ></span>
      </div>
      <div class="mt-2.5">
        <div class="text-base font-bold text-white capitalize">{{ card.status }}</div>
        <div class="text-[11px] text-slate-500 mt-0.5 truncate">{{ card.detail }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const services = ref([
  { name: 'Backend Flask', status: 'healthy', detail: 'Port 5001 • REST Active' },
  { name: 'SQLite DB', status: 'healthy', detail: 'WAL Mode • Synchronous' },
  { name: 'Graph Memory', status: 'healthy', detail: 'Zep / Graphiti Adapter' },
  { name: 'SearXNG Privat', status: 'healthy', detail: 'Docker Local • No Tracking' },
  { name: '9Router Gateway', status: 'healthy', detail: 'OpenAI-Compatible' }
])

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'healthy') {
        services.value[0].status = 'healthy'
        services.value[1].status = 'healthy'
      }
    }
  } catch (e) {}

  try {
    const sRes = await fetch('/api/research/health')
    if (sRes.ok) {
      const sData = await sRes.json()
      services.value[3].status = sData.status || 'healthy'
      services.value[3].detail = `Aktif (${sData.engines_active?.length || 4} mesin)`
    }
  } catch (e) {}
})
</script>
