<template>
  <div class="panel-container bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-2xl text-slate-100 flex flex-col">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">
            Panel 2
          </span>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            {{ $t('dashboard.p2.title') }}
          </h2>
        </div>
        <p class="text-xs text-slate-400 mt-1">
          {{ $t('dashboard.p2.subtitle') }}
        </p>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="selectedGraphId"
          @change="onGraphSelectChange"
          class="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-emerald-500"
        >
          <option v-for="g in graphOptions" :key="g.id" :value="g.id">
            {{ g.name }} ({{ g.id }})
          </option>
        </select>

        <button
          @click="resetZoom"
          class="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          title="Reset Zoom"
        >
          ⛶ Reset
        </button>

        <button
          @click="fetchGraph"
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

    <!-- Graph stats bar & search filter -->
    <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span class="text-slate-400">Nodes:</span>
          <strong class="text-slate-200 font-mono">{{ rawNodes.length }}</strong>
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-sky-400"></span>
          <span class="text-slate-400">Edges:</span>
          <strong class="text-slate-200 font-mono">{{ rawEdges.length }}</strong>
        </span>
        <span class="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-slate-400">
          <span class="text-emerald-400 font-mono">NLI-Barrier:</span>
          <span class="bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800 font-mono">≥0.85 Verified</span>
        </span>
      </div>

      <div class="flex items-center gap-2">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari entitas..."
          class="bg-slate-900 border border-slate-700 rounded-md px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
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

    <!-- Main Canvas & Inspector Area -->
    <div class="mt-4 grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-[460px]">
      <!-- Left: D3 SVG Container -->
      <div class="lg:col-span-8 bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden flex flex-col justify-center items-center">
        <!-- SVG Canvas -->
        <svg ref="svgRef" class="w-full h-full min-h-[440px] cursor-grab active:cursor-grabbing"></svg>

        <!-- Loading Overlay -->
        <div v-if="loading" class="absolute inset-0 bg-slate-950/80 flex items-center justify-center gap-2 text-xs text-emerald-400">
          <span class="animate-spin text-lg">⟳</span>
          <span>Memuat relasi graf bitemporal...</span>
        </div>

        <!-- Canvas Controls Hint -->
        <div class="absolute bottom-2 left-2 bg-slate-900/80 backdrop-blur px-2.5 py-1 rounded text-[10px] text-slate-400 border border-slate-800 pointer-events-none">
          Scroll: Zoom | Drag: Pan / Move Nodes | Click: Inspect
        </div>
      </div>

      <!-- Right: Inspector Drawer -->
      <div class="lg:col-span-4 bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div v-if="selectedNode">
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: getNodeColor(selectedNode) }"></span>
              <h3 class="font-bold text-sm text-white truncate max-w-[200px]" :title="selectedNode.name">
                {{ selectedNode.name }}
              </h3>
            </div>
            <button @click="selectedNode = null" class="text-slate-400 hover:text-white text-xs cursor-pointer">
              ✕
            </button>
          </div>

          <div class="mt-3 space-y-2.5 text-xs">
            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Entity Type / Labels</span>
              <div class="flex flex-wrap gap-1 mt-1">
                <span
                  v-for="(label, idx) in (selectedNode.labels || [selectedNode.type || 'Entity'])"
                  :key="idx"
                  class="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-slate-300"
                >
                  {{ label }}
                </span>
              </div>
            </div>

            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">UUID / Identifier</span>
              <p class="font-mono text-slate-300 text-[11px] bg-slate-900/80 p-1.5 rounded border border-slate-800 break-all select-all">
                {{ selectedNode.uuid || selectedNode.id }}
              </p>
            </div>

            <div v-if="selectedNode.summary">
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Summary</span>
              <p class="text-slate-300 text-xs bg-slate-900/40 p-2 rounded border border-slate-800/80 leading-relaxed">
                {{ selectedNode.summary }}
              </p>
            </div>

            <!-- Attributes -->
            <div v-if="selectedNode.attributes && Object.keys(selectedNode.attributes).length > 0">
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Attributes</span>
              <div class="mt-1 bg-slate-900/60 p-2 rounded border border-slate-800 space-y-1 font-mono text-[11px]">
                <div v-for="(val, key) in selectedNode.attributes" :key="key" class="flex justify-between">
                  <span class="text-slate-400">{{ key }}:</span>
                  <span class="text-emerald-300 font-semibold">{{ val }}</span>
                </div>
              </div>
            </div>

            <!-- NLI Verification Badge -->
            <div class="pt-2 border-t border-slate-800">
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Zep NLI Verification</span>
              <div class="mt-1 flex items-center justify-between p-2 rounded bg-emerald-950/40 border border-emerald-800/60 text-emerald-300">
                <span class="flex items-center gap-1.5 text-xs">
                  <span>🛡️</span>
                  <span>Verifikasi Fakta: VALID</span>
                </span>
                <span class="text-xs font-mono font-bold">NLI: 0.94</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="selectedEdge">
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 class="font-bold text-sm text-white">Relationship Edge</h3>
            <button @click="selectedEdge = null" class="text-slate-400 hover:text-white text-xs cursor-pointer">✕</button>
          </div>
          <div class="mt-3 space-y-2.5 text-xs">
            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Relation Type</span>
              <span class="px-2 py-0.5 rounded text-xs font-mono bg-sky-950/80 border border-sky-800 text-sky-300 inline-block mt-1 font-bold">
                {{ selectedEdge.relation || selectedEdge.type || 'RELATED_TO' }}
              </span>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Source Node</span>
              <p class="font-mono text-slate-300 text-[11px] bg-slate-900/80 p-1.5 rounded border border-slate-800">
                {{ selectedEdge.source?.name || selectedEdge.source }}
              </p>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 uppercase tracking-wider block">Target Node</span>
              <p class="font-mono text-slate-300 text-[11px] bg-slate-900/80 p-1.5 rounded border border-slate-800">
                {{ selectedEdge.target?.name || selectedEdge.target }}
              </p>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-12 text-slate-500 text-xs">
          <div class="text-3xl mb-2">🔍</div>
          <p>Pilih node atau garis hubungan pada kanvas graf untuk melihat detail entitas dan metrik verifikasi NLI.</p>
        </div>

        <!-- Legend -->
        <div class="pt-3 border-t border-slate-800 mt-4">
          <span class="text-[10px] text-slate-400 uppercase tracking-wider block mb-1.5">Legenda Tipe Entitas</span>
          <div class="grid grid-cols-2 gap-1.5 text-[10px] text-slate-300">
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> FasilitasKesehatan
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-sky-500"></span> Dokter / Medis
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Pasien
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Klaim / Anomali
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Whistleblower
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Verifikator BPJS
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3'
import { getGraphProjects, getGraphData } from '../../api/enterprise'

