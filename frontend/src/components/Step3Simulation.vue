<template>
  <div class="simulation-panel">
    <!-- Top Control Bar -->
    <div class="control-bar">
      <div class="status-group">
        <!-- 动态渲染所有活跃平台进度 (支持7大平台) -->
        <div
          v-for="pKey in activePlatformsList"
          :key="pKey"
          class="platform-status"
          :class="[pKey, { active: isPlatformRunning(pKey), completed: isPlatformCompleted(pKey), selected: activePlatformFilter === pKey }]"
          @click="togglePlatformFilter(pKey)"
          :title="`Filter platform ${getPlatformDisplayName(pKey)}`"
        >
          <div class="platform-header">
            <span class="platform-dot" :style="{ backgroundColor: getPlatformColor(pKey) }"></span>
            <span class="platform-icon-wrap" :style="{ color: getPlatformColor(pKey) }">
              <svg v-if="pKey === 'twitter'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              <svg v-else-if="pKey === 'reddit'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.688-.562-1.249-1.25-1.249zm-4.466 3.99a.327.327 0 0 0-.231.096.35.35 0 0 0 0 .486c.743.743 2.052.796 2.946.796.894 0 2.203-.053 2.946-.796a.35.35 0 0 0 0-.486.327.327 0 0 0-.462 0c-.547.546-1.636.634-2.484.634-.848 0-1.937-.088-2.484-.634a.332.332 0 0 0-.231-.096z"/></svg>
              <svg v-else-if="pKey === 'tiktok'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.98-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.24 1.07-.14 1.61.24 1.64 1.82 2.89 3.5 2.74 1.25-.03 2.39-.77 2.89-1.9.23-.46.33-.98.34-1.5.04-3.6.01-7.2.03-10.8.01-4.41-.01-8.82.02-13.23z"/></svg>
              <svg v-else-if="pKey === 'instagram'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
              <svg v-else-if="pKey === 'threads'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12.186 24h-.007c-3.581-.024-6.33-1.204-8.172-3.507C2.235 18.225 1.44 15.155 1.643 11.38c.241-4.484 2.227-8.082 5.897-10.695C9.728.536 12.392-.008 15.452.001c3.151.01 5.908.629 8.194 1.841l-1.378 2.658c-1.921-.994-4.215-1.503-6.818-1.512-2.433-.008-4.526.417-6.223 1.265-2.915 1.455-4.469 4.316-4.619 8.502-.158 2.923.407 5.253 1.681 6.924 1.341 1.758 3.398 2.664 6.113 2.697 2.457.029 4.417-.57 5.828-1.782.983-.844 1.674-2.025 2.052-3.51-.555-.224-1.217-.42-1.97-.583-.497 2.164-1.92 3.488-4.228 3.513-1.332.015-2.482-.39-3.418-1.203-1.096-.952-1.638-2.316-1.609-4.053.031-1.854.673-3.277 1.908-4.23 1.157-.893 2.766-1.343 4.783-1.337 1.839.006 3.35.344 4.49 1.006.183.106.353.22.509.341.055-.99-.026-1.879-.244-2.645-.487-1.71-1.583-2.946-3.256-3.673-1.425-.619-3.21-.933-5.305-.935l-.014-3.003c2.478.002 4.606.376 6.326 1.11 2.378 1.017 3.974 2.802 4.743 5.307.351 1.144.475 2.458.369 3.904l.006.01c-.044.82-.162 1.98-.363 3.35 1.066.86 1.968 1.94 2.628 3.14l-2.617 1.51c-.482-.876-1.157-1.673-1.982-2.33-.508 1.85-1.442 3.33-2.73 4.44-1.865 1.608-4.364 2.4-7.426 2.36z"/></svg>
              <svg v-else-if="pKey === 'linkedin'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              <svg v-else-if="pKey === 'youtube'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </span>
            <span class="platform-name">{{ getPlatformDisplayName(pKey) }}</span>
            <span v-if="isPlatformCompleted(pKey)" class="status-badge">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </span>
          </div>
          <div class="platform-stats">
            <span class="stat">
              <span class="stat-label">ROUND</span>
              <span class="stat-value mono">{{ getPlatformRound(pKey) }}<span class="stat-total">/{{ runStatus.total_rounds || maxRounds || '-' }}</span></span>
            </span>
            <span class="stat">
              <span class="stat-label">TIME</span>
              <span class="stat-value mono">{{ getPlatformElapsedTime(pKey) }}</span>
            </span>
            <span class="stat">
              <span class="stat-label">ACTS</span>
              <span class="stat-value mono">{{ getPlatformActionCount(pKey) || runStatus[`${pKey}_actions_count`] || 0 }}</span>
            </span>
          </div>
          <!-- 可用动作提示 -->
          <div class="actions-tooltip">
            <div class="tooltip-title">{{ getPlatformSubname(pKey) }} Actions</div>
            <div class="tooltip-actions">
              <span v-for="act in getPlatformActionsList(pKey)" :key="act" class="tooltip-action">{{ act }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="action-controls">
        <button
          class="action-btn primary"
          :disabled="phase !== 2 || isGeneratingReport"
          @click="handleNextStep"
        >
          <span v-if="isGeneratingReport" class="loading-spinner-small"></span>
          {{ isGeneratingReport ? $t('step3.generatingReportBtn') : $t('step3.startGenerateReportBtn') }}
          <span v-if="!isGeneratingReport" class="arrow-icon">→</span>
        </button>
      </div>
    </div>

    <!-- Main Content: Timeline Feed & Chat Frame -->
    <div class="main-content-area" ref="scrollContainer">
      <!-- Enhanced Timeline Header with Controls -->
      <div class="timeline-header" v-if="allActions.length > 0">
        <!-- Top Toolbar Row -->
        <div class="timeline-toolbar">
          <div class="timeline-stats">
            <span class="total-count">TOTAL: <span class="mono">{{ allActions.length }}</span></span>
            <span v-if="activePlatformFilter !== 'all'" class="filter-indicator">
              FILTER: <span class="mono" :style="{ color: getPlatformColor(activePlatformFilter) }">{{ activePlatformFilter.toUpperCase() }} ({{ chronologicalActions.length }})</span>
              <button class="clear-filter-mini" @click="activePlatformFilter = 'all'" title="Reset Filter">✕</button>
            </span>
          </div>

          <div class="timeline-actions-group">
            <!-- Layout Switcher: Stream vs Dual -->
            <div class="view-mode-toggle">
              <button
                class="mode-btn"
                :class="{ active: timelineLayoutMode === 'stream' }"
                @click="timelineLayoutMode = 'stream'"
                :title="$t('step3.streamMode')"
              >
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="8" y1="6" x2="21" y2="6"></line>
                  <line x1="8" y1="12" x2="21" y2="12"></line>
                  <line x1="8" y1="18" x2="21" y2="18"></line>
                  <line x1="3" y1="6" x2="3.01" y2="6"></line>
                  <line x1="3" y1="12" x2="3.01" y2="12"></line>
                  <line x1="3" y1="18" x2="3.01" y2="18"></line>
                </svg>
                <span>{{ $t('step3.streamMode') }}</span>
              </button>
              <button
                class="mode-btn"
                :class="{ active: timelineLayoutMode === 'dual' }"
                @click="timelineLayoutMode = 'dual'"
                :title="$t('step3.dualMode')"
              >
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="2" x2="12" y2="22"></line>
                  <rect x="2" y="5" width="7" height="5" rx="1"></rect>
                  <rect x="15" y="14" width="7" height="5" rx="1"></rect>
                </svg>
                <span>{{ $t('step3.dualMode') }}</span>
              </button>
            </div>

            <!-- Auto-scroll Toggle -->
            <button
              class="autoscroll-toggle-btn"
              :class="{ active: isAutoScrollEnabled }"
              @click="isAutoScrollEnabled = !isAutoScrollEnabled"
              :title="isAutoScrollEnabled ? $t('step3.autoScrollOn') : $t('step3.autoScrollPaused')"
            >
              <span class="status-indicator-dot" :class="{ running: isAutoScrollEnabled }"></span>
              <span class="autoscroll-text">{{ isAutoScrollEnabled ? $t('step3.autoScrollOn') : $t('step3.autoScrollPaused') }}</span>
            </button>
          </div>
        </div>

        <!-- Platform Filter Tabs Row -->
        <div class="platform-filter-tabs">
          <button
            class="filter-tab"
            :class="{ active: activePlatformFilter === 'all' }"
            @click="activePlatformFilter = 'all'"
          >
            <span class="tab-label">{{ $t('step3.allPlatforms') }}</span>
            <span class="tab-count mono">{{ allActions.length }}</span>
          </button>
          <button
            v-for="pKey in activePlatformsList"
            :key="pKey"
            class="filter-tab"
            :class="{ active: activePlatformFilter === pKey }"
            :style="activePlatformFilter === pKey ? { borderColor: getPlatformColor(pKey), color: getPlatformColor(pKey) } : {}"
            @click="togglePlatformFilter(pKey)"
          >
            <span class="tab-icon" :style="{ color: getPlatformColor(pKey) }">
              <svg v-if="pKey === 'twitter'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              <svg v-else-if="pKey === 'reddit'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.688-.562-1.249-1.25-1.249zm-4.466 3.99a.327.327 0 0 0-.231.096.35.35 0 0 0 0 .486c.743.743 2.052.796 2.946.796.894 0 2.203-.053 2.946-.796a.35.35 0 0 0 0-.486.327.327 0 0 0-.462 0c-.547.546-1.636.634-2.484.634-.848 0-1.937-.088-2.484-.634a.332.332 0 0 0-.231-.096z"/></svg>
              <svg v-else-if="pKey === 'tiktok'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.98-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.24 1.07-.14 1.61.24 1.64 1.82 2.89 3.5 2.74 1.25-.03 2.39-.77 2.89-1.9.23-.46.33-.98.34-1.5.04-3.6.01-7.2.03-10.8.01-4.41-.01-8.82.02-13.23z"/></svg>
              <svg v-else-if="pKey === 'instagram'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
              <svg v-else-if="pKey === 'threads'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M12.186 24h-.007c-3.581-.024-6.33-1.204-8.172-3.507C2.235 18.225 1.44 15.155 1.643 11.38c.241-4.484 2.227-8.082 5.897-10.695C9.728.536 12.392-.008 15.452.001c3.151.01 5.908.629 8.194 1.841l-1.378 2.658c-1.921-.994-4.215-1.503-6.818-1.512-2.433-.008-4.526.417-6.223 1.265-2.915 1.455-4.469 4.316-4.619 8.502-.158 2.923.407 5.253 1.681 6.924 1.341 1.758 3.398 2.664 6.113 2.697 2.457.029 4.417-.57 5.828-1.782.983-.844 1.674-2.025 2.052-3.51-.555-.224-1.217-.42-1.97-.583-.497 2.164-1.92 3.488-4.228 3.513-1.332.015-2.482-.39-3.418-1.203-1.096-.952-1.638-2.316-1.609-4.053.031-1.854.673-3.277 1.908-4.23 1.157-.893 2.766-1.343 4.783-1.337 1.839.006 3.35.344 4.49 1.006.183.106.353.22.509.341.055-.99-.026-1.879-.244-2.645-.487-1.71-1.583-2.946-3.256-3.673-1.425-.619-3.21-.933-5.305-.935l-.014-3.003c2.478.002 4.606.376 6.326 1.11 2.378 1.017 3.974 2.802 4.743 5.307.351 1.144.475 2.458.369 3.904l.006.01c-.044.82-.162 1.98-.363 3.35 1.066.86 1.968 1.94 2.628 3.14l-2.617 1.51c-.482-.876-1.157-1.673-1.982-2.33-.508 1.85-1.442 3.33-2.73 4.44-1.865 1.608-4.364 2.4-7.426 2.36z"/></svg>
              <svg v-else-if="pKey === 'linkedin'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              <svg v-else-if="pKey === 'youtube'" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </span>
            <span class="tab-label">{{ getPlatformDisplayName(pKey) }}</span>
            <span class="tab-count mono">{{ getPlatformActionCount(pKey) }}</span>
          </button>
        </div>
      </div>

      <!-- Timeline Feed Container -->
      <div
        class="timeline-feed"
        :class="[timelineLayoutMode === 'stream' ? 'mode-stream' : 'mode-dual']"
      >
        <div class="timeline-axis"></div>

        <TransitionGroup name="timeline-item">
          <div
            v-for="(action, aIdx) in chronologicalActions"
            :key="action._uniqueId || action.id || `${action.timestamp}-${action.agent_id}`"
            class="timeline-item"
            :class="[action.platform, aIdx % 2 === 0 ? 'item-left' : 'item-right']"
          >
            <div class="timeline-marker" :style="{ borderColor: getPlatformColor(action.platform) }">
              <div class="marker-dot" :style="{ backgroundColor: getPlatformColor(action.platform) }"></div>
            </div>

            <div class="timeline-card" :style="{ borderLeftColor: getPlatformColor(action.platform) }">
              <div class="card-header">
                <div class="agent-info">
                  <div class="avatar-placeholder" :style="{ backgroundColor: getPlatformColor(action.platform) }">
                    {{ (action.agent_name || 'A')[0].toUpperCase() }}
                  </div>
                  <div class="agent-details">
                    <span class="agent-name">{{ action.agent_name }}</span>
                    <span v-if="action.agent_id" class="agent-handle mono">@{{ action.agent_id }}</span>
                  </div>
                </div>

                <div class="header-meta">
                  <div
                    class="platform-indicator"
                    :class="action.platform"
                    :style="{ borderColor: getPlatformColor(action.platform) + '44', backgroundColor: getPlatformColor(action.platform) + '12' }"
                  >
                    <span class="platform-indicator-icon" :style="{ color: getPlatformColor(action.platform) }">
                      <svg v-if="action.platform === 'twitter'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                      <svg v-else-if="action.platform === 'reddit'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.688-.562-1.249-1.25-1.249zm-4.466 3.99a.327.327 0 0 0-.231.096.35.35 0 0 0 0 .486c.743.743 2.052.796 2.946.796.894 0 2.203-.053 2.946-.796a.35.35 0 0 0 0-.486.327.327 0 0 0-.462 0c-.547.546-1.636.634-2.484.634-.848 0-1.937-.088-2.484-.634a.332.332 0 0 0-.231-.096z"/></svg>
                      <svg v-else-if="action.platform === 'tiktok'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.98-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.24 1.07-.14 1.61.24 1.64 1.82 2.89 3.5 2.74 1.25-.03 2.39-.77 2.89-1.9.23-.46.33-.98.34-1.5.04-3.6.01-7.2.03-10.8.01-4.41-.01-8.82.02-13.23z"/></svg>
                      <svg v-else-if="action.platform === 'instagram'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                      <svg v-else-if="action.platform === 'threads'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M12.186 24h-.007c-3.581-.024-6.33-1.204-8.172-3.507C2.235 18.225 1.44 15.155 1.643 11.38c.241-4.484 2.227-8.082 5.897-10.695C9.728.536 12.392-.008 15.452.001c3.151.01 5.908.629 8.194 1.841l-1.378 2.658c-1.921-.994-4.215-1.503-6.818-1.512-2.433-.008-4.526.417-6.223 1.265-2.915 1.455-4.469 4.316-4.619 8.502-.158 2.923.407 5.253 1.681 6.924 1.341 1.758 3.398 2.664 6.113 2.697 2.457.029 4.417-.57 5.828-1.782.983-.844 1.674-2.025 2.052-3.51-.555-.224-1.217-.42-1.97-.583-.497 2.164-1.92 3.488-4.228 3.513-1.332.015-2.482-.39-3.418-1.203-1.096-.952-1.638-2.316-1.609-4.053.031-1.854.673-3.277 1.908-4.23 1.157-.893 2.766-1.343 4.783-1.337 1.839.006 3.35.344 4.49 1.006.183.106.353.22.509.341.055-.99-.026-1.879-.244-2.645-.487-1.71-1.583-2.946-3.256-3.673-1.425-.619-3.21-.933-5.305-.935l-.014-3.003c2.478.002 4.606.376 6.326 1.11 2.378 1.017 3.974 2.802 4.743 5.307.351 1.144.475 2.458.369 3.904l.006.01c-.044.82-.162 1.98-.363 3.35 1.066.86 1.968 1.94 2.628 3.14l-2.617 1.51c-.482-.876-1.157-1.673-1.982-2.33-.508 1.85-1.442 3.33-2.73 4.44-1.865 1.608-4.364 2.4-7.426 2.36z"/></svg>
                      <svg v-else-if="action.platform === 'linkedin'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
                      <svg v-else-if="action.platform === 'youtube'" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                    </span>
                    <span class="platform-indicator-tag" :style="{ color: getPlatformColor(action.platform) }">{{ (action.platform || 'net').toUpperCase() }}</span>
                  </div>
                  <div class="action-badge" :class="getActionTypeClass(action.action_type)">
                    {{ getActionTypeLabel(action.action_type) }}
                  </div>
                </div>
              </div>

              <div class="card-body">
                <!-- CREATE_POST: 发布帖子 -->
                <div v-if="action.action_type === 'CREATE_POST' && action.action_args?.content" class="content-text main-text">
                  {{ action.action_args.content }}
                </div>

                <!-- QUOTE_POST: 引用帖子 -->
                <template v-if="action.action_type === 'QUOTE_POST'">
                  <div v-if="action.action_args?.quote_content" class="content-text">
                    {{ action.action_args.quote_content }}
                  </div>
                  <div v-if="action.action_args?.original_content" class="quoted-block">
                    <div class="quote-header">
                      <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                      <span class="quote-label">@{{ action.action_args.original_author_name || 'User' }}</span>
                    </div>
                    <div class="quote-text">
                      {{ truncateContent(action.action_args.original_content, 150) }}
                    </div>
                  </div>
                </template>

                <!-- REPOST: 转发帖子 -->
                <template v-if="action.action_type === 'REPOST'">
                  <div class="repost-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>
                    <span class="repost-label">Reposted from @{{ action.action_args?.original_author_name || 'User' }}</span>
                  </div>
                  <div v-if="action.action_args?.original_content" class="repost-content">
                    {{ truncateContent(action.action_args.original_content, 200) }}
                  </div>
                </template>

                <!-- LIKE_POST: 点赞帖子 -->
                <template v-if="action.action_type === 'LIKE_POST'">
                  <div class="like-info">
                    <svg class="icon-small filled-heart" viewBox="0 0 24 24" width="14" height="14" fill="#e11d48"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    <span class="like-label">Liked @{{ action.action_args?.post_author_name || 'User' }}'s post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="liked-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- CREATE_COMMENT: 发表评论 -->
                <template v-if="action.action_type === 'CREATE_COMMENT'">
                  <div v-if="action.action_args?.content" class="content-text">
                    {{ action.action_args.content }}
                  </div>
                  <div v-if="action.action_args?.post_id" class="comment-context">
                    <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    <span>Reply to post #{{ action.action_args.post_id }}</span>
                  </div>
                </template>

                <!-- SEARCH_POSTS: 搜索帖子 -->
                <template v-if="action.action_type === 'SEARCH_POSTS'">
                  <div class="search-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span class="search-label">Search Query:</span>
                    <span class="search-query">"{{ action.action_args?.query || '' }}"</span>
                  </div>
                </template>

                <!-- FOLLOW: 关注用户 -->
                <template v-if="action.action_type === 'FOLLOW'">
                  <div class="follow-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    <span class="follow-label">Followed @{{ action.action_args?.target_user || action.action_args?.user_id || 'User' }}</span>
                  </div>
                </template>

                <!-- UPVOTE / DOWNVOTE -->
                <template v-if="action.action_type === 'UPVOTE_POST' || action.action_type === 'DOWNVOTE_POST'">
                  <div class="vote-info">
                    <svg v-if="action.action_type === 'UPVOTE_POST'" class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
                    <svg v-else class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    <span class="vote-label">{{ action.action_type === 'UPVOTE_POST' ? 'Upvoted' : 'Downvoted' }} Post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="voted-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- DO_NOTHING: 无操作（静默） -->
                <template v-if="action.action_type === 'DO_NOTHING'">
                  <div class="idle-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <span class="idle-label">Action Skipped</span>
                  </div>
                </template>

                <!-- 通用回退：未知类型或有 content 但未被上述处理 -->
                <div v-if="!['CREATE_POST', 'QUOTE_POST', 'REPOST', 'LIKE_POST', 'CREATE_COMMENT', 'SEARCH_POSTS', 'FOLLOW', 'UPVOTE_POST', 'DOWNVOTE_POST', 'DO_NOTHING'].includes(action.action_type) && action.action_args?.content" class="content-text">
                  {{ action.action_args.content }}
                </div>
              </div>

              <div class="card-footer">
                <span class="time-tag">R{{ action.round_num }} • {{ formatActionTime(action.timestamp) }}</span>
              </div>
            </div>
          </div>
        </TransitionGroup>

        <!-- Empty Filter State -->
        <div v-if="allActions.length > 0 && chronologicalActions.length === 0" class="empty-filter-state">
          <div class="empty-icon">🔍</div>
          <p class="empty-title">{{ $t('step3.noActionsFiltered') }}</p>
          <button class="clear-filter-btn" @click="activePlatformFilter = 'all'">
            {{ $t('step3.allPlatforms') }}
          </button>
        </div>

        <div v-if="allActions.length === 0" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>Waiting for agent actions...</span>
        </div>
      </div>

      <!-- Floating Jump-to-Latest Button -->
      <Transition name="fade-slide">
        <button
          v-if="!isNearBottom && chronologicalActions.length > 0"
          class="jump-latest-floating-btn"
          @click="resumeAutoScroll"
        >
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
          <span>{{ $t('step3.resumeAutoScroll') }}</span>
          <span v-if="unreadCount > 0" class="unread-pill">+{{ unreadCount }}</span>
        </button>
      </Transition>
    </div>

    <!-- Bottom Info / Logs -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SIMULATION MONITOR</span>
        <span class="log-id">{{ simulationId || 'NO_SIMULATION' }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  startSimulation,
  stopSimulation,
  getRunStatus,
  getRunStatusDetail
} from '../api/simulation'
import { generateReport } from '../api/report'

const { t } = useI18n()

const props = defineProps({
  simulationId: String,
  maxRounds: Number, // 从Step2传入的最大轮数
  minutesPerRound: {
    type: Number,
    default: 30 // 默认每轮30分钟
  },
  projectData: Object,
  simulationData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()

// State
const isGeneratingReport = ref(false)
const phase = ref(0) // 0: 未开始, 1: 运行中, 2: 已完成
const isStarting = ref(false)
const isStopping = ref(false)
const startError = ref(null)
const runStatus = ref({})
const allActions = ref([]) // 所有动作（增量累积）
const actionIds = ref(new Set()) // 用于去重的动作ID集合
const scrollContainer = ref(null)

// Enhanced Responsive & Feed States
const activePlatformFilter = ref('all')
const timelineLayoutMode = ref('stream') // 'stream' (clean left-rail stream) or 'dual' (alternating)
const isAutoScrollEnabled = ref(true)
const isNearBottom = ref(true)
const unreadCount = ref(0)

// Computed
// 按时间顺序显示动作，支持平台筛选
const chronologicalActions = computed(() => {
  if (activePlatformFilter.value === 'all') {
    return allActions.value
  }
  return allActions.value.filter(a => a.platform === activePlatformFilter.value)
})

const togglePlatformFilter = (platform) => {
  if (activePlatformFilter.value === platform) {
    activePlatformFilter.value = 'all'
  } else {
    activePlatformFilter.value = platform
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTo({
        top: scrollContainer.value.scrollHeight,
        behavior: 'smooth'
      })
      isNearBottom.value = true
      unreadCount.value = 0
    }
  })
}

const handleScroll = () => {
  if (!scrollContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
  const distanceToBottom = scrollHeight - scrollTop - clientHeight
  isNearBottom.value = distanceToBottom < 80
  if (isNearBottom.value) {
    unreadCount.value = 0
  }
}

const resumeAutoScroll = () => {
  isAutoScrollEnabled.value = true
  scrollToBottom()
}

// 7大平台元数据与可用动作定义
const PLATFORMS_META = {
  twitter: {
    name: 'Twitter / X',
    subname: 'Info Plaza',
    color: '#1DA1F2',
    actions: ['POST', 'LIKE', 'REPOST', 'QUOTE', 'FOLLOW', 'IDLE']
  },
  reddit: {
    name: 'Reddit',
    subname: 'Community',
    color: '#FF4500',
    actions: ['POST', 'COMMENT', 'UPVOTE', 'DOWNVOTE', 'SEARCH', 'FOLLOW', 'IDLE']
  },
  tiktok: {
    name: 'TikTok',
    subname: 'Short Video',
    color: '#00f2fe',
    actions: ['POST', 'COMMENT', 'LIKE', 'SHARE', 'FOLLOW', 'IDLE']
  },
  instagram: {
    name: 'Instagram',
    subname: 'Visual Feed',
    color: '#E1306C',
    actions: ['POST', 'LIKE', 'COMMENT', 'STORY', 'FOLLOW', 'IDLE']
  },
  linkedin: {
    name: 'LinkedIn',
    subname: 'Professional',
    color: '#0A66C2',
    actions: ['POST', 'CONNECT', 'LIKE', 'COMMENT', 'REPOST', 'IDLE']
  },
  threads: {
    name: 'Threads',
    subname: 'Conversations',
    color: '#71717a',
    actions: ['POST', 'REPLY', 'REPOST', 'LIKE', 'QUOTE', 'IDLE']
  },
  youtube: {
    name: 'YouTube',
    subname: 'Video Stream',
    color: '#FF0000',
    actions: ['POST', 'COMMENT', 'LIKE', 'SUBSCRIBE', 'SHARE', 'IDLE']
  }
}

const CANONICAL_PLATFORMS = ['twitter', 'reddit', 'tiktok', 'instagram', 'linkedin', 'threads', 'youtube']

// 活跃平台列表（优先读取配置，回退到历史动作中的平台）
const activePlatformsList = computed(() => {
  const pSet = new Set()
  if (runStatus.value?.platforms && Array.isArray(runStatus.value.platforms)) {
    runStatus.value.platforms.forEach(p => pSet.add(p))
  }
  if (runStatus.value?.platform_configs && typeof runStatus.value.platform_configs === 'object') {
    Object.keys(runStatus.value.platform_configs).forEach(p => pSet.add(p))
  }
  if (props.simulationData?.platforms && Array.isArray(props.simulationData.platforms)) {
    props.simulationData.platforms.forEach(p => pSet.add(p))
  }
  if (props.projectData?.platforms && Array.isArray(props.projectData.platforms)) {
    props.projectData.platforms.forEach(p => pSet.add(p))
  }
  allActions.value.forEach(a => {
    if (a.platform) pSet.add(a.platform)
  })
  if (pSet.size === 0) {
    return CANONICAL_PLATFORMS
  }
  return CANONICAL_PLATFORMS.filter(p => pSet.has(p)).concat(Array.from(pSet).filter(p => !CANONICAL_PLATFORMS.includes(p)))
})

const getPlatformDisplayName = (platform) => {
  return PLATFORMS_META[platform]?.name || platform.toUpperCase()
}

const getPlatformSubname = (platform) => {
  return PLATFORMS_META[platform]?.subname || platform.toUpperCase()
}

const getPlatformColor = (platform) => {
  return PLATFORMS_META[platform]?.color || '#6366f1'
}

const getPlatformActionsList = (platform) => {
  return PLATFORMS_META[platform]?.actions || ['POST', 'LIKE', 'COMMENT', 'FOLLOW', 'IDLE']
}

const getPlatformActionCount = (platform) => {
  return allActions.value.filter(a => a.platform === platform).length
}

const isPlatformRunning = (platform) => {
  if (runStatus.value[`${platform}_running`]) return true
  return runStatus.value.runner_status === 'running' && !isPlatformCompleted(platform)
}

const isPlatformCompleted = (platform) => {
  if (runStatus.value[`${platform}_completed`]) return true
  return runStatus.value.runner_status === 'completed'
}

const getPlatformRound = (platform) => {
  return runStatus.value[`${platform}_current_round`] || (platform === 'twitter' ? runStatus.value.twitter_current_round : (platform === 'reddit' ? runStatus.value.reddit_current_round : 0)) || runStatus.value.current_round || 0
}

const getPlatformElapsedTime = (platform) => {
  return formatElapsedTime(getPlatformRound(platform))
}

// 格式化模拟流逝时间（根据轮次和每轮分钟数计算）
const formatElapsedTime = (currentRound) => {
  if (!currentRound || currentRound <= 0) return '0h 0m'
  const totalMinutes = currentRound * props.minutesPerRound
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}h ${minutes}m`
}

// Twitter平台的模拟流逝时间
const twitterElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.twitter_current_round || 0)
})

// Reddit平台的模拟流逝时间
const redditElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.reddit_current_round || 0)
})

// 各平台动作计数
const twitterActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'twitter').length
})

const redditActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'reddit').length
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

// 追踪各平台的上一次轮次，用于检测变化并输出日志
const prevPlatformRounds = ref({})

// 重置所有状态（用于重新启动模拟）
const resetAllState = () => {
  phase.value = 0
  runStatus.value = {}
  allActions.value = []
  actionIds.value = new Set()
  prevPlatformRounds.value = {}
  startError.value = null
  isStarting.value = false
  isStopping.value = false
  stopPolling()  // 停止之前可能存在的轮询
}

// 启动模拟
const doStartSimulation = async () => {
  if (!props.simulationId) {
    addLog(t('log.errorMissingSimId'))
    return
  }

  // 先重置所有状态，确保不会受到上一次模拟的影响
  resetAllState()
  
  isStarting.value = true
  startError.value = null
  addLog(t('log.startingDualSim'))
  emit('update-status', 'processing')
  
  try {
    const params = {
      simulation_id: props.simulationId,
      platform: 'parallel',
      force: true,  // 强制重新开始
      enable_graph_memory_update: true  // 开启动态图谱更新
    }
    
    if (props.maxRounds) {
      params.max_rounds = props.maxRounds
      addLog(t('log.setMaxRounds', { rounds: props.maxRounds }))
    }
    
    addLog(t('log.graphMemoryUpdateEnabled'))
    
    const res = await startSimulation(params)
    
    if (res.success && res.data) {
      if (res.data.force_restarted) {
        addLog(t('log.oldSimCleared'))
      }
      addLog(t('log.engineStarted'))
      addLog(`  ├─ PID: ${res.data.process_pid || '-'}`)
      
      phase.value = 1
      runStatus.value = res.data
      
      startStatusPolling()
      startDetailPolling()
    } else {
      startError.value = res.error || '启动失败'
      addLog(t('log.startFailed', { error: res.error || t('common.unknownError') }))
      emit('update-status', 'error')
    }
  } catch (err) {
    startError.value = err.message
    addLog(t('log.startException', { error: err.message }))
    emit('update-status', 'error')
  } finally {
    isStarting.value = false
  }
}

// 停止模拟
const handleStopSimulation = async () => {
  if (!props.simulationId) return
  
  isStopping.value = true
  addLog(t('log.stoppingSim'))
  
  try {
    const res = await stopSimulation({ simulation_id: props.simulationId })
    
    if (res.success) {
      addLog(t('log.simStoppedSuccess'))
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    } else {
      addLog(t('log.stopFailed', { error: res.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('log.stopException', { error: err.message }))
  } finally {
    isStopping.value = false
  }
}

// 轮询状态
let statusTimer = null
let detailTimer = null

const startStatusPolling = () => {
  statusTimer = setInterval(fetchRunStatus, 2000)
}

const startDetailPolling = () => {
  detailTimer = setInterval(fetchRunStatusDetail, 3000)
}

const stopPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (detailTimer) {
    clearInterval(detailTimer)
    detailTimer = null
  }
}

const fetchRunStatus = async () => {
  if (!props.simulationId) return

  try {
    const res = await getRunStatus(props.simulationId)

    if (res.success && res.data) {
      const data = res.data

      runStatus.value = data

      // 动态检测各平台的轮次变化并输出日志 (支持全部7大平台)
      activePlatformsList.value.forEach(p => {
        const curRound = getPlatformRound(p)
        const prev = prevPlatformRounds.value[p] || 0
        if (curRound > prev) {
          const hours = data[`${p}_simulated_hours`] || Math.floor((curRound * props.minutesPerRound) / 60)
          const acts = data[`${p}_actions_count`] || getPlatformActionCount(p)
          const dispName = getPlatformDisplayName(p)
          addLog(`[${dispName}] R${curRound}/${data.total_rounds || props.maxRounds || '-'} | T:${hours}h | A:${acts}`)
          prevPlatformRounds.value[p] = curRound
        }
      })

      // 检测模拟是否已完成（通过 runner_status 或平台完成状态判断）
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped' || checkPlatformsCompleted(data)
      const isFailed = data.runner_status === 'failed'

      // runner_status is authoritative because the backend only publishes a
      // terminal state after the Zep ingestion barrier has completed.
      if (isFailed) {
        addLog(t('log.simFailed') + (data.error ? `: ${data.error}` : ''))
        phase.value = 2
        stopPolling()
        emit('update-status', 'error')
      } else if (isCompleted) {
        addLog(t('log.simCompleted'))
        phase.value = 2
        stopPolling()
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn('获取运行状态失败:', err)
  }
}

// 检查所有启用的平台是否已完成 (支持7大平台)
const checkPlatformsCompleted = (data) => {
  if (!data) return false
  const platforms = activePlatformsList.value
  if (!platforms || platforms.length === 0) return false

  let anyEnabled = false
  for (const p of platforms) {
    const completed = data[`${p}_completed`] === true
    const running = data[`${p}_running`] === true
    const actCount = data[`${p}_actions_count`] || 0
    const enabled = actCount > 0 || running || completed
    if (enabled) {
      anyEnabled = true
      if (!completed) return false
    }
  }
  return anyEnabled
}

const fetchRunStatusDetail = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatusDetail(props.simulationId)
    
    if (res.success && res.data) {
      // 使用 all_actions 获取完整的动作列表
      const serverActions = res.data.all_actions || []
      
      // 增量添加新动作（去重）
      let newActionsAdded = 0
      serverActions.forEach(action => {
        // 生成唯一ID
        const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`

        if (!actionIds.value.has(actionId)) {
          actionIds.value.add(actionId)
          allActions.value.push({
            ...action,
            _uniqueId: actionId
          })
          newActionsAdded++
        }
      })

      // Auto-scroll logic: smooth scroll to bottom if enabled and near bottom,
      // otherwise increment unread badge count
      if (newActionsAdded > 0) {
        if (isAutoScrollEnabled.value && isNearBottom.value) {
          scrollToBottom()
        } else if (!isNearBottom.value) {
          unreadCount.value += newActionsAdded
        }
      }
    }
  } catch (err) {
    console.warn('获取详细状态失败:', err)
  }
}

