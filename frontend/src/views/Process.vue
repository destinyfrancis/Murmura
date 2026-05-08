<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { cleanupSession } from '../api/simulation.js'
import PresetSelector from '../components/PresetSelector.vue'
import Step1GraphBuild from '../components/Step1GraphBuild.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import Step4Report from '../components/Step4Report.vue'
import Step5Interaction from '../components/Step5Interaction.vue'
import WorkflowGraphPulse from '../components/WorkflowGraphPulse.vue'
import { getWorkflow } from '../api/workflow.js'

const props = defineProps({
  scenarioType: { type: String, required: true },
})

const { t } = useI18n()
const route = useRoute()

const router = useRouter()

// domainPackId comes from query param (?domainPackId=market_sector)
// Defaults to 'hk_city' for backward compatibility
const domainPackId = ref(route.query.domainPackId || 'hk_city')

// Express mode — populated by /process/quick?express=1&sessionId=X&graphId=Y&...
const expressMode = computed(() => route.query.express === '1')
const expressSessionId = computed(() => route.query.sessionId || null)
const expressGraphId = computed(() => route.query.graphId || null)
const expressScenarioQuestion = computed(() => route.query.scenarioQuestion || '')
const expressWorkflowId = computed(() => route.query.workflowId || null)
const workflowState = ref(null)
const workflowError = ref('')
let _workflowPollId = null

const steps = computed(() => [
  { key: 1, label: t('process.nav.steps.graph.label'), navLabel: t('process.nav.steps.graph.navLabel') },
  { key: 2, label: t('process.nav.steps.env.label'), navLabel: t('process.nav.steps.env.navLabel') },
  { key: 3, label: t('process.nav.steps.sim.label'), navLabel: t('process.nav.steps.sim.navLabel') },
  { key: 4, label: t('process.nav.steps.report.label'), navLabel: t('process.nav.steps.report.navLabel') },
  { key: 5, label: t('process.nav.steps.interact.label'), navLabel: t('process.nav.steps.interact.navLabel') },
])

const currentStep = ref(1)

const currentStepMeta = computed(() => steps.value[currentStep.value - 1] || steps.value[0])
const currentStepNumber = computed(() => String(currentStep.value).padStart(2, '0'))
const viewMode = ref('workbench')

const session = reactive({
  scenarioType: props.scenarioType,
  domainPackId: domainPackId.value,
  graphId: null,
  graphData: null,
  sessionId: null,
  simulationComplete: false,
  reportId: null,
  scenarioQuestion: '',           // passed through to Step 4 report
  preset: { name: 'standard', agents: 300, rounds: 20 },
  config: {
    agentCount: 100,
    roundCount: 30,
    macroScenario: 'baseline',
    platforms: ['twitter', 'reddit'],
    shocks: [],
  },
  capabilities: {
    simulation: true,
  }
})

const stepConfig = {
  1: { leftWidth: 70 },
  2: { leftWidth: 50 },
  3: { leftWidth: 40 },
  4: { leftWidth: 75 },
  5: { leftWidth: 45 },
}

const stepStyle = computed(() => ({
  '--left-width': `${stepConfig[currentStep.value]?.leftWidth ?? 60}%`,
}))

const stepSlugs = ['graph', 'env', 'sim', 'report', 'interact']
const currentStepSlug = computed(() => stepSlugs[currentStep.value - 1] || 'graph')

const viewModes = computed(() => [
  { key: 'evidence', label: t('process.views.evidence') },
  { key: 'split', label: t('process.views.split') },
  { key: 'workbench', label: t('process.views.workbench') },
])

const stageFrameClass = computed(() => ({
  'mode-evidence': viewMode.value === 'evidence',
  'mode-workbench': viewMode.value === 'workbench',
}))

const currentStepContext = computed(() => ({
  title: t(`process.context.steps.${currentStepSlug.value}.title`),
  desc: t(`process.context.steps.${currentStepSlug.value}.desc`),
  output: t(`process.context.steps.${currentStepSlug.value}.output`),
}))

