<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
    <!-- Top Sticky Navigation -->
    <header class="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-xl px-4 lg:px-8 py-3">
      <div class="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <router-link
            to="/dashboard"
            class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors text-xs font-semibold flex items-center gap-1.5"
          >
            <span>← Kembali ke Dashboard</span>
          </router-link>

          <div class="h-5 w-px bg-slate-700 hidden sm:block"></div>

          <div class="flex items-center gap-2">
            <span class="text-xl">📚</span>
            <div>
              <h1 class="text-base font-extrabold text-white tracking-tight flex items-center gap-2">
                <span>Dokumentasi MiroFish Enterprise</span>
                <span class="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  v3.1 Specs
                </span>
              </h1>
              <p class="text-[11px] text-slate-400">
                Arsitektur, OpenAPI 3.1.0 Interactive Docs, MCP Tools, & Wikipedia Teknis
              </p>
            </div>
          </div>
        </div>

        <!-- Mode Toggle & Swagger Link -->
        <div class="flex items-center gap-2">
          <div class="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              @click="activeMode = 'wiki'"
              :class="[
                'px-3 py-1 rounded-md transition-colors cursor-pointer',
                activeMode === 'wiki' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              ]"
            >
              📖 Wiki Teknis
            </button>
            <button
              @click="activeMode = 'swagger'"
              :class="[
                'px-3 py-1 rounded-md transition-colors cursor-pointer',
                activeMode === 'swagger' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              ]"
            >
              ⚡ OpenAPI / Swagger
            </button>
          </div>

          <LanguageSwitcher />
        </div>
      </div>
    </header>

    <!-- Main Content Container -->
    <div class="max-w-7xl mx-auto w-full flex-1 flex flex-col md:flex-row p-4 lg:p-8 gap-6">
      
      <!-- MODE 1: SWAGGER UI EMBED -->
      <div v-if="activeMode === 'swagger'" class="w-full flex flex-col gap-4">
        <div class="flex items-center justify-between bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div>
            <h2 class="text-sm font-bold text-slate-200 flex items-center gap-2">
              <span>Interactive OpenAPI 3.1.0 Spec Explorer</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">
              Spesifikasi REST API lengkap: endpoints, skema request/response, dan otentikasi.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <a
              href="/api/enterprise/openapi.json"
              target="_blank"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1.5"
            >
              <span>openapi.json</span> ↗
            </a>
            <a
              href="/api/enterprise/openapi.yaml"
              target="_blank"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1.5"
            >
              <span>openapi.yaml</span> ↗
            </a>
          </div>
        </div>

        <div class="flex-1 min-h-[750px] bg-white rounded-xl overflow-hidden shadow-2xl border border-slate-800">
          <iframe
            src="/api/enterprise/docs"
            class="w-full h-full min-h-[750px] border-0"
            title="MiroFish OpenAPI Swagger"
          ></iframe>
        </div>
      </div>

      <!-- MODE 2: WIKI & TECHNICAL ARCHITECTURE -->
      <template v-else>
        <!-- Sidebar Navigation -->
        <aside class="w-full md:w-72 shrink-0 flex flex-col gap-3">
          <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
            <div class="flex items-center justify-between mb-2 pb-2 border-b border-slate-800">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Daftar Dokumen</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                {{ documents.length }} files
              </span>
            </div>

            <div v-if="loadingDocs" class="py-6 text-center text-xs text-slate-500 animate-pulse">
              Memuat katalog dokumen...
            </div>

            <div v-else class="space-y-1">
              <button
                v-for="doc in documents"
                :key="doc.id"
                @click="loadDocument(doc.id)"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex flex-col gap-0.5 cursor-pointer border',
                  selectedDocId === doc.id
                    ? 'bg-blue-600/20 border-blue-500/50 text-blue-200 font-semibold'
                    : 'bg-slate-950/40 hover:bg-slate-800/60 border-transparent text-slate-400 hover:text-slate-200'
                ]"
              >
                <div class="flex items-center justify-between">
                  <span class="line-clamp-1">{{ doc.title }}</span>
                  <span class="text-[9px] font-mono opacity-60 shrink-0 ml-1">
                    {{ Math.round(doc.size_bytes / 1024) }} KB
                  </span>
                </div>
                <span class="text-[10px] font-mono text-slate-500">{{ doc.filename }}</span>
              </button>
            </div>
          </div>

          <!-- Fast Links -->
          <div class="bg-slate-900/40 border border-slate-800/80 rounded-xl p-3 text-xs text-slate-400 flex flex-col gap-2">
            <span class="font-bold text-slate-300">Tautan Langsung</span>
            <router-link to="/dashboard" class="hover:text-blue-400 flex items-center justify-between">
              <span>Panel 5: MCP Sandbox</span> <span>→</span>
            </router-link>
            <a href="https://github.com/666ghj/MiroFish" target="_blank" class="hover:text-blue-400 flex items-center justify-between">
              <span>Repositori GitHub</span> <span>↗</span>
            </a>
          </div>
        </aside>

        <!-- Document Content Viewer -->
        <main class="flex-1 bg-slate-900/60 border border-slate-800 rounded-xl p-6 lg:p-8 flex flex-col overflow-hidden">
          <div v-if="loadingContent" class="py-20 text-center text-slate-500 text-sm animate-pulse">
            Memuat isi dokumen...
          </div>

          <div v-else-if="currentDoc">
            <div class="pb-4 mb-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 uppercase font-bold">
                  {{ currentDoc.id }}.md
                </span>
                <h2 class="text-xl font-bold text-white mt-1">{{ currentDocTitle }}</h2>
              </div>
              <button
                @click="copyContent"
                class="px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <span>{{ copied ? '✓ Tersalin' : '📋 Salin MD' }}</span>
              </button>
            </div>

            <!-- Formatted Markdown Render -->
            <div class="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed space-y-4 font-sans">
              <div v-html="renderedMarkdown" class="markdown-body"></div>
            </div>
          </div>

          <div v-else class="py-20 text-center text-slate-500 text-sm">
            Silakan pilih dokumen dari menu sebelah kiri.
          </div>
        </main>
      </template>

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { sanitizeUrl, sanitizeHtml } from '@/utils/sanitize'

