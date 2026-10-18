<template>
  <section class="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl" data-testid="simulation-visibility">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs font-mono uppercase tracking-widest text-blue-400">Panel 8</p>
        <h2 class="mt-1 text-xl font-bold text-white">Simulation visibility</h2>
        <p class="mt-1 text-xs text-slate-400">Read-only monitoring. No controls here can mutate a worker or simulation.</p>
      </div>
      <div class="text-right text-xs text-slate-400">
        <div>Polling: {{ polling ? 'active' : 'stopped' }} (10s)</div>
        <div>Last refresh: {{ lastRefresh || 'not available' }}</div>
      </div>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="item in summary" :key="item.label" class="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
        <div class="text-[11px] uppercase tracking-wide text-slate-500">{{ item.label }}</div>
        <div class="mt-1 break-words text-sm font-semibold text-slate-100">{{ item.value }}</div>
      </div>
    </div>

    <div class="mt-5 grid gap-4 lg:grid-cols-2">
      <!-- Platform states -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">Platform states</h3>
        <div class="mt-3 space-y-2 text-xs">
          <div v-for="item in platformItems" :key="item.label" class="flex justify-between gap-3 border-b border-slate-800/70 pb-2 last:border-0">
            <span class="text-slate-500">{{ item.label }}</span>
            <span class="text-right text-slate-200">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <!-- Run status -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">Run status</h3>
        <div class="mt-3 space-y-2 text-xs">
          <div v-for="item in runItems" :key="item.label" class="flex justify-between gap-3 border-b border-slate-800/70 pb-2 last:border-0">
            <span class="text-slate-500">{{ item.label }}</span>
            <span class="text-right text-slate-200">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">Timeline</h3>
        <div v-if="timelineItems.length" class="mt-3 max-h-40 space-y-2 overflow-auto text-xs">
          <div v-for="(item, index) in timelineItems" :key="index" class="rounded-lg bg-slate-900 p-2 text-slate-300">{{ item }}</div>
        </div>
        <p v-else class="mt-3 text-xs text-slate-500">No timeline records available.</p>
      </div>

      <!-- Actions -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">Actions</h3>
        <div v-if="actionItems.length" class="mt-3 max-h-40 space-y-2 overflow-auto text-xs">
          <div v-for="(item, index) in actionItems" :key="index" class="rounded-lg bg-slate-900 p-2 text-slate-300">{{ item }}</div>
        </div>
        <p v-else class="mt-3 text-xs text-slate-500">No action records available.</p>
      </div>

      <!-- Posts -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">Posts</h3>
        <div v-if="postItems.length" class="mt-3 max-h-40 space-y-2 overflow-auto text-xs">
          <div v-for="(item, index) in postItems" :key="index" class="rounded-lg bg-slate-900 p-2 text-slate-300">{{ item }}</div>
        </div>
        <p v-else class="mt-3 text-xs text-slate-500">No post records available.</p>
      </div>

      <!-- History -->
      <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <h3 class="font-semibold text-slate-200">History</h3>
        <div v-if="historyItems.length" class="mt-3 max-h-40 space-y-2 overflow-auto text-xs">
          <div v-for="(item, index) in historyItems" :key="index" class="rounded-lg bg-slate-900 p-2 text-slate-300">{{ item }}</div>
        </div>
        <p v-else class="mt-3 text-xs text-slate-500">No history records available.</p>
      </div>
    </div>

    <div v-if="errors.length" class="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
      <div class="font-semibold">Unavailable data</div>
      <div v-for="error in errors" :key="error">{{ error }}</div>
    </div>
  </section>
</template>

<script>
import {
  getSimulation,
  getRunStatus,
  getSimulationTimeline,
  getSimulationActions,
  getSimulationPosts,
  getSimulationHistory,
  getEnvStatus
} from '../../api/simulation'

const SIMULATION_ID = 'sim_b839625f8ac2'
const PROJECT_ID = 'proj_5e996d7cdf4b'
const CANONICAL_PLATFORMS = ['instagram', 'linkedin', 'reddit', 'threads', 'tiktok', 'twitter', 'youtube']

const value = (data, key, fallback = 'Unavailable') => data && data[key] !== undefined && data[key] !== null && data[key] !== '' ? data[key] : fallback
const dataOf = response => response?.data || {}