const contextMetrics = computed(() => [
  { label: t('process.context.metrics.session'), value: session.sessionId ? session.sessionId.slice(0, 8) : '--' },
  { label: t('process.context.metrics.graph'), value: session.graphId ? session.graphId.slice(0, 8) : '--' },
  { label: t('process.context.metrics.mode'), value: (session.scenarioType || 'custom').toUpperCase() },
])

const contextChecklist = computed(() =>
  steps.value.map((step) => ({
    ...step,
    state: currentStep.value === step.key
      ? t('process.workbench.active')
      : canGoToStep(step.key) && step.key < currentStep.value
        ? t('process.workbench.done')
        : !canGoToStep(step.key)
          ? t('process.workbench.locked')
          : t('process.workbench.ready'),
  }))
)

const currentComponent = computed(() => {
  const map = {
    1: Step1GraphBuild,
    2: Step2EnvSetup,
    3: Step3Simulation,
    4: Step4Report,
    5: Step5Interaction,
  }
  return map[currentStep.value]
})

function canGoToStep(step) {
  if (step > 2 && !session.capabilities.simulation) return false
  if (step <= 1) return true
  if (step === 2) return session.graphId !== null
  if (step === 3) return session.sessionId !== null
  if (step === 4) return session.simulationComplete === true
  if (step === 5) return session.reportId !== null
  return false
}

function stepLockedReason(step) {
  if (step > 2 && !session.capabilities.simulation) return t('process.errors.engineUnavailable')
  if (step === 2) return t('process.errors.graphFirst')
  if (step === 3) return t('process.errors.envFirst')
  if (step === 4) return t('process.errors.simFirst')
  if (step === 5) return t('process.errors.reportFirst')
  return ''
}

function goToStep(step) {
  if (canGoToStep(step)) {
    currentStep.value = step
  }
}

const roundLabel = computed(() =>
  (currentStep.value === 3 && session.sessionId) || workflowState.value?.status === 'running' ? 'RUNNING' : ''
)

const sessionTelemetry = computed(() => [
  { label: t('process.workbench.session'), value: session.sessionId ? session.sessionId.slice(0, 8) : '--' },
  { label: t('process.workbench.graph'), value: session.graphId ? session.graphId.slice(0, 8) : '--' },
  { label: t('process.workbench.preset'), value: (session.preset?.name || 'standard').toUpperCase() },
  { label: t('process.workbench.engine'), value: session.capabilities.simulation ? t('process.workbench.ready') : t('process.workbench.unavailable') },
])

function nextStep() {
  if (currentStep.value < 5) {
    currentStep.value += 1
  }
}

function onGraphBuilt(data) {
  session.graphId = data.graphId
  session.graphData = data.graphData
  nextStep()
}

function onSimulationCreated(data) {
  session.sessionId = data.sessionId
  nextStep()
}

function onSimulationComplete(data) {
  session.sessionId = data.sessionId
  session.simulationComplete = true
  nextStep()
}

function onReportGenerated(data) {
  session.reportId = data.reportId
  nextStep()
}

function onSessionUpdate(data) {
  Object.assign(session, data || {})
}

// currentComponentProps — passes scenarioQuestion to Step4Report, session to all others
const currentComponentProps = computed(() => {
  if (currentStep.value === 4) {
    return { session, scenarioQuestion: session.scenarioQuestion }
  }
  return { session }
})

// Express mode: unmount-safe guard
let _expressAdvanceCancelled = false
const _expressTimeoutIds = []

function _applyWorkflowState(data) {
  workflowState.value = data
  if (!data) return
  if (data.graph_id) session.graphId = data.graph_id
  if (data.session_id) session.sessionId = data.session_id
  if (data.report_id) session.reportId = data.report_id
  if (data.scenario_question) session.scenarioQuestion = data.scenario_question
  if (data.preset) session.preset = { ...(session.preset || {}), name: data.preset }
  if (data.step_index && data.step_index >= 1) {
    currentStep.value = Math.min(5, Math.max(currentStep.value, Number(data.step_index)))
  }
  if (data.status === 'completed' || data.status === 'degraded') {
    session.simulationComplete = true
    currentStep.value = data.report_id ? 5 : 4
  }
}

