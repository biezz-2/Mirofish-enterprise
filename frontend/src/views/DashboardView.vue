<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
    <!-- Top Sticky Control Header -->
    <header class="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-xl px-4 lg:px-8 py-3">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        <!-- Brand & Title -->
        <div class="flex items-center gap-3">
          <router-link
            to="/"
            class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors text-xs font-semibold flex items-center gap-1.5"
          >
            <span>{{ $t('dashboard.backHome') }}</span>
          </router-link>

          <div class="h-5 w-px bg-slate-700 hidden sm:block"></div>

          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-base sm:text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
                <span class="text-blue-500">🐟</span>
                <span>Mirofish Enterprise</span>
              </h1>
              <span class="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                Single Pane of Glass
              </span>
            </div>
            <p class="text-[11px] text-slate-400">
              {{ $t('dashboard.subtitle') }}
            </p>
          </div>
        </div>

        <!-- Controls: Status & Language Switcher -->
        <div class="flex items-center gap-3 self-end md:self-auto">
          <router-link
            to="/docs"
            class="px-2.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-md shadow-blue-500/20"
          >
            <span>📚</span>
            <span>Docs</span>
          </router-link>

          <div class="hidden lg:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Cluster SLA: 99.9% (&lt;250ms)</span>
          </div>

          <LanguageSwitcher />
        </div>
      </div>

      <!-- Quick Navigation & Panel Filter Bar -->
      <div class="max-w-7xl mx-auto mt-3 pt-2.5 border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto pb-1 text-xs scrollbar-thin">
        <button
          @click="selectTab('all')"
          :class="[
            'px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 text-xs',
            activeTab === 'all'
              ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-500/20'
              : 'bg-slate-800/80 hover:bg-slate-800 text-slate-300'
          ]"
        >
          <span>👁️</span>
          <span>{{ $t('dashboard.allPanels') }} (8)</span>
        </button>

        <button
          v-for="p in panels"
          :key="p.id"
          @click="selectTab(p.id)"
          :class="[
            'px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 text-xs border',
            activeTab === p.id
              ? 'bg-slate-800 text-white font-bold border-slate-600 ring-1 ring-blue-500/50'
              : 'bg-slate-900/60 hover:bg-slate-800 text-slate-400 border-slate-800 hover:text-slate-200'
          ]"
        >
          <span>{{ p.icon }}</span>
          <span>{{ p.label }}</span>
        </button>
      </div>
    </header>

    <!-- Main Content Container -->
    <main class="max-w-7xl mx-auto w-full px-4 lg:px-8 py-6 flex-1 space-y-6">
      <!-- Panel 1: RecSys Algorithm Calibration Matrix & Pareto Frontier -->
      <section v-show="activeTab === 'all' || activeTab === 'p1'" id="panel-1">
        <Panel1CalibrationMatrix />
      </section>

      <!-- Panel 2: GraphRAG & Graphiti Dual Knowledge Explorer -->
      <section v-show="activeTab === 'all' || activeTab === 'p2'" id="panel-2">
        <Panel2GraphExplorer />
      </section>

      <!-- Panel 3: Live Swarm Simulation Console & Feed Stream -->
      <section v-show="activeTab === 'all' || activeTab === 'p3'" id="panel-3">
        <Panel3SwarmConsole />
      </section>

      <!-- Panel 4: Webhooks, HMAC-SHA256 & DLQ Re-Drive -->
      <section v-show="activeTab === 'all' || activeTab === 'p4'" id="panel-4">
        <Panel4WebhookManager />
      </section>

      <!-- Panel 5: FastMCP 22 Tools Catalog & Sandbox Invoker -->
      <section v-show="activeTab === 'all' || activeTab === 'p5'" id="panel-5">
        <Panel5McpSandbox />
      </section>

      <!-- Panel 6: Cryptographic Audit, CaMeL Shield & Contracts -->
      <section v-show="activeTab === 'all' || activeTab === 'p6'" id="panel-6">
        <Panel6AuditSecurity />
      </section>

      <!-- Panel 7: System Health, Microservices Cluster & WAL Recovery -->
      <section v-show="activeTab === 'all' || activeTab === 'p7'" id="panel-7">
        <Panel7SystemHealth />
      </section>

      <section v-show="activeTab === 'all' || activeTab === 'p8'" id="panel-8">
        <Panel8SimulationVisibility />
      </section>
    </main>

    <!-- Footer -->
    <footer class="bg-slate-900 border-t border-slate-800 px-4 lg:px-8 py-6 text-xs text-slate-400">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-200">Mirofish Enterprise Platform</span>
          <span>•</span>
          <span class="font-mono text-slate-500">Subagent 19 Production Build</span>
        </div>

        <div class="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400">
          <span class="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">FastMCP RFC 7636</span>
          <span class="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">CaMeL 3-Layer Shield</span>
          <span class="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">AES-256-GCM Vault</span>
          <span class="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">OpenAPI 3.1 &amp; Webhooks</span>
        </div>
      </div>
    </footer>

    <!-- Floating Back to Top Button -->
    <button
      v-if="showBackToTop"
      @click="scrollToTop"
      class="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-blue-600 hover:bg-blue-500 text-white shadow-2xl transition-all cursor-pointer flex items-center justify-center border border-blue-400/40"
      title="Kembali ke atas"
    >
      ↑
    </button>
  </div>
