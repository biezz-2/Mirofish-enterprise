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

    <!-- Empty state if no simulation available -->
    <div v-if="!activeSimulationId" class="mt-5 rounded-xl border border-slate-800 bg-slate-950/70 p-8 text-center flex flex-col items-center justify-center">
      <div class="w-12 h-12 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-2xl mb-3">
        🔎
      </div>
      <h3 class="text-sm font-bold text-slate-200">Belum ada simulasi yang dipilih</h3>
      <p class="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
        Pilih simulasi aktif pada Panel 3 (Swarm Console) atau muat simulasi melalui parameter query URL (?simulation_id=...) untuk memantau visibilitas runtime platform.
      </p>
    </div>

    <div v-else class="mt-5 grid gap-4 lg:grid-cols-2">
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
import { getSimulationList } from '../../api/enterprise'

const CANONICAL_PLATFORMS = ['instagram', 'linkedin', 'reddit', 'threads', 'tiktok', 'twitter', 'youtube']

const value = (data, key, fallback = 'Unavailable') => data && data[key] !== undefined && data[key] !== null && data[key] !== '' ? data[key] : fallback
const dataOf = response => response?.data || {}

export default {
  name: 'Panel8SimulationVisibility',
  props: {
    simulationId: {
      type: String,
      default: ''
    },
    projectId: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      activeSimulationId: this.simulationId || '',
      activeProjectId: this.projectId || '',
      simulation: {},
      run: {},
      env: {},
      timeline: [],
      actions: [],
      posts: [],
      history: [],
      errors: [],
      lastRefresh: '',
      polling: false,
      timer: null,
      refreshSequence: 0
    }
  },
  computed: {
    summary() {
      return [
        { label: 'Simulation', value: this.activeSimulationId || 'Unavailable' },
        { label: 'Project', value: this.activeProjectId || value(this.simulation, 'project_id', 'Unavailable') },
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
  watch: {
    simulationId(newVal) {
      if (newVal !== this.activeSimulationId) {
        this.activeSimulationId = newVal || ''
        if (this.activeSimulationId) {
          this.refresh()
        }
      }
    },
    projectId(newVal) {
      if (newVal) {
        this.activeProjectId = newVal
      }
    }
  },
  mounted() {
    this.polling = true
    this.timer = setInterval(this.refresh, 10000)
    this.refresh()
  },
  beforeUnmount() {
    this.polling = false
    if (this.timer) clearInterval(this.timer)
  },
  methods: {
    async resolveLatestSimulation() {
      if (this.activeSimulationId) return
      try {
        const histRes = await getSimulationHistory(1)
        const histData = histRes?.data
        const items = Array.isArray(histData) ? histData : (Array.isArray(histData?.history) ? histData.history : [])
        if (items.length > 0 && (items[0].simulation_id || items[0].id)) {
          this.activeSimulationId = items[0].simulation_id || items[0].id
          if (!this.activeProjectId && items[0].project_id) {
            this.activeProjectId = items[0].project_id
          }
          return
        }
      } catch (e) {
        // Fallback to getSimulationList
      }

      try {
        const listRes = await getSimulationList()
        const listData = listRes?.data || listRes || []
        const list = Array.isArray(listData) ? listData : []
        if (list.length > 0) {
          const first = list[0]
          this.activeSimulationId = first.simulation_id || first.id || ''
          if (!this.activeProjectId && first.project_id) {
            this.activeProjectId = first.project_id
          }
        }
      } catch (e) {
        // No simulation found
      }
    },
    async refresh() {
      const sequence = ++this.refreshSequence
      if (!this.polling) return

      if (!this.activeSimulationId) {
        await this.resolveLatestSimulation()
      }

      if (!this.activeSimulationId) {
        this.errors = []
        this.lastRefresh = new Date().toLocaleTimeString()
        return
      }

      const simId = this.activeSimulationId
      const requests = [
        ['simulation', getSimulation(simId)],
        ['run status', getRunStatus(simId)],
        ['timeline', getSimulationTimeline(simId)],
        ['actions', getSimulationActions(simId, { limit: 50 })],
        ['posts', getSimulationPosts(simId, null, 50)],
        ['history', getSimulationHistory(20)],
        ['platform environment', getEnvStatus({ simulation_id: simId })]
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
    }
  }
}
</script>
