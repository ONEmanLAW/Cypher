<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Countdown from '@/components/ui/BaseCountdown.vue'

const router = useRouter()

/* ---- config ----------------------------------------------------------- */
const W = 540
const R = W / 2                  // 270
const CX = R, CY = R
const SLOT_RADIUS = 200
const SLOT_COUNT = 8
const TARGET_INDEX = 4           // bottom slot = the user's slot
const HIT_WINDOW_DEG = 26        // angular tolerance around target
const PERFECT_WINDOW_DEG = 9     // tighter window = "perfect"
const BPM = 80
const LOOP_MS = (60_000 / BPM) * SLOT_COUNT
const arcLength = 2 * Math.PI * (R - 12)
const HISTORY_MAX = 8

const SLOTS = [
  { i: 0, kind: 'coach',  label: 'HH' },
  { i: 1, kind: 'coach',  label: 'HH' },
  { i: 2, kind: 'coach',  label: 'HH' },
  { i: 3, kind: 'coach',  label: 'SN' },
  { i: 4, kind: 'target', label: 'YOU' },
  { i: 5, kind: 'coach',  label: 'HH' },
  { i: 6, kind: 'coach',  label: 'SN' },
  { i: 7, kind: 'coach',  label: 'HH' },
]
const SLOT_FREQ = { HH: 7200, SN: 320, YOU: 110 }

/* ---- geometry --------------------------------------------------------- */
const slotAngle = (i) => (i / SLOT_COUNT) * 360
const polar = (i, r = SLOT_RADIUS) => {
  const rad = (slotAngle(i) - 90) * Math.PI / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}
const angleDiff = (a, b) => {
  const d = Math.abs(((a - b) % 360 + 360) % 360)
  return d > 180 ? 360 - d : d
}

const graduations = SLOTS.map((_, i) => {
  const a = (slotAngle(i) - 90) * Math.PI / 180
  const r1 = R - 6, r2 = R - 18
  return {
    i,
    x1: CX + r1 * Math.cos(a), y1: CY + r1 * Math.sin(a),
    x2: CX + r2 * Math.cos(a), y2: CY + r2 * Math.sin(a),
  }
})
const slotStyle = (i) => {
  const p = polar(i)
  return { transform: `translate(${p.x - 44}px, ${p.y - 44}px)` }
}

/* ---- Web Audio click -------------------------------------------------- */
let audioCtx = null
function playClick(freq = 440, dur = 0.06, type = 'square') {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  }
  if (audioCtx.state === 'suspended') audioCtx.resume()
  const t = audioCtx.currentTime
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, t)
  gain.gain.setValueAtTime(0.0001, t)
  gain.gain.exponentialRampToValueAtTime(0.4, t + 0.005)
  gain.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  osc.connect(gain).connect(audioCtx.destination)
  osc.start(t)
  osc.stop(t + dur + 0.02)
}

/* ---- reactive state --------------------------------------------------- */
const mode = ref('pause')        // 'pause' | 'loop'
const status = ref('idle')       // 'idle' | 'countdown' | 'running'
const angle = ref(0)             // playhead clock angle 0..360
const waiting = ref(false)
const litSlot = ref(null)
const feedback = reactive({ kind: 'idle', text: 'Press start when ready' })
const history = ref([])          // [{ kind: 'perfect'|'good'|'miss' }]

/* ---- non-reactive loop refs ------------------------------------------ */
let rafId = 0
let lastTs = 0
let angleVal = 0
let lastSlot = -1
let hitThisLoop = false

/* ---- countdown component ref ----------------------------------------- */
const countdownEl = ref(null)

/* ---- helpers ---------------------------------------------------------- */
function setFeedback(kind, text) {
  feedback.kind = kind
  feedback.text = text
}
function pushHistory(kind) {
  history.value = [...history.value, { kind }].slice(-HISTORY_MAX)
}

