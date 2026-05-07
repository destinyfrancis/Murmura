<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const moduleKeys = [
  'overview',
  'workflow',
  'graph',
  'actors',
  'simulation',
  'probability',
  'uncertainty',
  'report',
  'interaction',
  'limits',
]

const activeKey = ref(moduleKeys[0])

const modules = computed(() => moduleKeys.map((key, index) => ({
  key,
  index: String(index + 1).padStart(2, '0'),
  code: t(`learn.modules.${key}.code`),
  title: t(`learn.modules.${key}.title`),
  summary: t(`learn.modules.${key}.summary`),
  outcome: t(`learn.modules.${key}.outcome`),
  steps: tm(`learn.modules.${key}.steps`),
  checks: tm(`learn.modules.${key}.checks`),
})))

const activeModule = computed(() =>
  modules.value.find(module => module.key === activeKey.value) || modules.value[0]
)

const workflow = computed(() => tm('learn.workflow'))
const glossary = computed(() => tm('learn.glossary'))

function setActive(key) {
  activeKey.value = key
}
</script>

<template>
  <div class="learn-page workbench-page">
    <section class="learn-hero workbench-panel">
      <div class="hero-copy">
        <span class="workbench-label">{{ t('learn.eyebrow') }}</span>
        <h1>{{ t('learn.title') }}</h1>
        <p>{{ t('learn.subtitle') }}</p>
      </div>
      <div class="hero-metrics" :aria-label="t('learn.metricsLabel')">
        <div
          v-for="metric in tm('learn.metrics')"
          :key="metric.label"
          class="hero-metric"
        >
          <span class="metric-value">{{ metric.value }}</span>
          <span class="metric-label">{{ metric.label }}</span>
        </div>
      </div>
    </section>

    <section class="operator-strip" aria-label="Murmura workflow">
      <div
        v-for="(step, index) in workflow"
        :key="step.label"
        class="operator-step workbench-panel"
      >
        <span class="operator-index">{{ String(index + 1).padStart(2, '0') }}</span>
        <strong>{{ step.label }}</strong>
        <span>{{ step.desc }}</span>
      </div>
    </section>

    <section class="learn-layout">
      <aside class="lesson-index workbench-panel" :aria-label="t('learn.indexLabel')">
        <button
          v-for="module in modules"
          :key="module.key"
          class="index-row"
          :class="{ active: activeKey === module.key }"
          @click="setActive(module.key)"
        >
          <span class="index-num">{{ module.index }}</span>
          <span class="index-copy">
            <strong>{{ module.title }}</strong>
            <small>{{ module.code }}</small>
          </span>
        </button>
      </aside>

      <article class="lesson-panel workbench-panel">
        <header class="lesson-header">
          <span class="lesson-code">{{ activeModule.code }}</span>
          <h2>{{ activeModule.title }}</h2>
          <p>{{ activeModule.summary }}</p>
        </header>

        <div class="lesson-grid">
          <section class="lesson-block">
            <span class="block-label">{{ t('learn.blocks.whatHappens') }}</span>
            <ol class="step-list">
              <li v-for="step in activeModule.steps" :key="step">
                {{ step }}
              </li>
            </ol>
          </section>

          <section class="lesson-block">
            <span class="block-label">{{ t('learn.blocks.howToRead') }}</span>
            <ul class="check-list">
              <li v-for="check in activeModule.checks" :key="check">
                {{ check }}
              </li>
            </ul>
          </section>
        </div>

        <footer class="lesson-outcome">
          <span class="workbench-label">{{ t('learn.blocks.operatorRule') }}</span>
          <p>{{ activeModule.outcome }}</p>
        </footer>
      </article>
    </section>

    <section class="glossary-band workbench-panel">
      <div class="glossary-heading">
        <span class="workbench-label">{{ t('learn.glossaryLabel') }}</span>
        <h2>{{ t('learn.glossaryTitle') }}</h2>
      </div>
      <div class="glossary-grid">
        <div
          v-for="item in glossary"
          :key="item.term"
          class="glossary-item"
        >
          <strong>{{ item.term }}</strong>
          <span>{{ item.desc }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.learn-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.learn-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.44fr);
  gap: 24px;
  padding: 26px;
  background:
    linear-gradient(90deg, rgba(0,0,0,0.035) 1px, transparent 1px),
    linear-gradient(rgba(0,0,0,0.035) 1px, transparent 1px),
    var(--bg-card);
  background-size: 28px 28px;
}