export default {
  name: 'Panel8SimulationVisibility',
  data: () => ({
    simulation: {}, run: {}, env: {}, timeline: [], actions: [], posts: [], history: [], errors: [], lastRefresh: '', polling: false, timer: null, refreshSequence: 0
  }),
  computed: {
    summary() {
      return [
        { label: 'Simulation', value: SIMULATION_ID },
        { label: 'Project', value: PROJECT_ID },
        { label: 'Graph', value: value(this.simulation, 'graph_id') },
        { label: 'Task', value: value(this.simulation, 'task_id', 'Not present in API state') },
        { label: 'Status', value: value(this.simulation, 'status') },
        { label: 'Round', value: `${value(this.run, 'current_round', value(this.simulation, 'current_round', 0))} / ${value(this.run, 'total_rounds', 'Unavailable')}` },
        { label: 'Profiles', value: value(this.simulation, 'profiles_count', 'Unavailable') },
        { label: 'Config', value: this.simulation.config_generated === true ? 'available' : 'Unavailable' }
      ]
    },
    platformItems() {
      const configured = Array.isArray(this.simulation.platforms) ? this.simulation.platforms : []
      return CANONICAL_PLATFORMS.map(platform => ({
        label: platform,
        value: configured.includes(platform)
          ? value(this.simulation.platform_statuses, platform, value(this.env, `${platform}_available`))
          : 'Unavailable (not configured)'
      }))
    },
    runItems() { return ['runner_status', 'progress_percent', 'total_actions_count', 'started_at', 'updated_at'].map(key => ({ label: key, value: value(this.run, key) })) },
    timelineItems() { return this.timeline.slice(0, 20).map(item => JSON.stringify(item)) },
    actionItems() { return this.actions.slice(0, 20).map(item => JSON.stringify(item)) },
    postItems() { return this.posts.slice(0, 20).map(item => JSON.stringify(item)) },
    historyItems() { return this.history.slice(0, 20).map(item => JSON.stringify(item)) }
  },
  mounted() { this.polling = true; this.refresh() },
  beforeUnmount() { this.polling = false; window.clearTimeout(this.timer) },
  methods: {
    scheduleRefresh() {
      window.clearTimeout(this.timer)
      if (this.polling) this.timer = window.setTimeout(() => this.refresh(), 10000)
    },
    async refresh() {
      const sequence = ++this.refreshSequence
      const requests = [
        ['simulation', getSimulation(SIMULATION_ID)],
        ['run status', getRunStatus(SIMULATION_ID)],
        ['timeline', getSimulationTimeline(SIMULATION_ID)],
        ['actions', getSimulationActions(SIMULATION_ID, { limit: 50 })],
        ['posts', getSimulationPosts(SIMULATION_ID, null, 50)],
        ['history', getSimulationHistory(20)],
        ['platform environment', getEnvStatus({ simulation_id: SIMULATION_ID })]
      ]
      const results = await Promise.allSettled(requests.map(([, request]) => request))
      if (sequence !== this.refreshSequence || !this.polling) return
      this.errors = []
      results.forEach((result, index) => {
        const label = requests[index][0]
        if (result.status === 'rejected') {
          this.errors.push(`${label}: unavailable`)
          if (label === 'simulation') this.simulation = {}
          if (label === 'run status') this.run = {}
          if (label === 'timeline') this.timeline = []
          if (label === 'actions') this.actions = []
          if (label === 'posts') this.posts = []
          if (label === 'history') this.history = []
          if (label === 'platform environment') this.env = {}
          return
        }
        const data = dataOf(result.value)
        if (label === 'simulation') this.simulation = data
        if (label === 'run status') this.run = data
        if (label === 'timeline') this.timeline = Array.isArray(data.timeline) ? data.timeline : []
        if (label === 'actions') this.actions = Array.isArray(data.actions) ? data.actions : []
        if (label === 'posts') this.posts = Array.isArray(data.posts) ? data.posts : []
        if (label === 'history') this.history = Array.isArray(data) ? data : (Array.isArray(data.history) ? data.history : [])
        if (label === 'platform environment') this.env = data
      })
      this.lastRefresh = new Date().toLocaleTimeString()
      this.scheduleRefresh()
    }
  }
}
</script>