async function _pollWorkflowOnce() {
  if (!expressWorkflowId.value) return
  try {
    const res = await getWorkflow(expressWorkflowId.value)
    const data = res.data?.data || res.data
    workflowError.value = ''
    _applyWorkflowState(data)
    if (data?.status === 'completed' || data?.status === 'degraded' || data?.status === 'failed') {
      if (_workflowPollId) clearInterval(_workflowPollId)
      _workflowPollId = null
    }
  } catch (err) {
    workflowError.value = err.response?.data?.detail || err.message || t('process.errors.workflowPolling')
  }
}

// --- Resource cleanup on navigation away or browser close ---
function _releaseSessionResources() {
  if (session.sessionId) {
    // Fire-and-forget — navigator.sendBeacon is unreliable for POST with body,
    // so use a plain fetch with keepalive to survive page unload.
    fetch(`/api/simulation/${session.sessionId}/cleanup`, {
      method: 'POST',
      keepalive: true,
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    }).catch(() => {})
  }
}

function _onBeforeUnload() {
  _releaseSessionResources()
}

onMounted(() => {
  window.addEventListener('beforeunload', _onBeforeUnload)
})

onUnmounted(() => {
  _expressAdvanceCancelled = true
  _expressTimeoutIds.forEach(id => clearTimeout(id))
  _expressTimeoutIds.length = 0
  if (_workflowPollId) clearInterval(_workflowPollId)
  _workflowPollId = null
  window.removeEventListener('beforeunload', _onBeforeUnload)
  // Release resources when navigating away within the SPA
  if (session.sessionId) {
    cleanupSession(session.sessionId).catch(() => {})
  }
})

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    const health = await res.json()
    if (health.capabilities) {
      session.capabilities = { ...session.capabilities, ...health.capabilities }
    }
  } catch (err) {
    console.error('Failed to fetch capabilities', err)
  }

  if (!expressMode.value) return
  _expressAdvanceCancelled = false

  if (expressWorkflowId.value) {
    Object.assign(session, {
      scenarioQuestion: expressScenarioQuestion.value,
      preset: { ...(session.preset || {}), name: route.query.preset || session.preset.name },
    })
    currentStep.value = 1
    await _pollWorkflowOnce()
    if (!_workflowPollId) {
      _workflowPollId = setInterval(_pollWorkflowOnce, 1500)
    }
    return
  }

  // Pre-populate session from URL params (reactive() mutation is intentional here —
  // direct field mutation is Vue's intended pattern for reactive(); accepted exception
  // to the project's immutability rule)
  Object.assign(session, {
    graphId: expressGraphId.value,
    sessionId: expressSessionId.value,
    scenarioQuestion: expressScenarioQuestion.value,
    // Express mode: simulation already started — unlock step 3 nav immediately
    // simulationComplete is set to true by Step3 when WS 'complete' event fires
  })

  // Auto-advance: briefly show each step as "auto-completed" before landing on Step 3
  currentStep.value = 1
  await new Promise((r) => {
    const id = setTimeout(r, 600)
    _expressTimeoutIds.push(id)
  })
  if (_expressAdvanceCancelled) return
  currentStep.value = 2
  await new Promise((r) => {
    const id = setTimeout(r, 400)
    _expressTimeoutIds.push(id)
  })
  if (_expressAdvanceCancelled) return
  currentStep.value = 3
})

// Sync preset agents/rounds into config whenever preset changes
watch(
  () => session.preset,
  (p) => {
    if (p && p.agents) session.config.agentCount = p.agents
    if (p && p.rounds) session.config.roundCount = p.rounds
  },
  { deep: true },
)
</script>

