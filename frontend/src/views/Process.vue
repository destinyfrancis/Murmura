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
  currentStep.value === 3 && session.sessionId ? 'RUNNING' : ''
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
        <span class="workbench-label">STEP {{ currentStepNumber }}</span>
        <h1>{{ currentStepMeta?.label }}</h1>
        <p>{{ t('process.workbench.subtitle') }}</p>
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

    <!-- Step content — preserve existing PresetSelector + component bindings -->
    <main class="step-content" :style="stepStyle">
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
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 2px;
  color: var(--text-primary);
  background: transparent;
  border: 1px solid var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  text-transform: uppercase;
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
  font-size: 24px;
  font-weight: 800;
  margin: 3px 0 2px;
}

.process-heading p {
  color: var(--text-muted);
  font-size: 13px;
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
  letter-spacing: 0.1em;
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
  gap: 10px;
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
  background: var(--bg-card);
  color: var(--text-secondary);
  text-align: left;
}

.rail-step:hover:not(:disabled) {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.rail-step.active {
  border-color: var(--text-primary);
  background: var(--text-primary);
  color: var(--text-inverse);
}

.rail-step.done {
  border-color: var(--accent);
}

.rail-step.locked {
  color: var(--text-quaternary);
  background: #F3F3F0;
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
  letter-spacing: 0.1em;
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
  background: var(--accent, #FF6B35);
  color: #FFF;
  padding: 2px 8px;
  border-radius: 2px;
  letter-spacing: 0.05em;
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
  background: var(--bg-card, #FFF);
  color: var(--text-primary, #000);
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
  height: 4px;
  display: flex;
  background: var(--bg-app);
}
.progress-seg { flex: 1; background: var(--border); }
.progress-seg.done { background: var(--accent); }
.progress-seg.active { background: var(--accent); opacity: .5; }

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 18px 24px 28px;
  min-height: 0;
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
  background: #FFF4E5;
  color: #663C00;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  border: 1px solid #FFD8A8;
}

@media (max-width: 1060px) {
  .process-header {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .process-telemetry {
    min-width: 100%;
  }

  .workflow-rail {
    display: none;
  }

  .compact-switcher {
    display: block;
  }
}

@media (max-width: 680px) {
  .process-header,
  .step-content {
    padding-left: 14px;
    padding-right: 14px;
  }

  .process-telemetry {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
