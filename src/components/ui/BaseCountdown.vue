<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  from: { type: Number, default: 3 },      // valeur de départ (3 → 2 → 1)
  interval: { type: Number, default: 700 }, // ms entre chaque tick
  label: { type: String, default: 'Get ready' }
})

const emit = defineEmits(['done'])

const count = ref(0)        // 0 = inactif
let timer = null

function start () {
  stop()
  count.value = props.from
  timer = setInterval(() => {
    count.value -= 1
    if (count.value <= 0) {
      stop()
      emit('done')
    }
  }, props.interval)
}

function stop () {
  clearInterval(timer)
  timer = null
  count.value = 0
}

defineExpose({ start, stop })
onBeforeUnmount(stop)
</script>

<template>
  <div v-if="count > 0" class="countdown">
    <div class="countdown-num" :key="count">{{ count }}</div>
    <div class="countdown-label">{{ label }}</div>
  </div>
</template>

<style scoped>
.countdown {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--s-2);
  background: rgba(11, 11, 12, 0.82);
}
.countdown-num {
  font-family: var(--font-display);
  font-size: var(--t-counter);
  line-height: 1;
  color: var(--brand);
  text-shadow: 0 0 40px rgba(255, 107, 26, 0.6);
  animation: countdown-pop var(--dur-stage) var(--ease-out-snap);
}
.countdown-label {
  font-family: var(--font-mono);
  font-size: var(--t-meta);
  letter-spacing: var(--ls-tag);
  text-transform: uppercase;
  color: var(--fg-muted);
}
@keyframes countdown-pop {
  0%   { transform: scale(0.4); opacity: 0; }
  35%  { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
</style>