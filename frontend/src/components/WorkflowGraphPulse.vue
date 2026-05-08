<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  workflow: { type: Object, default: null },
})

const { t } = useI18n()

const events = computed(() => props.workflow?.events || [])
const artifacts = computed(() => props.workflow?.artifacts || {})

const agentsEvent = computed(() =>
  [...events.value].reverse().find((event) => event.event_type === 'agents_generated')
)

const graphEvent = computed(() =>
  [...events.value].reverse().find((event) => event.event_type === 'graph_built')
)

const agentNames = computed(() => {
  const names = agentsEvent.value?.payload?.agents || []
  if (names.length) return names
  const count = Number(agentsEvent.value?.payload?.agent_count || artifacts.value.agent_count || 18)
  return Array.from({ length: Math.min(count, 30) }, (_, idx) => `${t('workflowGraph.agent')} ${idx + 1}`)
})

const graphStats = computed(() => ({
  nodes: graphEvent.value?.payload?.node_count || artifacts.value.node_count || 0,
  edges: graphEvent.value?.payload?.edge_count || artifacts.value.edge_count || 0,
  agents: agentsEvent.value?.payload?.agent_count || agentNames.value.length,
}))

const stageNodes = computed(() => [
  { key: 'seed', label: t('workflowGraph.seed'), x: 96, y: 190, active: true },
  { key: 'graph', label: t('workflowGraph.graph'), x: 250, y: 108, active: graphStats.value.nodes > 0 },
  { key: 'agents', label: t('workflowGraph.agents'), x: 430, y: 186, active: graphStats.value.agents > 0 },
  { key: 'sim', label: t('workflowGraph.sim'), x: 612, y: 118, active: (props.workflow?.step_index || 0) >= 3 },
  { key: 'report', label: t('workflowGraph.report'), x: 764, y: 194, active: (props.workflow?.step_index || 0) >= 4 },
])

const agentDots = computed(() => {
  const names = agentNames.value.slice(0, 30)
  return names.map((name, index) => {
    const angle = (index / Math.max(1, names.length)) * Math.PI * 2
    const ring = 72 + (index % 3) * 24
    return {
      name,
      x: 430 + Math.cos(angle) * ring,
      y: 186 + Math.sin(angle) * ring * 0.62,
      delay: `${(index % 9) * 0.16}s`,
      duration: `${3.6 + (index % 5) * 0.45}s`,
    }
  })
})

const timeline = computed(() => events.value.slice(-8).reverse())
</script>

<template>
  <section class="workflow-graph workbench-panel" :aria-label="t('workflowGraph.title')">
    <div class="wf-head">
      <div>
        <span class="workbench-label">{{ t('workflowGraph.kicker') }}</span>
        <h2>{{ t('workflowGraph.title') }}</h2>
      </div>
      <div class="wf-status" :class="workflow?.status || 'queued'">
        {{ workflow?.status || t('workflowGraph.queued') }}
      </div>
    </div>

    <div class="wf-body">
      <svg viewBox="0 0 860 330" role="img" class="wf-svg">
        <line
          v-for="idx in stageNodes.length - 1"
          :key="`edge-${idx}`"
          :x1="stageNodes[idx - 1].x"
          :y1="stageNodes[idx - 1].y"
          :x2="stageNodes[idx].x"
          :y2="stageNodes[idx].y"
          class="wf-edge"
          :class="{ live: stageNodes[idx].active }"
        />

        <g v-for="dot in agentDots" :key="dot.name" class="agent-dot" :style="{ animationDelay: dot.delay, animationDuration: dot.duration }">
          <circle :cx="dot.x" :cy="dot.y" r="4.5" />
        </g>

        <g v-for="node in stageNodes" :key="node.key" class="stage-node" :class="{ active: node.active }">
          <circle :cx="node.x" :cy="node.y" r="24" />
          <text :x="node.x" :y="node.y + 45">{{ node.label }}</text>
        </g>
      </svg>

      <div class="wf-metrics">
        <div>
          <span>{{ t('workflowGraph.nodes') }}</span>
          <strong>{{ graphStats.nodes }}</strong>
        </div>
        <div>
          <span>{{ t('workflowGraph.edges') }}</span>
          <strong>{{ graphStats.edges }}</strong>
        </div>
        <div>
          <span>{{ t('workflowGraph.agentCount') }}</span>
          <strong>{{ graphStats.agents }}</strong>
        </div>
      </div>
    </div>

    <div class="wf-log" aria-live="polite">
      <div v-for="event in timeline" :key="`${event.created_at}-${event.event_type}`" class="wf-log-row">
        <span>{{ event.step }}</span>
        <strong>{{ event.message }}</strong>
      </div>
      <div v-if="!timeline.length" class="wf-log-empty">{{ t('workflowGraph.waiting') }}</div>
    </div>
  </section>
</template>

<style scoped>
.workflow-graph {
  padding: 16px;
  margin-bottom: 14px;
  background: var(--bg-card);
}

.wf-head,
.wf-metrics,
.wf-log-row {
  display: flex;
  align-items: center;
}

.wf-head {
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
}

.wf-head h2 {
  margin: 4px 0 0;
  font-family: var(--font-editorial);
  font-size: 22px;
  letter-spacing: 0;
}

.wf-status {
  border: 1px solid var(--border-hover);
  padding: 6px 9px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  background: var(--bg-input);
}

.wf-status.running {
  color: var(--accent);
  border-color: var(--accent);
}

.wf-status.completed {
  color: var(--accent-blue-note);
  border-color: var(--accent-blue-note);
}

.wf-status.degraded {
  color: var(--accent);
  border-color: var(--accent);
}

.wf-status.failed {
  color: var(--accent-danger);
  border-color: var(--accent-danger);
}

.wf-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px;
  gap: 14px;
  align-items: stretch;
}

.wf-svg {
  width: 100%;
  min-height: 260px;
  display: block;
}

.wf-edge {
  stroke: rgba(33, 31, 27, 0.18);
  stroke-width: 1.4;
}

.wf-edge.live {
  stroke: var(--accent);
  stroke-dasharray: 5 6;
  animation: dash 1.6s linear infinite;
}

.stage-node circle {
  fill: var(--bg-input);
  stroke: var(--border-hover);
  stroke-width: 1.5;
}

.stage-node.active circle {
  fill: var(--text-primary);
  stroke: var(--accent);
}

.stage-node text {
  fill: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  text-anchor: middle;
}

.stage-node.active text {
  fill: var(--text-primary);
}

.agent-dot {
  animation: drift 4s ease-in-out infinite alternate;
}

.agent-dot circle {
  fill: var(--accent);
  opacity: 0.78;
}

.wf-metrics {
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.wf-metrics div {
  width: 100%;
  border: 1px solid var(--border);
  background: rgba(255,253,247,0.78);
  padding: 10px;
}

.wf-metrics span,
.wf-log-row span {
  display: block;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
}

.wf-metrics strong {
  display: block;
  margin-top: 4px;
  font-family: var(--font-mono);
  font-size: 20px;
}

.wf-log {
  border-top: 1px solid var(--border);
  padding-top: 10px;
  display: grid;
  gap: 6px;
}

.wf-log-row {
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  padding: 7px 9px;
}

.wf-log-row strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--text-primary);
}

.wf-log-empty {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

@keyframes drift {
  from { transform: translate(-4px, 2px); }
  to { transform: translate(5px, -5px); }
}

@keyframes dash {
  to { stroke-dashoffset: -22; }
}

@media (max-width: 820px) {
  .wf-body {
    grid-template-columns: 1fr;
  }

  .wf-metrics {
    flex-direction: row;
  }
}
</style>
