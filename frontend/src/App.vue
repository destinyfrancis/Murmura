<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DemoModeBanner from '@/components/DemoModeBanner.vue'

const router = useRouter()
const { t } = useI18n()

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <DemoModeBanner />
    <header class="app-header">
      <div class="header-left" @click="goHome">
        <span class="logo">⬡</span>
        <span class="brand">Murmura</span>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link">{{ t('nav.home') }}</router-link>
        <router-link to="/app" class="nav-link">{{ t('nav.workspace') }}</router-link>
        <router-link to="/learn" class="nav-link">{{ t('nav.learn') }}</router-link>
        <router-link to="/landing" class="nav-link">{{ t('nav.about') }}</router-link>
        <router-link to="/settings" class="nav-link nav-icon" :title="t('nav.settings')" :aria-label="t('nav.settings')">⚙</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* === Murmura Workbench: monochrome control room + orange signal === */
  --bg-app:     #F7F7F5;
  --bg-graph:   #F1F1EF;
  --bg-card:    #FFFFFF;
  --bg-nav:     #050505;
  --bg-input:   #FAFAFA;
  --bg-inverse: #050505;

  --accent:        #FF5A1F;
  --accent-hover:  #E64500;
  --accent-subtle: rgba(255, 90, 31, 0.10);
  --accent-warn:   #B45309;
  --accent-danger: #B91C1C;
  --accent-success:#047857;
  --accent-yellow: #B45309;
  --accent-blue-note: var(--accent);

  --text-primary:   #050505;
  --text-secondary: #525252;
  --text-muted:     #8A8A8A;
  --text-quaternary:#A3A3A3;
  --text-inverse:   #FFFFFF;
  --border:         #DCDCDC;
  --border-hover:   #050505;

  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans HK', sans-serif;
  --font-body: 'Inter', 'Noto Sans HK', system-ui, sans-serif;
  --font-editorial: var(--font-sans);

  /* Legacy aliases */
  --bg-primary:      var(--bg-app);
  --bg-secondary:    var(--bg-app);
  --bg-surface:      var(--bg-card);
  --border-color:    var(--border);
  --border-emphasis: var(--border-hover);
  --accent-blue:     var(--accent);
  --accent-green:    var(--accent-success);
  --accent-orange:   var(--accent-warn);
  --accent-red:      var(--accent-danger);
  --accent-cyan:     var(--accent-hover);
  --accent-purple:   var(--accent-blue-note);
  --accent-pink:     var(--accent);
  --accent-blue-light: var(--accent-subtle);
  --accent-rgb: 255, 107, 53;

  /* Geometry */
  --font-size-base: 14px;
  --radius-xs: 2px;
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;
  --radius-xl: 8px;
  --radius-pill: 4px;
  --shadow-card:    0 1px 0 rgba(0,0,0,0.04);
  --shadow-hover:   0 8px 18px rgba(0,0,0,0.07);
  --shadow-elevated:0 18px 50px rgba(0,0,0,0.12);
  --shadow-md:      var(--shadow-hover);

  /* Motion */
  --transition: all 0.2s ease;
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0.0, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.23, 1, 0.32, 1);
  --duration-fast: 0.15s;
  --duration-standard: 0.2s;
  --duration-medium: 0.3s;
  --duration-layout: 0.35s;

  /* Legacy glow + glass tokens mapped to workbench surfaces */
  --shadow-glow-cyan: none;
  --glass-bg: #FFFFFF;
  --glass-blur: 0;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-app);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--accent);
  text-decoration: none;
}

button {
  cursor: pointer;
  font-family: inherit;
}

input,
select,
textarea {
  font-family: inherit;
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.font-mono { font-family: var(--font-mono); }

.text-accent-cyan {
  color: var(--accent-cyan);
}

.text-accent-blue {
  color: var(--accent);
}

@keyframes pulse-subtle {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--accent-rgb), 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(var(--accent-rgb), 0); }
}

.status-pulse { animation: pulse-subtle 2s infinite; }

/* Skeleton loading shimmer */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(90deg, #F0F0F0 25%, #E0E0E0 50%, #F0F0F0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

.skeleton-text {
  height: 14px;
  margin-bottom: 8px;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  margin-bottom: 12px;
}

.skeleton-circle {
  border-radius: 50%;
}

.skeleton-card {
  height: 120px;
  border-radius: var(--radius-md);
}

/* ── Animation Polish (Phase 5) ────────────────────────────────── */

/* Card hover lift */
.card-hover-lift {
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

/* Table row hover */
table tbody tr {
  transition: background 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}
table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

/* Focus glow ring */
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg-card), 0 0 0 4px rgba(255, 107, 53, 0.3);
}

/* Smooth transitions for interactive elements */
a, button, input, select, textarea {
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
              background 0.2s cubic-bezier(0.4, 0, 0.2, 1),
              border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.3);
}

/* ── Shared Workbench primitives ───────────────────────────────────── */
.workbench-page {
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 24px 72px;
}

.workbench-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.workbench-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.workbench-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  padding: 9px 16px;
  border: 1px solid var(--text-primary);
  border-radius: var(--radius-sm);
  background: var(--text-primary);
  color: var(--text-inverse);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.workbench-button.secondary {
  background: var(--bg-card);
  color: var(--text-primary);
}

.workbench-button:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--accent);
  color: #FFFFFF;
}

.workbench-button:disabled {
  border-color: var(--border);
  background: #E9E9E6;
  color: var(--text-muted);
}

.workbench-input,
.workbench-textarea,
.workbench-select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-primary);
}

.workbench-input:focus,
.workbench-textarea:focus,
.workbench-select:focus {
  border-color: var(--text-primary);
  background: var(--bg-card);
}
</style>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 56px;
  background: var(--bg-nav);
  border-bottom: 1px solid #222;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.logo {
  font-size: 18px;
  color: var(--accent);
}

.brand {
  font-size: 18px;
  font-weight: 800;
  font-family: var(--font-mono);
  letter-spacing: 0;
  text-transform: uppercase;
  color: var(--text-inverse);
}

.header-nav {
  display: flex;
  gap: 16px;
}

.nav-link {
  color: #BDBDBD;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
  padding: 8px 10px;
  border-radius: var(--radius-xs);
  text-transform: uppercase;
}

.nav-link:hover {
  opacity: 1;
  color: var(--text-inverse);
  background: rgba(255,255,255,0.08);
}

.nav-link.router-link-active {
  color: var(--text-inverse);
  background: rgba(255, 90, 31, 0.2);
}

.app-main {
  flex: 1;
}

.nav-icon {
  font-size: 18px;
  padding: 6px 8px;
  line-height: 1;
  color: #BDBDBD;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
}

.nav-icon:hover {
  color: var(--text-inverse);
}

.nav-icon.router-link-active {
  color: var(--text-inverse);
  background: var(--accent-subtle);
}

@media (max-width: 760px) {
  .app-header {
    padding: 0 16px;
    height: auto;
    min-height: 56px;
    gap: 12px;
    flex-wrap: wrap;
  }

  .header-nav {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 8px;
  }
}
</style>