// Helpers
const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': 'POST',
    'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE',
    'CREATE_COMMENT': 'COMMENT',
    'LIKE_COMMENT': 'LIKE',
    'DO_NOTHING': 'IDLE',
    'FOLLOW': 'FOLLOW',
    'SEARCH_POSTS': 'SEARCH',
    'QUOTE_POST': 'QUOTE',
    'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE'
  }
  return labels[type] || type || 'UNKNOWN'
}

const getActionTypeClass = (type) => {
  const classes = {
    'CREATE_POST': 'badge-post',
    'REPOST': 'badge-action',
    'LIKE_POST': 'badge-action',
    'CREATE_COMMENT': 'badge-comment',
    'LIKE_COMMENT': 'badge-action',
    'QUOTE_POST': 'badge-post',
    'FOLLOW': 'badge-meta',
    'SEARCH_POSTS': 'badge-meta',
    'UPVOTE_POST': 'badge-action',
    'DOWNVOTE_POST': 'badge-action',
    'DO_NOTHING': 'badge-idle'
  }
  return classes[type] || 'badge-default'
}

const truncateContent = (content, maxLength = 100) => {
  if (!content) return ''
  if (content.length > maxLength) return content.substring(0, maxLength) + '...'
  return content
}

const formatActionTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

const handleNextStep = async () => {
  if (!props.simulationId) {
    addLog(t('log.errorMissingSimId'))
    return
  }

  if (isGeneratingReport.value) {
    addLog(t('log.reportRequestSent'))
    return
  }
  
  isGeneratingReport.value = true
  addLog(t('log.startingReportGen'))
  
  try {
    const res = await generateReport({
      simulation_id: props.simulationId,
      force_regenerate: true
    })
    
    if (res.success && res.data) {
      const reportId = res.data.report_id
      addLog(t('log.reportGenTaskStarted', { reportId }))
      
      // 跳转到报告页面
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog(t('log.reportGenFailed', { error: res.error || t('common.unknownError') }))
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(t('log.reportGenException', { error: err.message }))
    isGeneratingReport.value = false
  }
}

// Scroll log to bottom
const logContent = ref(null)
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  addLog(t('log.step3Init'))
  if (scrollContainer.value) {
    scrollContainer.value.addEventListener('scroll', handleScroll, { passive: true })
  }
  if (props.simulationId) {
    doStartSimulation()
  }
})

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', handleScroll)
  }
  stopPolling()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  overflow: hidden;
}

