<script setup>
import { computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettings } from '../composables/useSettings.js'
import { testApiKey, listProviderModels, updateSettings } from '../api/settings.js'

const { settings, saveStatus, loadSettings, saveApiKey } = useSettings()
const { t } = useI18n()

// ── Tab state ──────────────────────────────────────────────────────────────────
const activeTab = ref('api')

const tabs = computed(() => [
  { id: 'api',        label: t('settings.tabs.api.title'),   icon: 'API' },
  { id: 'model',      label: t('settings.tabs.model.title'), icon: 'LLM' },
  { id: 'simulation', label: t('settings.tabs.sim.title'),   icon: 'SIM' },
  { id: 'ui',         label: t('settings.tabs.ui.title'),    icon: 'UI' },
  { id: 'data',       label: t('settings.tabs.data.title'),  icon: 'DATA' },
])

// ── API key editing state ──────────────────────────────────────────────────────
const keyDraft = ref({
  openrouter: '',
  google: '',
  openai: '',
  anthropic: '',
  deepseek: '',
  fireworks: '',
  fred: '',
})

const keyVisibility = ref({
  openrouter: false,
  google: false,
  openai: false,
  anthropic: false,
  deepseek: false,
  fireworks: false,
  fred: false,
})

const keyTestStatus = ref({
  openrouter: null,   // null | 'testing' | 'ok' | 'error'
  google: null,
  openai: null,
  anthropic: null,
  deepseek: null,
  fireworks: null,
  fred: null,
})

const keyTestMessage = ref({})

// ── Providers config ─────────────────────────────────────────────────────────
const providers = [
  { id: 'openrouter', name: 'OpenRouter', placeholder: 'sk-or-v1-...', color: '#7C3AED' },
  { id: 'google',     name: 'Google AI',  placeholder: 'AIza...',       color: '#4285F4' },
  { id: 'openai',     name: 'OpenAI',     placeholder: 'sk-...',        color: '#10A37F' },
  { id: 'anthropic',  name: 'Anthropic',  placeholder: 'sk-ant-...',    color: '#CC7A00' },
  { id: 'deepseek',   name: 'DeepSeek',   placeholder: 'sk-...',        color: '#1875D1' },
  { id: 'fireworks',  name: 'Fireworks',  placeholder: 'fw-...',        color: '#FF6B35' },
]

const providerOptions = providers.map(p => ({ value: p.id, label: p.name }))
const discoverableProviders = new Set(['openrouter', 'fireworks'])
const providerModels = ref({})
const modelListStatus = ref({})
const modelListMessage = ref({})

function providerSupportsModels(provider) {
  return discoverableProviders.has(provider)
}

function modelOptionsFor(provider) {
  return providerModels.value[provider] || []
}

function modelListSummary(provider) {
  if (!provider) return t('settings.tabs.model.models.chooseProvider')
  if (!providerSupportsModels(provider)) return t('settings.tabs.model.models.unsupported')
  if (modelListStatus.value[provider] === 'loading') return t('settings.tabs.model.models.loading')
  const models = modelOptionsFor(provider)
  if (models.length) return t('settings.tabs.model.models.loaded', { count: models.length })
  return t('settings.tabs.model.models.notLoaded')
}

async function fetchProviderModels(provider, apiKey = null) {
  if (!provider) return
  if (!providerSupportsModels(provider)) {
    modelListStatus.value[provider] = 'error'
    modelListMessage.value[provider] = t('settings.tabs.model.models.unsupported')
    return
  }
  modelListStatus.value[provider] = 'loading'
  modelListMessage.value[provider] = ''
  try {
    const res = await listProviderModels(provider, apiKey)
    if (res.data.success) {
      providerModels.value[provider] = res.data.models || []
      modelListStatus.value[provider] = 'ok'
      modelListMessage.value[provider] = res.data.message
    } else {
      providerModels.value[provider] = []
      modelListStatus.value[provider] = 'error'
      modelListMessage.value[provider] = res.data.message
    }
  } catch (err) {
    providerModels.value[provider] = []
    modelListStatus.value[provider] = 'error'
    modelListMessage.value[provider] = err.response?.data?.detail || t('settings.tabs.api.connFailed')
  }
}

// ── Key actions ───────────────────────────────────────────────────────────────
async function handleSaveKey(provider) {
  const key = keyDraft.value[provider].trim()
  if (!key) return
  await saveApiKey(provider, key)
  if (providerSupportsModels(provider)) {
    await fetchProviderModels(provider, key)
  }
  keyDraft.value[provider] = ''
}

async function handleTestKey(provider) {
  const draftKey = keyDraft.value[provider].trim()
  const storedKey = settings.apiKeys[provider]
  const key = draftKey || (storedKey && !storedKey.includes('***') ? storedKey : null)
  if (!key && !storedKey) {
    keyTestMessage.value[provider] = t('settings.tabs.api.verifying')
    keyTestStatus.value[provider] = 'error'
    return
  }
  keyTestStatus.value[provider] = 'testing'
  keyTestMessage.value[provider] = ''
  try {
    const testProvider = provider === 'fred' ? 'fred' : provider
    const res = await testApiKey(testProvider, key)
    if (res.data.success) {
      keyTestStatus.value[provider] = 'ok'
      keyTestMessage.value[provider] = res.data.message
      if (providerSupportsModels(provider)) {
        await fetchProviderModels(provider, draftKey || null)
      }
    } else {
      keyTestStatus.value[provider] = 'error'
      keyTestMessage.value[provider] = res.data.message
    }
  } catch (err) {
    keyTestStatus.value[provider] = 'error'
    keyTestMessage.value[provider] = err.response?.data?.detail || t('settings.tabs.api.verifying')
  }
}