<template>
  <div class="process-root">
    <header class="process-header">
      <button class="process-brand nav-brand" @click="router.push('/')">Murmura</button>
      <div class="process-heading">
        <span class="workbench-label">{{ t('process.workbench.step') }} {{ currentStepNumber }}</span>
        <h1>{{ currentStepMeta?.label }}</h1>
        <p>{{ t('process.workbench.subtitle') }}</p>
      </div>
      <div class="process-view-switcher" :aria-label="t('process.views.label')">
        <button
          v-for="mode in viewModes"
          :key="mode.key"
          class="process-view-btn"
          :class="{ active: viewMode === mode.key }"
          @click="viewMode = mode.key"
        >
          {{ mode.label }}
        </button>
      </div>
      <div class="process-telemetry">
        <div v-for="item in sessionTelemetry" :key="item.label" class="telemetry-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
      <span v-if="roundLabel" class="nav-step-badge">
        <span class="status-dot processing" />
        {{ roundLabel }}
      </span>
    </header>

    <nav class="workflow-rail" :aria-label="t('home.pipelineTitle')">
      <div class="rail-line" />
      <button
        v-for="step in steps"
        :key="step.key"
        class="rail-step"
        :class="{
          active: currentStep === step.key,
          done: canGoToStep(step.key) && step.key < currentStep,
          locked: !canGoToStep(step.key),
        }"
        :disabled="!canGoToStep(step.key)"
        :title="!canGoToStep(step.key) ? stepLockedReason(step.key) : step.label"
        @click="goToStep(step.key)"
      >
        <span class="rail-num">{{ String(step.key).padStart(2, '0') }}</span>
        <span class="rail-copy">
          <strong>{{ step.navLabel }}</strong>
          <small>
            {{ currentStep === step.key
              ? t('process.workbench.active')
              : canGoToStep(step.key) && step.key < currentStep
                ? t('process.workbench.done')
                : !canGoToStep(step.key)
                  ? t('process.workbench.locked')
                  : t('process.workbench.ready')
            }}
          </small>
        </span>
      </button>
    </nav>

    <div class="compact-switcher">
      <div class="nav-view-switcher">
        <button
          v-for="step in steps"
          :key="step.key"
          class="view-switch-btn"
          :class="{ active: currentStep === step.key, done: canGoToStep(step.key) && step.key < currentStep }"
          :disabled="!canGoToStep(step.key)"
          :title="!canGoToStep(step.key) ? stepLockedReason(step.key) : step.label"
          @click="goToStep(step.key)"
        >
          {{ step.navLabel }}
        </button>
      </div>
    </div>

    <!-- 3px progress bar -->
    <div class="step-progress-bar">
      <div
        v-for="step in steps"
        :key="step.key"
        class="progress-seg"
        :class="{
          done: currentStep > step.key,
          active: currentStep === step.key,
        }"
      />
    </div>

    <!-- Express mode indicator -->
    <div v-if="expressMode" class="express-badge">{{ t('process.nav.expressBadge') }}</div>

    <div v-if="!session.capabilities.simulation" class="capability-warning">
      {{ t('process.errors.engineUnavailableDetail') }}
    </div>

    <main class="step-content" :style="stepStyle">
      <div class="stage-frame" :class="stageFrameClass">
        <aside class="stage-context workbench-panel" :aria-label="t('process.context.label')">
          <div class="context-header">
            <span class="workbench-label">{{ t('process.context.label') }}</span>
            <span class="context-step">{{ t('process.workbench.step') }} {{ currentStepNumber }}</span>
          </div>

          <div class="context-note">
            <h2>{{ currentStepContext.title }}</h2>
            <p>{{ currentStepContext.desc }}</p>
          </div>

          <div class="context-metrics">
            <div v-for="item in contextMetrics" :key="item.label" class="context-metric">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>

          <div class="context-output">
            <span class="workbench-label">{{ t('process.context.expectedOutput') }}</span>
            <p>{{ currentStepContext.output }}</p>
          </div>

          <div class="context-checklist">
            <span class="workbench-label">{{ t('process.context.pipeline') }}</span>
            <button
              v-for="step in contextChecklist"
              :key="step.key"
              class="context-check"
              :class="{
                active: currentStep === step.key,
                done: canGoToStep(step.key) && step.key < currentStep,
                locked: !canGoToStep(step.key),
              }"
              :disabled="!canGoToStep(step.key)"
              @click="goToStep(step.key)"
            >
              <span>{{ String(step.key).padStart(2, '0') }}</span>
              <strong>{{ step.navLabel }}</strong>
              <small>{{ step.state }}</small>
            </button>
          </div>
        </aside>

        <section class="stage-workbench">
          <WorkflowGraphPulse
            v-if="expressWorkflowId"
            :workflow="workflowState"
          />
          <div v-if="workflowError" class="workflow-error">
            {{ workflowError }}
          </div>
          <PresetSelector
            v-if="currentStep === 2"
            v-model="session.preset"
            class="preset-selector-row"
          />
          <component
            :is="currentComponent"
            v-bind="currentComponentProps"
            @graph-built="onGraphBuilt"
            @simulation-created="onSimulationCreated"
            @simulation-complete="onSimulationComplete"
            @report-generated="onReportGenerated"
            @update:session="onSessionUpdate"
            @switch-step="goToStep"
          />
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.process-root {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 56px);
  background: var(--bg-app);
}

