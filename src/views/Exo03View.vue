<script setup>
/* ============================================================
   EXO 03 · CONTROL MODE
   8 paliers d'intensité progressifs. 5 bulles visibles :
   le carrousel se recentre sur le palier actif.
   Détection micro via RMS — il faut produire un son DANS la
   zone cible [min,max] et la maintenir HOLD_MS pour valider.
   ============================================================ */
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ---------- CONFIG ---------- */
const HOLD_MS = 400        // maintien requis dans la zone
const SMOOTHING = 0.25     // lissage du niveau capté
const VISIBLE = 5          // bulles affichées (carrousel)

/* 8 paliers : la zone cible glisse de bas en haut.
   center/halfWidth -> zone [min,max] normalisée 0..1. */
const LABELS = ['soft', 'soft +', 'medium', 'medium +',
                'loud', 'loud +', 'very loud', 'max']

const steps = LABELS.map((label, i) => {
  const center = 0.12 + (i / 7) * 0.76
  const half = 0.085
  return {
    id: i + 1,
    label,
    min: Math.max(0, center - half),
    max: Math.min(1, center + half),
  }
})

/* ---------- STATE ---------- */
const activeIdx = ref(0)
const micOn = ref(false)
const level = ref(0)             // intensité courante 0..1 (lissée)
const holdProgress = ref(0)      // 0..1

const audio = reactive({
  ctx: null, analyser: null, stream: null, data: null, raf: null, holdStart: null,
})

const pad = (n) => String(n).padStart(2, '0')

/* ---------- CARROUSEL : 5 bulles centrées sur l'actif ---------- */
// fenêtre glissante : on garde toujours l'actif au centre (offset 2)
const windowSteps = computed(() => {
  const out = []
  for (let off = -2; off <= 2; off++) {
    const idx = activeIdx.value + off
    out.push({
      slot: off,                       // -2..2 (0 = centre)
      idx,
      step: steps[idx] || null,
      status: idx < activeIdx.value ? 'done'
            : idx === activeIdx.value ? 'active'
            : idx < steps.length ? 'todo' : 'empty',
    })
  }
  return out
})

const activeStep = computed(() => steps[activeIdx.value])

/* ---------- FEEDBACK ---------- */
const feedback = computed(() => {
  if (!micOn.value) return { tone: 'idle', text: 'Turn on your mic to start' }
  const { min, max } = activeStep.value
  if (level.value < min - 0.04) return { tone: 'low',  text: 'Not loud enough' }
  if (level.value > max + 0.04) return { tone: 'high', text: 'Too loud' }
  if (level.value < min || level.value > max)
    return { tone: 'near', text: 'Almost there' }
  return { tone: 'good', text: 'Perfect · hold it' }
})

const holdHint = computed(() => {
  if (!micOn.value) return 'mic paused'
  if (feedback.value.tone !== 'good') return 'reach the target zone'
  const remain = ((1 - holdProgress.value) * HOLD_MS / 1000).toFixed(1)
  return `hold it · ${remain}s left`
})

const zoneStyle = computed(() => ({
  left: (activeStep.value.min * 100) + '%',
  width: ((activeStep.value.max - activeStep.value.min) * 100) + '%',
}))

/* ---------- MICRO ---------- */
async function toggleMic() {
  if (micOn.value) return stopMic()
  try {
    audio.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    })
    const Ctx = window.AudioContext || window.webkitAudioContext
    audio.ctx = new Ctx()
    const src = audio.ctx.createMediaStreamSource(audio.stream)
    audio.analyser = audio.ctx.createAnalyser()
    audio.analyser.fftSize = 1024
    src.connect(audio.analyser)
    audio.data = new Uint8Array(audio.analyser.fftSize)
    micOn.value = true
    loop()
  } catch (e) {
    micOn.value = false
    console.warn('[Exo03] micro indisponible', e)
  }
}

function stopMic() {
  micOn.value = false
  if (audio.raf) cancelAnimationFrame(audio.raf)
  audio.stream?.getTracks().forEach((t) => t.stop())
  audio.ctx?.close()
  audio.ctx = audio.analyser = audio.stream = audio.data = null
  audio.holdStart = null
  level.value = 0
  holdProgress.value = 0
}