function toggleKeyVisibility(provider) {
  keyVisibility.value[provider] = !keyVisibility.value[provider]
}

// ── Preset options ─────────────────────────────────────────────────────────
const presetOptions = computed(() => [
  { value: 'fast',     label: `FAST · ${t('home.presets.fast')} (10 rounds, 30 agents)` },
  { value: 'standard', label: `STD · ${t('home.presets.standard')} (20 rounds, 50 agents)` },
  { value: 'deep',     label: `DEEP · ${t('home.presets.deep')} (50 rounds, 200 agents)` },
])

const languageOptions = [
  { value: 'zh-HK', label: '繁體中文（香港）' },
  { value: 'zh-TW', label: '繁體中文（台灣）' },
  { value: 'en-US', label: 'English (US)' },
  { value: 'ja-JP', label: '日本語' },
]

const itemsPerPageOptions = [10, 20, 50, 100]

// ── Model routing ──────────────────────────────────────────────────────────────
const SIMPLE_MODEL_DEFAULT = {
  provider: 'openrouter',
  model: 'deepseek/deepseek-chat-v3.1',
}

const simpleModelDraft = ref({
  provider: SIMPLE_MODEL_DEFAULT.provider,
  model: SIMPLE_MODEL_DEFAULT.model,
  testStatus: null,
  testMsg: '',
})

const simpleModelStatus = ref(null)
const simpleModelMessage = ref('')

const QUICK_APPLY_PRESETS = {
  deepseek: { provider: SIMPLE_MODEL_DEFAULT.provider, model: SIMPLE_MODEL_DEFAULT.model },
  gemini:   { provider: 'google',     model: 'gemini-3.1-pro-preview' },
  gpt4o:    { provider: 'openai',     model: 'gpt-4o' },
}

const stepDefs = computed(() => [
  { step: 1, label: t('settings.tabs.model.steps.step1.label'), hint: t('settings.tabs.model.steps.step1.hint') },
  { step: 2, label: t('settings.tabs.model.steps.step2.label'), hint: t('settings.tabs.model.steps.step2.hint') },
  { step: 3, label: t('settings.tabs.model.steps.step3.label'), hint: t('settings.tabs.model.steps.step3.hint'), hasLite: true },
  { step: 4, label: t('settings.tabs.model.steps.step4.label'), hint: t('settings.tabs.model.steps.step4.hint') },
  { step: 5, label: t('settings.tabs.model.steps.step5.label'), hint: t('settings.tabs.model.steps.step5.hint') },
])

const stepDraft = ref(
  Object.fromEntries([1, 2, 3, 4, 5].map(s => [
    s, { provider: '', model: '', model_lite: '', testStatus: null, testMsg: '' }
  ]))
)

function applyPreset(presetKey) {
  const p = QUICK_APPLY_PRESETS[presetKey]
  simpleModelDraft.value.provider = p.provider
  simpleModelDraft.value.model = p.model
  for (const s of [1, 2, 3, 4, 5]) {
    stepDraft.value[s].provider = p.provider
    stepDraft.value[s].model    = p.model
  }
}

function resetStepDrafts() {
  for (const s of [1, 2, 3, 4, 5]) {
    stepDraft.value[s].provider = ''
    stepDraft.value[s].model = ''
    stepDraft.value[s].model_lite = ''
    stepDraft.value[s].testStatus = null
    stepDraft.value[s].testMsg = ''
  }
}

async function handleSimpleProviderChange() {
  const provider = simpleModelDraft.value.provider
  if (providerSupportsModels(provider) && !modelOptionsFor(provider).length) {
    await fetchProviderModels(provider)
  }
}

async function testSimpleModel() {
  const draft = simpleModelDraft.value
  if (!draft.provider || !draft.model) {
    draft.testStatus = 'error'
    draft.testMsg = t('settings.tabs.model.simple.fillBoth')
    return
  }
  draft.testStatus = 'testing'
  draft.testMsg = ''
  try {
    const res = await testApiKey(draft.provider, null, draft.model)
    draft.testStatus = res.data.success ? 'ok' : 'error'
    draft.testMsg = res.data.message
  } catch (err) {
    draft.testStatus = 'error'
    draft.testMsg = err.response?.data?.detail || t('settings.tabs.api.connFailed')
  }
}

async function saveSimpleModel() {
  const draft = simpleModelDraft.value
  if (!draft.provider || !draft.model) {
    simpleModelStatus.value = 'error'
    simpleModelMessage.value = t('settings.tabs.model.simple.fillBoth')
    return
  }
  simpleModelStatus.value = 'testing'
  simpleModelMessage.value = t('settings.tabs.model.simple.saving')
  const payload = {
    agent_provider: draft.provider,
    agent_model: draft.model,
    agent_model_lite: '',
    report_provider: draft.provider,
    report_model: draft.model,
    step1_provider: '',
    step1_model: '',
    step2_provider: '',
    step2_model: '',
    step3_provider: '',
    step3_model: '',
    step3_model_lite: '',
    step4_provider: '',
    step4_model: '',
    step5_provider: '',
    step5_model: '',
  }
  try {
    const res = await updateSettings(payload)
    const data = res.data?.settings || res.data
    if (data?.llm) Object.assign(settings.llm, data.llm)
    resetStepDrafts()
    simpleModelStatus.value = 'ok'
    simpleModelMessage.value = t('settings.tabs.model.simple.saved')
  } catch (err) {
    console.error('[Settings] saveSimpleModel failed:', err)
    simpleModelStatus.value = 'error'
    simpleModelMessage.value = err.response?.data?.detail || t('settings.tabs.api.connFailed')
  }
}