.process-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}

.process-brand {
  font-family: var(--font-editorial);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0;
  color: var(--text-primary);
  background: transparent;
  border: 1px solid var(--border-hover);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  text-transform: none;
  cursor: pointer;
}

.process-brand:hover {
  background: var(--text-primary);
  color: var(--text-inverse);
}

.process-heading {
  min-width: 240px;
  flex: 1;
}

.process-heading h1 {
  font-family: var(--font-editorial);
  font-size: 28px;
  font-weight: 700;
  margin: 3px 0 2px;
}

.process-heading p {
  color: var(--text-muted);
  font-size: 13px;
}

.process-view-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-graph);
  flex-shrink: 0;
}

.process-view-btn {
  min-height: 32px;
  padding: 7px 12px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  white-space: nowrap;
}

.process-view-btn:hover {
  color: var(--text-primary);
}

.process-view-btn.active {
  background: var(--bg-card);
  color: var(--accent);
  box-shadow: 0 1px 0 rgba(33,31,27,0.06);
}

.process-telemetry {
  display: grid;
  grid-template-columns: repeat(4, minmax(72px, 1fr));
  gap: 6px;
  min-width: min(520px, 46vw);
}

.telemetry-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  padding: 8px 10px;
  min-height: 50px;
}

.telemetry-item span {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0;
  color: var(--text-muted);
}

.telemetry-item strong {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
}

.workflow-rail {
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  padding: 16px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}

.rail-line {
  position: absolute;
  left: 44px;
  right: 44px;
  top: 36px;
  height: 1px;
  background: var(--border);
  pointer-events: none;
}

.rail-step {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 1;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-secondary);
  text-align: left;
}

.rail-step:hover:not(:disabled) {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.rail-step.active {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--text-inverse);
}

.rail-step.done {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.rail-step.locked {
  color: var(--text-quaternary);
  background: #E9E9E6;
  cursor: not-allowed;
}

.rail-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
  background: inherit;
}

