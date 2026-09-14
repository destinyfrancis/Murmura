<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

const steps = computed(() => [
  { num: '01', label: t('landing.workflow.steps.graph.label'), title: t('landing.workflow.steps.graph.title'), desc: t('landing.workflow.steps.graph.desc') },
  { num: '02', label: t('landing.workflow.steps.env.label'), title: t('landing.workflow.steps.env.title'), desc: t('landing.workflow.steps.env.desc') },
  { num: '03', label: t('landing.workflow.steps.sim.label'), title: t('landing.workflow.steps.sim.title'), desc: t('landing.workflow.steps.sim.desc') },
  { num: '04', label: t('landing.workflow.steps.report.label'), title: t('landing.workflow.steps.report.title'), desc: t('landing.workflow.steps.report.desc') },
  { num: '05', label: t('landing.workflow.steps.interact.label'), title: t('landing.workflow.steps.interact.title'), desc: t('landing.workflow.steps.interact.desc') },
])

const features = computed(() => [
  { icon: '◈', title: t('landing.features.list.universal.title'), desc: t('landing.features.list.universal.desc') },
  { icon: '⬡', title: t('landing.features.list.kg.title'), desc: t('landing.features.list.kg.desc') },
  { icon: '⊕', title: t('landing.features.list.emergence.title'), desc: t('landing.features.list.emergence.desc') },
  { icon: '◱', title: t('landing.features.list.monteCarlo.title'), desc: t('landing.features.list.monteCarlo.desc') },
  { icon: '⟳', title: t('landing.features.list.macro.title'), desc: t('landing.features.list.macro.desc') },
  { icon: '⊞', title: t('landing.features.list.scenarios.title'), desc: t('landing.features.list.scenarios.desc') },
])

const useCases = computed(() => [
  { tag: t('landing.useCases.list.geopolitics.tag'), desc: t('landing.useCases.list.geopolitics.desc') },
  { tag: t('landing.useCases.list.finance.tag'), desc: t('landing.useCases.list.finance.desc') },
  { tag: t('landing.useCases.list.society.tag'), desc: t('landing.useCases.list.society.desc') },
  { tag: t('landing.useCases.list.property.tag'), desc: t('landing.useCases.list.property.desc') },
  { tag: t('landing.useCases.list.product.tag'), desc: t('landing.useCases.list.product.desc') },
  { tag: t('landing.useCases.list.reputation.tag'), desc: t('landing.useCases.list.reputation.desc') },
  { tag: t('landing.useCases.list.relationships.tag'), desc: t('landing.useCases.list.relationships.desc') },
  { tag: t('landing.useCases.list.fiction.tag'), desc: t('landing.useCases.list.fiction.desc') },
])

const lenses = computed(() => [
  { mark: '01', title: t('landing.lenses.list.interactions.title'), desc: t('landing.lenses.list.interactions.desc') },
  { mark: '02', title: t('landing.lenses.list.feedback.title'), desc: t('landing.lenses.list.feedback.desc') },
  { mark: '03', title: t('landing.lenses.list.emergence.title'), desc: t('landing.lenses.list.emergence.desc') },
])

const audiences = computed(() => [
  { label: t('landing.audiences.policy.label'), title: t('landing.audiences.policy.title'), desc: t('landing.audiences.policy.desc') },
  { label: t('landing.audiences.business.label'), title: t('landing.audiences.business.title'), desc: t('landing.audiences.business.desc') },
  { label: t('landing.audiences.individual.label'), title: t('landing.audiences.individual.title'), desc: t('landing.audiences.individual.desc') },
])
</script>