/* ---------- BOUCLE DE DÉTECTION (RMS) ---------- */
function loop() {
  if (!micOn.value || !audio.analyser) return
  audio.analyser.getByteTimeDomainData(audio.data)

  let sum = 0
  for (let i = 0; i < audio.data.length; i++) {
    const v = (audio.data[i] - 128) / 128
    sum += v * v
  }
  const rms = Math.sqrt(sum / audio.data.length)
  const raw = Math.min(1, rms * 3.3)            // ~0.3 RMS = max
  level.value += (raw - level.value) * SMOOTHING

  checkHold()
  audio.raf = requestAnimationFrame(loop)
}

/* ---------- VALIDATION ---------- */
function checkHold() {
  const now = performance.now()
  if (feedback.value.tone === 'good') {
    if (audio.holdStart === null) audio.holdStart = now
    holdProgress.value = Math.min(1, (now - audio.holdStart) / HOLD_MS)
    if (holdProgress.value >= 1) validateStep()
  } else {
    audio.holdStart = null
    holdProgress.value = 0
  }
}

function validateStep() {
  audio.holdStart = null
  holdProgress.value = 0
  if (activeIdx.value < steps.length - 1) {
    activeIdx.value++
  } else {
    stopMic()
    // exercice terminé
  }
}

function skip() {
  stopMic()
  router.push('/')
}

onBeforeUnmount(stopMic)
</script>

<template>
  <div class="exo">
    <!-- ============ HEADER ============ -->
    <header class="exo-header">
      <div class="exo-header-side">
        <button class="exo-back" type="button" @click="router.push('/')">
          ← Back
        </button>
        <span class="exo-header-num">Sound · <em>Kick Drum</em></span>
      </div>
      <div class="exo-header-title">
        <div class="kicker">Exo 03 · Academy</div>
        <div class="name">Control Mode</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Step <em>3/6</em> · Control
          <span class="exo-step-dots">
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot curr" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
          </span>
        </span>
      </div>
    </header>

    <!-- ============ STAGE ============ -->
    <div class="stage">
      <div class="stage-pad">

        <!-- progress meta -->
        <div class="e02-objectif-row">
          <span class="mono-label">Progress</span>
          <span class="mono-label">
            Level <em>{{ pad(activeIdx + 1) }} / {{ pad(steps.length) }}</em>
          </span>
        </div>

        <!-- ===== center : carrousel 5 bulles ===== -->
        <div class="e03-center">
          <div class="mono-label" style="letter-spacing: 0.4em">
            — Go louder, stay in the zone —
          </div>

          <!-- carrousel -->
          <div class="e03-track">
            <template v-for="w in windowSteps" :key="w.idx">
              <div v-if="w.step" class="e03-node" :data-slot="w.slot">
                <div class="e03-bubble" :class="w.status">
                  <span v-if="w.status === 'done'" class="e03-check">✓</span>
                  <span v-else>{{ w.step.id }}</span>
                  <!-- anneau de maintien sur la bulle active -->
                  <svg
                    v-if="w.status === 'active'"
                    class="e03-ring" viewBox="0 0 100 100"
                  >
                    <circle
                      cx="50" cy="50" r="48"
                      :stroke-dasharray="2 * Math.PI * 48"
                      :stroke-dashoffset="2 * Math.PI * 48 * (1 - holdProgress)"
                    />
                  </svg>
                </div>
                <div class="e03-label" :class="{ strong: w.status === 'active' }">
                  {{ w.step.label }}
                </div>
                <div class="e03-sub">
                  <template v-if="w.status === 'done'">cleared</template>
                  <template v-else-if="w.status === 'active'">your turn</template>
                  <template v-else>locked</template>
                </div>
              </div>
              <div v-else class="e03-node empty" />
            </template>
          </div>

          <!-- feedback pill -->
          <div class="e03-feedback-pill" :class="feedback.tone">
            {{ feedback.text }}
          </div>

          <!-- ===== intensity meter ===== -->
          <div class="e03-meter">
            <div class="mono-label">
              Detected intensity · target <em>{{ activeStep.label }}</em>
            </div>
            <div class="e03-meter-track">
              <!-- zone cible -->
              <div class="e03-meter-zone" :style="zoneStyle">
                <span class="e03-zone-tag">target</span>
              </div>
              <!-- niveau capté -->
              <div
                class="e03-meter-fill"
                :class="feedback.tone"
                :style="{ width: (level * 100) + '%' }"
              />
              <!-- curseur -->
              <div class="e03-meter-cursor" :style="{ left: (level * 100) + '%' }" />
            </div>
            <div class="mono-label e03-hint" :class="feedback.tone">
              {{ holdHint }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ FOOTER ============ -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Review the demo</button>
        <button class="footer-btn" type="button">♪ Listen to the sound</button>
        <button class="footer-btn" type="button">ⓘ Tips</button>
      </div>
      <div class="exo-footer-actions">
        <button
          class="footer-mic"
          :class="{ on: micOn }"
          type="button"
          @click="toggleMic"
        >
          <span class="dot" /> Mic {{ micOn ? 'on' : 'off' }}
        </button>
        <button class="footer-cta" type="button" @click="skip">Skip →</button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.exo {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-stage);
}