</template>

<script>
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import Panel1CalibrationMatrix from '../components/dashboard/Panel1CalibrationMatrix.vue'
import Panel2GraphExplorer from '../components/dashboard/Panel2GraphExplorer.vue'
import Panel3SwarmConsole from '../components/dashboard/Panel3SwarmConsole.vue'
import Panel4WebhookManager from '../components/dashboard/Panel4WebhookManager.vue'
import Panel5McpSandbox from '../components/dashboard/Panel5McpSandbox.vue'
import Panel6AuditSecurity from '../components/dashboard/Panel6AuditSecurity.vue'
import Panel7SystemHealth from '../components/dashboard/Panel7SystemHealth.vue'
import Panel8SimulationVisibility from '../components/dashboard/Panel8SimulationVisibility.vue'

export default {
  name: 'DashboardView',
  components: {
    LanguageSwitcher,
    Panel1CalibrationMatrix,
    Panel2GraphExplorer,
    Panel3SwarmConsole,
    Panel4WebhookManager,
    Panel5McpSandbox,
    Panel6AuditSecurity,
    Panel7SystemHealth,
    Panel8SimulationVisibility
  },
  data() {
    return {
      activeTab: 'all',
      showBackToTop: false,
      panels: [
        { id: 'p1', label: '1. Kalibrasi Algoritma', icon: '📊' },
        { id: 'p2', label: '2. Graf & GraphRAG', icon: '🕸️' },
        { id: 'p3', label: '3. Simulasi Swarm', icon: '🚀' },
        { id: 'p4', label: '4. Webhooks & DLQ', icon: '⚡' },
        { id: 'p5', label: '5. FastMCP Sandbox', icon: '🛠️' },
        { id: 'p6', label: '6. Audit & Keamanan', icon: '🛡️' },
        { id: 'p7', label: '7. Kesehatan Sistem', icon: '🖥️' },
        { id: 'p8', label: '8. Simulation Visibility', icon: '🔎' }
      ]
    }
  },
  mounted() {
    window.addEventListener('scroll', this.handleScroll)
  },
  beforeUnmount() {
    window.removeEventListener('scroll', this.handleScroll)
  },
  methods: {
    selectTab(tabId) {
      this.activeTab = tabId
      if (tabId === 'all') {
        this.scrollToTop()
      } else {
        const el = document.getElementById(`panel-${tabId.replace('p', '')}`)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }
    },
    handleScroll() {
      this.showBackToTop = window.scrollY > 400
    },
    scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  height: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 2px;
}
</style>