async function saveStepModel(step) {
  const d = stepDraft.value[step]
  const payload = {
    [`step${step}_provider`]: d.provider,
    [`step${step}_model`]:    d.model,
  }
  if (step === 3) {
    payload['step3_model_lite'] = d.model_lite
  }
  try {
    await updateSettings(payload)
  } catch (err) {
    console.error('[Settings] saveStepModel failed:', err)
  }
}

async function handleStepProviderChange(step) {
  const provider = stepDraft.value[step].provider
  if (providerSupportsModels(provider) && !modelOptionsFor(provider).length) {
    await fetchProviderModels(provider)
  }
}

async function testStepModel(step) {
  const d = stepDraft.value[step]
  if (!d.provider || !d.model) {
    d.testStatus = 'error'
    d.testMsg = t('settings.tabs.model.steps.fillBoth')
    return
  }
  d.testStatus = 'testing'
  d.testMsg = ''
  try {
    const res = await testApiKey(d.provider, null, d.model)
    d.testStatus = res.data.success ? 'ok' : 'error'
    d.testMsg    = res.data.message
  } catch (err) {
    d.testStatus = 'error'
    d.testMsg    = err.response?.data?.detail || t('settings.tabs.api.connFailed')
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadSettings()
  simpleModelDraft.value.provider = settings.llm?.report_provider || settings.llm?.agent_provider || SIMPLE_MODEL_DEFAULT.provider
  simpleModelDraft.value.model = settings.llm?.report_model || settings.llm?.agent_model || SIMPLE_MODEL_DEFAULT.model
  // Populate step drafts from loaded settings
  const steps = settings.llm?.steps || {}
  for (const s of [1, 2, 3, 4, 5]) {
    const st = steps[String(s)] || {}
    if (st.provider) stepDraft.value[s].provider = st.provider
    if (st.model)    stepDraft.value[s].model    = st.model
    if (st.model_lite) stepDraft.value[s].model_lite = st.model_lite
  }
})

// ── Save indicator helpers ─────────────────────────────────────────────────────
const saveStatusLabel = computed(() => ({
  idle:   '',
  saving: '● ' + t('settings.tabs.data.verifying').replace('...', '').replace('…', ''), // Basic loading
  saved:  '✓ ' + t('settings.tabs.data.save'),
  error:  '✗',
}))

const saveStatusClass = {
  idle:   '',
  saving: 'status-saving',
  saved:  'status-saved',
  error:  'status-error',
}
</script>