.rail-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.rail-copy strong,
.rail-copy small {
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rail-copy strong {
  font-size: 12px;
  font-weight: 800;
}

.rail-copy small {
  font-size: 9px;
  letter-spacing: 0;
  opacity: 0.72;
}

.compact-switcher {
  display: none;
  padding: 10px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}
.nav-step-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  background: var(--accent);
  color: #FFF;
  padding: 2px 8px;
  border-radius: 2px;
  letter-spacing: 0;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 4px;
}
.nav-view-switcher {
  display: flex;
  background: var(--bg-graph);
  border: 1px solid var(--border);
  padding: 3px;
  border-radius: var(--radius-md, 4px);
  gap: 4px;
  overflow-x: auto;
}
.view-switch-btn {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  color: var(--text-secondary, #666);
  background: none;
  border: none;
  padding: 6px 16px;
  border-radius: var(--radius-sm, 2px);
  cursor: pointer;
  transition: background var(--duration-fast, 0.15s), color var(--duration-fast, 0.15s);
}
.view-switch-btn:hover:not(:disabled) {
  color: var(--text-primary, #000);
}
.view-switch-btn.active {
  background: var(--bg-card);
  color: var(--accent);
  box-shadow: none;
}
.view-switch-btn.done {
  color: var(--text-muted, #999);
}
.view-switch-btn:disabled {
  color: #D1D5DB;
  cursor: not-allowed;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.processing {
  background: #FFF;
  animation: nav-pulse 1s infinite;
}
@keyframes nav-pulse {
  50% { opacity: 0.5; }
}

.step-progress-bar {
  height: 3px;
  display: flex;
  background: var(--bg-app);
}
.progress-seg { flex: 1; background: var(--border); }
.progress-seg.done { background: var(--accent); }
.progress-seg.active { background: var(--accent); opacity: .72; }

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 18px 24px 28px;
  min-height: 0;
}

.stage-frame {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 16px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns var(--duration-layout) var(--ease-standard);
}

.stage-frame.mode-workbench {
  grid-template-columns: 0 minmax(0, 1fr);
  gap: 0;
}

.stage-frame.mode-evidence {
  grid-template-columns: minmax(320px, 560px) 0;
  gap: 0;
}

.stage-context {
  padding: 18px;
  min-width: 0;
  overflow: hidden auto;
  max-height: calc(100vh - 228px);
  background: var(--bg-card);
}

.stage-frame.mode-workbench .stage-context,
.stage-frame.mode-evidence .stage-workbench {
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
  padding: 0;
  border: 0;
}

.stage-workbench {
  min-width: 0;
  min-height: 0;
  transition: opacity var(--duration-standard) var(--ease-standard);
}

.workflow-error {
  border: 1px solid var(--accent-danger);
  background: var(--accent-subtle);
  color: var(--accent-danger);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  padding: 9px 10px;
  margin-bottom: 12px;
}

.context-header,
.context-metric,
.context-check {
  display: flex;
  align-items: center;
}

.context-header {
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.context-step {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 4px 7px;
  color: var(--accent);
  background: var(--accent-subtle);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
}

.context-note {
  padding: 18px 0 14px;
}

.context-note h2 {
  font-family: var(--font-editorial);
  font-size: 25px;
  font-weight: 700;
  line-height: 1.08;
  margin: 0 0 10px;
}

.context-note p,
.context-output p {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.65;
}

.context-metrics {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  padding: 12px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.context-metric {
  justify-content: space-between;
  gap: 10px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  padding: 8px 9px;
}

.context-metric span,
.context-check small {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
}

.context-metric strong {
  min-width: 0;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.context-output {
  display: grid;
  gap: 8px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.context-checklist {
  display: grid;
  gap: 6px;
  padding-top: 14px;
}

.context-checklist > .workbench-label {
  margin-bottom: 3px;
}

.context-check {
  width: 100%;
  min-width: 0;
  justify-content: flex-start;
  gap: 9px;
  padding: 9px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-secondary);
  text-align: left;
}

.context-check:hover:not(:disabled) {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.context-check.active {
  border-color: var(--accent);
  background: var(--accent-subtle);
  color: var(--accent);
}

.context-check.done {
  border-color: var(--accent);
}

.context-check.locked {
  color: var(--text-quaternary);
  background: #E9E9E6;
  cursor: not-allowed;
}

.context-check span,
.context-check strong {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
}

.context-check strong {
  flex: 1;
  min-width: 0;
}

.stage-workbench :deep(.step1),
.stage-workbench :deep(.step2),
.stage-workbench :deep(.step3),
.stage-workbench :deep(.step4),
.stage-workbench :deep(.step5) {
  min-width: 0;
}

.express-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-subtle);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 0.2rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 600;
  margin: 12px 24px 0;
  width: fit-content;
}

.capability-warning {
  margin: 16px 24px;
  padding: 12px 16px;
  background: #F6E7C8;
  color: #6B4210;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  border: 1px solid #D8B468;
}

@media (max-width: 1060px) {
  .process-header {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .process-telemetry {
    min-width: 100%;
  }

  .process-view-switcher {
    order: 3;
  }

  .workflow-rail {
    display: none;
  }

  .compact-switcher {
    display: block;
  }

  .stage-frame,
  .stage-frame.mode-evidence,
  .stage-frame.mode-workbench {
    grid-template-columns: 1fr;
  }

  .stage-frame.mode-workbench .stage-context,
  .stage-frame.mode-evidence .stage-workbench {
    display: none;
  }

  .stage-context {
    max-height: none;
  }
}

@media (max-width: 680px) {
  .process-header,
  .step-content {
    padding-left: 14px;
    padding-right: 14px;
  }

  .process-heading {
    min-width: 0;
  }

  .process-view-switcher {
    width: 100%;
    overflow-x: auto;
  }

  .process-view-btn {
    flex: 1;
  }

  .process-telemetry {
    grid-template-columns: repeat(2, 1fr);
  }

  .stage-context {
    padding: 14px;
  }
}
</style>