/* --- Control Bar --- */
.control-bar {
  background: #FFF;
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #EAEAEA;
  z-index: 10;
  min-height: 64px;
  gap: 12px;
}

.status-group {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 4px;
  scrollbar-width: thin;
  flex: 1;
}

.status-group::-webkit-scrollbar {
  height: 4px;
}

.status-group::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 2px;
}

/* Platform Status Cards */
.platform-status {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 10px;
  border-radius: 4px;
  background: #FAFAFA;
  border: 1px solid #EAEAEA;
  opacity: 0.7;
  transition: all 0.3s;
  min-width: 125px;
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
}

.platform-status.active {
  opacity: 1;
  border-color: #333;
  background: #FFF;
}

.platform-status.completed {
  opacity: 1;
  border-color: #1A936F;
  background: #F2FAF6;
}

.platform-status.selected {
  opacity: 1;
  box-shadow: 0 0 0 2px #0F172A;
  background: #FFF;
}

.platform-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Actions Tooltip */
.actions-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 8px;
  padding: 10px 14px;
  background: #000;
  color: #FFF;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 100;
  min-width: 180px;
  pointer-events: none;
}

.actions-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid #000;
}

.platform-status:hover .actions-tooltip {
  opacity: 1;
  visibility: visible;
}

.tooltip-title {
  font-size: 10px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.tooltip-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tooltip-action {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  color: #FFF;
  letter-spacing: 0.03em;
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.platform-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.platform-name {
  font-size: 11px;
  font-weight: 700;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.platform-status.twitter .platform-icon { color: #1DA1F2; }
.platform-status.reddit .platform-icon { color: #FF4500; }
.platform-status.tiktok .platform-icon { color: #00f2fe; }
.platform-status.instagram .platform-icon { color: #E1306C; }
.platform-status.linkedin .platform-icon { color: #0A66C2; }
.platform-status.threads .platform-icon { color: #71717a; }
.platform-status.youtube .platform-icon { color: #FF0000; }

.platform-stats {
  display: flex;
  gap: 10px;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.stat-label {
  font-size: 8px;
  color: #999;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 11px;
  font-weight: 600;
  color: #333;
}

.stat-total, .stat-unit {
  font-size: 9px;
  color: #999;
  font-weight: 400;
}

.status-badge {
  margin-left: auto;
  color: #1A936F;
  display: flex;
  align-items: center;
}

.action-controls {
  flex-shrink: 0;
  margin-left: 8px;
}

/* Action Button */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.action-btn.primary {
  background: #000;
  color: #FFF;
}

.action-btn.primary:hover:not(:disabled) {
  background: #333;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* --- Main Content Area --- */
.main-content-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  background: #FFF;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #E0E0E0 transparent;
}

.main-content-area::-webkit-scrollbar {
  width: 6px;
}

.main-content-area::-webkit-scrollbar-track {
  background: transparent;
}

.main-content-area::-webkit-scrollbar-thumb {
  background: #E0E0E0;
  border-radius: 3px;
}

.main-content-area::-webkit-scrollbar-thumb:hover {
  background: #CCCCCC;
}

/* Timeline Header */
.timeline-header {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 10px 16px;
  border-bottom: 1px solid #EAEAEA;
  z-index: 15;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timeline-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  flex-wrap: wrap;
  gap: 8px;
}

.timeline-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #64748B;
}

.total-count {
  font-weight: 700;
  color: #0F172A;
  background: #F1F5F9;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
}

.filter-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #F8FAFC;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #E2E8F0;
  font-size: 10px;
  font-weight: 600;
}

.clear-filter-mini {
  background: transparent;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  font-size: 10px;
  padding: 0 2px;
  line-height: 1;
}
.clear-filter-mini:hover { color: #EF4444; }

.timeline-actions-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Layout Switcher */
.view-mode-toggle {
  display: inline-flex;
  background: #F1F5F9;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #64748B;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn.active {
  background: #FFF;
  color: #0F172A;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Auto-scroll Toggle */
.autoscroll-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  background: #FFF;
  color: #64748B;
  cursor: pointer;
  transition: all 0.2s;
}

.autoscroll-toggle-btn.active {
  background: #F0FDF4;
  border-color: #86EFAC;
  color: #166534;
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94A3B8;
}

.status-indicator-dot.running {
  background: #22C55E;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
}

/* Platform Filter Tabs */
.platform-filter-tabs {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  width: 100%;
  padding-bottom: 2px;
  scrollbar-width: thin;
}

.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
  background: #F8FAFC;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-tab:hover {
  border-color: #CBD5E1;
  color: #0F172A;
}

.filter-tab.active {
  background: #FFF;
  border-color: #0F172A;
  color: #0F172A;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.tab-icon {
  display: inline-flex;
  align-items: center;
}

.tab-count {
  font-size: 9px;
  opacity: 0.75;
}

/* --- Timeline Feed --- */
.timeline-feed {
  padding: 24px 16px;
  position: relative;
  min-height: 100%;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
  container-type: inline-size;
  container-name: timeline;
}

/* Mode Stream (clean left-rail stream, ideal for split views) */
.timeline-feed.mode-stream .timeline-axis {
  left: 24px;
  transform: none;
}

.timeline-feed.mode-stream .timeline-marker {
  left: 24px;
  transform: translateX(-50%);
}

.timeline-feed.mode-stream .timeline-item.item-left,
.timeline-feed.mode-stream .timeline-item.item-right {
  justify-content: flex-start;
  padding-left: 48px;
  padding-right: 0;
}

.timeline-feed.mode-stream .timeline-item .timeline-card {
  margin-left: 0;
  margin-right: 0;
  width: 100%;
  max-width: 100%;
}

.timeline-axis {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #EAEAEA;
  transform: translateX(-50%);
}

.timeline-item {
  display: flex;
  position: relative;
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 32px;
}

.timeline-marker {
  position: absolute;
  left: 50%;
  top: 24px;
  width: 12px;
  height: 12px;
  background: #FFF;
  border: 2px solid #CCC;
  border-radius: 50%;
  transform: translateX(-50%);
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.marker-dot {
  width: 4px;
  height: 4px;
  background: #CCC;
  border-radius: 50%;
}

/* Platform Colors & Marker Indicators (7 Platforms - Color & Border ONLY, NO layout padding) */
.timeline-item.twitter .marker-dot { background: #1DA1F2; }
.timeline-item.twitter .timeline-marker { border-color: #1DA1F2; }
.timeline-item.twitter .timeline-card { border-left: 3px solid #1DA1F2; }

.timeline-item.reddit .marker-dot { background: #FF4500; }
.timeline-item.reddit .timeline-marker { border-color: #FF4500; }
.timeline-item.reddit .timeline-card { border-left: 3px solid #FF4500; }

.timeline-item.tiktok .marker-dot { background: #00f2fe; }
.timeline-item.tiktok .timeline-marker { border-color: #00f2fe; }
.timeline-item.tiktok .timeline-card { border-left: 3px solid #00f2fe; }

.timeline-item.instagram .marker-dot { background: #E1306C; }
.timeline-item.instagram .timeline-marker { border-color: #E1306C; }
.timeline-item.instagram .timeline-card { border-left: 3px solid #E1306C; }

.timeline-item.linkedin .marker-dot { background: #0A66C2; }
.timeline-item.linkedin .timeline-marker { border-color: #0A66C2; }
.timeline-item.linkedin .timeline-card { border-left: 3px solid #0A66C2; }

.timeline-item.threads .marker-dot { background: #71717a; }
.timeline-item.threads .timeline-marker { border-color: #71717a; }
.timeline-item.threads .timeline-card { border-left: 3px solid #71717a; }

.timeline-item.youtube .marker-dot { background: #FF0000; }
.timeline-item.youtube .timeline-marker { border-color: #FF0000; }
.timeline-item.youtube .timeline-card { border-left: 3px solid #FF0000; }

/* Card Layout */
.timeline-card {
  box-sizing: border-box;
  width: calc(100% - 32px);
  max-width: calc(100% - 32px);
  word-break: break-word;
  overflow-wrap: break-word;
  background: #FFF;
  border-radius: 4px;
  padding: 16px 20px;
  border: 1px solid #EAEAEA;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  position: relative;
  transition: all 0.2s;
}

.timeline-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border-color: #DDD;
}

/* Left side (Item Left ONLY) */
.timeline-item.item-left {
  justify-content: flex-start;
  padding-right: 50%;
  padding-left: 0;
}
.timeline-item.item-left .timeline-card {
  margin-left: auto;
  margin-right: 32px; /* Gap from axis */
}

/* Right side (Item Right ONLY) */
.timeline-item.item-right {
  justify-content: flex-end;
  padding-left: 50%;
  padding-right: 0;
}
.timeline-item.item-right .timeline-card {
  margin-right: auto;
  margin-left: 32px; /* Gap from axis */
}

/* Responsive Single-Column Stream for Narrow Panels or Small Viewports */
@container timeline (max-width: 680px) {
  .timeline-feed {
    padding: 16px 12px;
  }
  .timeline-axis {
    left: 18px;
    transform: none;
  }
  .timeline-marker {
    left: 18px;
    transform: translateX(-50%);
  }
  .timeline-item.item-left,
  .timeline-item.item-right {
    justify-content: flex-start;
    padding-left: 38px;
    padding-right: 0;
  }
  .timeline-item.item-left .timeline-card,
  .timeline-item.item-right .timeline-card {
    margin-left: 0;
    margin-right: 0;
    width: 100%;
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .timeline-feed {
    padding: 16px 12px;
  }
  .timeline-axis {
    left: 18px;
    transform: none;
  }
  .timeline-marker {
    left: 18px;
    transform: translateX(-50%);
  }
  .timeline-item.item-left,
  .timeline-item.item-right {
    justify-content: flex-start;
    padding-left: 38px;
    padding-right: 0;
  }
  .timeline-item.item-left .timeline-card,
  .timeline-item.item-right .timeline-card {
    margin-left: 0;
    margin-right: 0;
    width: 100%;
    max-width: 100%;
  }
}

/* Card Content Styles */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F5F5F5;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-details {
  display: flex;
  flex-direction: column;
}

.agent-handle {
  font-size: 10px;
  color: #64748B;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.2;
}

.avatar-placeholder {
  width: 28px;
  height: 28px;
  background: #000;
  color: #FFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: #000;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #EAEAEA;
  background: #FAFAFA;
}

.platform-indicator-icon {
  display: inline-flex;
  align-items: center;
}

.platform-indicator-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  font-family: 'JetBrains Mono', monospace;
}

.action-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: 1px solid transparent;
}

/* Monochromatic Badges */
.badge-post { background: #F0F0F0; color: #333; border-color: #E0E0E0; }
.badge-comment { background: #F0F0F0; color: #666; border-color: #E0E0E0; }
.badge-action { background: #FFF; color: #666; border: 1px solid #E0E0E0; }
.badge-meta { background: #FAFAFA; color: #999; border: 1px dashed #DDD; }
.badge-idle { opacity: 0.5; }

.content-text {
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 10px;
  word-break: break-word;
  overflow-wrap: break-word;
}

.content-text.main-text {
  font-size: 14px;
  color: #000;
  font-weight: 500;
}

/* Info Blocks (Quote, Repost, etc) */
.quoted-block, .repost-content {
  background: #F9F9F9;
  border: 1px solid #EEE;
  padding: 10px 12px;
  border-radius: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: #555;
  word-break: break-word;
  overflow-wrap: break-word;
}

.liked-content,
.voted-content {
  font-size: 12px;
  line-height: 1.5;
  color: #555;
  font-style: italic;
  background: #F9F9F9;
  border-left: 2px solid #EAEAEA;
  padding: 6px 10px;
  border-radius: 0 4px 4px 0;
  margin-top: 6px;
  word-break: break-word;
  overflow-wrap: break-word;
}

.quote-header, .repost-info, .like-info, .search-info, .follow-info, .vote-info, .idle-info, .comment-context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 11px;
  color: #666;
}

.icon-small {
  color: #999;
}
.icon-small.filled {
  color: #999; /* Keep icons neutral unless highlighted */
}

.search-query {
  font-family: 'JetBrains Mono', monospace;
  background: #F0F0F0;
  padding: 0 4px;
  border-radius: 2px;
}

.card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  font-size: 10px;
  color: #BBB;
  font-family: 'JetBrains Mono', monospace;
}

/* Empty Filter State */
.empty-filter-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 16px;
  color: #64748B;
  text-align: center;
}

.empty-icon {
  font-size: 28px;
  opacity: 0.8;
}

.empty-title {
  font-size: 13px;
  color: #64748B;
  margin: 0;
}

.clear-filter-btn {
  padding: 6px 14px;
  font-size: 11px;
  font-weight: 600;
  background: #0F172A;
  color: #FFF;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-filter-btn:hover {
  background: #334155;
}

/* Floating Jump-to-Latest Button */
.jump-latest-floating-btn {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: #0F172A;
  color: #FFF;
  font-size: 11px;
  font-weight: 600;
  border-radius: 20px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
  border: none;
  cursor: pointer;
  z-index: 25;
  transition: all 0.2s;
}

.jump-latest-floating-btn:hover {
  background: #1E293B;
  transform: translateX(-50%) translateY(-2px);
}

.unread-pill {
  background: #3B82F6;
  color: #FFF;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 6px;
  line-height: 1.2;
}

/* Fade-slide Transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease-out;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* Waiting State */
.waiting-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #CCC;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.pulse-ring {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #EAEAEA;
  animation: ripple 2s infinite;
}

@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; border-color: #CCC; }
  100% { transform: scale(2.5); opacity: 0; border-color: #EAEAEA; }
}

/* Animation */
.timeline-item-enter-active,
.timeline-item-leave-active {
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.timeline-item-leave-to {
  opacity: 0;
}

/* Logs */
.system-logs {
  background: #000;
  color: #DDD;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid #222;
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: #666;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar { width: 4px; }
.log-content::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time { color: #555; min-width: 75px; }
.log-msg { color: #BBB; word-break: break-all; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* Loading spinner for button */
.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}
</style>
