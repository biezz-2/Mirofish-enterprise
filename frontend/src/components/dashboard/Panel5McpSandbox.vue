<template>
  <div class="panel-container bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-2xl text-slate-100 flex flex-col">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded">
            Panel 5
          </span>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            {{ $t('dashboard.p5.title') }}
          </h2>
        </div>
        <p class="text-xs text-slate-400 mt-1">
          {{ $t('dashboard.p5.subtitle') }}
        </p>
      </div>

      <!-- Controls & Health -->
      <div class="flex items-center gap-2">
        <span class="px-2.5 py-1 text-[11px] font-mono rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>FastMCP RFC 7636: OK</span>
        </span>

        <button
          @click="fetchTools"
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

    <!-- Category Filter & Search Bar -->
    <div class="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          :class="[
            'px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer',
            selectedCategory === cat.id
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          ]"
        >
          {{ cat.name }}
          <span class="text-[10px] opacity-75 font-mono ml-0.5">({{ getCategoryCount(cat.id) }})</span>
        </button>
      </div>

      <div class="flex items-center gap-2">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari alat MCP..."
          class="bg-slate-900 border border-slate-700 rounded-md px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="text-slate-400 hover:text-slate-200"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- 2-Column Layout: Catalog vs Sandbox Runner -->
    <div class="mt-4 grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-[480px]">
      <!-- Left: Tools Catalog List (5 cols) -->
      <div class="lg:col-span-5 bg-slate-950/60 rounded-xl border border-slate-800 p-3 flex flex-col">
        <div class="text-xs font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-800 flex justify-between items-center">
          <span>Katalog Alat FastMCP</span>
          <span class="font-mono text-amber-400">{{ filteredTools.length }} Tersedia</span>
        </div>

        <div class="space-y-2 mt-2.5 flex-1 overflow-y-auto max-h-[500px] pr-1">
          <button
            v-for="tool in filteredTools"
            :key="tool.name"
            @click="selectTool(tool)"
            :class="[
              'w-full text-left p-2.5 rounded-lg border transition-all cursor-pointer flex flex-col gap-1',
              selectedTool?.name === tool.name
                ? 'bg-amber-950/40 border-amber-500/80 ring-1 ring-amber-500/40'
                : 'bg-slate-900/70 border-slate-800/80 hover:bg-slate-800/60 hover:border-slate-700'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="font-mono font-bold text-xs" :class="selectedTool?.name === tool.name ? 'text-amber-300' : 'text-slate-200'">
                {{ tool.name }}
              </span>
              <span class="text-[9px] px-1.5 py-0.5 rounded font-mono bg-slate-800 text-slate-400 border border-slate-700">
                {{ getToolCategoryTag(tool.name) }}
              </span>
            </div>
            <p class="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
              {{ tool.description || 'Tidak ada deskripsi rinci.' }}
            </p>
          </button>

          <div v-if="filteredTools.length === 0" class="text-center py-10 text-slate-500 text-xs">
            Tidak ada alat yang cocok dengan pencarian.
          </div>
        </div>
      </div>

      <!-- Right: Interactive Sandbox Runner & Live Output (7 cols) -->
      <div class="lg:col-span-7 bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div v-if="selectedTool">
          <!-- Tool Header -->
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 class="font-bold text-sm text-white font-mono flex items-center gap-2">
                <span>⚙️</span>
                <span>{{ selectedTool.name }}</span>
              </h3>
              <p class="text-xs text-slate-400 mt-1 leading-relaxed">
                {{ selectedTool.description }}
              </p>
            </div>
          </div>

          <!-- JSON Parameters Editor -->
          <div class="mt-3">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-slate-300 font-semibold flex items-center gap-1.5">
                <span>Parameter Payload (JSON)</span>
              </span>
              <div class="flex gap-2">
                <button
                  @click="loadSamplePayload"
                  class="text-[11px] text-amber-400 hover:text-amber-300 cursor-pointer underline"
                >
                  Muat Contoh
                </button>
                <button
                  @click="payloadJson = '{}'"
                  class="text-[11px] text-slate-400 hover:text-slate-200 cursor-pointer"
                >
                  Bersihkan
                </button>
              </div>
            </div>

            <textarea
              v-model="payloadJson"
              rows="6"
              class="w-full bg-slate-950 font-mono text-xs text-emerald-400 border border-slate-700 rounded-lg p-2.5 focus:outline-none focus:border-amber-500 leading-relaxed resize-y"
              placeholder="{}"
            ></textarea>
          </div>

          <!-- Execution Controls -->
          <div class="mt-3 flex items-center justify-between">
            <span class="text-[11px] text-slate-400 font-mono">
              POST /api/enterprise/mcp/invoke
            </span>

            <button
              @click="executeTool"
              :disabled="executing"
              class="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded-lg text-xs shadow-lg transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <span v-if="executing" class="animate-spin text-sm">⟳</span>
              <span>{{ executing ? 'Mengeksekusi Sandbox...' : 'Jalankan Alat MCP (Invoke)' }}</span>
            </button>
          </div>

          <!-- Live Output Console -->
          <div class="mt-4 pt-3 border-t border-slate-800">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="font-semibold text-slate-300">Konsol Output Eksekusi</span>
              <div v-if="execResult" class="flex items-center gap-2 text-[10px] font-mono">
                <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  HTTP 200 OK
                </span>
                <span class="text-slate-400">
                  Latency: <strong class="text-amber-300">{{ execLatency }} ms</strong>
                </span>
                <span v-if="execResult.webhook_dispatched" class="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                  Webhook Broadcasted
                </span>
              </div>
            </div>

            <div class="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] max-h-[180px] overflow-y-auto">
              <pre v-if="execResult" class="text-slate-200 whitespace-pre-wrap">{{ JSON.stringify(execResult, null, 2) }}</pre>
              <div v-else-if="executing" class="text-amber-400 animate-pulse">
                &gt; Mengirim panggilan alat ke FastMCP runner...
              </div>
              <div v-else class="text-slate-500 italic">
                Belum ada eksekusi. Klik "Jalankan Alat MCP" untuk memicu eksekusi nyata pada backend enterprise.
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-20 text-slate-500 text-xs">
          <div class="text-4xl mb-3">🛠️</div>
          <p>Pilih alat FastMCP dari katalog di sebelah kiri untuk melihat skema parameter dan menjalankan simulasi di sandbox.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getMcpTools, invokeMcpTool } from '../../api/enterprise'

