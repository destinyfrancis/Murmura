<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DomainBuilder from '../components/DomainBuilder.vue'
import DataConnectorPanel from '../components/DataConnectorPanel.vue'
import OnboardingTooltip from '../components/OnboardingTooltip.vue'
import { quickStart, quickStartWithFile } from '../api/simulation.js'
import { useOnboarding } from '../composables/useOnboarding.js'

const router = useRouter()
const { t } = useI18n()
const { steps: onboardingSteps, currentStep, dismissed: onboardingDismissed, nextStep: onboardingNext, dismiss: onboardingDismiss } = useOnboarding()
const quickStartText = ref('')
const quickStartLoading = ref(false)
const quickStartQuestion = ref('')
const quickStartPreset = ref('fast')
const quickStartFile = ref(null)
const quickStartDragging = ref(false)
const quickStartError = ref(null)

const domainPacks = ref([])
const selectedDomain = ref('hk_city')
const showDomainBuilder = ref(false)
const showDataConnector = ref(false)
const customDomainPack = ref(null)

const PRESETS = computed(() => [
  { key: 'fast',     label: t('home.presets.fast'),     hint: t('home.presets.fastHint') },
  { key: 'standard', label: t('home.presets.standard'), hint: t('home.presets.standardHint') },
  { key: 'deep',     label: t('home.presets.deep'),     hint: t('home.presets.deepHint') },
])

const STATUS_METRICS = computed(() => [
  { value: '01', label: t('home.metrics.zeroConfig') },
  { value: 'KG', label: t('home.metrics.kg') },
  { value: 'MAS', label: t('home.metrics.oasis') },
  { value: 'XAI', label: t('home.metrics.react') },
])

const WORKFLOW_STEPS = computed(() => [
  { num: '01', label: t('process.nav.steps.graph.navLabel'), desc: t('home.workflow.graph') },
  { num: '02', label: t('process.nav.steps.env.navLabel'), desc: t('home.workflow.env') },
  { num: '03', label: t('process.nav.steps.sim.navLabel'), desc: t('home.workflow.sim') },
  { num: '04', label: t('process.nav.steps.report.navLabel'), desc: t('home.workflow.report') },
  { num: '05', label: t('process.nav.steps.interact.navLabel'), desc: t('home.workflow.interact') },
])

const EXAMPLE_SEEDS = computed(() => [
  t('home.sampleWar'),
  t('home.sampleFiction'),
  t('home.sampleCompany'),
])

function useExampleSeed(seed) {
  quickStartFile.value = null
  quickStartText.value = seed
}

const QS_MAX_BYTES = 10 * 1024 * 1024
const QS_ALLOWED_EXTS = ['.pdf', '.txt', '.md', '.markdown']

function qsFileExt(name) {
  const i = name.lastIndexOf('.')
  return i >= 0 ? name.slice(i).toLowerCase() : ''
}

function onQSDragOver(e) { e.preventDefault(); quickStartDragging.value = true }
function onQSDragLeave() { quickStartDragging.value = false }
function onQSDrop(e) {
  e.preventDefault()
  quickStartDragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) setQSFile(f)
}
function onQSFileInput(e) {
  const f = e.target.files?.[0]
  if (f) setQSFile(f)
}
function setQSFile(f) {
  quickStartError.value = null
  const ext = qsFileExt(f.name)
  if (!QS_ALLOWED_EXTS.includes(ext)) {
    quickStartError.value = t('home.errors.format', { ext })
    return
  }
  if (f.size > QS_MAX_BYTES) {
    quickStartError.value = t('home.errors.size')
    return
  }
  quickStartFile.value = f
  quickStartText.value = ''   // clear textarea when file selected
}
function clearQSFile() { quickStartFile.value = null }

const canQuickStart = computed(() =>
  !quickStartLoading.value && (quickStartFile.value || quickStartText.value.trim())
)

async function selectDomain(packId) {
  selectedDomain.value = packId
}

onMounted(async () => {
  try {
    const res = await fetch('/api/domain-packs')
    if (res.ok) {
      const data = await res.json()
      domainPacks.value = data.packs || []
    }
  } catch {
    // Fallback: no domain tabs shown
  }
})

