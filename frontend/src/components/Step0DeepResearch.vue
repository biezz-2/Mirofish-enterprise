<template>
  <div class="step0-container p-6 bg-slate-900 text-slate-100 rounded-xl shadow-lg border border-slate-800">
    <div class="step-header mb-6">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold tracking-tight text-white">{{ $t('step0.title') }}</h2>
        <div class="privacy-badge inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 rounded-full text-xs font-medium">
          <span>🔒</span>
          <span>{{ $t('step0.privacyFriendly') }}</span>
          <span class="bg-emerald-800/80 text-white px-1.5 py-0.5 rounded text-[10px]">SearXNG</span>
        </div>
      </div>
      <p class="text-sm text-slate-400 mt-2">{{ $t('step0.description') }}</p>
    </div>

    <div class="research-config bg-slate-800/60 p-5 rounded-lg border border-slate-700/60 mb-6">
      <label class="block text-sm font-semibold text-slate-300 mb-2">{{ $t('step0.mainQuery') }}</label>
      <div class="flex gap-3 mb-4">
        <input
          v-model="mainQuery"
          @keyup.enter="startResearch"
          :placeholder="$t('step0.queryPlaceholder')"
          class="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-sm"
        />
        <button
          class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-lg text-sm transition-colors"
          @click="startResearch"
          :disabled="!mainQuery || isResearching"
        >
          {{ isResearching ? $t('step0.researching') : $t('step0.startResearch') }}
        </button>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-xs font-medium text-slate-400">{{ $t('step0.researchType') }}:</span>
        <div class="flex gap-2">
          <button
            v-for="t in researchTypes"
            :key="t"
            @click="researchType = t"
            :class="researchType === t ? 'bg-indigo-900/80 text-indigo-300 border-indigo-600' : 'bg-slate-800 text-slate-400 border-slate-700'"
            class="px-3 py-1 rounded border text-xs font-medium transition-colors"
          >
            {{ $t('step0.type' + t.charAt(0).toUpperCase() + t.slice(1)) }}
          </button>
        </div>
      </div>
    </div>

    <!-- Hasil Riset -->
    <div v-if="researchResult" class="research-results bg-slate-800/40 p-5 rounded-lg border border-slate-700/60 mb-6">
      <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
        <div class="flex gap-3">
          <button
            v-for="tab in ['facts', 'entities', 'sources', 'trends']"
            :key="tab"
            @click="activeTab = tab"
            :class="activeTab === tab ? 'text-indigo-400 border-b-2 border-indigo-500 pb-1 font-semibold' : 'text-slate-400 font-medium'"
            class="text-sm px-1 transition-colors"
          >
            {{ $t('step0.tab' + tab.charAt(0).toUpperCase() + tab.slice(1)) }}
          </button>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <span class="text-slate-400">{{ $t('step0.credibilityScore') }}:</span>
          <span class="font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            {{ (researchResult.credibility_score * 100).toFixed(0) }}%
          </span>
        </div>
      </div>

      <div v-show="activeTab === 'facts'" class="space-y-2.5">
        <div v-for="(fact, i) in researchResult.summarized_facts" :key="i" class="text-sm text-slate-200 bg-slate-900/60 p-3 rounded border border-slate-800/80">
          <span class="text-indigo-400 font-bold mr-2">{{ i + 1 }}.</span> {{ fact }}
        </div>
      </div>

      <div v-show="activeTab === 'entities'" class="grid grid-cols-2 md:grid-cols-4 gap-2.5">
        <div v-for="(e, i) in researchResult.entities_mentioned" :key="i" class="p-3 bg-slate-900/80 rounded border border-slate-800">
          <div class="text-sm font-semibold text-slate-100">{{ e.name }}</div>
          <div class="text-xs text-indigo-400 uppercase mt-0.5">{{ e.type }}</div>
        </div>
      </div>

      <div v-show="activeTab === 'sources'" class="space-y-2">
        <a
          v-for="(s, i) in researchResult.web_results.slice(0, 8)"
          :key="i"
          :href="s.url"
          target="_blank"
          class="block p-3 bg-slate-900/60 hover:bg-slate-900 rounded border border-slate-800 transition-colors"
        >
          <div class="text-sm font-medium text-indigo-300 hover:underline">{{ s.title }}</div>
          <div class="text-xs text-slate-400 mt-1 line-clamp-2">{{ s.content }}</div>
          <div class="text-[11px] text-slate-500 mt-1 flex gap-2">
            <span>Mesin: {{ s.engine }}</span>
            <span>Skor: {{ (s.relevance_score * 100).toFixed(0) }}%</span>
          </div>
        </a>
      </div>

      <div v-show="activeTab === 'trends'" class="space-y-2">
        <div v-for="(t, i) in researchResult.trends" :key="i" class="text-sm text-slate-300 bg-slate-900/60 p-3 rounded">
          ⚡ {{ t }}
        </div>
      </div>
    </div>

    <!-- Tombol Aksi -->
    <div class="action-buttons flex justify-between items-center pt-2">
      <button
        class="px-5 py-2.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 text-sm font-medium transition-colors"
        @click="skipResearch"
        :disabled="isResearching"
      >
        {{ $t('common.close') }} / Lewati
      </button>
      <button
        class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-lg text-sm transition-colors shadow"
        @click="proceedToStep1"
        :disabled="isResearching"
      >
        {{ $t('step0.proceed') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['completed', 'skip'])

const mainQuery = ref('')
const researchType = ref('general')
const researchTypes = ['general', 'news', 'images']
const isResearching = ref(false)
const researchResult = ref(null)
const activeTab = ref('facts')

const startResearch = async () => {
  if (!mainQuery.value) return
  isResearching.value = true
  try {
    const resp = await fetch('/api/research/searchxng', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: mainQuery.value,
        research_type: researchType.value,
        max_results: 15
      })
    })
    if (!resp.ok) throw new Error('Riset web gagal')
    const data = await resp.json()
    researchResult.value = data.data
  } catch (err) {
    console.error('Kesalahan riset SearXNG:', err)
  } finally {
    isResearching.value = false
  }
}

const skipResearch = () => {
  emit('skip')
}

const proceedToStep1 = () => {
  if (researchResult.value) {
    sessionStorage.setItem('webResearchData', JSON.stringify(researchResult.value))
  }
  emit('completed', researchResult.value)
}
</script>