/* ---------- HEADER (identique Exo 02) ---------- */
.exo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.exo-header-side { flex: 1; display: flex; align-items: center; }
.exo-header-side.right { justify-content: flex-end; }

.exo-back,
.footer-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--fg-secondary);
  border: 1px solid var(--line);
  padding: 8px 12px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.exo-back:hover,
.footer-btn:hover { border-color: var(--brand); color: var(--fg-primary); }

.exo-header-num {
  margin-left: 24px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.exo-header-num em { font-style: normal; color: var(--fg-primary); }
.exo-header-title { text-align: center; }
.exo-header-title .kicker {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-tag);
  text-transform: uppercase;
  color: var(--fg-muted);
  margin-bottom: 6px;
}
.exo-header-title .name {
  font-family: var(--font-display);
  font-size: 24px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  line-height: var(--lh-tight);
}
.exo-step {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.exo-step em { font-style: normal; color: var(--fg-primary); }
.exo-step-dots { display: inline-flex; gap: 4px; margin-left: 12px; }
.exo-step-dot { width: 10px; height: 10px; background: var(--ink-4); }
.exo-step-dot.done { background: var(--orange-700); }
.exo-step-dot.curr { background: var(--orange-500); }

/* ---------- STAGE ---------- */
.stage { flex: 1; display: flex; min-height: 0; }
.stage-pad {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 32px 40px;
}

.e02-objectif-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}
.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.mono-label em { font-style: normal; color: var(--brand); }

/* ---------- CENTER ---------- */
.e03-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 36px;
}

/* ---------- CARROUSEL 5 BULLES ---------- */
.e03-track {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 28px;
}
.e03-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 150px;
  transition: opacity var(--dur-base) var(--ease-out-snap);
}
/* effet "carrousel" : les bulles latérales sont atténuées */
.e03-node[data-slot="-2"],
.e03-node[data-slot="2"]  { opacity: 0.35; transform: scale(0.78); }
.e03-node[data-slot="-1"],
.e03-node[data-slot="1"]  { opacity: 0.7;  transform: scale(0.9); }
.e03-node[data-slot="0"]  { opacity: 1;    transform: scale(1.1); }
.e03-node.empty { visibility: hidden; }

.e03-bubble {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-family: var(--font-display);
  font-size: 48px;
  transition: background var(--dur-base) var(--ease-out-snap),
              box-shadow var(--dur-base) var(--ease-out-snap);
}
.e03-bubble.todo {
  background: transparent;
  border: 2px solid var(--line);
  color: var(--fg-muted);
}
.e03-bubble.done {
  background: var(--ink-3);
  border: 2px solid var(--ink-4);
  color: var(--state-good);
}
.e03-bubble.active {
  background: var(--brand);
  color: var(--fg-on-orange);
  box-shadow: var(--shadow-glow);
}
.e03-check { font-size: 52px; }

