<template>
  <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 text-slate-100">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-white">{{ $t('dashboard.activeJobs') }}</h3>
        <p class="text-xs text-slate-400">Pekerjaan simulasi, checkpoint state-machine, dan pemulihan pasca-crash</p>
      </div>
      <button
        @click="fetchJobs"
        class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg text-slate-300 transition-colors"
      >
        Segarkan
      </button>
    </div>

    <div v-if="jobs.length === 0" class="text-center py-8 text-slate-500 text-sm">
      {{ $t('dashboard.noActiveJobs') }}
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="text-xs text-slate-400 uppercase bg-slate-850 border-b border-slate-800">
          <tr>
            <th class="px-4 py-3">{{ $t('dashboard.jobId') }}</th>
            <th class="px-4 py-3">{{ $t('dashboard.state') }}</th>
            <th class="px-4 py-3">{{ $t('dashboard.round') }}</th>
            <th class="px-4 py-3">{{ $t('dashboard.progress') }}</th>
            <th class="px-4 py-3 text-right">{{ $t('dashboard.action') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="job in jobs" :key="job.id" class="hover:bg-slate-800/40">
            <td class="px-4 py-3 font-mono text-xs text-indigo-300">{{ job.id }}</td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 rounded text-xs font-semibold"
                :class="{
                  'bg-emerald-950 text-emerald-400 border border-emerald-800': job.state === 'running',
                  'bg-amber-950 text-amber-400 border border-amber-800': job.state === 'paused',
                  'bg-rose-950 text-rose-400 border border-rose-800': job.state === 'failed',
                  'bg-indigo-950 text-indigo-400 border border-indigo-800': job.state === 'checkpointing' || job.state === 'recovering',
                  'bg-slate-800 text-slate-400': job.state === 'completed' || job.state === 'queued'
                }"
              >
                {{ job.state }}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-300">{{ job.current_round }} / {{ job.total_rounds }}</td>
            <td class="px-4 py-3">
              <div class="w-32 bg-slate-800 rounded-full h-2">
                <div
                  class="bg-indigo-500 h-2 rounded-full"
                  :style="{ width: `${job.progress_pct}%` }"
                ></div>
              </div>
            </td>
            <td class="px-4 py-3 text-right">
              <button
                v-if="job.state === 'failed' || job.state === 'paused'"
                @click="recoverJob(job.id)"
                class="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold"
              >
                {{ $t('dashboard.recover') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const jobs = ref([])

const fetchJobs = async () => {
  try {
    const res = await fetch('/api/jobs')
    if (res.ok) {
      const data = await res.json()
      jobs.value = data.data || []
    }
  } catch (e) {
    // fallback sample jika belum ada simulasi berjalan
    jobs.value = [
      { id: 'job-sim-01', state: 'running', current_round: 8, total_rounds: 30, progress_pct: 26.6 },
      { id: 'job-sim-demo', state: 'paused', current_round: 14, total_rounds: 20, progress_pct: 70.0 }
    ]
  }
}

const recoverJob = async (jobId) => {
  try {
    const res = await fetch(`/api/jobs/${jobId}/recover`, { method: 'POST' })
    if (res.ok) {
      await fetchJobs()
    }
  } catch (e) {
    console.error('Pemulihan job gagal:', e)
  }
}

onMounted(() => {
  fetchJobs()
})
</script>