function crossSlot(i) {
  const s = SLOTS[i]
  litSlot.value = i
  setTimeout(() => { if (litSlot.value === i) litSlot.value = null }, 110)
  if (s.kind === 'coach') {
    playClick(SLOT_FREQ[s.label], 0.05, s.label === 'HH' ? 'highpass' : 'square')
  }
}

/* ---- animation loop --------------------------------------------------- */
function tick(ts) {
  if (!lastTs) lastTs = ts
  const dt = ts - lastTs
  lastTs = ts

  if (status.value === 'running' && !waiting.value) {
    let a = angleVal + (dt / LOOP_MS) * 360

    const prevSlot = Math.floor(angleVal / 45) % SLOT_COUNT
    const nextSlot = Math.floor((a % 360) / 45) % SLOT_COUNT
    if (nextSlot !== prevSlot && nextSlot !== lastSlot) {
      lastSlot = nextSlot
      crossSlot(nextSlot)
    }

    // pause mode: freeze BEFORE the target so the hit window still matters
    const targetDeg = slotAngle(TARGET_INDEX)
    const freezeDeg = targetDeg - HIT_WINDOW_DEG
    if (mode.value === 'pause' && !hitThisLoop &&
        angleVal < freezeDeg && a >= freezeDeg) {
      a = freezeDeg
      waiting.value = true
    }

    if (a >= 360) {
      a -= 360
      if (!hitThisLoop) {
        pushHistory('miss')
        setFeedback('bad', 'Missed')
      }
      hitThisLoop = false
      lastSlot = -1
    }

    angleVal = a
    angle.value = a
  }
  rafId = requestAnimationFrame(tick)
}

/* ---- countdown / start ----------------------------------------------- */
function startCountdown() {
  if (status.value !== 'idle') return
  status.value = 'countdown'
  setFeedback('idle', 'Get ready')
  countdownEl.value.start()       // onCountdownDone() au terme
}

function onCountdownDone() {
  status.value = 'running'
  lastTs = 0
  setFeedback('idle', 'Hit SPACE on the orange slot')
}

/* ---- hit -------------------------------------------------------------- */
function registerHit() {
  if (status.value !== 'running' || hitThisLoop) return
  const targetDeg = slotAngle(TARGET_INDEX)
  const diff = angleDiff(angleVal, targetDeg)

  if (diff <= HIT_WINDOW_DEG) {
    hitThisLoop = true
    const perfect = diff <= PERFECT_WINDOW_DEG
    playClick(SLOT_FREQ.YOU, 0.09, 'sine')
    litSlot.value = TARGET_INDEX
    setTimeout(() => {
      if (litSlot.value === TARGET_INDEX) litSlot.value = null
    }, 140)
    pushHistory(perfect ? 'perfect' : 'good')
    setFeedback(perfect ? 'perfect' : 'good', perfect ? 'Perfect' : 'On time')
    if (waiting.value) waiting.value = false
  } else {
    setFeedback('bad', 'Off beat')
  }
}

/* ---- key handling ----------------------------------------------------- */
function onKey(e) {
  if (e.code !== 'Space') return
  e.preventDefault()
  if (status.value === 'idle') startCountdown()
  else registerHit()
}

/* ---- lifecycle -------------------------------------------------------- */
onMounted(() => {
  window.addEventListener('keydown', onKey)
  rafId = requestAnimationFrame(tick)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  cancelAnimationFrame(rafId)
})
</script>

