<script setup>
const props = defineProps({
  graphId: { type: String, default: null },
  sessionId: { type: String, default: null },
  running: { type: Boolean, default: false },
})
import { ref, computed, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import GraphCanvas from './GraphCanvas.vue'
import { getGraph, getNodeEvidence } from '../api/graph.js'
import { getSessionActions } from '../api/simulation.js'
import { unwrapApi } from '../api/utils.js'

const { t } = useI18n()
const nodes = ref([])
const edges = ref([])
const actions = ref([])
const selected = ref(null)
const evidence = ref(null)
const nodeLabel = node => node?.label || node?.title || node?.name || node?.id || t('research.unknown')
const evidenceText = computed(() => {
  if (!evidence.value) return t('research.loading')
  const snippets = [...(evidence.value.source_texts || []), ...(evidence.value.memories || []).map(item => item.memory_text),
    ...(evidence.value.provenance || []).map(item => item.source_url || item.notes)].filter(Boolean)
  return snippets.join('\n\n') || t('research.unknown')
})
const error = ref('')
const loading = ref(false)
let disposed = false
let timer = null
let revision = 0

async function refresh() {
  const captured = ++revision
  const graphId = props.graphId
  const sessionId = props.sessionId
  if (!graphId) return
  loading.value = !nodes.value.length
  const results = await Promise.allSettled([
    getGraph(graphId),
    sessionId ? getSessionActions(sessionId, { limit: 40, latest: true }) : Promise.resolve(null),
  ])
  if (disposed || captured !== revision) return
  loading.value = false
  if (results[0].status === 'fulfilled') {
    const graph = unwrapApi(results[0].value, {})
    nodes.value = graph.nodes || []
    edges.value = graph.edges || []
    error.value = ''
  } else error.value = t('research.failed')
  if (results[1].status === 'fulfilled' && results[1].value) {
    actions.value = unwrapApi(results[1].value, [])
  } else if (results[1].status === 'rejected') error.value = t('research.failed')
}

async function selectNode(node) {
  if (!node) return
  selected.value = node
  evidence.value = null
  const graphId = props.graphId
  try {
    const result = await getNodeEvidence(graphId, node.id)
    if (!disposed && graphId === props.graphId && selected.value?.id === node.id) {
      evidence.value = unwrapApi(result, {})
    }
  } catch {
    if (!disposed && selected.value?.id === node.id) evidence.value = { unavailable: true }
  }
}

watch(() => [props.graphId, props.sessionId], () => {
  revision++
  nodes.value = []; edges.value = []; actions.value = []; selected.value = null
  refresh()
}, { immediate: true })
watch(() => props.running, (running) => {
  if (timer) clearInterval(timer)
  timer = running ? setInterval(refresh, 4000) : null
  refresh()
}, { immediate: true })
onUnmounted(() => { disposed = true; revision++; if (timer) clearInterval(timer) })
</script>

<template>
  <section class="world" :aria-label="t('research.world')">
    <header>
      <div><h2>{{ t('research.world') }}</h2><p>{{ t('research.worldHint') }}</p></div>
      <span class="counts">{{ nodes.length }} {{ t('research.nodes') }} · {{ edges.length }} {{ t('research.edges') }}</span>
    </header>
    <div v-if="error" class="notice" role="alert">{{ error }} <button @click="refresh">{{ t('research.retry') }}</button></div>
    <div class="canvas">
      <GraphCanvas v-if="nodes.length" :nodes="nodes" :edges="edges" @node-click="selectNode" />
      <p v-else class="empty" role="status">{{ loading ? t('research.loading') : t('research.empty') }}</p>
    </div>
    <label v-if="nodes.length" class="actor-picker">{{ t('research.source') }}
      <select :value="selected?.id || ''" @change="selectNode(nodes.find(node => node.id === $event.target.value))">
        <option disabled value="">{{ t('research.chooseActor') }}</option>
        <option v-for="node in nodes" :key="node.id" :value="node.id">{{ nodeLabel(node) }}</option>
      </select>
    </label>
    <div v-if="selected" class="selection">
      <strong>{{ nodeLabel(selected) }}</strong>
      <p>{{ selected.description }}</p>
      <details><summary>{{ t('research.source') }}</summary><pre>{{ evidenceText }}</pre></details>
    </div>
    <div class="activity">
      <h3>{{ t('research.events') }}</h3>
      <p v-if="!actions.length" class="empty">{{ t('research.unknown') }}</p>
      <ol v-else>
        <li v-for="(action, index) in actions" :key="action.id || index">
          <span class="round">R{{ action.round_number }}</span>
          <div><strong>{{ action.oasis_username }}</strong> <small>{{ action.action_type }}</small><p>{{ action.content }}</p></div>
        </li>
      </ol>
    </div>
    <p class="boundary">{{ t('research.unverified') }}</p>
  </section>
</template>

<style scoped>
.world { min-width: 0; border: 1px solid var(--border); background: var(--bg-card); }
header { padding: 16px; display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--border); }
h2, h3 { font-size: 14px; margin: 0 0 6px; } p { margin: 4px 0; line-height: 1.6; }
header p, small, .counts, .boundary { color: var(--text-secondary); font-size: 11px; }
.counts, .round { font-family: var(--font-mono); white-space: nowrap; }
.canvas { height: 380px; position: relative; }
.empty { color: var(--text-secondary); padding: 24px; font-size: 13px; }
.actor-picker { display: flex; padding: 12px 16px; gap: 12px; font-size: 12px; }
.actor-picker select { min-width: 0; flex: 1; padding: 5px; border: 1px solid var(--border); }
.selection, .activity { padding: 16px; border-top: 1px solid var(--border); font-size: 13px; }
.activity { max-height: 340px; overflow-y: auto; }
ol { padding: 0; margin: 0; list-style: none; }
li { display: flex; align-items: baseline; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
li p { overflow-wrap: anywhere; white-space: pre-wrap; }
.round { color: var(--accent); font-size: 11px; }
.boundary, .notice { padding: 12px 16px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 180px; overflow: auto; }
button, summary { cursor: pointer; } button:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
@media(max-width: 700px) { header { flex-direction: column; } .canvas { height: 290px; } }
</style>