async function handleQuickStart() {
  if (!canQuickStart.value) return
  quickStartLoading.value = true
  quickStartError.value = null
  try {
    let res
    if (quickStartFile.value) {
      res = await quickStartWithFile(
        quickStartFile.value,
        quickStartQuestion.value,
        quickStartPreset.value,
      )
    } else {
      res = await quickStart(
        quickStartText.value,
        quickStartQuestion.value,
        quickStartPreset.value,
      )
    }
    const d = res?.data?.data || res?.data
    const sessionId = d?.session_id
    const graphId = d?.graph_id || ''
    if (sessionId) {
      const q = new URLSearchParams({
        express: '1',
        sessionId,
        graphId,
        scenarioQuestion: quickStartQuestion.value,
        preset: quickStartPreset.value,
      })
      router.push(`/process/quick?${q.toString()}`)
    }
  } catch (e) {
    quickStartError.value = e.response?.data?.detail || e.message || t('home.errors.launch')
  } finally {
    quickStartLoading.value = false
  }
}


</script>

<template>
  <div class="home workbench-page">
    <section class="home-console">
      <div class="mission-panel workbench-panel">
        <div class="mission-topline">
          <span class="workbench-label">{{ t('home.eyebrow') }}</span>
          <span class="live-chip">{{ t('home.consoleStatusLive') }}</span>
        </div>

        <h1 class="hero-title">Murmura</h1>
        <p class="hero-subtitle">{{ t('home.subtitle') }}</p>
        <p class="hero-desc">{{ t('home.description') }}</p>

        <div class="status-metrics" :aria-label="t('home.consoleStatus')">
          <div v-for="metric in STATUS_METRICS" :key="metric.label" class="metric-tile">
            <span class="metric-value">{{ metric.value }}</span>
            <span class="metric-label">{{ metric.label }}</span>
          </div>
        </div>

        <div class="workflow-panel">
          <div class="workflow-header">
            <span class="workbench-label">{{ t('home.pipelineTitle') }}</span>
            <span class="workflow-signal">{{ t('home.consoleSignal') }}</span>
          </div>
          <div class="workflow-list">
            <div v-for="step in WORKFLOW_STEPS" :key="step.num" class="workflow-item">
              <span class="workflow-num">{{ step.num }}</span>
              <span class="workflow-label">{{ step.label }}</span>
              <span class="workflow-desc">{{ step.desc }}</span>
            </div>
          </div>
        </div>

        <div class="examples-panel">
          <span class="workbench-label">{{ t('home.examplesTitle') }}</span>
          <button
            v-for="seed in EXAMPLE_SEEDS"
            :key="seed"
            class="example-seed"
            @click="useExampleSeed(seed)"
          >
            {{ seed }}
          </button>
        </div>
      </div>

      <div class="prediction-console workbench-panel" v-if="!showDomainBuilder && !showDataConnector">
        <div class="console-header">
          <div>
            <span class="workbench-label">{{ t('home.consoleTitle') }}</span>
            <h2>{{ t('home.startTitle') }}</h2>
          </div>
          <span class="console-code">READY</span>
        </div>
        <p class="qs-subtitle">{{ t('home.startSubtitle') }}</p>

        <label class="console-field-label">{{ t('home.fileLabel') }}</label>
        <div
          class="qs-drop-zone"
          :class="{ dragging: quickStartDragging, 'has-file': quickStartFile }"
          @dragover="onQSDragOver"
          @dragleave="onQSDragLeave"
          @drop="onQSDrop"
          @click="!quickStartFile && $refs.qsFileInput.click()"
        >
          <input
            ref="qsFileInput"
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            class="qs-file-hidden"
            @change="onQSFileInput"
          />
          <template v-if="quickStartFile">
            <span class="qs-file-icon">DOC</span>
            <span class="qs-file-name">{{ quickStartFile.name }}</span>
            <button class="qs-file-clear" @click.stop="clearQSFile">x</button>
          </template>
          <template v-else>
            <span class="qs-drop-icon">UPLOAD</span>
            <span class="qs-drop-label">{{ t('home.dropLabel') }}</span>
            <span class="qs-drop-hint">{{ t('home.dropHint') }}</span>
          </template>
        </div>

        <div class="qs-or-row">
          <span class="qs-or-line" /><span class="qs-or-text">{{ t('home.or') }}</span><span class="qs-or-line" />
        </div>

        <label class="console-field-label">{{ t('home.seedLabel') }}</label>
        <textarea
          v-model="quickStartText"
          :disabled="!!quickStartFile"
          class="qs-textarea"
          :placeholder="t('home.textareaPlaceholder')"
          rows="5"
        />

        <label class="console-field-label">{{ t('home.questionLabel') }}</label>
        <input
          v-model="quickStartQuestion"
          class="qs-question"
          :placeholder="t('home.questionPlaceholder')"
        />

        <label class="console-field-label">{{ t('home.presetLabel') }}</label>
        <div class="qs-presets">
          <button
            v-for="p in PRESETS"
            :key="p.key"
            class="qs-preset-pill"
            :class="{ active: quickStartPreset === p.key }"
            :title="p.hint"
            @click="quickStartPreset = p.key"
          >
            {{ p.label }}
          </button>
        </div>

        <p v-if="quickStartError" class="qs-error">{{ quickStartError }}</p>

        <button
          class="quick-start-btn"
          :disabled="!canQuickStart"
          @click="handleQuickStart"
        >
          {{ quickStartLoading ? t('home.launching') : t('home.launchBtn') }}
        </button>
      </div>
    </section>

    <section class="home-tools workbench-panel">
      <div class="tools-header">
        <span class="workbench-label">{{ t('home.toolsTitle') }}</span>
        <span>{{ domainPacks.length }} {{ t('home.domainPacks') }}</span>
      </div>

      <div v-if="domainPacks.length > 0" class="domain-tabs-wrap">
        <div class="domain-tabs">
          <button
            v-for="pack in domainPacks"
            :key="pack.id"
            :class="['domain-tab', { active: selectedDomain === pack.id }]"
            @click="selectDomain(pack.id)"
          >
            {{ pack.name_zh || pack.name_en }}
          </button>
        </div>
      </div>

      <div class="tools-row">
        <button class="tool-toggle" @click="showDomainBuilder = !showDomainBuilder">
          <span class="toggle-icon">{{ showDomainBuilder ? '▾' : '▸' }}</span>
          {{ t('home.customDomain') }}
        </button>
        <button class="tool-toggle" @click="showDataConnector = !showDataConnector">
          <span class="toggle-icon">{{ showDataConnector ? '▾' : '▸' }}</span>
          {{ t('home.dataConnector') }}
        </button>
        <button class="tool-toggle god-view-btn" @click="router.push('/god-view')">
          <span class="toggle-icon">⬡</span>
          {{ t('nav.godView') }}
        </button>
      </div>
    </section>

    <div v-if="showDomainBuilder" class="tool-panel workbench-panel">
      <DomainBuilder v-model="customDomainPack" />
    </div>

    <div v-if="showDataConnector" class="tool-panel workbench-panel">
      <DataConnectorPanel />
    </div>

    <OnboardingTooltip
      v-if="!onboardingDismissed"
      :title="onboardingSteps[currentStep].title"
      :description="onboardingSteps[currentStep].description"
      :step="currentStep"
      :total-steps="onboardingSteps.length"
      @next="onboardingNext"
      @dismiss="onboardingDismiss"
    />
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.home-console {
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(380px, 0.96fr);
  gap: 18px;
  align-items: stretch;
}

