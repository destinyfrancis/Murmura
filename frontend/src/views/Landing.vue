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
  { tag: t('landing.useCases.list.fiction.tag'), desc: t('landing.useCases.list.fiction.desc') },
])
</script>

<template>
  <div class="landing">
    <!-- Background grid -->
    <div class="bg-grid" />

    <!-- Nav -->
    <nav class="nav">
      <div class="nav-inner">
        <span class="nav-logo">Murmura</span>
        <div class="nav-links">
          <a href="#how-it-works" class="nav-link">{{ t('landing.nav.howItWorks') }}</a>
          <a href="#features" class="nav-link">{{ t('landing.nav.features') }}</a>
          <button class="nav-cta" @click="router.push('/app')">{{ t('landing.nav.launch') }}</button>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-eyebrow">{{ t('landing.hero.eyebrow') }}</div>
      <h1 class="hero-title">
        {{ t('landing.hero.title') }}<br/>
        <span class="hero-title-accent">{{ t('landing.hero.titleAccent') }}</span>
      </h1>
      <p class="hero-sub">{{ t('landing.hero.sub') }}</p>
      <div class="hero-actions">
        <button class="btn-primary" @click="router.push('/app')">{{ t('landing.hero.cta') }}</button>
        <button class="btn-ghost" @click="router.push('/app/workspace')">{{ t('landing.hero.workspace') }}</button>
      </div>
      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-n">50–10,000</span>
          <span class="stat-l">{{ t('landing.hero.stats.agents') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">11</span>
          <span class="stat-l">{{ t('landing.hero.stats.macro') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">100+</span>
          <span class="stat-l">{{ t('landing.hero.stats.monteCarlo') }}</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-n">14</span>
          <span class="stat-l">{{ t('landing.hero.stats.xai') }}</span>
        </div>
      </div>
      <!-- Hero visual: animated graph -->
      <div class="hero-visual">
        <svg viewBox="0 0 480 200" class="hero-svg" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- connection lines -->
          <line x1="240" y1="40" x2="80" y2="120" stroke="#ff5a1f" stroke-width="1" stroke-dasharray="4 4" opacity="0.42"/>
          <line x1="240" y1="40" x2="400" y2="120" stroke="#f59e0b" stroke-width="1" stroke-dasharray="4 4" opacity="0.36"/>
          <line x1="80" y1="120" x2="160" y2="180" stroke="#047857" stroke-width="1" stroke-dasharray="4 4" opacity="0.38"/>
          <line x1="400" y1="120" x2="320" y2="180" stroke="#ff5a1f" stroke-width="1" stroke-dasharray="4 4" opacity="0.42"/>
          <line x1="160" y1="180" x2="320" y2="180" stroke="#f59e0b" stroke-width="1" stroke-dasharray="4 4" opacity="0.3"/>
          <line x1="80" y1="120" x2="400" y2="120" stroke="#047857" stroke-width="1" stroke-dasharray="4 4" opacity="0.22"/>
          <!-- nodes -->
          <circle cx="240" cy="40" r="10" fill="#ff5a1f" opacity="0.9" class="pulse-node"/>
          <circle cx="80" cy="120" r="8" fill="#047857" opacity="0.8"/>
          <circle cx="400" cy="120" r="8" fill="#f59e0b" opacity="0.8"/>
          <circle cx="160" cy="180" r="7" fill="#ff5a1f" opacity="0.7"/>
          <circle cx="320" cy="180" r="7" fill="#047857" opacity="0.7"/>
          <circle cx="240" cy="120" r="5" fill="#f59e0b" opacity="0.5"/>
          <!-- labels -->
          <text x="240" y="24" text-anchor="middle" fill="#ff5a1f" font-size="9" font-family="monospace" opacity="0.78">SEED EVENT</text>
          <text x="60" y="116" text-anchor="middle" fill="#9aa8ba" font-size="8" font-family="monospace">ACTOR A</text>
          <text x="420" y="116" text-anchor="middle" fill="#9aa8ba" font-size="8" font-family="monospace">ACTOR B</text>
          <text x="150" y="196" text-anchor="middle" fill="#9aa8ba" font-size="8" font-family="monospace">POLICY</text>
          <text x="330" y="196" text-anchor="middle" fill="#9aa8ba" font-size="8" font-family="monospace">MARKET</text>
        </svg>
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
.nav-logo {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 4px;
  color: var(--accent);
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
}
.nav-links { display: flex; align-items: center; gap: 24px; }
.nav-link {
  font-size: 13px;
  color: #9A9A9A;
  text-decoration: none;
  transition: color 0.2s;
}
.nav-link:hover { color: #F5F5F5; }
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
.hero-sub {
  font-size: 17px;
  color: #A3A3A3;
  line-height: 1.8;
  margin-bottom: 36px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
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
}
.hero-svg {
  width: 100%;
  max-width: 480px;
  height: 200px;
  opacity: 0.7;
}
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

/* ─── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 900px) {
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .use-case-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .features-grid { grid-template-columns: 1fr; }
  .use-case-row { grid-template-columns: 1fr; }
  .steps-row { flex-direction: column; }
  .step-arrow { display: none; }
  .hero-stats { gap: 24px; }
  .stat-divider { display: none; }
  .footer { flex-direction: column; text-align: center; }
}
</style>
