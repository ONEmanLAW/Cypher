<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  barCount: { type: Number, default: 80 },
})

const levels = ref(Array.from({ length: props.barCount }, () => 0))
const active = ref(false)

let audioCtx = null
let analyser = null
let source = null
let stream = null
let rafId = null
let freqData = null

function start() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((s) => {
      stream = s
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      source = audioCtx.createMediaStreamSource(stream)
      analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      source.connect(analyser)
      freqData = new Uint8Array(analyser.frequencyBinCount)
      loop()
    })
    .catch((err) => {
      console.warn('Micro indisponible:', err)
    })
}

function loop() {
  analyser.getByteFrequencyData(freqData)

  // on n'utilise que la plage utile (voix/beatbox), pas tout le spectre
  const usable = Math.floor(freqData.length * 0.6)

  let sum = 0
  for (let i = 0; i < usable; i++) sum += freqData[i]
  const avg = sum / usable
  active.value = avg > 20   // seuil revenu à la valeur d'origine

  const out = new Array(props.barCount)
  const step = usable / props.barCount
  for (let i = 0; i < props.barCount; i++) {
    out[i] = freqData[Math.floor(i * step)] / 255
  }
  levels.value = out

  rafId = requestAnimationFrame(loop)
}

function stop() {
  if (rafId) cancelAnimationFrame(rafId)
  if (stream) stream.getTracks().forEach((t) => t.stop())
  if (audioCtx) audioCtx.close()
}

onMounted(start)
onBeforeUnmount(stop)
</script>

<template>
  <div class="bars" :class="{ active }">
    <span
      v-for="(h, i) in levels"
      :key="i"
      class="bar"
      :style="{ height: `${Math.max(h, 0.04) * 100}%` }"
    />
  </div>
</template>

<style scoped>
.bars {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  height: 100px;
  gap: 3px;
}

.bar {
  width: 4px;
  background: var(--ink-5);
  transform-origin: center;
  transition: height 0.08s linear, background-color 0.2s;
}

.bars.active .bar {
  background: var(--orange-500);
}
</style>