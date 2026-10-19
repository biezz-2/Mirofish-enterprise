<template>
  <div class="panel-container bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-2xl text-slate-100">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded">
            Panel 1
          </span>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            {{ $t('dashboard.p1.title') }}
          </h2>
        </div>
        <p class="text-xs text-slate-400 mt-1">
          {{ $t('dashboard.p1.subtitle') }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="fetchPlatforms"
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

    <!-- Platform Selection Cards (7 Platforms) -->
    <div class="mt-5 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
      <button
        v-for="p in platformsList"
        :key="p.id"
        @click="selectedPlatformId = p.id"
        :class="[
          'p-3 rounded-lg border text-left transition-all cursor-pointer relative overflow-hidden',
          selectedPlatformId === p.id
            ? 'bg-indigo-950/60 border-indigo-500 ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-950/50'
            : 'bg-slate-800/60 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600'
        ]"
      >
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-base">{{ getPlatformIcon(p.id) }}</span>
          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-700/50">
            α {{ p.alpha?.toFixed(2) || '1.10' }}
          </span>
        </div>
        <div class="font-semibold text-xs text-slate-100 truncate">{{ p.name }}</div>
        <div class="text-[10px] text-slate-400 flex items-center justify-between mt-1">
          <span>Gini</span>
          <span class="font-mono text-indigo-300 font-medium">{{ p.gini?.toFixed(2) }}</span>
        </div>
      </button>
    </div>

    <!-- Active Platform Details & Pareto Simulator -->
    <div v-if="activePlatform" class="mt-5 grid grid-cols-1 lg:grid-cols-12 gap-5">
      <!-- Left: Active Platform Specs -->
      <div class="lg:col-span-7 bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <div class="flex items-center gap-2.5">
              <span class="text-2xl">{{ getPlatformIcon(activePlatform.id) }}</span>
              <div>
                <h3 class="text-base font-bold text-white">{{ activePlatform.name }}</h3>
                <p class="text-[11px] text-slate-400 font-mono">ID: {{ activePlatform.id }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 font-medium">
                {{ $t('dashboard.p1.epsilon') }}: ε={{ activePlatform.epsilon ?? '0.08' }}
              </span>
            </div>
          </div>

          <!-- 90-9-1 Rule Visualization -->
          <div class="mt-4">
            <div class="flex justify-between items-center text-xs mb-1.5">
              <span class="text-slate-300 font-medium">{{ $t('dashboard.p1.participationRule') }} (90-9-1)</span>
              <span class="text-[11px] text-slate-400 font-mono">
                L:{{ (activePlatform.participation?.lurker * 100).toFixed(0) }}% |
                C:{{ (activePlatform.participation?.contributor * 100).toFixed(0) }}% |
                Cr:{{ (activePlatform.participation?.creator * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="w-full h-3 rounded-full bg-slate-700/60 overflow-hidden flex">
              <div
                class="bg-sky-500 h-full transition-all"
                :style="{ width: `${(activePlatform.participation?.lurker || 0.9) * 100}%` }"
                title="Lurkers"
              />
              <div
                class="bg-indigo-500 h-full transition-all"
                :style="{ width: `${(activePlatform.participation?.contributor || 0.09) * 100}%` }"
                title="Contributors"
              />
              <div
                class="bg-amber-400 h-full transition-all"
                :style="{ width: `${(activePlatform.participation?.creator || 0.01) * 100}%` }"
                title="Creators"
              />
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 mt-1">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-sky-500 inline-block"></span> Lurker ({{ (activePlatform.participation?.lurker * 100).toFixed(0) }}%)</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-indigo-500 inline-block"></span> Contributor ({{ (activePlatform.participation?.contributor * 100).toFixed(0) }}%)</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400 inline-block"></span> Creator ({{ (activePlatform.participation?.creator * 100).toFixed(0) }}%)</span>
            </div>
          </div>

          <!-- Multi-Task Objective Weights -->
          <div class="mt-4 pt-3 border-t border-slate-800">
            <h4 class="text-xs font-semibold text-slate-300 mb-2">{{ $t('dashboard.p1.rankingWeights') }}</h4>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div class="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div class="text-[10px] text-slate-400">w_dwell (Waktu)</div>
                <div class="text-sm font-mono font-bold text-sky-400">{{ activePlatform.weights?.dwell?.toFixed(2) }}</div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                  <div class="bg-sky-400 h-full" :style="{ width: `${(activePlatform.weights?.dwell || 0) * 100}%` }"></div>
                </div>
              </div>
              <div class="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div class="text-[10px] text-slate-400">w_like (Suka)</div>
                <div class="text-sm font-mono font-bold text-emerald-400">{{ activePlatform.weights?.like?.toFixed(2) }}</div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                  <div class="bg-emerald-400 h-full" :style="{ width: `${(activePlatform.weights?.like || 0) * 100}%` }"></div>
                </div>
              </div>
              <div class="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div class="text-[10px] text-slate-400">w_reply (Komentar)</div>
                <div class="text-sm font-mono font-bold text-indigo-400">{{ activePlatform.weights?.reply?.toFixed(2) }}</div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                  <div class="bg-indigo-400 h-full" :style="{ width: `${(activePlatform.weights?.reply || 0) * 100}%` }"></div>
                </div>
              </div>
              <div class="bg-slate-900/80 p-2 rounded border border-slate-800">
                <div class="text-[10px] text-slate-400">w_share (Virality)</div>
                <div class="text-sm font-mono font-bold text-rose-400">{{ activePlatform.weights?.share?.toFixed(2) }}</div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                  <div class="bg-rose-400 h-full" :style="{ width: `${(activePlatform.weights?.share || 0) * 100}%` }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Parameter Metrics Grid -->
          <div class="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.halflife') }}</span>
              <span class="text-sm font-bold font-mono text-slate-200">{{ activePlatform.halflife_hours }} Jam</span>
            </div>
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.viralityDecay') }}</span>
              <span class="text-sm font-bold font-mono text-amber-300">{{ activePlatform.virality_decay_rate?.toFixed(2) }}</span>
            </div>
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.echoVulnerability') }}</span>
              <span class="text-sm font-bold font-mono text-purple-300">{{ (activePlatform.echo_chamber_vulnerability * 100).toFixed(0) }}%</span>
            </div>
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.top10Share') }}</span>
              <span class="text-sm font-bold font-mono text-teal-300">{{ (activePlatform.top10_share * 100).toFixed(1) }}%</span>
            </div>
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.top1Share') }}</span>
              <span class="text-sm font-bold font-mono text-rose-300">{{ (activePlatform.top1_share * 100).toFixed(1) }}%</span>
            </div>
            <div class="bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
              <span class="text-[10px] text-slate-400 block">{{ $t('dashboard.p1.visualAffinity') }}</span>
              <span class="text-sm font-bold font-mono text-blue-300">{{ (activePlatform.visual_affinity * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Live Pareto Simulator -->
      <div class="lg:col-span-5 bg-slate-800/40 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 class="text-sm font-bold text-white flex items-center gap-1.5">
              <span>⚡</span> {{ $t('dashboard.p1.simulatorTitle') }}
            </h3>
            <span class="text-[11px] text-slate-400">Monte-Carlo Sampling</span>
          </div>

          <!-- Controls -->
          <div class="mt-3 space-y-3">
            <div>
              <div class="flex justify-between text-xs text-slate-300 mb-1">
                <span>{{ $t('dashboard.p1.paramAlpha') }} (α)</span>
                <span class="font-mono text-indigo-300 font-bold">{{ simAlpha.toFixed(2) }}</span>
              </div>
              <input
                type="range"
                v-model.number="simAlpha"
                min="1.01"
                max="3.0"
                step="0.05"
                class="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <div class="flex justify-between text-xs text-slate-300 mb-1">
                <span>{{ $t('dashboard.p1.paramEpsilon') }} (ε)</span>
                <span class="font-mono text-indigo-300 font-bold">{{ simEpsilon.toFixed(2) }}</span>
              </div>
              <input
                type="range"
                v-model.number="simEpsilon"
                min="0.01"
                max="0.30"
                step="0.01"
                class="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <div class="flex justify-between text-xs text-slate-300 mb-1">
                <span>{{ $t('dashboard.p1.paramSampleSize') }} (N)</span>
                <span class="font-mono text-indigo-300 font-bold">{{ simSampleSize }}</span>
              </div>
              <select
                v-model.number="simSampleSize"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option :value="500">500 agen</option>
                <option :value="1000">1,000 agen</option>
                <option :value="2000">2,000 agen</option>
                <option :value="5000">5,000 agen</option>
              </select>
            </div>
          </div>

          <!-- Action Button -->
          <div class="mt-4 flex gap-2">
            <button
              @click="runParetoSim"
              :disabled="simRunning"
              class="flex-1 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md transition-colors flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <span v-if="simRunning" class="animate-spin">⟳</span>
              <span>{{ simRunning ? $t('dashboard.p1.simulating') : $t('dashboard.p1.runSimulation') }}</span>
            </button>
            <button
              @click="resetToPlatformDefaults"
              class="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-medium cursor-pointer"
            >
              Reset
            </button>
          </div>

          <!-- Simulation Output Results -->
          <div v-if="simResult" class="mt-4 p-3 bg-slate-900/90 rounded-lg border border-slate-800">
            <div class="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
              <span>{{ $t('dashboard.p1.simulationOutput') }}</span>
              <span class="text-[10px] font-mono text-emerald-400">OK 200</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center">
              <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
                <div class="text-[10px] text-slate-400">Gini Output</div>
                <div class="text-sm font-bold font-mono text-indigo-300">{{ simResult.gini?.toFixed(3) }}</div>
              </div>
              <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
                <div class="text-[10px] text-slate-400">Top 10% Share</div>
                <div class="text-sm font-bold font-mono text-teal-300">{{ (simResult.top_10_percent_share * 100).toFixed(1) }}%</div>
              </div>
              <div class="p-2 rounded bg-slate-800/60 border border-slate-700/50">
                <div class="text-[10px] text-slate-400">Top 1% Share</div>
                <div class="text-sm font-bold font-mono text-rose-300">{{ (simResult.top_1_percent_share * 100).toFixed(1) }}%</div>
              </div>
            </div>

            <!-- Mini Attention Distribution Curve -->
            <div class="mt-3">
              <div class="text-[10px] text-slate-400 mb-1 flex justify-between">
                <span>{{ $t('dashboard.p1.attentionCurve') }}</span>
                <span class="font-mono text-slate-500">Pareto (α={{ simResult.alpha }})</span>
              </div>
              <div class="h-10 w-full flex items-end gap-1 bg-slate-950 p-1 rounded border border-slate-800/70">
                <div
                  v-for="(bar, i) in curveBars"
                  :key="i"
                  class="flex-1 bg-indigo-500/80 hover:bg-indigo-400 rounded-t transition-all"
                  :style="{ height: `${Math.max(bar, 6)}%` }"
                  :title="`Bin ${i + 1}: ${bar.toFixed(1)}%`"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Comparative Matrix Table across all 7 platforms -->
    <div class="mt-6 pt-5 border-t border-slate-800">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-slate-200">
          {{ $t('dashboard.p1.matrixTableTitle') }}
        </h3>
        <span class="text-xs text-slate-400">7 Platforms Calibrated</span>
      </div>

      <div class="overflow-x-auto rounded-lg border border-slate-800">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th class="py-2.5 px-3">Platform</th>
              <th class="py-2.5 px-3 text-right">Alpha (α)</th>
              <th class="py-2.5 px-3 text-right">Gini Coeff</th>
              <th class="py-2.5 px-3 text-right">Halflife (t½)</th>
              <th class="py-2.5 px-3 text-right">90-9-1 (Cr%)</th>
              <th class="py-2.5 px-3 text-right">Virality Decay</th>
              <th class="py-2.5 px-3 text-right">Echo Chamber</th>
              <th class="py-2.5 px-3 text-right">Exploration (ε)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 bg-slate-900/40">
            <tr
              v-for="p in platformsList"
              :key="p.id"
              @click="selectedPlatformId = p.id"
              :class="[
                'hover:bg-slate-800/60 transition-colors cursor-pointer',
                selectedPlatformId === p.id ? 'bg-indigo-950/30 font-medium' : ''
              ]"
            >
              <td class="py-2.5 px-3 flex items-center gap-2">
                <span>{{ getPlatformIcon(p.id) }}</span>
                <span class="text-slate-100 font-semibold">{{ p.name }}</span>
              </td>
              <td class="py-2.5 px-3 text-right font-mono">{{ p.alpha?.toFixed(2) }}</td>
              <td class="py-2.5 px-3 text-right font-mono text-indigo-300">{{ p.gini?.toFixed(2) }}</td>
              <td class="py-2.5 px-3 text-right font-mono">{{ p.halflife_hours }}h</td>
              <td class="py-2.5 px-3 text-right font-mono text-amber-300">{{ ((p.participation?.creator || 0.01) * 100).toFixed(1) }}%</td>
              <td class="py-2.5 px-3 text-right font-mono">{{ p.virality_decay_rate?.toFixed(2) }}</td>
              <td class="py-2.5 px-3 text-right font-mono" :class="p.echo_chamber_vulnerability > 0.7 ? 'text-rose-400 font-bold' : 'text-slate-300'">
                {{ ((p.echo_chamber_vulnerability || 0) * 100).toFixed(0) }}%
              </td>
              <td class="py-2.5 px-3 text-right font-mono text-sky-300">ε={{ p.epsilon ?? '0.08' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { getPlatformMatrix, simulatePareto } from '../../api/enterprise'

export default {
  name: 'Panel1CalibrationMatrix',
  data() {
    return {
      loading: false,
      error: null,
      platforms: {},
      selectedPlatformId: 'x',
      // Simulation parameters
      simAlpha: 1.15,
      simEpsilon: 0.08,
      simSampleSize: 1000,
      simRunning: false,
      simResult: null
    }
  },
  computed: {
    platformsList() {
      return Object.entries(this.platforms).map(([id, data]) => ({
        id,
        ...data
      }))
    },
    activePlatform() {
      return this.platforms[this.selectedPlatformId]
        ? { id: this.selectedPlatformId, ...this.platforms[this.selectedPlatformId] }
        : null
    },
    curveBars() {
      if (!this.simResult) {
        return [85, 45, 25, 15, 10, 7, 5, 4, 3, 2]
      }
      const alpha = this.simResult.alpha || 1.15
      // Generate 10 power-law decay buckets for visualization
      return Array.from({ length: 10 }, (_, i) => {
        const rank = i + 1
        const raw = 100 / Math.pow(rank, alpha)
        return Math.min(100, Math.max(4, raw))
      })
    }
  },
  watch: {
    selectedPlatformId() {
      this.resetToPlatformDefaults()
    }
  },
  mounted() {
    this.fetchPlatforms()
  },
  methods: {
    getPlatformIcon(id) {
      const normalizedId = (id || '').toLowerCase()
      const icons = {
        x: '𝕏',
        twitter: '𝕏',
        reddit: '🤖',
        tiktok: '🎵',
        instagram: '📷',
        facebook: '👥',
        youtube: '▶️',
        linkedin: '💼',
        threads: '🧵'
      }
      return icons[normalizedId] || '🌐'
    },
    async fetchPlatforms() {
      this.loading = true
      this.error = null
      try {
        const res = await getPlatformMatrix()
        const matrixData = res?.matrix || res?.data?.matrix || (res?.platforms && typeof res.platforms === 'object' && !Array.isArray(res.platforms) ? res.platforms : null)
        if (matrixData && typeof matrixData === 'object') {
          // Normalize API response fields to component expectations
          const normalized = {}
          for (const [key, val] of Object.entries(matrixData)) {
            normalized[key] = {
              name: val.platform_name || key.toUpperCase(),
              alpha: val.pareto_alpha ?? val.alpha ?? 1.15,
              gini: val.gini_coefficient ?? val.gini ?? 0.65,
              halflife_hours: val.halflife_hours ?? 1.0,
              participation: {
                creator: val.creator_ratio ?? 0.01,
                contributor: val.contributor_ratio ?? 0.09,
                lurker: val.lurker_ratio ?? 0.90
              },
              virality_decay_rate: val.virality_decay_rate ?? 0.75,
              echo_chamber_vulnerability: val.echo_chamber_vulnerability ?? 0.70,
              epsilon: val.recommended_epsilon ?? val.epsilon ?? 0.08,
              weights: {
                dwell: val.multi_task_weights?.w_dwell ?? val.weights?.dwell ?? 0.15,
                like: val.multi_task_weights?.w_like ?? val.weights?.like ?? 0.25,
                reply: val.multi_task_weights?.w_reply ?? val.weights?.reply ?? 0.25,
                share: val.multi_task_weights?.w_share ?? val.weights?.share ?? 0.35
              },
              ranking_weights: val.multi_task_weights || { w_dwell: 0.15, w_like: 0.25, w_reply: 0.25, w_share: 0.35 },
              visual_affinity: val.visual_affinity ?? 0.5,
              top10_share: val.top_10_percent_attention_share ?? val.top_10_percent_share ?? 0.60,
              top1_share: val.top_1_percent_attention_share ?? val.top_1_percent_share ?? 0.35
            }
          }
          this.platforms = normalized
          if (!this.platforms[this.selectedPlatformId] && Object.keys(normalized).length > 0) {
            this.selectedPlatformId = Object.keys(normalized)[0]
          }
          this.resetToPlatformDefaults()
        }
      } catch (err) {
        this.error = err.message || 'Gagal memuat matriks kalibrasi platform'
      } finally {
        this.loading = false
      }
    },
    resetToPlatformDefaults() {
      if (this.activePlatform) {
        this.simAlpha = this.activePlatform.alpha || 1.15
        this.simEpsilon = this.activePlatform.epsilon ?? 0.08
        this.simResult = {
          alpha: this.activePlatform.alpha,
          gini: this.activePlatform.gini,
          top_10_percent_share: this.activePlatform.top10_share,
          top_1_percent_share: this.activePlatform.top1_share
        }
      }
    },
    async runParetoSim() {
      this.simRunning = true
      try {
        const res = await simulatePareto({
          platform: this.selectedPlatformId,
          n_agents: this.simSampleSize,
          sample_size: this.simSampleSize,
          alpha: this.simAlpha,
          epsilon: this.simEpsilon
        })
        if (res && res.simulation) {
          const sim = res.simulation
          this.simResult = {
            ...sim,
            alpha: sim.alpha || this.simAlpha,
            gini: sim.gini ?? sim.empirical_gini_coefficient ?? sim.theoretical_gini_coefficient ?? 0.65,
            top_10_percent_share: sim.top_10_percent_share ?? sim.top_10_percent_attention_share ?? 0.60,
            top_1_percent_share: sim.top_1_percent_share ?? sim.top_1_percent_attention_share ?? 0.35
          }
        }
      } catch (err) {
        this.error = 'Simulasi Pareto gagal: ' + err.message
      } finally {
        this.simRunning = false
      }
    }
  }
}
</script>