.mission-panel,
.prediction-console,
.home-tools,
.tool-panel {
  padding: 22px;
}

.mission-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background:
    linear-gradient(90deg, rgba(0,0,0,0.035) 1px, transparent 1px),
    linear-gradient(rgba(0,0,0,0.035) 1px, transparent 1px),
    var(--bg-card);
  background-size: 28px 28px;
}

.mission-topline,
.workflow-header,
.tools-header,
.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.live-chip,
.console-code,
.workflow-signal {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.82);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-title {
  font-family: var(--font-mono);
  font-size: clamp(48px, 9vw, 112px);
  font-weight: 800;
  line-height: 0.86;
  letter-spacing: 0;
  color: var(--text-primary);
  text-transform: uppercase;
  margin: 20px 0 0;
}

.hero-subtitle {
  width: fit-content;
  background: var(--text-primary);
  color: var(--text-inverse);
  padding: 5px 10px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-desc {
  color: var(--text-secondary);
  max-width: 680px;
  font-size: 15px;
  line-height: 1.75;
}

.status-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.metric-tile {
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.86);
  padding: 12px;
  min-height: 74px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
}

.metric-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
}

.workflow-panel,
.examples-panel {
  border-top: 1px solid var(--border);
  padding-top: 16px;
}

.workflow-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.workflow-item {
  display: grid;
  grid-template-columns: 42px 86px 1fr;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.9);
  padding: 10px 12px;
}

.workflow-num,
.workflow-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
}

.workflow-num {
  color: var(--text-muted);
}

.workflow-label {
  color: var(--text-primary);
}

.workflow-desc {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.45;
}

.examples-panel {
  display: grid;
  gap: 8px;
}

.example-seed {
  text-align: left;
  padding: 9px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
}

.example-seed:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.prediction-console {
  display: flex;
  flex-direction: column;
}

.console-header {
  margin-bottom: 10px;
}

.console-header h2 {
  font-size: 22px;
  font-weight: 800;
  margin-top: 4px;
}

.qs-subtitle { color: var(--text-muted); font-size: 13px; margin-bottom: 18px; line-height: 1.5; }