export default {
  name: 'Panel5McpSandbox',
  data() {
    return {
      loading: false,
      error: null,
      tools: [],
      selectedTool: null,
      selectedCategory: 'all',
      searchQuery: '',
      payloadJson: '{}',
      executing: false,
      execResult: null,
      execLatency: 0,
      categories: [
        { id: 'all', name: 'Semua (22)' },
        { id: 'simulation', name: 'Simulasi Swarm' },
        { id: 'research', name: 'Research & Graph' },
        { id: 'recsys', name: 'RecSys Kalibrasi' },
        { id: 'bettafish', name: 'BettaFish Intel' },
        { id: 'diagnostics', name: 'Diagnostik' }
      ]
    }
  },
  computed: {
    filteredTools() {
      let list = this.tools
      if (this.selectedCategory !== 'all') {
        list = list.filter(t => this.getToolCategory(t.name) === this.selectedCategory)
      }
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase().trim()
        list = list.filter(t =>
          (t.name && t.name.toLowerCase().includes(q)) ||
          (t.description && t.description.toLowerCase().includes(q))
        )
      }
      return list
    }
  },
  mounted() {
    this.fetchTools()
  },
  methods: {
    getToolCategory(name) {
      if (name.includes('simulation') || name.includes('oasis') || name.includes('project')) return 'simulation'
      if (name.includes('research') || name.includes('graph') || name.includes('knowledge')) return 'research'
      if (name.includes('calibrate') || name.includes('platform')) return 'recsys'
      if (name.includes('bettafish') || name.includes('report') || name.includes('sentiment') || name.includes('risk')) return 'bettafish'
      return 'diagnostics'
    },
    getToolCategoryTag(name) {
      const cat = this.getToolCategory(name)
      const tags = {
        simulation: 'Swarm',
        research: 'GraphRAG',
        recsys: 'RecSys',
        bettafish: 'Intel',
        diagnostics: 'Infra'
      }
      return tags[cat] || 'Tool'
    },
    getCategoryCount(catId) {
      if (catId === 'all') return this.tools.length
      return this.tools.filter(t => this.getToolCategory(t.name) === catId).length
    },
    async fetchTools() {
      this.loading = true
      this.error = null
      try {
        const res = await getMcpTools()
        if (res && res.tools) {
          this.tools = res.tools
          if (!this.selectedTool && this.tools.length > 0) {
            this.selectTool(this.tools[0])
          }
        }
      } catch (err) {
        this.error = err.message || 'Gagal memuat katalog alat MCP'
      } finally {
        this.loading = false
      }
    },
    selectTool(tool) {
      this.selectedTool = tool
      this.execResult = null
      this.loadSamplePayload()
    },
    loadSamplePayload() {
      if (!this.selectedTool) return
      const name = this.selectedTool.name
      const samples = {
        bettafish_analyze_polar_sentiment: {
          text: 'Investigasi awal menunjukkan anomali klaim di RS Aegis Medika telah ditinjau verifikator BPJS.',
          domain: 'healthcare_fraud'
        },
        audit_system_diagnostics: {
          include_vault: true,
          include_backends: true
        },
        calibrate_platform_algorithms: {
          platform: 'twitter',
          alpha: 1.15,
          epsilon: 0.08
        },
        bettafish_assess_corporate_risk: {
          target_entity: 'RS Aegis Medika A',
          risk_dimensions: ['FINANCIAL_FRAUD', 'REPUTATION_CONTRACTION']
        },
        query_graph_insights: {
          graph_id: 'mirofish_aegis_jkn_graph',
          query: 'Siapa dokter dan entitas yang terhubung dengan klaim PCI?'
        }
      }
      const sample = samples[name] || {}
      this.payloadJson = JSON.stringify(sample, null, 2)
    },
    async executeTool() {
      if (!this.selectedTool) return
      this.executing = true
      this.error = null
      this.execResult = null
      const startTime = performance.now()

      let params = {}
      try {
        params = JSON.parse(this.payloadJson)
      } catch (e) {
        this.error = 'Format JSON parameter tidak valid: ' + e.message
        this.executing = false
        return
      }

      try {
        const res = await invokeMcpTool(this.selectedTool.name, params)
        this.execLatency = Math.round(performance.now() - startTime)
        this.execResult = res
      } catch (err) {
        this.execLatency = Math.round(performance.now() - startTime)
        this.error = 'Eksekusi alat gagal: ' + err.message
      } finally {
        this.executing = false
      }
    }
  }
}
</script>