.hero-copy h1 {
  margin: 12px 0 10px;
  max-width: 760px;
  font-size: clamp(34px, 5vw, 68px);
  line-height: 0.98;
  letter-spacing: 0;
  text-transform: uppercase;
}

.hero-copy p {
  max-width: 760px;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  align-content: end;
}

.hero-metric {
  min-height: 86px;
  padding: 13px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.92);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-value,
.metric-label,
.operator-index,
.lesson-code,
.block-label,
.index-num,
.index-copy small {
  font-family: var(--font-mono);
  font-weight: 800;
}

.metric-value {
  color: var(--accent);
  font-size: 24px;
}

.metric-label {
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.operator-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.operator-step {
  min-height: 116px;
  padding: 14px;
  display: grid;
  gap: 8px;
  align-content: start;
}

.operator-index {
  color: var(--accent);
  font-size: 11px;
}

.operator-step strong {
  font-size: 13px;
  color: var(--text-primary);
}

.operator-step span:last-child {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.learn-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.lesson-index {
  position: sticky;
  top: 72px;
  padding: 8px;
}

.index-row {
  width: 100%;
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 10px;
  padding: 11px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  text-align: left;
}

.index-row:hover {
  border-color: var(--border);
  background: var(--bg-input);
}

.index-row.active {
  border-color: var(--text-primary);
  background: var(--text-primary);
  color: var(--text-inverse);
}

.index-num {
  color: var(--accent);
  font-size: 11px;
}

.index-copy {
  display: grid;
  gap: 4px;
}

.index-copy strong {
  font-size: 13px;
  line-height: 1.35;
}

.index-copy small {
  color: var(--text-muted);
  font-size: 9px;
  letter-spacing: 0.1em;
}

.index-row.active .index-copy small {
  color: #BDBDBD;
}

.lesson-panel {
  padding: 26px;
}

.lesson-header {
  padding-bottom: 22px;
  border-bottom: 1px solid var(--border);
}

.lesson-code {
  display: inline-flex;
  padding: 4px 7px;
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 10px;
  letter-spacing: 0.08em;
}

.lesson-header h2 {
  margin: 12px 0 8px;
  font-size: clamp(28px, 4vw, 48px);
  line-height: 1;
  letter-spacing: 0;
}

.lesson-header p {
  max-width: 820px;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.75;
}

.lesson-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 22px;
}

.lesson-block {
  min-height: 280px;
  padding: 18px;
  border: 1px solid var(--border);
  background: var(--bg-input);
}

.block-label {
  display: block;
  margin-bottom: 14px;
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.step-list,
.check-list {
  display: grid;
  gap: 12px;
  padding-left: 18px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.step-list li::marker {
  color: var(--accent);
  font-family: var(--font-mono);
  font-weight: 800;
}

.check-list {
  list-style: square;
}

.check-list li::marker {
  color: var(--text-primary);
}

.lesson-outcome {
  margin-top: 18px;
  padding: 18px;
  border: 1px solid var(--text-primary);
  background: var(--text-primary);
  color: var(--text-inverse);
}

.lesson-outcome p {
  margin-top: 8px;
  max-width: 880px;
  color: #E8E8E8;
  font-size: 15px;
  line-height: 1.65;
}

.glossary-band {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 22px;
  padding: 24px;
}

.glossary-heading h2 {
  margin-top: 8px;
  font-size: 28px;
  line-height: 1.05;
}

.glossary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.glossary-item {
  min-height: 92px;
  padding: 14px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  display: grid;
  gap: 8px;
}

.glossary-item strong {
  font-size: 13px;
}

.glossary-item span {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 980px) {
  .learn-hero,
  .learn-layout,
  .glossary-band {
    grid-template-columns: 1fr;
  }

  .operator-strip,
  .lesson-grid,
  .glossary-grid {
    grid-template-columns: 1fr;
  }

  .lesson-index {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .learn-page {
    padding-left: 16px;
    padding-right: 16px;
  }

  .learn-hero,
  .lesson-panel,
  .glossary-band {
    padding: 18px;
  }

  .hero-metrics,
  .lesson-index {
    grid-template-columns: 1fr;
  }

  .lesson-block {
    min-height: auto;
  }
}
</style>
