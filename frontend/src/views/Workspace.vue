<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { listSessions } from '../api/simulation.js'
import ScaleBenchmarkPanel from '../components/ScaleBenchmarkPanel.vue'

const router = useRouter()
const { t } = useI18n()
const sessions = ref([])
const total = ref(0)
const loading = ref(true)
const error = ref(null)
const limit = 20
const offset = ref(0)
const showAdmin = ref(false)

const statusColors = {
  completed: 'var(--accent-green)',
  running: 'var(--accent)',
  failed: 'var(--accent-red)',
  pending: 'var(--accent-orange)',
  created: 'var(--text-muted)',
}

const statusLabels = {
  completed: t('workspace.status.completed'),
  running: t('workspace.status.running'),
  failed: t('workspace.status.failed'),
  pending: t('workspace.status.pending'),
  created: t('workspace.status.created'),
}

const scenarioCodes = {
  property: 'PROP',
  emigration: 'MIG',
  economic: 'ECO',
  political: 'POL',
  social: 'SOC',
}

async function fetchSessions() {
  loading.value = true
  error.value = null
  try {
    const res = await listSessions(limit, offset.value)
    const data = res.data?.data || res.data
    sessions.value = data.sessions || []
    total.value = data.total || 0
  } catch (e) {
    error.value = e.message || '載入失敗'
  } finally {
    loading.value = false
  }
}

function loadMore() {
  offset.value += limit
  fetchMore()
}

async function fetchMore() {
  try {
    const res = await listSessions(limit, offset.value)
    const data = res.data?.data || res.data
    sessions.value = [...sessions.value, ...(data.sessions || [])]
  } catch (e) {
    error.value = e.message || '載入更多失敗'
  }
}

function goToSession(session) {
  router.push(`/app/graph/${session.id}`)
}

function goNew() {
  router.push('/')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-HK', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchSessions)
</script>

<template>
  <div class="workspace-page">
    <div class="workspace-header">
      <div>
        <span class="workbench-label">WORKSPACE</span>
        <h1 class="workspace-title">{{ t('workspace.title') }}</h1>
        <p class="workspace-subtitle">{{ t('workspace.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <button
          class="btn-admin"
          :class="{ active: showAdmin }"
          @click="showAdmin = !showAdmin"
        >
          {{ t('workspace.adminBtn') }}
        </button>
        <button class="btn-new" @click="goNew">{{ t('workspace.newBtn') }}</button>
      </div>
    </div>

    <!-- Admin panel -->
    <Transition name="panel-slide">
      <div v-if="showAdmin" class="admin-section">
        <ScaleBenchmarkPanel />
      </div>
    </Transition>

    <!-- Loading -->
    <div v-if="loading && sessions.length === 0" class="session-grid">
      <div v-for="i in 6" :key="i" class="skeleton skeleton-card" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchSessions">{{ t('workspace.retry') }}</button>
    </div>

    <!-- Empty -->
    <div v-else-if="sessions.length === 0" class="empty-state">
      <div class="empty-icon">⬡</div>
      <h2>{{ t('workspace.empty.title') }}</h2>
      <p>{{ t('workspace.empty.description') }}</p>
      <button class="btn-new" @click="goNew">{{ t('workspace.newBtn') }}</button>
    </div>

    <!-- Sessions grid -->
    <div v-else class="session-grid">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-card glass-panel"
        @click="goToSession(session)"
      >
        <div class="card-header">
          <span class="scenario-icon">{{ scenarioCodes[session.scenario_type] || 'SIM' }}</span>
          <span
            class="status-badge"
            :style="{ color: statusColors[session.status] || 'var(--text-muted)', borderColor: statusColors[session.status] || 'var(--border-color)' }"
          >
            {{ statusLabels[session.status] || session.status }}
          </span>
        </div>
        <h3 class="card-title">{{ session.name || session.scenario_type || 'Untitled' }}</h3>
        <div class="card-meta">
          <span>{{ session.agent_count || 0 }} {{ t('workspace.meta.agents') }}</span>
          <span>{{ session.current_round || 0 }}/{{ session.round_count || 0 }} {{ t('workspace.meta.rounds') }}</span>
        </div>
        <div class="card-date">{{ formatDate(session.created_at) }}</div>
        <div class="card-actions" @click.stop>
          <router-link
            :to="`/app/evidence/${session.id}`"
            class="evidence-link"
          >{{ t('workspace.evidence') }}</router-link>
        </div>
      </div>
    </div>

    <!-- Load more -->
    <div v-if="sessions.length < total" class="load-more">
      <button class="btn-load-more" @click="loadMore">{{ t('workspace.loadMore') }}</button>
    </div>
  </div>
</template>

<style scoped>
.workspace-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 24px 72px;
}

.workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 28px;
}

.workspace-title {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin-top: 4px;
}

.workspace-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-admin {
  padding: 10px 16px;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: var(--transition);
}

.btn-admin:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.btn-admin.active {
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: #FFFFFF;
}

.btn-new {
  padding: 10px 20px;
  background: var(--text-primary);
  color: #FFFFFF;
  border: 1px solid var(--text-primary);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: var(--transition);
}

.btn-new:hover {
  background: var(--accent);
  border-color: var(--accent);
}

.admin-section {
  margin-bottom: 24px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
  padding: 0 20px;
}

.session-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.session-card {
  padding: 20px;
  cursor: pointer;
  transition: var(--transition);
  border-radius: var(--radius-lg);
}

.session-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--accent);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.scenario-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 28px;
  border: 1px solid var(--border);
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.status-badge {
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 800;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  text-transform: capitalize;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.card-date {
  font-size: 11px;
  color: var(--text-muted);
}

.card-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.evidence-link {
  font-size: 12px;
  color: var(--accent);
  text-decoration: none;
  padding: 3px 8px;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.evidence-link:hover {
  background: var(--accent);
  color: #FFFFFF;
}

.empty-state {
  text-align: center;
  padding: 80px 24px;
}

.empty-icon {
  font-size: 48px;
  color: var(--accent);
  margin-bottom: 16px;
}

.empty-state h2 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-muted);
  margin-bottom: 20px;
}

.error-state {
  text-align: center;
  padding: 60px 24px;
  color: var(--accent-red);
}

.btn-retry {
  margin-top: 12px;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-primary);
}

.load-more {
  text-align: center;
  margin-top: 24px;
}

.btn-load-more {
  padding: 10px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
}

.btn-load-more:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
