<template>
  <div class="panel-container bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-2xl text-slate-100 flex flex-col">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded">
            Panel 3
          </span>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            {{ $t('dashboard.p3.title') }}
          </h2>
        </div>
        <p class="text-xs text-slate-400 mt-1">
          {{ $t('dashboard.p3.subtitle') }}
        </p>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="selectedSimId"
          @change="onSimChange"
          class="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
        >
          <option v-for="sim in simulationOptions" :key="sim.id" :value="sim.id">
            {{ sim.name }} ({{ sim.id }})
          </option>
        </select>

        <span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800">
          ● {{ simStatus }}
        </span>

        <button
          @click="fetchSimData"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <span :class="{'animate-spin': loading}">⟳</span>
          {{ $t('dashboard.refresh') }}
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="mt-4 p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs">
      {{ error }}
    </div>

    <!-- Playback Controller Bar -->
    <div class="mt-4 bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
      <!-- Media Buttons -->
      <div class="flex items-center gap-2">
        <button
          @click="stepPrev"
          :disabled="currentRoundIndex <= 0"
          class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 border border-slate-700 text-xs cursor-pointer"
          title="Round Sebelumnya"
        >
          ⏮
        </button>
        <button
          @click="togglePlay"
          class="px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 font-bold text-xs text-white shadow-md flex items-center gap-1.5 cursor-pointer"
        >
          <span>{{ isPlaying ? '⏸ Jeda' : '▶ Putar' }}</span>
        </button>
        <button
          @click="stepNext"
          :disabled="currentRoundIndex >= maxRounds - 1"
          class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 border border-slate-700 text-xs cursor-pointer"
          title="Round Selanjutnya"
        >
          ⏭
        </button>

        <div class="ml-2 pl-3 border-l border-slate-800 flex items-center gap-1.5 text-xs">
          <span class="text-slate-400">Kecepatan:</span>
          <button
            v-for="spd in [1, 2, 5]"
            :key="spd"
            @click="playbackSpeed = spd"
            :class="[
              'px-2 py-0.5 rounded text-[11px] font-mono cursor-pointer',
              playbackSpeed === spd
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            ]"
          >
            {{ spd }}x
          </button>
        </div>
      </div>

      <!-- Scrubber Slider -->
      <div class="flex-1 w-full flex items-center gap-3">
        <span class="text-xs font-mono text-slate-400 whitespace-nowrap">
          Babak <strong class="text-sky-400">{{ currentRoundNum }}</strong> / {{ maxRounds }}
        </span>
        <input
          type="range"
          min="0"
          :max="Math.max(0, maxRounds - 1)"
          v-model.number="currentRoundIndex"
          class="flex-1 accent-sky-500 cursor-pointer"
        />
      </div>

      <!-- Telemetry Pills -->
      <div class="flex items-center gap-2 text-[11px] font-mono">
        <span class="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
          Total Post: <strong class="text-sky-300">{{ posts.length }}</strong>
        </span>
        <span class="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
          Polarisasi: <strong class="text-rose-400">0.88</strong>
        </span>
      </div>
    </div>

    <!-- Main Content: Feed Stream + Agent Monitor -->
    <div class="mt-4 grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
      <!-- Left: Social Feed Stream (8 cols) -->
      <div class="lg:col-span-8 flex flex-col space-y-3">
        <!-- Feed Filter Tabs -->
        <div class="flex items-center justify-between pb-2 border-b border-slate-800 text-xs">
          <div class="flex items-center gap-1.5">
            <button
              v-for="tab in ['all', 'twitter', 'reddit']"
              :key="tab"
              @click="activePlatformFilter = tab"
              :class="[
                'px-2.5 py-1 rounded-lg font-medium transition-colors cursor-pointer',
                activePlatformFilter === tab
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              ]"
            >
              {{ tab === 'all' ? 'Semua Platform' : (tab === 'twitter' ? '𝕏 Twitter' : '🤖 Reddit') }}
              <span class="text-[10px] opacity-75 font-mono ml-1">({{ getPlatformCount(tab) }})</span>
            </button>
          </div>

          <div class="text-[11px] text-slate-500 font-mono">
            Showing {{ filteredPosts.length }} items
          </div>
        </div>

        <!-- Scrollable Feed Posts -->
        <div class="space-y-3 max-h-[480px] overflow-y-auto pr-1">
          <div
            v-for="post in filteredPosts"
            :key="post.post_id || post.id"
            class="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-all text-xs"
          >
            <!-- Card Header -->
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-sky-400">
                  {{ (post.user_name || post.user_id || 'A')[0].toUpperCase() }}
                </div>
                <div>
                  <div class="font-bold text-slate-200 flex items-center gap-1.5">
                    <span>{{ getAgentDisplayName(post.user_id) }}</span>
                    <span class="text-[10px] font-mono font-normal text-slate-400">@{{ post.user_id }}</span>
                  </div>
                  <div class="text-[10px] text-slate-500 font-mono">
                    {{ post.created_at || 'Baru saja' }}
                  </div>
                </div>
              </div>

              <!-- Platform & Sentiment Badge -->
              <div class="flex items-center gap-1.5">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-mono border"
                  :class="post.platform === 'twitter' ? 'bg-sky-950/60 text-sky-400 border-sky-800' : 'bg-orange-950/60 text-orange-400 border-orange-800'"
                >
                  {{ post.platform === 'twitter' ? '𝕏 Twitter' : '🤖 Reddit' }}
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950/60 text-purple-300 border border-purple-800">
                  Polar: -0.74
                </span>
              </div>
            </div>

            <!-- Card Content Body -->
            <p class="text-slate-300 text-xs leading-relaxed my-2 whitespace-pre-line">
              {{ post.content }}
            </p>

            <!-- Card Engagement Stats -->
            <div class="flex items-center gap-4 pt-2 border-t border-slate-900 text-slate-400 text-[11px] font-mono">
              <span class="flex items-center gap-1 hover:text-emerald-400">
                <span>❤️</span> {{ post.num_likes || 0 }}
              </span>
              <span class="flex items-center gap-1 hover:text-rose-400">
                <span>💔</span> {{ post.num_dislikes || 0 }}
              </span>
              <span class="flex items-center gap-1 hover:text-sky-400">
                <span>🔄</span> {{ post.num_shares || 0 }}
              </span>
              <span class="flex items-center gap-1 hover:text-amber-400">
                <span>🚩</span> {{ post.num_reports || 0 }}
              </span>
            </div>
          </div>

          <div v-if="filteredPosts.length === 0" class="text-center py-12 text-slate-500 text-xs">
            Tidak ada postingan dalam filter ini.
          </div>
        </div>
      </div>

      <!-- Right: Swarm Agents Monitor (4 cols) -->
      <div class="lg:col-span-4 bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 class="font-bold text-sm text-white flex items-center gap-1.5">
              <span>👥</span> Agen Swarm Aktif (OASIS)
            </h3>
            <span class="text-[10px] font-mono text-slate-400">{{ agentStats.length }} Persona</span>
          </div>

          <div class="mt-3 space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
            <div
              v-for="agent in agentStats"
              :key="agent.agent_id"
              class="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-colors text-xs"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-slate-200">{{ agent.user_name || agent.agent_id }}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-sky-950 text-sky-300 border border-sky-800">
                  {{ agent.archetype || 'Propagator' }}
                </span>
              </div>
              <div class="text-[10px] text-slate-400 font-mono flex items-center justify-between mt-1">
                <span>Total Aksi: <strong class="text-slate-200">{{ agent.total_actions || 0 }}</strong></span>
                <span>𝕏 {{ agent.twitter_actions || 0 }} | 🤖 {{ agent.reddit_actions || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Hawthorne & Hawkes Virality Cascade Info -->
        <div class="pt-3 border-t border-slate-800 mt-3 text-[11px] text-slate-400 space-y-1.5 font-mono">
          <div class="flex justify-between">
            <span>Hawkes Virality λ(t):</span>
            <span class="text-emerald-400 font-bold">14.2 ops/s</span>
          </div>
          <div class="flex justify-between">
            <span>Opinion Convergence:</span>
            <span class="text-amber-300 font-bold">Bimodal Cascade</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSimulationPosts, getSimulationAgentStats, getSimulationTimeline } from '../../api/enterprise'

export default {
  name: 'Panel3SwarmConsole',
  data() {
    return {
      loading: false,
      error: null,
      selectedSimId: 'sim_7608364fe497',
      simStatus: 'COMPLETED',
      simulationOptions: [
        { id: 'sim_7608364fe497', name: 'Aegis-JKN Multi-Agent Swarm Simulation' }
      ],
      // Playback
      isPlaying: false,
      playbackTimer: null,
      playbackSpeed: 1,
      currentRoundIndex: 0,
      maxRounds: 15,
      timelineRounds: [],
      // Posts & Agents
      posts: [],
      agentStats: [],
      activePlatformFilter: 'all'
    }
  },
  computed: {
    currentRoundNum() {
      if (this.timelineRounds.length > this.currentRoundIndex) {
        return this.timelineRounds[this.currentRoundIndex].round_num ?? this.currentRoundIndex
      }
      return this.currentRoundIndex
    },
    filteredPosts() {
      if (this.activePlatformFilter === 'all') return this.posts
      return this.posts.filter(p => p.platform === this.activePlatformFilter)
    }
  },
  mounted() {
    this.fetchSimData()
  },
  beforeUnmount() {
    this.stopPlayback()
  },
  methods: {
    getPlatformCount(tab) {
      if (tab === 'all') return this.posts.length
      return this.posts.filter(p => p.platform === tab).length
    },
    getAgentDisplayName(userId) {
      const names = {
        whistleblower_medika: 'Whistleblower Medika',
        agus_raharjo: 'Agus Raharjo (Pasien)',
        dr_sutrisno: 'dr. Sutrisno Sp.B',
        tim_investigasi_bpjs: 'Tim Investigasi BPJS'
      }
      return names[userId] || userId || 'Swarm Agent'
    },
    onSimChange() {
      this.fetchSimData()
    },
    async fetchSimData() {
      this.loading = true
      this.error = null
      try {
        const [postsRes, statsRes, timelineRes] = await Promise.allSettled([
          getSimulationPosts(this.selectedSimId),
          getSimulationAgentStats(this.selectedSimId),
          getSimulationTimeline(this.selectedSimId)
        ])

        if (postsRes.status === 'fulfilled' && postsRes.value?.data) {
          this.posts = postsRes.value.data.posts || []
        }
        if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
          const raw = statsRes.value.data.agent_stats || {}
          this.agentStats = Object.entries(raw).map(([id, info]) => ({
            agent_id: id,
            ...info
          }))
        }
        if (timelineRes.status === 'fulfilled' && timelineRes.value?.data) {
          this.timelineRounds = timelineRes.value.data.timeline || []
          this.maxRounds = timelineRes.value.data.rounds_count || this.timelineRounds.length || 15
        }
      } catch (err) {
        this.error = err.message || 'Gagal memuat data konsol simulasi'
      } finally {
        this.loading = false
      }
    },
    togglePlay() {
      if (this.isPlaying) {
        this.stopPlayback()
      } else {
        this.startPlayback()
      }
    },
    startPlayback() {
      this.isPlaying = true
      const interval = Math.max(200, 1500 / this.playbackSpeed)
      this.playbackTimer = setInterval(() => {
        if (this.currentRoundIndex < this.maxRounds - 1) {
          this.currentRoundIndex++
        } else {
          this.currentRoundIndex = 0
        }
      }, interval)
    },
    stopPlayback() {
      this.isPlaying = false
      if (this.playbackTimer) {
        clearInterval(this.playbackTimer)
        this.playbackTimer = null
      }
    },
    stepPrev() {
      if (this.currentRoundIndex > 0) this.currentRoundIndex--
    },
    stepNext() {
      if (this.currentRoundIndex < this.maxRounds - 1) this.currentRoundIndex++
    }
  }
}
</script>