.console-field-label {
  display: block;
  margin: 12px 0 7px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.qs-drop-zone {
  border: 1px dashed var(--border-hover);
  background: var(--bg-input);
  padding: 24px 20px;
  text-align: center;
  min-height: 112px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background 0.2s, border-color 0.2s;
  cursor: pointer;
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}
.qs-drop-zone.dragging {
  background: var(--accent-subtle);
  border-color: var(--accent);
}
.qs-drop-zone.has-file {
  border-style: solid;
  border-color: var(--accent-success);
  cursor: default;
  flex-direction: row;
  justify-content: center;
  padding: 1rem 2rem;
}
.qs-file-hidden { display: none; }
.qs-drop-icon,
.qs-file-icon {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 2px 6px;
}
.qs-drop-label { font-weight: 800; color: var(--text-primary); }
.qs-drop-hint { font-size: 12px; color: var(--text-muted); }
.qs-file-name { font-weight: 600; flex: 1; text-align: left; margin-left: 0.5rem; }
.qs-file-clear {
  background: none; border: none; cursor: pointer;
  color: var(--text-muted); font-size: 1rem; padding: 0 0.25rem;
}
.qs-or-row { display: flex; align-items: center; gap: 0.75rem; margin: 10px 0; }
.qs-or-line { flex: 1; height: 1px; background: var(--border-color); }
.qs-or-text { color: var(--text-muted); font-family: var(--font-mono); font-size: 10px; white-space: nowrap; }
.qs-textarea {
  width: 100%; background: var(--bg-input, var(--bg-secondary));
  border: 1px solid var(--border-color); border-radius: var(--radius-sm);
  color: var(--text-primary); padding: 12px; font-size: 14px;
  resize: vertical; box-sizing: border-box;
  font-family: inherit;
  min-height: 132px;
}
.qs-textarea:disabled { opacity: 0.4; cursor: not-allowed; }
.qs-question {
  width: 100%; background: var(--bg-input, var(--bg-secondary));
  border: 1px solid var(--border-color); border-radius: var(--radius-sm);
  color: var(--text-primary); padding: 11px 12px;
  font-size: 14px; box-sizing: border-box;
  font-family: inherit;
}
.qs-presets { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.qs-preset-pill {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  padding: 7px 14px;
  border: 1px solid var(--border);
  background: var(--bg-card, #FFF);
  color: var(--text-secondary, #666);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
  text-transform: uppercase;
}
.qs-preset-pill.active {
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: #FFF;
}
.qs-preset-pill:hover:not(.active) {
  border-color: var(--border-hover, #999);
}
.qs-error { color: var(--accent-red); font-size: 0.85rem; margin-bottom: 0.5rem; }

.quick-start-btn {
  width: 100%;
  padding: 16px;
  background: var(--text-primary);
  color: #FFF;
  border: 1px solid var(--text-primary);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  animation: engine-pulse 2s infinite;
  transition: background 0.2s, border-color 0.2s;
}
.quick-start-btn:hover:not(:disabled) {
  background: var(--accent, #FF6B35);
  border-color: var(--accent, #FF6B35);
  transform: translateY(-2px);
}
.quick-start-btn:disabled {
  background: #E9E9E6;
  border-color: #E9E9E6;
  color: var(--text-muted);
  animation: none;
}
@keyframes engine-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0,0,0,0.2); }
  50%      { box-shadow: 0 0 0 6px rgba(0,0,0,0); }
}

.home-tools {
  display: grid;
  gap: 14px;
}

.tools-header {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 12px;
}

/* Domain tabs */
.domain-tabs-wrap {
  display: flex;
  justify-content: flex-start;
}

.domain-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.domain-tab {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.domain-tab:hover {
  color: var(--text-primary);
  border-color: var(--text-primary);
}

.domain-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #FFFFFF;
}

/* Tools row (domain builder + data connector toggles) */
.tools-row {
  display: flex;
  gap: 12px;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.tool-toggle {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 10px 20px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
}

.tool-toggle:hover {
  color: var(--text-primary);
  border-color: var(--text-primary);
}

.god-view-btn {
  border-color: var(--accent);
  color: var(--accent);
  font-family: var(--font-mono);
  letter-spacing: 1px;
  font-weight: 700;
}

.god-view-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: #FFFFFF;
}

.toggle-icon {
  font-size: 12px;
}

.tool-panel {
  margin-bottom: 32px;
}

@media (max-width: 980px) {
  .home-console {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .mission-panel,
  .prediction-console,
  .home-tools,
  .tool-panel {
    padding: 16px;
  }

  .status-metrics {
    grid-template-columns: repeat(2, 1fr);
  }

  .workflow-item {
    grid-template-columns: 38px 1fr;
  }

  .workflow-desc {
    grid-column: 2;
  }
}
</style>