/* anneau de progression du maintien */
.e03-ring {
  position: absolute;
  inset: -8px;
  width: calc(100% + 16px);
  height: calc(100% + 16px);
  transform: rotate(-90deg);
}
.e03-ring circle {
  fill: none;
  stroke: var(--state-good);
  stroke-width: 4;
  stroke-linecap: round;
  transition: stroke-dashoffset var(--dur-flash) linear;
}

.e03-label {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 14px;
  color: var(--fg-secondary);
  text-transform: uppercase;
  letter-spacing: var(--ls-tight);
  transition: all var(--dur-base) var(--ease-out-snap);
}
/* label actif : plus gros, plus imposant */
.e03-label.strong {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 32px;
  color: var(--brand);
}
.e03-sub {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

/* ---------- FEEDBACK PILL ---------- */
.e03-feedback-pill {
  font-family: var(--font-display);
  font-size: 16px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  padding: 10px 24px;
  border-radius: 2px;
  transition: all var(--dur-base) var(--ease-out-snap);
}
.e03-feedback-pill.idle { background: var(--ink-3); color: var(--fg-muted); }
.e03-feedback-pill.low  { background: var(--orange-900); color: var(--orange-200); }
.e03-feedback-pill.high { background: var(--state-bad);  color: var(--ink-0); }
.e03-feedback-pill.near { background: var(--state-warn); color: var(--ink-0); }
.e03-feedback-pill.good {
  background: var(--state-good); color: var(--ink-0);
  animation: pulse 1.6s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.04); }
}

/* ---------- INTENSITY METER ---------- */
.e03-meter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 560px;
  max-width: 80vw;
}
.e03-meter-track {
  position: relative;
  width: 100%;
  height: 36px;
  background: var(--ink-3);
  border: 1px solid var(--line);
  overflow: hidden;
}
.e03-meter-zone {
  position: absolute;
  top: 0; bottom: 0;
  background: rgba(77, 208, 140, 0.14);
  border-left: 1.5px dashed var(--state-good);
  border-right: 1.5px dashed var(--state-good);
}
.e03-zone-tag {
  position: absolute;
  top: -16px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--state-good);
}
.e03-meter-fill {
  position: absolute;
  top: 0; left: 0; bottom: 0;
  transition: width var(--dur-flash) linear, background var(--dur-flash) linear;
}
.e03-meter-fill.idle { background: var(--ink-5); }
.e03-meter-fill.low  { background: var(--orange-500); }
.e03-meter-fill.near { background: var(--state-warn); }
.e03-meter-fill.good { background: var(--state-good); }
.e03-meter-fill.high { background: var(--state-bad); }
.e03-meter-cursor {
  position: absolute;
  top: -4px; bottom: -4px;
  width: 2px;
  background: var(--fg-primary);
  transition: left var(--dur-flash) linear;
}
.e03-hint { transition: color var(--dur-base); }
.e03-hint.good { color: var(--state-good); }
.e03-hint.high { color: var(--state-bad); }
.e03-hint.near { color: var(--state-warn); }

/* ---------- FOOTER (identique Exo 02) ---------- */
.exo-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid var(--line);
  flex-shrink: 0;
}
.exo-footer-actions { display: flex; gap: 8px; align-items: center; }
.footer-mic {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid var(--line);
  padding: 8px 12px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-secondary);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.footer-mic.on { border-color: var(--state-good); color: var(--fg-primary); }
.footer-mic .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--ink-5);
}
.footer-mic.on .dot {
  background: var(--state-good);
  box-shadow: 0 0 8px 0 var(--state-good);
}
.footer-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--brand);
  color: var(--fg-on-orange);
  border: none;
  padding: 12px 20px;
  border-radius: 4px;
  font-family: var(--font-display);
  font-size: 16px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  cursor: pointer;
  transition: background-color var(--dur-fast);
}
.footer-cta:hover { background: var(--brand-hover); }
</style>