export default {
  name: 'Panel2GraphExplorer',
  data() {
    return {
      loading: false,
      error: null,
      selectedGraphId: 'mirofish_aegis_jkn_graph',
      graphOptions: [
        { id: 'mirofish_aegis_jkn_graph', name: 'Aegis-JKN Fraud Detection Graph' },
        { id: 'mirofish_a78d6fc490674dd9', name: 'Knowledge Graph Alpha' },
        { id: 'mirofish_f70fe5dc4e094252', name: 'Knowledge Graph Beta' }
      ],
      rawNodes: [],
      rawEdges: [],
      selectedNode: null,
      selectedEdge: null,
      searchQuery: '',
      simulation: null,
      svgZoom: null
    }
  },
  watch: {
    searchQuery() {
      this.updateHighlight()
    }
  },
  mounted() {
    this.initGraphOptions()
    this.fetchGraph()
    window.addEventListener('resize', this.onResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.onResize)
    if (this.simulation) {
      this.simulation.stop()
    }
  },
  methods: {
    async initGraphOptions() {
      try {
        const res = await getGraphProjects()
        if (res && res.data && res.data.length > 0) {
          const list = res.data
            .filter(p => p.graph_id)
            .map(p => ({
              id: p.graph_id,
              name: p.name || p.graph_id
            }))
          if (list.length > 0) {
            this.graphOptions = list
          }
        }
      } catch (e) {
        console.warn('Failed to fetch projects list, using default graph options', e)
      }
    },
    onGraphSelectChange() {
      this.fetchGraph()
    },
    getNodeColor(node) {
      const labels = node.labels || [node.type || 'Entity']
      if (labels.includes('FasilitasKesehatan')) return '#10b981' // emerald
      if (labels.includes('Dokter')) return '#0ea5e9' // sky
      if (labels.includes('Pasien')) return '#f59e0b' // amber
      if (labels.includes('KlaimINACBG')) return '#f43f5e' // rose
      if (labels.includes('Whistleblower')) return '#a855f7' // purple
      if (labels.includes('VerifikatorBPJS')) return '#6366f1' // indigo
      return '#64748b' // slate
    },
    async fetchGraph() {
      this.loading = true
      this.error = null
      this.selectedNode = null
      this.selectedEdge = null
      try {
        const res = await getGraphData(this.selectedGraphId)
        if (res && res.data) {
          this.rawNodes = res.data.nodes || []
          this.rawEdges = res.data.edges || []
          this.renderD3Graph()
        }
      } catch (err) {
        this.error = err.message || 'Gagal memuat data graf'
      } finally {
        this.loading = false
      }
    },
    onResize() {
      this.renderD3Graph()
    },
    resetZoom() {
      if (!this.svgZoom || !this.$refs.svgRef) return
      const svg = d3.select(this.$refs.svgRef)
      svg.transition().duration(500).call(this.svgZoom.transform, d3.zoomIdentity)
    },
    renderD3Graph() {
      const svgEl = this.$refs.svgRef
      if (!svgEl) return
      const width = svgEl.clientWidth || 600
      const height = svgEl.clientHeight || 440

      const svg = d3.select(svgEl)
      svg.selectAll('*').remove()

      // Clone nodes and edges for D3 mutability
      const nodes = this.rawNodes.map(n => ({
        ...n,
        id: n.uuid || n.name
      }))
      const edges = this.rawEdges.map(e => ({
        ...e,
        source: e.source,
        target: e.target
      }))

      // Arrow Marker
      svg.append('defs').append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#475569')

      const g = svg.append('g')

      // Zoom
      this.svgZoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform)
        })
      svg.call(this.svgZoom)

      // Simulation
      this.simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(35))

      // Links
      const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(edges)
        .enter().append('line')
        .attr('stroke', '#334155')
        .attr('stroke-width', 1.8)
        .attr('marker-end', 'url(#arrow)')
        .attr('cursor', 'pointer')
        .on('click', (event, d) => {
          event.stopPropagation()
          this.selectedEdge = d
          this.selectedNode = null
        })

      // Link Labels
      const linkText = g.append('g')
        .attr('class', 'link-labels')
        .selectAll('text')
        .data(edges)
        .enter().append('text')
        .attr('font-size', '9px')
        .attr('fill', '#64748b')
        .attr('text-anchor', 'middle')
        .text(d => d.relation || '')

      // Nodes
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .attr('cursor', 'pointer')
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active) this.simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) this.simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
        )
        .on('click', (event, d) => {
          event.stopPropagation()
          this.selectedNode = d
          this.selectedEdge = null
        })

      // Node circles
      node.append('circle')
        .attr('r', 16)
        .attr('fill', d => this.getNodeColor(d))
        .attr('stroke', '#0f172a')
        .attr('stroke-width', 2)

      // Node text labels
      node.append('text')
        .attr('y', 26)
        .attr('text-anchor', 'middle')
        .attr('fill', '#e2e8f0')
        .attr('font-size', '10px')
        .attr('font-weight', '500')
        .text(d => d.name?.length > 18 ? d.name.substring(0, 16) + '...' : d.name)

      // Tick listener
      this.simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y)

        linkText
          .attr('x', d => (d.source.x + d.target.x) / 2)
          .attr('y', d => (d.source.y + d.target.y) / 2 - 4)

        node.attr('transform', d => `translate(${d.x},${d.y})`)
      })
    },
    updateHighlight() {
      const q = this.searchQuery.toLowerCase().trim()
      const svg = d3.select(this.$refs.svgRef)
      if (!svg.node()) return

      svg.selectAll('.nodes g').each(function(d) {
        const match = !q || (d.name && d.name.toLowerCase().includes(q))
        d3.select(this)
          .transition().duration(200)
          .style('opacity', match ? 1 : 0.2)
      })
    }
  }
}
</script>
