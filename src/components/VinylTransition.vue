<script setup>
import { useVinylTransition } from '@/composables/useVinylTransition'

const { active, phase } = useVinylTransition()
</script>

<template>
  <div v-if="active" class="veil" :class="phase">
    <div class="disc">
      <div class="disc-spin">
        <div class="grooves" />
        <div class="shine" />
      </div>
      <div class="label"><span /></div>
    </div>
  </div>
</template>

<style scoped>
.veil {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  overflow: hidden;
}
/* grain par-dessus le disque, dans l'esprit du DS */
.veil::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: var(--grain-overlay);
  opacity: 0.06;
  mix-blend-mode: screen;
}

.disc {
  position: relative;
  width: 150vmax;
  height: 150vmax;
  border-radius: var(--r-pill);
  background: var(--ink-0);
  transform: scale(0);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.04),
    inset 0 0 120px rgba(0, 0, 0, 0.7);
}
.veil.cover .disc {
  animation: disc-in var(--dur-slow) var(--ease-out-snap) forwards;
}
.veil.reveal .disc {
  animation: disc-out var(--dur-slow) var(--ease-in-quick) forwards;
}

@keyframes disc-in {
  from { transform: scale(0); }
  to   { transform: scale(1); }
}
@keyframes disc-out {
  from { transform: scale(1); }
  to   { transform: scale(0); }
}

/* rotation continue, séparée du scale */
.disc-spin {
  position: absolute;
  inset: 6%;
  border-radius: var(--r-pill);
  animation: vinyl-spin 1.4s linear infinite;
}
.grooves {
  position: absolute;
  inset: 0;
  border-radius: var(--r-pill);
  background: repeating-radial-gradient(
    circle at center,
    rgba(255, 255, 255, 0.07) 0,
    rgba(255, 255, 255, 0.07) 1px,
    transparent 1px,
    transparent 8px
  );
}
.shine {
  position: absolute;
  inset: 0;
  border-radius: var(--r-pill);
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    rgba(255, 255, 255, 0.14) 30deg,
    transparent 80deg,
    transparent 210deg,
    rgba(255, 255, 255, 0.07) 240deg,
    transparent 290deg
  );
  mix-blend-mode: screen;
}
.label {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16vmax;
  height: 16vmax;
  transform: translate(-50%, -50%);
  border-radius: var(--r-pill);
  background: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
}
.label span {
  width: 12%;
  height: 12%;
  border-radius: var(--r-pill);
  background: var(--ink-0);
}

@keyframes vinyl-spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .disc-spin { animation: none; }
  .veil.cover .disc,
  .veil.reveal .disc { animation-duration: 1ms; }
}
</style>