<template>
  <div class="dashboard-page min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-8 pb-4 border-b border-slate-800">
        <div>
          <h1 class="text-3xl font-extrabold text-white tracking-tight">{{ $t('dashboard.title') }}</h1>
          <p class="text-sm text-slate-400 mt-1">{{ $t('dashboard.subtitle') }}</p>
        </div>
        <router-link
          to="/"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-lg transition-colors border border-slate-700"
        >
          {{ $t('dashboard.backHome') }}
        </router-link>
      </div>

      <!-- Kartu Kesehatan Layanan -->
      <HealthCards />

      <!-- Tabel Pekerjaan dan Pemulihan Checkpoint -->
      <div class="grid grid-cols-1 gap-6">
        <JobRecoveryTable />
      </div>
    </div>
  </div>
</template>

<script setup>
import HealthCards from '../components/HealthCards.vue'
import JobRecoveryTable from '../components/JobRecoveryTable.vue'
</script>