<template>
  <div class="exo">
    <!-- header -->
    <header class="exo-header">
      <div class="exo-header-side">
        <button class="exo-back" type="button" @click="router.push('/')">
          ← Back
        </button>
        <span class="exo-header-num">Sound · <em>Kick Drum</em></span>
      </div>
      <div class="exo-header-title">
        <div class="kicker">Exo 06 · Academy</div>
        <div class="name">Fill the Beat</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Step <em>4/6</em> · Timing
          <span class="exo-step-dots">
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot curr" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
          </span>
        </span>
      </div>
    </header>

    <!-- stage -->
    <div class="stage">
      <!-- compte à rebours avant la phase de jeu -->
      <Countdown ref="countdownEl" :from="3" :interval="1000" @done="onCountdownDone" />

      <div class="e06-stage">
        <!-- clock -->
        <div class="e06-clock-wrap">
          <div class="e06-clock">
            <svg :width="W" :height="W"
                 style="position:absolute;inset:0;pointer-events:none">
              <line v-for="g in graduations" :key="g.i"
                    :x1="g.x1" :y1="g.y1" :x2="g.x2" :y2="g.y2"
                    stroke="var(--ink-5)" stroke-width="1.5" />
              <circle :cx="CX" :cy="CY" :r="R - 12"
                      fill="none" stroke="var(--orange-900)" stroke-width="2" />
              <circle :cx="CX" :cy="CY" :r="R - 12"
                      fill="none" stroke="var(--orange-500)" stroke-width="2"
                      stroke-linecap="round"
                      :stroke-dasharray="arcLength"
                      :stroke-dashoffset="arcLength * (1 - angle / 360)"
                      :transform="`rotate(-90 ${CX} ${CY})`" />
            </svg>

            <div v-for="s in SLOTS" :key="s.i"
                 class="e06-slot" :class="[s.kind, { lit: litSlot === s.i }]"
                 :style="slotStyle(s.i)">
              <div class="e06-slot-inner">{{ s.label }}</div>
            </div>

            <!-- center: start / running -->
            <div class="e06-clock-center">
              <template v-if="status === 'running'">
                <div class="e06-clock-label">loop · 8 steps</div>
                <div class="e06-clock-step">{{ waiting ? 'your turn' : 'step 5' }}</div>
              </template>
              <template v-else-if="status === 'idle'">
                <button class="e06-start" type="button" @click="startCountdown">
                  Start
                </button>
              </template>
            </div>

            <!-- playhead -->
            <div v-show="status === 'running'" class="e06-cursor-line"
                 :style="{ transform: `rotate(${angle - 180}deg)` }" />
          </div>
        </div>

        <!-- side -->
        <div class="e06-side">
          <div class="e06-title">Drop your kick<em>right on time.</em></div>
          <div class="e06-subtitle">
            Watch the cursor sweep around the loop. When it reaches the orange
            slot, hit <strong>SPACE</strong> to drop your kick on the beat.
          </div>

          <div class="e06-row">
            <div class="mono-label">Mode</div>
            <div class="chip-row">
              <button class="chip" :class="{ active: mode === 'pause' }"
                      type="button" @click="mode = 'pause'">
                Easy · pause
              </button>
              <button class="chip" :class="{ active: mode === 'loop' }"
                      type="button" @click="mode = 'loop'">
                Natural · loop
              </button>
            </div>
          </div>

          <div class="e06-row">
            <div class="mono-label">History · last {{ HISTORY_MAX }} loops</div>
            <div class="e06-loops">
              <div v-for="i in HISTORY_MAX" :key="i"
                   class="e06-loop"
                   :class="history[i - 1] ? `h-${history[i - 1].kind}` : ''" />
            </div>
          </div>

          <div class="e06-feedback" :class="`fb-${feedback.kind}`">
            {{ feedback.text }}
          </div>
        </div>
      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Review the demo</button>
        <button class="footer-btn" type="button">♪ Listen to the sound</button>
        <button class="footer-btn" type="button">ⓘ Tips</button>
      </div>
      <div class="exo-footer-actions">
        <span class="footer-mic"><span class="dot" /> Mic on</span>
        <button class="footer-cta" type="button">Skip →</button>
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

/* ---- header ---- */
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

/* ---- stage layout ---- */
.stage { flex: 1; display: flex; min-height: 0; position: relative; }
.e06-stage {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 64px;
  padding: 32px 64px;
}