<template>
  <div class="landing">
    <!-- Background grid -->
    <div class="bg-grid" />

    <!-- Nav -->
    <nav class="nav">
      <div class="nav-inner">
        <div class="brand-lockup"><a href="#top" class="nav-logo">Murmura</a><span class="nav-zh-name">{{ t('landing.brandZh') }}</span></div>
        <div class="nav-links">
          <a href="#how-it-works" class="nav-link">{{ t('landing.nav.howItWorks') }}</a>
          <a href="#features" class="nav-link">{{ t('landing.nav.features') }}</a>
          <a href="https://github.com/destinyfrancis/Murmura" class="nav-link nav-github" target="_blank" rel="noreferrer">{{ t('landing.nav.github') }} ↗</a>
          <button class="nav-cta" @click="router.push('/app')">{{ t('landing.nav.launch') }}</button>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section id="top" class="hero">
      <div class="hero-eyebrow">{{ t('landing.hero.eyebrow') }}</div>
      <h1 class="hero-title">
        {{ t('landing.hero.title') }}<br/>
        <span class="hero-title-accent">{{ t('landing.hero.titleAccent') }}</span><br/>
        <span class="hero-title-zh">{{ t('landing.hero.titleZh') }}</span>
      </h1>
      <p class="hero-sub">{{ t('landing.hero.sub') }}</p>
      <p class="hero-note">{{ t('landing.hero.note') }}</p>
      <div class="hero-actions">
        <button class="btn-primary" @click="router.push('/app')">{{ t('landing.hero.cta') }}</button>
        <button class="btn-ghost" @click="router.push('/app/workspace')">{{ t('landing.hero.workspace') }}</button>
      </div>
      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-n">50–50,000</span>
          <span class="stat-l">{{ t('landing.hero.stats.agents') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">11</span>
          <span class="stat-l">{{ t('landing.hero.stats.macro') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">500</span>
          <span class="stat-l">{{ t('landing.hero.stats.monteCarlo') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">18</span>
          <span class="stat-l">{{ t('landing.hero.stats.xai') }}</span>
        </div>
      </div>
      <!-- A single seed splitting into many possible futures. -->
      <div class="hero-visual" aria-hidden="true">
        <svg viewBox="0 0 900 260" class="hero-svg" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="futureLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#ff5a1f" stop-opacity=".95"/><stop offset="1" stop-color="#f7b955" stop-opacity=".2"/>
            </linearGradient>
            <filter id="softGlow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>
          <path class="future-path path-main" d="M20 130 C190 130 220 130 330 130 S440 130 520 130 C650 130 720 50 880 28" stroke="url(#futureLine)" stroke-width="3"/>
          <path class="future-path" d="M20 130 C190 130 220 130 330 130 S440 130 520 130 C640 130 700 88 880 78" stroke="url(#futureLine)" stroke-width="2"/>
          <path class="future-path" d="M20 130 C190 130 220 130 330 130 S440 130 520 130 C630 130 700 125 880 130" stroke="url(#futureLine)" stroke-width="2"/>
          <path class="future-path" d="M20 130 C190 130 220 130 330 130 S440 130 520 130 C640 130 700 170 880 182" stroke="url(#futureLine)" stroke-width="2"/>
          <path class="future-path" d="M20 130 C190 130 220 130 330 130 S440 130 520 130 C650 130 720 220 880 234" stroke="url(#futureLine)" stroke-width="3"/>
          <g class="field-points" filter="url(#softGlow)">
            <circle cx="20" cy="130" r="7" fill="#ff5a1f"/><circle cx="330" cy="130" r="5" fill="#f7b955"/><circle cx="520" cy="130" r="6" fill="#f7b955"/>
            <circle cx="680" cy="75" r="3" fill="#f7b955"/><circle cx="745" cy="150" r="3" fill="#ff5a1f"/><circle cx="790" cy="210" r="3" fill="#f7b955"/>
          </g>
          <text x="20" y="105" fill="#ffb089" font-size="12" font-family="monospace" letter-spacing="2">{{ t('landing.hero.seed') }}</text>
          <text x="760" y="18" fill="#c9a86a" font-size="11" font-family="monospace" letter-spacing="2">{{ t('landing.hero.possibleFutures') }}</text>
        </svg>
      </div>
    </section>

    <!-- The promise, in plain language. -->
    <section class="promise-section">
      <div class="promise-copy">
        <div class="section-label section-label-left">{{ t('landing.promise.label') }}</div>
        <h2 class="section-title section-title-left">{{ t('landing.promise.title') }}</h2>
        <p>{{ t('landing.promise.desc') }}</p>
      </div>
      <div class="lens-grid">
        <article v-for="lens in lenses" :key="lens.mark" class="lens-card">
          <span class="lens-mark">{{ lens.mark }}</span><h3>{{ lens.title }}</h3><p>{{ lens.desc }}</p>
        </article>
      </div>
    </section>

    <!-- 5-Step Workflow -->
    <section id="how-it-works" class="workflow">
      <div class="section-label">{{ t('landing.workflow.label') }}</div>
      <h2 class="section-title">{{ t('landing.workflow.title') }}</h2>
      <div class="steps-row">
        <template v-for="(step, i) in steps" :key="step.num">
          <div class="step-card">
            <div class="step-num">{{ step.num }}</div>
            <div class="step-label-tag">{{ step.label }}</div>
            <h3 class="step-name">{{ step.title }}</h3>
            <p class="step-desc">{{ step.desc }}</p>
          </div>
          <div v-if="i < steps.length - 1" class="step-arrow">→</div>
        </template>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="features">
      <div class="section-label">{{ t('landing.features.label') }}</div>
      <h2 class="section-title">{{ t('landing.features.title') }}</h2>
      <div class="features-grid">
        <div v-for="f in features" :key="f.title" class="feature-card">
          <span class="feature-icon">{{ f.icon }}</span>
          <h3 class="feature-title">{{ f.title }}</h3>
          <p class="feature-desc">{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Audience stories make the product concrete. -->
    <section class="audience-section">
      <div class="section-label">{{ t('landing.audiences.label') }}</div>
      <h2 class="section-title">{{ t('landing.audiences.title') }}</h2>
      <div class="audience-grid">
        <article v-for="audience in audiences" :key="audience.label" class="audience-card">
          <span class="audience-label">{{ audience.label }}</span>
          <h3>{{ audience.title }}</h3>
          <p>{{ audience.desc }}</p>
        </article>
      </div>
    </section>

    <!-- Example Use Cases -->
    <section class="use-cases">
      <div class="section-label">{{ t('landing.useCases.label') }}</div>
      <h2 class="section-title">{{ t('landing.useCases.title') }}</h2>
      <div class="use-case-row">
        <div v-for="useCase in useCases" :key="useCase.tag" class="use-case-item">
          <span class="uc-tag">{{ useCase.tag }}</span>
          <p>{{ useCase.desc }}</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="cta-box">
        <div class="cta-label">{{ t('landing.cta.label') }}</div>
        <h2 class="cta-title">{{ t('landing.cta.title') }}</h2>
        <p class="cta-sub">{{ t('landing.cta.sub') }}</p>
        <button class="btn-primary btn-large" @click="router.push('/app')">
          {{ t('landing.cta.btn') }}
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <span class="footer-brand">Murmura</span>
      <span class="footer-desc">{{ t('landing.footer.desc') }}</span>
      <a class="footer-github" href="https://github.com/destinyfrancis/Murmura" target="_blank" rel="noreferrer">{{ t('landing.footer.github') }} ↗</a>
      <span class="footer-copy">{{ t('landing.footer.copy') }}</span>
    </footer>
  </div>
</template>

<style scoped>
/* ─── Base ─────────────────────────────────────────────────────────────── */
.landing {
  background: #080808;
  color: #F5F5F5;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
}

.bg-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 90, 31, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 90, 31, 0.045) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ─── Nav ───────────────────────────────────────────────────────────────── */
.nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(5, 5, 5, 0.92);
  backdrop-filter: none;
  border-bottom: 1px solid #2A2A2A;
}
.nav-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.brand-lockup { display: flex; align-items: baseline; gap: 8px; }
.nav-logo {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 4px;
  color: var(--accent);
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  text-decoration: none;
}
.nav-zh-name {
  color: #b4b4b4;
  font-family: 'Noto Serif TC', 'Songti TC', serif;
  font-size: 13px;
  letter-spacing: 1px;
  font-weight: 500;
}
.nav-links { display: flex; align-items: center; gap: 24px; }
.nav-link {
  font-size: 13px;
  color: #9A9A9A;
  text-decoration: none;
  transition: color 0.2s;
}
.nav-link:hover { color: #F5F5F5; }
.nav-github { color: #d7a867; }
.nav-cta {
  padding: 8px 18px;
  background: rgba(255, 90, 31, 0.12);
  border: 1px solid rgba(255, 90, 31, 0.44);
  border-radius: 4px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-cta:hover {
  background: var(--accent);
  color: #FFFFFF;
}

/* ─── Hero ──────────────────────────────────────────────────────────────── */
.hero {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 100px 24px 60px;
  text-align: center;
}
.hero-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 24px;
  opacity: 0.8;
}
.hero-title {
  font-size: clamp(36px, 6vw, 64px);
  font-weight: 800;
  line-height: 1.15;
  color: #F5F5F5;
  margin-bottom: 24px;
  letter-spacing: -1px;
}
.hero-title-accent {
  color: var(--accent);
}
.hero-title-zh {
  color: #e9e4db;
  font-family: 'Noto Serif TC', 'Songti TC', serif;
  font-size: .48em;
  font-weight: 500;
  letter-spacing: .08em;
}
.hero-sub {
  font-size: 17px;
  color: #A3A3A3;
  line-height: 1.8;
  margin-bottom: 36px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
.hero-note {
  max-width: 620px;
  margin: -18px auto 30px;
  color: #d3ac72;
  font-family: 'Noto Serif TC', 'Songti TC', serif;
  font-size: 14px;
  line-height: 1.8;
}
.hero-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 48px;
}
.btn-primary {
  padding: 12px 28px;
  background: var(--accent);
  color: #FFFFFF;
  border: 1px solid var(--accent);
  border-radius: 4px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}
.btn-primary:hover {
  transform: translateY(-1px);
  background: #FFFFFF;
  color: #050505;
  border-color: #FFFFFF;
}
.btn-primary.btn-large {
  padding: 16px 40px;
  font-size: 16px;
}
.btn-ghost {
  padding: 12px 28px;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  color: #BDBDBD;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-ghost:hover {
  border-color: rgba(255,255,255,0.3);
  color: #F5F5F5;
}
.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0;
  margin-bottom: 48px;
  flex-wrap: wrap;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32px;
}
.stat-n {
  font-size: 26px;
  font-weight: 800;
  color: #F5F5F5;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  margin-bottom: 4px;
}
.stat-l {
  font-size: 11px;
  color: #777;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255,255,255,0.08);
}
.hero-visual {
  display: flex;
  justify-content: center;
  margin: 12px -8vw 0;
  overflow: hidden;
}
.hero-svg {
  width: 100%;
  max-width: 900px;
  height: 260px;
  opacity: 0.92;
}
.future-path {
  stroke-dasharray: 11 16;
  stroke-linecap: round;
  animation: drift 18s linear infinite;
}
.future-path:nth-of-type(2) { animation-duration: 21s; animation-delay: -5s; }
.future-path:nth-of-type(3) { animation-duration: 24s; animation-delay: -8s; }
.future-path:nth-of-type(4) { animation-duration: 20s; animation-delay: -11s; }
.future-path:nth-of-type(5) { animation-duration: 17s; animation-delay: -3s; }
.field-points circle { animation: point-breathe 4s ease-in-out infinite; }
.field-points circle:nth-child(2) { animation-delay: -.8s; }
.field-points circle:nth-child(3) { animation-delay: -1.7s; }
@keyframes drift { to { stroke-dashoffset: -600; } }
@keyframes point-breathe { 0%,100% { opacity: .55; transform: scale(.85); } 50% { opacity: 1; transform: scale(1.2); } }

/* ─── Promise / lenses ──────────────────────────────────────────────────── */
.promise-section, .audience-section {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 84px 24px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.promise-section {
  display: grid;
  grid-template-columns: .85fr 1.15fr;
  gap: 72px;
  align-items: start;
}
.section-label-left, .section-title-left { text-align: left; }
.promise-copy p { color: #a3a3a3; font-size: 16px; line-height: 1.9; max-width: 440px; }
.lens-grid { display: grid; gap: 1px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.1); }
.lens-card { background: #101010; padding: 24px 26px 26px 62px; position: relative; min-height: 108px; }
.lens-card h3 { color: #f5f5f5; font-size: 18px; margin: 0 0 8px; }
.lens-card p { color: #8e8e8e; font-size: 13px; line-height: 1.65; margin: 0; }
.lens-mark { position: absolute; left: 24px; top: 24px; color: var(--accent); font: 700 11px 'JetBrains Mono', monospace; letter-spacing: 1px; }

/* ─── Audience stories ─────────────────────────────────────────────────── */
.audience-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.audience-card { border: 1px solid rgba(255,255,255,.1); padding: 28px 26px 30px; min-height: 205px; background: linear-gradient(145deg, rgba(255,255,255,.035), rgba(255,255,255,.01)); }
.audience-label { color: #d3ac72; font: 700 10px 'JetBrains Mono', monospace; letter-spacing: 2px; text-transform: uppercase; }
.audience-card h3 { font-size: 20px; color: #f5f5f5; margin: 20px 0 12px; }
.audience-card p { color: #929292; font-size: 13px; line-height: 1.7; margin: 0; }
.pulse-node {
  animation: pulse-glow 2.5s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%, 100% { opacity: 0.9; filter: drop-shadow(0 0 5px rgba(255,90,31,0.55)); }
  50% { opacity: 0.6; filter: drop-shadow(0 0 11px rgba(255,90,31,0.8)); }
}

/* ─── Section Label ─────────────────────────────────────────────────────── */
.section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 4px;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 12px;
  text-align: center;
}
.section-title {
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 700;
  text-align: center;
  color: #F5F5F5;
  margin-bottom: 48px;
  letter-spacing: -0.5px;
}

/* ─── Workflow ──────────────────────────────────────────────────────────── */
.workflow {
  position: relative;
  z-index: 1;
  padding: 80px 24px;
  max-width: 1200px;
  margin: 0 auto;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.steps-row {
  display: flex;
  align-items: flex-start;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 8px;
}
.step-card {
  flex: 1;
  min-width: 160px;
  padding: 24px 20px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  transition: border-color 0.2s, background 0.2s;
}
.step-card:hover {
  border-color: rgba(255, 90, 31, 0.42);
  background: rgba(255, 90, 31, 0.05);
}
.step-num {
  font-size: 28px;
  font-weight: 800;
  color: rgba(255,255,255,0.07);
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  margin-bottom: 8px;
}
.step-label-tag {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(255, 90, 31, 0.12);
  border: 1px solid rgba(255, 90, 31, 0.32);
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 10px;
}
.step-name {
  font-size: 14px;
  font-weight: 600;
  color: #F5F5F5;
  margin-bottom: 6px;
}
.step-desc {
  font-size: 12px;
  color: #8A8A8A;
  line-height: 1.6;
}
.step-arrow {
  padding: 0 8px;
  color: rgba(255,255,255,0.15);
  font-size: 18px;
  align-self: center;
  flex-shrink: 0;
  margin-top: -16px;
}

/* ─── Features ──────────────────────────────────────────────────────────── */
.features {
  position: relative;
  z-index: 1;
  padding: 80px 24px;
  max-width: 1200px;
  margin: 0 auto;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.feature-card {
  padding: 28px 24px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  transition: all 0.2s;
}
.feature-card:hover {
  border-color: rgba(255, 90, 31, 0.35);
  background: rgba(255, 90, 31, 0.04);
}
.feature-icon {
  display: block;
  font-size: 20px;
  color: var(--accent);
  margin-bottom: 14px;
}
.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #F5F5F5;
  margin-bottom: 8px;
}
.feature-desc {
  font-size: 13px;
  color: #8A8A8A;
  line-height: 1.65;
}

/* ─── Use Cases ─────────────────────────────────────────────────────────── */
.use-cases {
  position: relative;
  z-index: 1;
  padding: 80px 24px;
  max-width: 1200px;
  margin: 0 auto;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.use-case-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.use-case-item {
  padding: 24px 20px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
}
.uc-tag {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(255, 90, 31, 0.12);
  border: 1px solid rgba(255, 90, 31, 0.32);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.use-case-item p {
  font-size: 13px;
  color: #8A8A8A;
  line-height: 1.6;
}

/* ─── CTA ───────────────────────────────────────────────────────────────── */
.cta-section {
  position: relative;
  z-index: 1;
  padding: 80px 24px;
  max-width: 1200px;
  margin: 0 auto;
}
.cta-box {
  text-align: center;
  padding: 72px 40px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255, 90, 31, 0.28);
  border-radius: 8px;
}
.cta-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 4px;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 16px;
}
.cta-title {
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 700;
  color: #F5F5F5;
  margin-bottom: 12px;
}
.cta-sub {
  font-size: 15px;
  color: #8A8A8A;
  margin-bottom: 32px;
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */
.footer {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  border-top: 1px solid rgba(255,255,255,0.05);
  flex-wrap: wrap;
  gap: 8px;
}
.footer-brand {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 3px;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
}
.footer-desc, .footer-copy {
  font-size: 11px;
  color: #777;
}
.footer-github { color: #d3ac72; font-size: 11px; text-decoration: none; }
.footer-github:hover { color: #fff; }

/* ─── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 900px) {
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .use-case-row { grid-template-columns: repeat(2, 1fr); }
  .promise-section { grid-template-columns: 1fr; gap: 40px; }
  .audience-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .features-grid { grid-template-columns: 1fr; }
  .use-case-row { grid-template-columns: 1fr; }
  .steps-row { flex-direction: column; }
  .step-arrow { display: none; }
  .hero-stats { gap: 24px; }
  .stat-divider { display: none; }
  .footer { flex-direction: column; text-align: center; }
  .nav-links { gap: 10px; }
  .nav-link:not(.nav-github) { display: none; }
  .nav-zh-name { display: none; }
  .hero { padding-top: 72px; }
  .hero-visual { margin-left: -24px; margin-right: -24px; }
  .hero-svg { height: 190px; }
}
</style>