<template>
  <div class="settings-page">
    <!-- Page header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ $t('settings.header.title') }}</h1>
        <p class="page-subtitle">{{ $t('settings.header.subtitle') }}</p>
      </div>
      <div class="save-indicator" :class="saveStatusClass[saveStatus]" aria-live="polite">
        {{ saveStatusLabel[saveStatus] }}
      </div>
    </div>

    <!-- Layout: tab sidebar + content -->
    <div class="settings-layout">

      <!-- Tab sidebar -->
      <nav class="settings-sidebar" role="navigation" :aria-label="$t('settings.tabs.navLabel')">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :id="`settings-tab-${tab.id}`"
          class="sidebar-tab"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
          :aria-selected="activeTab === tab.id"
          role="tab"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </nav>

      <!-- Content area -->
      <div class="settings-content" role="tabpanel" :aria-labelledby="`settings-tab-${activeTab}`">

        <!-- ═══ Tab: API 金鑰 ═══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'api'" class="tab-pane" id="tab-panel-api">
          <div class="tab-header">
            <h2 class="tab-title">{{ $t('settings.tabs.api.title') }}</h2>
            <p class="tab-desc">{{ $t('settings.tabs.api.desc') }}</p>
          </div>

          <div class="api-key-list">
            <div
              v-for="p in providers"
              :key="p.id"
              class="api-key-card"
            >
              <div class="key-card-header">
                <div class="provider-badge" :style="{ background: p.color + '18', borderColor: p.color + '40', color: p.color }">
                  {{ p.name }}
                </div>
                <div class="current-key" v-if="settings.apiKeys[p.id]">
                  <span class="key-masked font-mono">{{ settings.apiKeys[p.id] }}</span>
                </div>
                <div class="current-key empty" v-else>
                  <span class="key-empty">{{ $t('settings.tabs.api.empty') }}</span>
                </div>
              </div>

              <div class="key-input-row">
                <div class="key-input-wrapper">
                  <input
                    :id="`key-input-${p.id}`"
                    v-model="keyDraft[p.id]"
                    :type="keyVisibility[p.id] ? 'text' : 'password'"
                    class="key-input"
                    :placeholder="p.placeholder"
                    autocomplete="off"
                    spellcheck="false"
                    @keyup.enter="handleSaveKey(p.id)"
                    :aria-label="$t('settings.tabs.api.keyInputAria', { provider: p.name })"
                  />
                  <button
                    class="btn-eye"
                    @click="toggleKeyVisibility(p.id)"
                    :title="keyVisibility[p.id] ? $t('settings.tabs.api.hideKey') : $t('settings.tabs.api.showKey')"
                    :aria-label="keyVisibility[p.id] ? $t('settings.tabs.api.hideKey') : $t('settings.tabs.api.showKey')"
                  >
                    {{ keyVisibility[p.id] ? $t('settings.tabs.api.hide') : $t('settings.tabs.api.show') }}
                  </button>
                </div>
                <button
                  class="btn-secondary"
                  @click="handleTestKey(p.id)"
                  :disabled="keyTestStatus[p.id] === 'testing'"
                  :aria-label="$t('settings.tabs.api.testKeyAria', { provider: p.name })"
                >
                  <span v-if="keyTestStatus[p.id] === 'testing'">{{ $t('settings.tabs.api.testing') }}</span>
                  <span v-else>{{ $t('settings.tabs.api.test') }}</span>
                </button>
                <button
                  class="btn-primary"
                  @click="handleSaveKey(p.id)"
                  :disabled="!keyDraft[p.id].trim()"
                  :aria-label="$t('settings.tabs.api.saveKeyAria', { provider: p.name })"
                >
                  {{ $t('settings.tabs.api.save') }}
                </button>
                <button
                  v-if="providerSupportsModels(p.id)"
                  class="btn-secondary"
                  @click="fetchProviderModels(p.id, keyDraft[p.id].trim() || null)"
                  :disabled="modelListStatus[p.id] === 'loading'"
                  :aria-label="`${$t('settings.tabs.model.models.sync')} ${p.name}`"
                >
                  <span v-if="modelListStatus[p.id] === 'loading'">{{ $t('settings.tabs.model.models.syncing') }}</span>
                  <span v-else>{{ $t('settings.tabs.model.models.sync') }}</span>
                </button>
              </div>

              <!-- Test result badge -->
              <div v-if="keyTestStatus[p.id]" class="test-result" :class="`test-${keyTestStatus[p.id]}`">
                <span v-if="keyTestStatus[p.id] === 'ok'">✓ {{ keyTestMessage[p.id] }}</span>
                <span v-else-if="keyTestStatus[p.id] === 'error'">✗ {{ keyTestMessage[p.id] }}</span>
                <span v-else>{{ $t('settings.tabs.api.verifying') }}</span>
              </div>
              <div
                v-if="providerSupportsModels(p.id) && modelListStatus[p.id]"
                class="test-result"
                :class="`test-${modelListStatus[p.id]}`"
              >
                {{ modelListMessage[p.id] || modelListSummary(p.id) }}
              </div>
            </div>
          </div>
        </div>

        <!-- ═══ Tab: 模型選擇 ════════════════════════════════════════════════ -->
        <div v-if="activeTab === 'model'" class="tab-pane" id="tab-panel-model">
          <div class="tab-header">
            <h2 class="tab-title">{{ $t('settings.tabs.model.title') }}</h2>
            <p class="tab-desc">{{ $t('settings.tabs.model.desc') }}</p>
          </div>

          <section class="simple-model-panel">
            <div class="simple-model-copy">
              <span class="model-eyebrow">{{ $t('settings.tabs.model.simple.eyebrow') }}</span>
              <h3 class="simple-model-title">{{ $t('settings.tabs.model.simple.title') }}</h3>
              <p class="simple-model-desc">{{ $t('settings.tabs.model.simple.desc') }}</p>
            </div>

            <div class="simple-model-fields">
              <div class="form-field">
                <label class="field-label" for="simple-provider">{{ $t('settings.tabs.model.provider') }}</label>
                <select
                  id="simple-provider"
                  v-model="simpleModelDraft.provider"
                  class="field-select"
                  @change="handleSimpleProviderChange"
                >
                  <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="form-field">
                <label class="field-label" for="simple-model">{{ $t('settings.tabs.model.model') }}</label>
                <div class="model-input-row">
                  <input
                    id="simple-model"
                    v-model="simpleModelDraft.model"
                    class="field-input"
                    list="models-simple"
                    placeholder="deepseek/deepseek-chat-v3.1"
                    spellcheck="false"
                  />
                  <button
                    class="btn-secondary"
                    @click="fetchProviderModels(simpleModelDraft.provider)"
                    :disabled="!providerSupportsModels(simpleModelDraft.provider) || modelListStatus[simpleModelDraft.provider] === 'loading'"
                  >
                    <span v-if="modelListStatus[simpleModelDraft.provider] === 'loading'">{{ $t('settings.tabs.model.models.syncing') }}</span>
                    <span v-else>{{ $t('settings.tabs.model.models.sync') }}</span>
                  </button>
                </div>
                <datalist id="models-simple">
                  <option
                    v-for="model in modelOptionsFor(simpleModelDraft.provider)"
                    :key="model.id"
                    :value="model.id"
                  >
                    {{ model.name }}
                  </option>
                </datalist>
                <p class="field-hint">{{ modelListSummary(simpleModelDraft.provider) }}</p>
              </div>
            </div>

            <div class="simple-model-actions">
              <button class="btn-ghost btn-sm" @click="applyPreset('deepseek')">
                {{ $t('settings.tabs.model.simple.recommended') }}
              </button>
              <button
                class="btn-secondary"
                @click="testSimpleModel"
                :disabled="simpleModelDraft.testStatus === 'testing'"
              >
                <span v-if="simpleModelDraft.testStatus === 'testing'">{{ $t('settings.tabs.api.testing') }}</span>
                <span v-else>{{ $t('settings.tabs.api.test') }}</span>
              </button>
              <button class="btn-primary" @click="saveSimpleModel">
                {{ $t('settings.tabs.model.simple.save') }}
              </button>
            </div>

            <div
              v-if="simpleModelDraft.testStatus"
              class="test-result"
              :class="`test-${simpleModelDraft.testStatus}`"
            >
              <span v-if="simpleModelDraft.testStatus === 'ok'">✓ {{ simpleModelDraft.testMsg }}</span>
              <span v-else-if="simpleModelDraft.testStatus === 'error'">✗ {{ simpleModelDraft.testMsg }}</span>
              <span v-else>{{ $t('settings.tabs.api.verifying') }}</span>
            </div>
            <div
              v-if="simpleModelStatus"
              class="test-result"
              :class="`test-${simpleModelStatus}`"
            >
              <span v-if="simpleModelStatus === 'ok'">✓ {{ simpleModelMessage }}</span>
              <span v-else-if="simpleModelStatus === 'error'">✗ {{ simpleModelMessage }}</span>
              <span v-else>{{ simpleModelMessage }}</span>
            </div>

            <div class="model-routing-strip">
              <div class="routing-item">
                <span>{{ $t('settings.tabs.model.simple.routingSeed') }}</span>
                <strong>{{ simpleModelDraft.provider }}</strong>
              </div>
              <div class="routing-item">
                <span>{{ $t('settings.tabs.model.simple.routingSimulation') }}</span>
                <strong>{{ simpleModelDraft.model }}</strong>
              </div>
              <div class="routing-item">
                <span>{{ $t('settings.tabs.model.simple.routingReport') }}</span>
                <strong>{{ $t('settings.tabs.model.simple.sameModel') }}</strong>
              </div>
            </div>
          </section>

          <details class="global-fallback-section">
            <summary class="global-fallback-toggle">{{ $t('settings.tabs.model.advanced') }}</summary>

            <div class="quick-apply-bar">
              <span class="qa-label">{{ $t('settings.tabs.model.quickApply') }}</span>
              <button class="btn-ghost btn-sm" @click="applyPreset('deepseek')">DeepSeek</button>
              <button class="btn-ghost btn-sm" @click="applyPreset('gemini')">Gemini</button>
              <button class="btn-ghost btn-sm" @click="applyPreset('gpt4o')">GPT-4o</button>
            </div>

            <div class="step-model-list">
              <div v-for="def in stepDefs" :key="def.step" class="step-model-card">
                <div class="step-card-header">
                  <span class="step-badge">{{ def.step }}</span>
                  <h3 class="step-card-title">{{ def.label }}</h3>
                </div>
                <p class="step-card-hint">{{ def.hint }}</p>

                <div class="step-model-fields">
                  <div class="form-field">
                    <label class="field-label">{{ $t('settings.tabs.model.provider') }}</label>
                    <select
                      v-model="stepDraft[def.step].provider"
                      class="field-select"
                      @change="handleStepProviderChange(def.step)"
                    >
                      <option value="">— {{ $t('settings.tabs.model.steps.useGlobal') }} —</option>
                      <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                    </select>
                  </div>
                  <div class="form-field">
                    <label class="field-label">{{ $t('settings.tabs.model.model') }}</label>
                    <div class="model-input-row">
                      <input
                        v-model="stepDraft[def.step].model"
                        class="field-input"
                        :list="`models-step-${def.step}`"
                        placeholder="deepseek/deepseek-chat-v3.1"
                        spellcheck="false"
                      />
                      <button
                        class="btn-secondary"
                        @click="fetchProviderModels(stepDraft[def.step].provider)"
                        :disabled="!providerSupportsModels(stepDraft[def.step].provider) || modelListStatus[stepDraft[def.step].provider] === 'loading'"
                      >
                        <span v-if="modelListStatus[stepDraft[def.step].provider] === 'loading'">{{ $t('settings.tabs.model.models.syncing') }}</span>
                        <span v-else>{{ $t('settings.tabs.model.models.sync') }}</span>
                      </button>
                    </div>
                    <datalist :id="`models-step-${def.step}`">
                      <option
                        v-for="model in modelOptionsFor(stepDraft[def.step].provider)"
                        :key="model.id"
                        :value="model.id"
                      >
                        {{ model.name }}
                      </option>
                    </datalist>
                    <p class="field-hint">{{ modelListSummary(stepDraft[def.step].provider) }}</p>
                  </div>
                  <div v-if="def.hasLite" class="form-field">
                    <label class="field-label">{{ $t('settings.tabs.model.agent.lite') }}</label>
                    <input
                      v-model="stepDraft[def.step].model_lite"
                      class="field-input"
                      :list="`models-step-${def.step}`"
                      :placeholder="$t('settings.tabs.model.agent.liteHint')"
                      spellcheck="false"
                    />
                  </div>
                </div>

                <div class="step-card-actions">
                  <button
                    class="btn-secondary"
                    @click="testStepModel(def.step)"
                    :disabled="stepDraft[def.step].testStatus === 'testing'"
                  >
                    <span v-if="stepDraft[def.step].testStatus === 'testing'">{{ $t('settings.tabs.api.testing') }}</span>
                    <span v-else>{{ $t('settings.tabs.api.test') }}</span>
                  </button>
                  <button class="btn-primary" @click="saveStepModel(def.step)">
                    {{ $t('settings.tabs.api.save') }}
                  </button>
                </div>

                <div
                  v-if="stepDraft[def.step].testStatus"
                  class="test-result"
                  :class="`test-${stepDraft[def.step].testStatus}`"
                >
                  <span v-if="stepDraft[def.step].testStatus === 'ok'">✓ {{ stepDraft[def.step].testMsg }}</span>
                  <span v-else-if="stepDraft[def.step].testStatus === 'error'">✗ {{ stepDraft[def.step].testMsg }}</span>
                  <span v-else>{{ $t('settings.tabs.api.verifying') }}</span>
                </div>
              </div>
            </div>
          </details>
        </div>

        <!-- ═══ Tab: 模擬預設 ════════════════════════════════════════════════ -->
        <div v-if="activeTab === 'simulation'" class="tab-pane" id="tab-panel-simulation">
          <div class="tab-header">
            <h2 class="tab-title">{{ $t('settings.tabs.sim.title') }}</h2>
            <p class="tab-desc">{{ $t('settings.tabs.sim.desc') }}</p>
          </div>

          <div class="settings-grid single">

            <div class="settings-group">

              <div class="form-field">
                <label class="field-label" for="default-preset">{{ $t('settings.tabs.sim.preset') }}</label>
                <div class="preset-selector">
                  <label
                    v-for="opt in presetOptions"
                    :key="opt.value"
                    class="preset-option"
                    :class="{ selected: settings.simulation.default_preset === opt.value }"
                  >
                    <input
                      type="radio"
                      :id="`preset-${opt.value}`"
                      v-model="settings.simulation.default_preset"
                      :value="opt.value"
                      class="preset-radio"
                    />
                    {{ opt.label }}
                  </label>
                </div>
              </div>

              <div class="form-field">
                <label class="field-label" for="agent-count">{{ $t('settings.tabs.sim.agents') }}</label>
                <div class="input-with-unit">
                  <input
                    id="agent-count"
                    v-model.number="settings.simulation.default_agent_count"
                    type="number"
                    min="5"
                    max="500"
                    class="field-input narrow"
                  />
                  <span class="unit">{{ $t('settings.tabs.sim.agentsUnit') || 'agents' }}</span>
                </div>
                <p class="field-hint">{{ $t('settings.tabs.sim.agentsHint') }}</p>
              </div>

              <div class="form-field">
                <label class="field-label" for="concurrency-limit">
                  {{ $t('settings.tabs.sim.concurrency') }}
                  <span class="field-value">{{ settings.simulation.concurrency_limit }}</span>
                </label>
                <input
                  id="concurrency-limit"
                  v-model.number="settings.simulation.concurrency_limit"
                  type="range"
                  min="1"
                  max="200"
                  class="field-range"
                />
                <div class="range-labels">
                  <span>1</span>
                  <span>200</span>
                </div>
                <p class="field-hint">{{ $t('settings.tabs.sim.concurrencyHint') }}</p>
              </div>

              <div class="form-field">
                <label class="field-label" for="default-domain">{{ $t('settings.tabs.sim.domain') }}</label>
                <input
                  id="default-domain"
                  v-model="settings.simulation.default_domain"
                  class="field-input"
                  placeholder="e.g. hk_city"
                  spellcheck="false"
                />
                <p class="field-hint">{{ $t('settings.tabs.sim.domainHint') }}</p>
              </div>

            </div>
          </div>
        </div>

        <!-- ═══ Tab: 介面偏好 ════════════════════════════════════════════════ -->
        <div v-if="activeTab === 'ui'" class="tab-pane" id="tab-panel-ui">
          <div class="tab-header">
            <h2 class="tab-title">{{ $t('settings.tabs.ui.title') }}</h2>
            <p class="tab-desc">{{ $t('settings.tabs.ui.desc') }}</p>
          </div>

          <div class="settings-grid single">
            <div class="settings-group">

              <div class="form-field">
                <label class="field-label" for="ui-language">{{ $t('settings.tabs.ui.lang') }}</label>
                <select id="ui-language" v-model="settings.ui.language" class="field-select">
                  <option v-for="opt in languageOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>

              <div class="form-field">
                <label class="field-label" for="items-per-page">{{ $t('settings.tabs.ui.itemsPerPage') }}</label>
                <div class="segmented-control">
                  <button
                    v-for="n in itemsPerPageOptions"
                    :key="n"
                    :id="`items-per-page-${n}`"
                    class="seg-btn"
                    :class="{ active: settings.ui.items_per_page === n }"
                    @click="settings.ui.items_per_page = n"
                  >{{ n }}</button>
                </div>
              </div>

              <div class="form-field toggle-field">
                <div class="toggle-info">
                  <label class="field-label" for="auto-open-report">{{ $t('settings.tabs.ui.autoOpen') }}</label>
                  <p class="field-hint">{{ $t('settings.tabs.ui.autoOpenHint') }}</p>
                </div>
                <label class="toggle-switch" :class="{ active: settings.ui.auto_open_report }">
                  <input
                    id="auto-open-report"
                    v-model="settings.ui.auto_open_report"
                    type="checkbox"
                    class="toggle-input"
                    role="switch"
                    :aria-checked="settings.ui.auto_open_report"
                  />
                  <span class="toggle-track">
                    <span class="toggle-thumb" />
                  </span>
                </label>
              </div>

            </div>
          </div>
        </div>

        <!-- ═══ Tab: 資料來源 ═══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'data'" class="tab-pane" id="tab-panel-data">
          <div class="tab-header">
            <h2 class="tab-title">{{ $t('settings.tabs.data.title') }}</h2>
            <p class="tab-desc">{{ $t('settings.tabs.data.desc') }}</p>
          </div>

          <div class="settings-grid single">
            <div class="settings-group">

              <!-- FRED API Key -->
              <div class="form-field">
                <label class="field-label" for="fred-key-input">{{ $t('settings.tabs.data.fred') }}</label>
                <div class="key-card-header minimal">
                  <div class="current-key" v-if="settings.data.fred_api_key">
                    <span class="key-masked font-mono">{{ settings.data.fred_api_key }}</span>
                  </div>
                  <div class="current-key empty" v-else>
                    <span class="key-empty">{{ $t('settings.tabs.data.empty') }}</span>
                  </div>
                </div>
                <div class="key-input-row">
                  <div class="key-input-wrapper">
                    <input
                      id="fred-key-input"
                      v-model="keyDraft.fred"
                      :type="keyVisibility.fred ? 'text' : 'password'"
                      class="key-input"
                      placeholder="Your FRED API key"
                      autocomplete="off"
                      @keyup.enter="handleSaveKey('fred')"
                      :aria-label="$t('settings.tabs.api.keyInputAria', { provider: 'FRED' })"
                    />
                    <button
                      class="btn-eye"
                      @click="toggleKeyVisibility('fred')"
                      :title="keyVisibility.fred ? $t('settings.tabs.api.hideKey') : $t('settings.tabs.api.showKey')"
                      :aria-label="keyVisibility.fred ? $t('settings.tabs.api.hideKey') : $t('settings.tabs.api.showKey')"
                    >
                      {{ keyVisibility.fred ? $t('settings.tabs.api.hide') : $t('settings.tabs.api.show') }}
                    </button>
                  </div>
                  <button class="btn-secondary" @click="handleTestKey('fred')" :disabled="keyTestStatus.fred === 'testing'">
                    <span v-if="keyTestStatus.fred === 'testing'">⏳</span>
                    <span v-else>{{ $t('settings.tabs.data.test') }}</span>
                  </button>
                  <button class="btn-primary" @click="handleSaveKey('fred')" :disabled="!keyDraft.fred.trim()">
                    {{ $t('settings.tabs.data.save') }}
                  </button>
                </div>
                <div v-if="keyTestStatus.fred" class="test-result" :class="`test-${keyTestStatus.fred}`">
                  <span v-if="keyTestStatus.fred === 'ok'">✓ {{ keyTestMessage.fred }}</span>
                  <span v-else-if="keyTestStatus.fred === 'error'">✗ {{ keyTestMessage.fred }}</span>
                  <span v-else>{{ $t('settings.tabs.data.verifying') }}</span>
                </div>
                <p class="field-hint"><span v-html="$t('settings.tabs.data.fredHint')"></span></p>
              </div>

              <!-- External Feed Toggle -->
              <div class="form-field toggle-field">
                <div class="toggle-info">
                  <label class="field-label" for="external-feed-toggle">{{ $t('settings.tabs.data.externalFeed') }}</label>
                  <p class="field-hint">{{ $t('settings.tabs.data.externalFeedHint') }}</p>
                </div>
                <label class="toggle-switch" :class="{ active: settings.data.external_feed_enabled }">
                  <input
                    id="external-feed-toggle"
                    v-model="settings.data.external_feed_enabled"
                    type="checkbox"
                    class="toggle-input"
                    role="switch"
                    :aria-checked="settings.data.external_feed_enabled"
                  />
                  <span class="toggle-track">
                    <span class="toggle-thumb" />
                  </span>
                </label>
              </div>

              <!-- Refresh interval -->
              <div class="form-field" v-if="settings.data.external_feed_enabled">
                <label class="field-label" for="refresh-interval">{{ $t('settings.tabs.data.refreshInterval') }}</label>
                <div class="input-with-unit">
                  <input
                    id="refresh-interval"
                    v-model.number="settings.data.feed_refresh_interval"
                    type="number"
                    min="300"
                    max="86400"
                    step="300"
                    class="field-input narrow"
                  />
                  <span class="unit">{{ $t('settings.tabs.data.seconds') }}</span>
                </div>
                <p class="field-hint">{{ $t('settings.tabs.data.refreshHint') }}</p>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Page layout ─────────────────────────────────────────────────────────── */