/* ---- clock ---- */
.e06-clock-wrap {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.e06-clock {
  position: relative;
  width: 540px;
  height: 540px;
}

/* slots */
.e06-slot {
  position: absolute;
  top: 0; left: 0;
  width: 88px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow var(--dur-fast);
}
.e06-slot-inner {
  width: 88px;
  height: 88px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 22px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  transition: background-color var(--dur-fast), color var(--dur-fast);
}
.e06-slot.coach .e06-slot-inner {
  background: var(--ink-3);
  color: var(--fg-secondary);
}
.e06-slot.target .e06-slot-inner {
  background: transparent;
  color: var(--orange-500);
  border: 3px solid var(--orange-500);
}
.e06-slot.lit { box-shadow: var(--shadow-glow); }
.e06-slot.target.lit .e06-slot-inner {
  background: var(--orange-500);
  color: var(--fg-on-orange);
}

/* center: perfectly centered overlay */
.e06-clock-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
}
.e06-clock-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e06-clock-step {
  font-family: var(--font-display);
  font-size: 56px;
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}
.e06-start {
  background: var(--brand);
  color: var(--fg-on-orange);
  border: none;
  padding: 18px 44px;
  border-radius: 4px;
  font-family: var(--font-display);
  font-size: 32px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  cursor: pointer;
  transition: background-color var(--dur-fast), transform var(--dur-fast);
}
.e06-start:hover { background: var(--brand-hover); transform: scale(1.04); }
.e06-start:active { background: var(--brand-press); }

/* playhead */
.e06-cursor-line {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 3px;
  height: 200px;
  background: linear-gradient(var(--orange-500), transparent);
  transform-origin: top center;
  margin-left: -1.5px;
}

/* ---- side ---- */
.e06-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.e06-title {
  font-family: var(--font-display);
  font-size: var(--t-h1);
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}
.e06-title em {
  display: block;
  font-style: normal;
  color: var(--brand);
}
.e06-subtitle {
  font-family: var(--font-ui);
  font-size: 16px;
  line-height: var(--lh-body);
  color: var(--fg-secondary);
  max-width: 420px;
}
.e06-subtitle strong { color: var(--fg-primary); }

.e06-row { display: flex; flex-direction: column; gap: 8px; }
.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

/* chips */
.chip-row { display: flex; gap: 8px; }
.chip {
  background: transparent;
  color: var(--fg-secondary);
  border: 1px solid var(--line);
  padding: 6px 14px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  transition: border-color var(--dur-fast), color var(--dur-fast), background-color var(--dur-fast);
}
.chip:hover { border-color: var(--line-strong); color: var(--fg-primary); }
.chip.active {
  background: var(--brand);
  color: var(--fg-on-orange);
  border-color: var(--brand);
}

/* history bars (8) */
.e06-loops { display: flex; gap: 6px; }
.e06-loop {
  flex: 1;
  height: 14px;
  background: var(--ink-3);
  transition: background-color var(--dur-base);
}
.e06-loop.h-perfect { background: var(--accent-lime); }
.e06-loop.h-good    { background: var(--state-good); }
.e06-loop.h-miss    { background: var(--state-bad); }

/* feedback */
.e06-feedback {
  align-self: flex-start;
  padding: 10px 18px;
  border-radius: 2px;
  font-family: var(--font-display);
  font-size: 16px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
}
.e06-feedback.fb-idle {
  background: var(--ink-3);
  color: var(--fg-muted);
}
.e06-feedback.fb-good {
  background: var(--state-good);
  color: var(--ink-1);
}
.e06-feedback.fb-perfect {
  background: var(--accent-lime);
  color: var(--ink-1);
}
.e06-feedback.fb-bad {
  background: var(--state-bad);
  color: var(--bone-0);
}

/* ---- footer ---- */
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
  transition: background-color var(--dur-fast);
}
.footer-cta:hover { background: var(--brand-hover); }
</style>