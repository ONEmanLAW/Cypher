<script setup>
import { ref, watch, nextTick } from 'vue'
import { usePanelTransition } from '@/composables/usePanelTransition'

const { active, phase, origin } = usePanelTransition()

const panelStyle = ref({})

watch(active, async (a) => {
  if (a && origin.value) {
    const o = origin.value
    panelStyle.value = {
      top: o.top + 'px',
      left: o.left + 'px',
      width: o.width + 'px',
      height: o.height + 'px',
    }
    await nextTick()
    requestAnimationFrame(() => {
      panelStyle.value = { top: '0px', left: '0px', width: '100vw', height: '100vh' }
    })
  }
})
</script>

<template>
  <div v-if="active" class="veil" :class="phase">
    <div class="panel" :style="panelStyle">
      <span class="panel-label">{{ origin?.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.veil {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  overflow: hidden;
}
.veil::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: var(--grain-overlay);
  opacity: 0.06;
  mix-blend-mode: screen;
}

.panel {
  position: fixed;
  background: var(--ink-2);
  border: var(--bw-hair) solid var(--orange-500);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: var(--shadow-glow);
  transition:
    top var(--dur-slow) var(--ease-out-snap),
    left var(--dur-slow) var(--ease-out-snap),
    width var(--dur-slow) var(--ease-out-snap),
    height var(--dur-slow) var(--ease-out-snap);
}
.veil.reveal .panel {
  opacity: 0;
  transition: opacity var(--dur-stage) var(--ease-out-soft);
}
.panel-label {
  font-family: var(--font-display);
  font-size: clamp(52px, 9vw, 140px);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  text-transform: uppercase;
  color: var(--bone-2);
  opacity: 0;
  transform: translateY(14px);
  animation: label-in var(--dur-base) var(--ease-out-snap) 160ms forwards;
}
@keyframes label-in { to { opacity: 1; transform: none; } }

@media (prefers-reduced-motion: reduce) {
  .panel { transition-duration: 1ms; }
  .panel-label { animation: none; opacity: 1; transform: none; }
}
</style>