.settings-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 24px 72px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 36px;
}

.page-title {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Save indicator ──────────────────────────────────────────────────────── */

.save-indicator {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  transition: all 0.25s ease;
  min-width: 90px;
  text-align: right;
}

.status-saving {
  color: var(--accent-warn);
}

.status-saved {
  color: var(--accent-success);
}

.status-error {
  color: var(--accent-danger);
}

/* ── Layout ──────────────────────────────────────────────────────────────── */

.settings-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  min-height: 560px;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */

.settings-sidebar {
  background: var(--bg-graph);
  border-right: 1px solid var(--border);
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-tab {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  border-left: 3px solid transparent;
  text-align: left;
  cursor: pointer;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  transition: all 0.15s ease;
}

.sidebar-tab:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary);
}

.sidebar-tab.active {
  border-left-color: var(--accent);
  background: var(--text-primary);
  color: #FFFFFF;
  font-weight: 700;
}

.tab-icon {
  display: inline-flex;
  min-width: 34px;
  justify-content: center;
  border: 1px solid currentColor;
  padding: 2px 5px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
  flex-shrink: 0;
}

.tab-label {
  flex: 1;
}

/* ── Content ─────────────────────────────────────────────────────────────── */

.settings-content {
  padding: 32px;
  overflow-y: auto;
}

