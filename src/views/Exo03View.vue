<script setup>
/* ============================================================
   EXO 03 · CONTROL MODE
   10 paliers : 1->5 de plus en plus FORT, 6->10 de plus en
   plus DOUCEMENT (courbe d'intensité montante puis descendante).
   Son percussif (beatbox) : détection par PIC.
   On suit le niveau ; quand il redescend (fin du coup), on
   compare le MAX atteint à la zone cible -> validation.
   Le micro est actif en permanence.
   ============================================================ */
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ---------- CONFIG ---------- */
const SMOOTHING = 0.5         // lissage du niveau
const GAIN = 5.5              // calibrage sensibilité (RMS -> 0..1)
const HIT_THRESHOLD = 0.05    // niveau mini pour démarrer un "coup"
const RELEASE_RATIO = 0.6     // fin du coup quand le niveau retombe sous max*ratio
const FEEDBACK_MS = 900       // durée d'affichage du feedback avant d'avancer

/* 10 paliers : intensité cible monte (1->5) puis descend (6->10).
   center = position visée sur le meter (0..1). */
const INTENSITY = [
  { id: 1,  label: 'soft',      center: 0.18 },
  { id: 2,  label: 'medium',    center: 0.36 },
  { id: 3,  label: 'loud',      center: 0.56 },
  { id: 4,  label: 'louder',    center: 0.74 },
  { id: 5,  label: 'max',       center: 0.90 },
  { id: 6,  label: 'louder',    center: 0.74 },
  { id: 7,  label: 'loud',      center: 0.56 },
  { id: 8,  label: 'medium',    center: 0.36 },
  { id: 9,  label: 'soft',      center: 0.18 },
  { id: 10, label: 'very soft', center: 0.10 },
]

const HALF = 0.085            // demi-largeur de la zone cible (resserrée)

const steps = INTENSITY.map((s) => ({
  ...s,
  min: Math.max(0, s.center - HALF),
  max: Math.min(1, s.center + HALF),
}))

/* ---------- STATE ---------- */
const activeIdx = ref(0)
const level = ref(0)                  // intensité courante 0..1 (lissée)
const flash = ref(null)               // 'good' | 'low' | 'high'

const audio = reactive({
  ctx: null, analyser: null, stream: null, data: null, raf: null,
  peak: 0, rising: false, locked: false,
})

const activeStep = computed(() => steps[activeIdx.value])

/* ---------- CARROUSEL : 5 bulles centrées sur l'actif ---------- */
const windowSteps = computed(() => {
  const out = []
  for (let off = -2; off <= 2; off++) {
    const idx = activeIdx.value + off
    out.push({
      slot: off,
      idx,
      step: steps[idx] || null,
      status: idx < activeIdx.value ? 'done'
            : idx === activeIdx.value ? 'active'
            : idx < steps.length ? 'todo' : 'empty',
    })
  }
  return out
})

/* ---------- FEEDBACK ---------- */
const feedback = computed(() => {
  switch (flash.value) {
    case 'good': return { tone: 'good', text: 'Perfect hit' }
    case 'low':  return { tone: 'low',  text: 'Not loud enough' }
    case 'high': return { tone: 'high', text: 'Too loud' }
    default:     return { tone: 'idle', text: 'Hit the kick' }
  }
})

const zoneStyle = computed(() => ({
  left: (activeStep.value.min * 100) + '%',
  width: ((activeStep.value.max - activeStep.value.min) * 100) + '%',
}))

/* ---------- MICRO (ON en permanence) ---------- */
async function startMic() {
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
    loop()
  } catch (e) {
    console.warn('[Exo03] micro indisponible', e)
  }
}

function stopMic() {
  if (audio.raf) cancelAnimationFrame(audio.raf)
  audio.stream?.getTracks().forEach((t) => t.stop())
  audio.ctx?.close()
  audio.ctx = audio.analyser = audio.stream = audio.data = null
}

/* ---------- BOUCLE : RMS + détection de pic ---------- */
function loop() {
  if (!audio.analyser) return

  // FIX micro qui se coupe : le contexte peut passer "suspended"
  // (après inactivité ou pics forts) -> on le réveille.
  if (audio.ctx && audio.ctx.state === 'suspended') {
    audio.ctx.resume().catch(() => {})
  }

  audio.analyser.getByteTimeDomainData(audio.data)

  let sum = 0
  for (let i = 0; i < audio.data.length; i++) {
    const v = (audio.data[i] - 128) / 128
    sum += v * v
  }
  const rms = Math.sqrt(sum / audio.data.length)
  const raw = Math.min(1, rms * GAIN)
  level.value += (raw - level.value) * SMOOTHING

  detectPeak()
  audio.raf = requestAnimationFrame(loop)
}

