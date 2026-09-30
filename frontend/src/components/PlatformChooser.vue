<template>
  <div class="platform-chooser bg-slate-900 border border-slate-800 rounded-xl p-5 text-slate-100">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-white">{{ $t('platforms.title') }}</h3>
        <p class="text-xs text-slate-400">{{ $t('platforms.selectPlatforms') }}</p>
      </div>
      <div class="text-xs px-2.5 py-1 bg-indigo-950 text-indigo-400 border border-indigo-800/60 rounded font-medium">
        {{ selectedPlatforms.length }} / {{ Object.keys(platforms).length }} Aktif
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
      <div
        v-for="(p, key) in platforms"
        :key="key"
        @click="togglePlatform(key)"
        :class="isSelected(key) ? 'border-indigo-500 bg-indigo-950/30' : 'border-slate-800 bg-slate-850/60 hover:border-slate-700'"
        class="cursor-pointer border rounded-lg p-3.5 transition-all flex flex-col justify-between"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="font-bold text-sm text-white flex items-center gap-2">
              <span>{{ p.display_name }}</span>
            </div>
            <div class="text-xs text-slate-400 mt-1 capitalize">{{ p.interaction_style.replace('_', ' ') }}</div>
          </div>
          <input
            type="checkbox"
            :checked="isSelected(key)"
            class="rounded text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-slate-900 border-slate-700 pointer-events-none mt-0.5"
          />
        </div>

        <div class="mt-3 pt-2.5 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
          <div>Kebaruan: <span class="text-slate-200 font-semibold">{{ p.recency_weight }}</span></div>
          <div>Viral: <span class="text-slate-200 font-semibold">{{ p.viral_threshold.toLocaleString() }}</span></div>
          <div>Echo: <span class="text-slate-200 font-semibold">{{ p.echo_chamber_strength }}</span></div>
          <div>Maks Teks: <span class="text-slate-200 font-semibold">{{ p.max_content_length }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => ['twitter', 'reddit']
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedPlatforms = ref([...props.modelValue])
const platforms = ref({
  twitter: { display_name: 'Twitter', recency_weight: 0.8, viral_threshold: 5000, echo_chamber_strength: 0.5, max_content_length: 280, interaction_style: 'ephemeral' },
  x: { display_name: 'X', recency_weight: 0.8, viral_threshold: 8000, echo_chamber_strength: 0.5, max_content_length: 25000, interaction_style: 'ephemeral_long' },
  reddit: { display_name: 'Reddit', recency_weight: 0.4, viral_threshold: 300, echo_chamber_strength: 0.7, max_content_length: 40000, interaction_style: 'persistent_deep' },
  tiktok: { display_name: 'TikTok', recency_weight: 0.6, viral_threshold: 50000, echo_chamber_strength: 0.4, max_content_length: 150, interaction_style: 'algorithmic_viral' },
  instagram: { display_name: 'Instagram', recency_weight: 0.5, viral_threshold: 10000, echo_chamber_strength: 0.5, max_content_length: 2200, interaction_style: 'visual_follower' },
  facebook: { display_name: 'Facebook', recency_weight: 0.4, viral_threshold: 8000, echo_chamber_strength: 0.8, max_content_length: 63000, interaction_style: 'broad_network' },
  threads: { display_name: 'Threads', recency_weight: 0.7, viral_threshold: 5000, echo_chamber_strength: 0.5, max_content_length: 500, interaction_style: 'conversational' },
})

const isSelected = (key) => selectedPlatforms.value.includes(key)

const togglePlatform = (key) => {
  const idx = selectedPlatforms.value.indexOf(key)
  if (idx > -1) {
    if (selectedPlatforms.value.length > 1) {
      selectedPlatforms.value.splice(idx, 1)
    }
  } else {
    selectedPlatforms.value.push(key)
  }
  emit('update:modelValue', selectedPlatforms.value)
}

onMounted(async () => {
  try {
    const res = await fetch('/api/platforms')
    if (res.ok) {
      const data = await res.json()
      if (data.data) {
        platforms.value = data.data
      }
    }
  } catch (e) {
    // fallback default
  }
})
</script>