.tab-pane {
  animation: fadeIn 0.18s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.tab-header {
  margin-bottom: 28px;
}

.tab-title {
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.tab-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* ── Settings grid ───────────────────────────────────────────────────────── */

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.settings-grid.single {
  grid-template-columns: 1fr;
  max-width: 540px;
}

.settings-group {}

.group-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin: 0 0 16px;
}

/* ── Form fields ─────────────────────────────────────────────────────────── */

.form-field {
  margin-bottom: 24px;
}

.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.field-value {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
  font-weight: 700;
}

.field-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin: 6px 0 0;
  line-height: 1.4;
}

.field-hint a {
  color: var(--accent);
}

.field-input, .field-select {
  width: 100%;
  padding: 9px 12px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}

.field-input:focus, .field-select:focus {
  border-color: var(--accent);
  background: var(--bg-card);
}

.field-input.narrow {
  width: 100px;
}

.field-range {
  width: 100%;
  accent-color: var(--accent);
  margin: 4px 0;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ── API key cards ───────────────────────────────────────────────────────── */

.api-key-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.api-key-card {
  padding: 18px;
  background: var(--bg-graph);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: border-color 0.15s;
}

.api-key-card:hover {
  border-color: var(--border-hover);
}

.key-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.key-card-header.minimal {
  margin-bottom: 8px;
}

.provider-badge {
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.current-key {
  flex: 1;
}

.key-masked {
  font-size: 13px;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
}

.key-empty {
  font-size: 12px;
  color: var(--text-muted);
}

.key-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.key-input-wrapper {
  flex: 1;
  position: relative;
}

.key-input {
  width: 100%;
  padding: 8px 36px 8px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-mono);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}

.key-input:focus {
  border-color: var(--accent);
}

.btn-eye {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
  cursor: pointer;
  padding: 2px 4px;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.btn-eye:hover { opacity: 1; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */

.btn-primary {
  padding: 8px 16px;
  background: var(--text-primary);
  color: #fff;
  border: 1px solid var(--text-primary);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  flex-shrink: 0;
}

.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  padding: 8px 14px;
  background: none;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Test result ─────────────────────────────────────────────────────────── */

.test-result {
  margin-top: 8px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
}

.test-ok    { background: rgba(16,185,129,0.1); color: var(--accent-success); }
.test-error { background: rgba(220,38,38,0.1);  color: var(--accent-danger); }
.test-testing { background: rgba(255,152,0,0.1); color: var(--accent-warn); }
.test-loading { background: rgba(255,152,0,0.1); color: var(--accent-warn); }

/* ── Preset selector ─────────────────────────────────────────────────────── */

.preset-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preset-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--bg-graph);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.15s;
}

.preset-option:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.preset-option.selected {
  border-color: var(--accent);
  background: var(--accent-subtle);
  font-weight: 600;
  color: var(--accent);
}

.preset-radio {
  display: none;
}

/* ── Segmented control ───────────────────────────────────────────────────── */

.segmented-control {
  display: flex;
  gap: 4px;
  background: var(--bg-graph);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 4px;
  width: fit-content;
}

.seg-btn {
  padding: 6px 16px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.seg-btn:hover:not(.active) {
  background: rgba(0,0,0,0.05);
  color: var(--text-primary);
}

.seg-btn.active {
  background: var(--bg-card);
  color: var(--accent);
  font-weight: 700;
  box-shadow: var(--shadow-card);
}

/* ── Toggle switch ───────────────────────────────────────────────────────── */

.toggle-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.toggle-info {
  flex: 1;
}

.toggle-info .field-label {
  justify-content: flex-start;
}

.toggle-switch {
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-track {
  display: flex;
  align-items: center;
  width: 44px;
  height: 24px;
  background: var(--border);
  border-radius: var(--radius-sm);
  padding: 2px;
  transition: background 0.2s ease;
}

.toggle-switch.active .toggle-track {
  background: var(--accent);
}

.toggle-thumb {
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: var(--radius-xs);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s ease;
}

.toggle-switch.active .toggle-thumb {
  transform: translateX(20px);
}

/* ── Font mono util ──────────────────────────────────────────────────────── */
.font-mono { font-family: var(--font-mono); }

/* ── Responsive ──────────────────────────────────────────────────────────── */

@media (max-width: 768px) {
  .settings-page {
    padding: 24px 16px;
  }

  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-sidebar {
    flex-direction: row;
    flex-wrap: nowrap;
    overflow-x: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
    padding: 8px;
    gap: 4px;
  }

  .sidebar-tab {
    flex-shrink: 0;
    border-left: none;
    border-bottom: 3px solid transparent;
    padding: 8px 12px;
    border-radius: var(--radius-sm);
  }

  .sidebar-tab.active {
    border-left-color: transparent;
    border-bottom-color: var(--accent);
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .settings-content {
    padding: 20px;
  }
}

/* ── Model setup UI ────────────────────────────────────────────────── */
.simple-model-panel {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  padding: 18px;
  margin-bottom: 18px;
}

.simple-model-copy {
  max-width: 720px;
  margin-bottom: 16px;
}

.model-eyebrow {
  display: block;
  margin-bottom: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0;
  color: var(--text-muted);
  text-transform: uppercase;
}

.simple-model-title {
  margin: 0 0 6px;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
}

.simple-model-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.simple-model-fields {
  display: grid;
  grid-template-columns: minmax(180px, 0.75fr) minmax(260px, 1.5fr);
  gap: 12px;
  margin-bottom: 14px;
}

.simple-model-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.model-routing-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--border);
}

.routing-item {
  min-width: 0;
  padding: 10px 12px;
  background: var(--bg-input);
}

.routing-item span,
.routing-item strong {
  display: block;
  min-width: 0;
}

.routing-item span {
  margin-bottom: 4px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.routing-item strong {
  overflow-wrap: anywhere;
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
}

.quick-apply-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.qa-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-right: 4px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
}

.step-model-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.step-model-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  background: var(--bg-card);
  transition: border-color 0.15s;
}

.step-model-card:hover {
  border-color: var(--border-hover);
}

.step-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--text-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.step-card-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.step-model-fields {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 10px;
  margin-bottom: 12px;
}

.model-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.model-input-row .field-input {
  min-width: 0;
}

.step-card-actions {
  display: flex;
  gap: 8px;
}

.global-fallback-section {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0 16px 4px;
}

.global-fallback-toggle {
  padding: 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  list-style: none;
  user-select: none;
}

.global-fallback-toggle::-webkit-details-marker { display: none; }

.global-fallback-toggle::before {
  content: '▸ ';
  color: var(--text-muted);
}

details[open] .global-fallback-toggle::before {
  content: '▾ ';
}

@media (max-width: 768px) {
  .quick-apply-bar,
  .key-input-row,
  .model-input-row,
  .step-card-actions {
    flex-wrap: wrap;
  }

  .simple-model-fields,
  .model-routing-strip {
    grid-template-columns: 1fr;
  }

  .step-model-fields {
    grid-template-columns: 1fr;
  }

  .model-input-row .btn-secondary {
    width: 100%;
  }
}
</style>