/* ---------- DÉTECTION DE PIC ----------
   Un "coup" = montée au-dessus du seuil puis redescente.
   On ne ré-évalue pas tant que le feedback est affiché (locked). */
function detectPeak() {
  if (audio.locked) return
  const l = level.value

  if (!audio.rising && l > HIT_THRESHOLD) {
    audio.rising = true
    audio.peak = l
  } else if (audio.rising) {
    audio.peak = Math.max(audio.peak, l)
    if (l < audio.peak * RELEASE_RATIO || l < HIT_THRESHOLD) {
      evaluateHit(audio.peak)
      audio.rising = false
      audio.peak = 0
    }
  }
}

function evaluateHit(peak) {
  const { min, max } = activeStep.value
  // validation stricte : le pic doit être DANS la zone, pas l'effleurer
  if (peak < min) {
    flash.value = 'low'
    resetFlash()
  } else if (peak > max) {
    flash.value = 'high'
    resetFlash()
  } else {
    flash.value = 'good'
    audio.locked = true
    setTimeout(nextStep, FEEDBACK_MS)   // laisse le temps de voir le feedback
  }
}

// efface le feedback d'échec après un délai (sans bloquer la détection)
function resetFlash() {
  audio.locked = true
  setTimeout(() => {
    flash.value = null
    audio.locked = false
    audio.rising = false
    audio.peak = 0
  }, FEEDBACK_MS)
}

function nextStep() {
  if (activeIdx.value < steps.length - 1) {
    activeIdx.value++
    flash.value = null
    audio.locked = false
    audio.rising = false
    audio.peak = 0
  } else {
    stopMic()
    // exercice terminé
  }
}

function skip() {
  stopMic()
  router.push('/')
}

onMounted(startMic)
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

        <!-- ===== center : carrousel 5 bulles ===== -->
        <div class="e03-center">
          <div class="mono-label" style="letter-spacing: 0.4em">
            — Match the target intensity —
          </div>

          <!-- carrousel -->
          <div class="e03-track">
            <template v-for="w in windowSteps" :key="w.idx">
              <div v-if="w.step" class="e03-node" :data-slot="w.slot">
                <div class="e03-bubble" :class="w.status">
                  <span v-if="w.status === 'done'" class="e03-check">✓</span>
                  <span v-else>{{ w.step.id }}</span>
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
            <span class="e03-feedback-icon">
              <template v-if="feedback.tone === 'good'">✓</template>
              <template v-else-if="feedback.tone === 'high'">▲</template>
              <template v-else-if="feedback.tone === 'low'">▼</template>
              <template v-else>♪</template>
            </span>
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
        <span class="footer-mic on"><span class="dot" /> Mic on</span>
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
  gap: 40px;
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
  transition: opacity var(--dur-base) var(--ease-out-snap),
              transform var(--dur-base) var(--ease-out-snap);
}
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

.e03-label {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 14px;
  color: var(--fg-secondary);
  text-transform: uppercase;
  letter-spacing: var(--ls-tight);
  transition: all var(--dur-base) var(--ease-out-snap);
}
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
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-size: 16px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  padding: 10px 24px;
  border-radius: 2px;
  border: 2px solid transparent;
  transition: all var(--dur-base) var(--ease-out-snap);
}
.e03-feedback-icon { font-size: 13px; }

.e03-feedback-pill.idle {
  background: var(--ink-3);
  color: var(--fg-muted);
  border-color: var(--line);
}
.e03-feedback-pill.low {
  background: var(--orange-900);
  color: var(--orange-200);
  border-color: var(--orange-700);
}
.e03-feedback-pill.high {
  background: var(--state-bad);
  color: var(--ink-0);
}
.e03-feedback-pill.good {
  background: var(--state-good);
  color: var(--ink-0);
  animation: hit-pop var(--dur-stage) var(--ease-bounce);
}
@keyframes hit-pop {
  0%   { transform: scale(0.7); }
  45%  { transform: scale(1.12); }
  100% { transform: scale(1); }
}

/* ---------- INTENSITY METER ---------- */
.e03-meter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
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
.e03-meter-fill.good { background: var(--state-good); }
.e03-meter-fill.high { background: var(--state-bad); }
.e03-meter-cursor {
  position: absolute;
  top: -4px; bottom: -4px;
  width: 2px;
  background: var(--fg-primary);
  transition: left var(--dur-flash) linear;
}

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
  border: 1px solid var(--line);
  padding: 8px 12px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-secondary);
}
.footer-mic.on { border-color: var(--state-good); color: var(--fg-primary); }
.footer-mic .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
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