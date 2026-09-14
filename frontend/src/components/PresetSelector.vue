<script setup>
const props = defineProps({ modelValue: { type: Object, default: () => ({ name: 'research', agents: 16, rounds: 5 }) } })
const emit = defineEmits(['update:modelValue'])
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const customAgents = ref(props.modelValue.agents || 16)
const customRounds = ref(props.modelValue.rounds || 5)
const advanced = [
  { name: 'fast', agents: 100, rounds: 15 },
  { name: 'standard', agents: 300, rounds: 20 },
  { name: 'deep', agents: 500, rounds: 30 },
  { name: 'large', agents: 1000, rounds: 25 },
  { name: 'massive', agents: 3000, rounds: 20 },
]
function choose(preset) { emit('update:modelValue', preset) }
function applyCustom() {
  choose({ name: 'custom', agents: Math.min(50000, Math.max(2, Number(customAgents.value) || 16)), rounds: Math.min(100, Math.max(1, Number(customRounds.value) || 5)) })
}
</script>
<template>
  <section class="preset-selector" :aria-label="t('research.scale')">
    <button class="small-world" :aria-pressed="modelValue.name === 'research'" @click="choose({ name: 'research', agents: 16, rounds: 5 })">
      <strong>{{ t('research.preset') }}</strong><span>{{ t('research.presetHint') }}</span>
    </button>
    <details>
      <summary>{{ t('research.advanced') }}</summary>
      <div class="options"><button v-for="p in advanced" :key="p.name" :aria-pressed="modelValue.name === p.name" @click="choose(p)">{{ p.name.toUpperCase() }} · {{ p.agents }} / {{ p.rounds }}</button></div>
      <div class="custom"><label>{{ t('research.agents') }} <input v-model.number="customAgents" type="number" min="2" max="50000" /></label><label>{{ t('research.rounds') }} <input v-model.number="customRounds" type="number" min="1" max="100" /></label><button @click="applyCustom">{{ t('research.custom') }}</button></div>
    </details>
  </section>
</template>
<style scoped>
.preset-selector { padding: 16px; background: var(--bg-card); border: 1px solid var(--border); }
button { cursor: pointer; padding: 12px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary); border-radius: 4px; }
button[aria-pressed="true"] { border-color: var(--accent); background: var(--accent-subtle); }
.small-world { display: flex; flex-direction: column; gap: 6px; text-align: left; width: 100%; }
.small-world span { font-size: 12px; color: var(--text-secondary); }
summary { cursor: pointer; font-size: 12px; padding: 14px 0; }
.options, .custom { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.custom { margin-top: 14px; font-size: 12px; }
input { width: 75px; padding: 8px; border: 1px solid var(--border); }
button:focus-visible, input:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
</style>