export default {
  name: 'DocsView',
  components: {
    LanguageSwitcher
  },
  data() {
    return {
      activeMode: 'wiki',
      documents: [],
      selectedDocId: 'index',
      currentDoc: null,
      loadingDocs: false,
      loadingContent: false,
      copied: false
    }
  },
  computed: {
    currentDocTitle() {
      const doc = this.documents.find(d => d.id === this.selectedDocId)
      return doc ? doc.title : this.selectedDocId
    },
    renderedMarkdown() {
      if (!this.currentDoc || !this.currentDoc.content) return ''
      return this.parseMarkdown(this.currentDoc.content)
    }
  },
  async mounted() {
    await this.fetchDocCatalog()
    if (this.documents.length > 0) {
      const initialId = this.$route.query.doc || (this.documents.find(d => d.id === 'index') ? 'index' : this.documents[0].id)
      await this.loadDocument(initialId)
    }
  },
  methods: {
    async fetchDocCatalog() {
      this.loadingDocs = true
      try {
        const lang = this.$i18n.locale === 'zh' ? 'en' : this.$i18n.locale
        const res = await axios.get('/api/enterprise/wiki', { params: { lang } })
        if (res.data && res.data.success) {
          this.documents = res.data.documents || []
        }
      } catch (err) {
        console.error('Failed to load wiki catalog:', err)
      } finally {
        this.loadingDocs = false
      }
    },
    async loadDocument(docId) {
      this.selectedDocId = docId
      this.loadingContent = true
      try {
        const lang = this.$i18n.locale === 'zh' ? 'en' : this.$i18n.locale
        const res = await axios.get(`/api/enterprise/wiki/${docId}`, { params: { lang } })
        if (res.data && res.data.success) {
          this.currentDoc = res.data
        }
      } catch (err) {
        console.error('Failed to load document content:', err)
      } finally {
        this.loadingContent = false
      }
    },
    copyContent() {
      if (this.currentDoc && this.currentDoc.content) {
        navigator.clipboard.writeText(this.currentDoc.content)
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      }
    },
    parseMarkdown(md) {
      if (!md) return ''
      
      // Strip YAML frontmatter if present
      let text = md.replace(/^---[\s\S]*?---\s*/, '')
      
      // Escape HTML tags to prevent XSS
      text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

      // Code blocks with syntax formatting
      text = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="bg-slate-950 p-4 rounded-lg border border-slate-800 overflow-x-auto text-xs font-mono text-emerald-300 my-4"><code>${code}</code></pre>`
      })

      // Inline code
      text = text.replace(/`([^`]+)`/g, '<code class="bg-slate-800 text-amber-300 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>')

      // Headers
      text = text.replace(/^### (.*$)/gim, '<h3 class="text-base font-bold text-slate-100 mt-6 mb-2 border-b border-slate-800/80 pb-1">$1</h3>')
      text = text.replace(/^## (.*$)/gim, '<h2 class="text-lg font-extrabold text-blue-300 mt-8 mb-3 border-b border-slate-800 pb-1.5 flex items-center gap-2"><span>§</span> <span>$1</span></h2>')
      text = text.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-black text-white mt-4 mb-4 pb-2 border-b border-slate-700">$1</h1>')

      // Blockquotes
      text = text.replace(/^\> (.*$)/gim, '<blockquote class="border-l-4 border-blue-500 pl-4 py-1.5 my-3 bg-blue-950/20 text-slate-300 italic rounded-r">$1</blockquote>')

      // Bold & Italic
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
      text = text.replace(/\*(.*?)\*/g, '<em class="text-slate-300 italic">$1</em>')

      // Bullet lists
      text = text.replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc text-slate-300 my-1">$1</li>')

      // Links with safe URL sanitization (blocks javascript:, vbscript:, data:text/html)
      text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
        const safeUrl = sanitizeUrl(url, '#')
        return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline underline-offset-2">${linkText}</a>`
      })

      // Paragraphs (lines separated by double newlines)
      const rawHtml = text.split('\n\n').map(p => {
        p = p.trim()
        if (!p) return ''
        if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<block') || p.startsWith('<li')) {
          return p
        }
        return `<p class="my-2 leading-relaxed text-slate-300 text-xs sm:text-sm">${p.replace(/\n/g, '<br/>')}</p>`
      }).join('\n')

      return sanitizeHtml(rawHtml)
    }
  }
}
</script>

<style scoped>
.markdown-body :deep(li) {
  margin-left: 1.25rem;
}
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: 0.8rem;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #334155;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
.markdown-body :deep(th) {
  background-color: #0f172a;
  color: #93c5fd;
  font-weight: 700;
}
.markdown-body :deep(tr:nth-child(even)) {
  background-color: #0b1120;
}
</style>