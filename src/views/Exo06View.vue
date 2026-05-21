<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Countdown from '@/components/ui/BaseCountdown.vue'
import { useProgressStore } from '@/stores/progress'

const router = useRouter()
const progress = useProgressStore()

/* ============================================================
   EXO 06 · FILL THE BEAT — radial 8-step clock
   ============================================================ */

const W = 540
const R = W / 2
const CX = R, CY = R
const SLOT_RADIUS = 200
const SLOT_COUNT = 8
const arcLength = 2 * Math.PI * (R - 12)

const HIT_WINDOW_DEG = 26
const PERFECT_WINDOW_DEG = 9
const WARN_WINDOW_DEG = 18
const PAUSE_FREEZE_MARGIN_DEG = 3

const BPM = 80
const LOOP_MS = (60_000 / BPM) * SLOT_COUNT
const TOTAL_LOOPS = 8
const HISTORY_MAX = TOTAL_LOOPS

const MAX_WARN = 1
const MAX_BAD = 0

const FILLERS = ['HH', 'HH', 'HH', 'SN', 'HH', 'SN', 'HH', 'HH']

const PATTERNS = {
  easy:   { label: 'Easy',   targets: [4] },
  medium: { label: 'Medium', targets: [2, 6] },
  hard:   { label: 'Hard',   targets: [1, 4, 6] },
}

const difficulty = ref('easy')
const targets = computed(() => PATTERNS[difficulty.value].targets)

const slots = computed(() => {
  const t = new Set(targets.value)
  return Array.from({ length: SLOT_COUNT }, (_, i) => {
    if (t.has(i)) return { i, kind: 'target', label: 'YOU' }
    return { i, kind: 'coach', label: FILLERS[i] }
  })
})

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

const graduations = Array.from({ length: SLOT_COUNT }, (_, i) => {
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

/* ---- Web Audio -------------------------------------------------------- */
let audioCtx = null
function ensureCtx() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  }
  if (audioCtx.state === 'suspended') audioCtx.resume()
  return audioCtx
}
function playClick(freq = 440, dur = 0.06, type = 'square') {
  const ctx = ensureCtx()
  const t = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, t)
  gain.gain.setValueAtTime(0.0001, t)
  gain.gain.exponentialRampToValueAtTime(0.4, t + 0.005)
  gain.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  osc.connect(gain).connect(ctx.destination)
  osc.start(t)
  osc.stop(t + dur + 0.02)
}

/* ---- état ------------------------------------------------------------- */
const mode = ref('pause')
const status = ref('idle')        // 'idle' | 'countdown' | 'running' | 'done'
const angle = ref(0)
const waiting = ref(false)
const litSlot = ref(null)
const history = ref([])
const loopCount = ref(0)
const streak = ref(0)

/* feedback central (style Exo04) */
const statusKind = ref('idle')
const statusText = ref('Press play to start')

const slotFeedback = reactive({})

const sessionHits = ref(0)
const totalHits = computed(() => targets.value.length * TOTAL_LOOPS)

const bestScores = ref({})
const bestKey = (d, m) => `${d}-${m}`
const bestFor = (d, m) => bestScores.value[bestKey(d, m)] ?? null
const isNewBest = ref(false)
const playedMode = ref('pause')

const completedDiffs = ref(new Set())

/* ---- refs non réactives ---------------------------------------------- */
let rafId = 0
let lastTs = 0
let angleVal = 0
let lastSlot = -1
let loopHitsGood = 0
let loopHitsWarn = 0
let loopHitsBad = 0
const hitTargets = new Set()

const countdownEl = ref(null)

/* ---- helpers ---------------------------------------------------------- */
function crossSlot(i) {
  const s = slots.value[i]
  litSlot.value = i
  setTimeout(() => { if (litSlot.value === i) litSlot.value = null }, 110)
  if (s.kind === 'coach') {
    playClick(SLOT_FREQ[s.label], 0.05, s.label === 'HH' ? 'highpass' : 'square')
  }
}

function nextTargetAhead(a) {
  const sorted = [...targets.value].sort((x, y) => x - y)
  for (const i of sorted) {
    if (hitTargets.has(i)) continue
    if (slotAngle(i) > a) return i
  }
  return null
}

function clearSlotFeedback() {
  for (const k of Object.keys(slotFeedback)) delete slotFeedback[k]
}

/* ---- session ---------------------------------------------------------- */
function resetSession() {
  history.value = []
  loopCount.value = 0
  streak.value = 0
  sessionHits.value = 0
  loopHitsGood = 0
  loopHitsWarn = 0
  loopHitsBad = 0
  hitTargets.clear()
  clearSlotFeedback()
  lastSlot = -1
  angleVal = 0
  angle.value = 0
  waiting.value = false
  isNewBest.value = false
}

function finishLoop() {
  const missed = targets.value.length - hitTargets.size
  loopHitsBad += missed

  const valid = loopHitsBad <= MAX_BAD && loopHitsWarn <= MAX_WARN
  history.value = [...history.value, valid ? 'good' : 'bad']
  streak.value = valid ? streak.value + 1 : 0
  loopCount.value += 1

  statusKind.value = valid ? 'good' : 'bad'
  if (valid) {
    statusText.value = `Loop ${loopCount.value} · clean`
  } else {
    statusText.value = `Loop ${loopCount.value} · ${loopHitsBad}x ${loopHitsWarn}~`
  }

  loopHitsGood = 0
  loopHitsWarn = 0
  loopHitsBad = 0
  hitTargets.clear()
  clearSlotFeedback()
}

function finishSession() {
  status.value = 'done'

  const key = bestKey(difficulty.value, playedMode.value)
  const prev = bestScores.value[key] ?? -1
  isNewBest.value = sessionHits.value > prev
  if (isNewBest.value) {
    bestScores.value = { ...bestScores.value, [key]: sessionHits.value }
  }

  /* score final affiché dans le centre, identique Exo04 */
  statusKind.value = sessionHits.value >= totalHits.value * 0.7 ? 'good' : 'bad'
  statusText.value = `Score ${sessionHits.value} / ${totalHits.value}`

  completedDiffs.value.add(difficulty.value)
  if (
    completedDiffs.value.has('easy') &&
    completedDiffs.value.has('medium') &&
    completedDiffs.value.has('hard')
  ) {
    progress.markDone('06')
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

    if (mode.value === 'pause') {
      const next = nextTargetAhead(angleVal)
      if (next !== null) {
        const freezeDeg = slotAngle(next) - PAUSE_FREEZE_MARGIN_DEG
        if (angleVal < freezeDeg && a >= freezeDeg) {
          a = freezeDeg
          waiting.value = true
        }
      }
    }

    if (a >= 360) {
      a -= 360
      finishLoop()
      lastSlot = -1
      if (loopCount.value >= TOTAL_LOOPS) {
        finishSession()
        return
      }
    }

    angleVal = a
    angle.value = a
  }
  rafId = requestAnimationFrame(tick)
}

/* ---- start / countdown ----------------------------------------------- */
function startCountdown() {
  if (status.value === 'running' || status.value === 'countdown') return
  resetSession()
  playedMode.value = mode.value
  status.value = 'countdown'
  countdownEl.value.start()
}
function onCountdownDone() {
  status.value = 'running'
  lastTs = 0
  /* pas de texte parasite — le badge garde sa valeur précédente
     (Press play to start au 1er run, dernier feedback ensuite) */
}

function restart() {
  status.value = 'idle'
  statusKind.value = 'idle'
  statusText.value = 'Press play to start'
  resetSession()
  startCountdown()
}

/* ---- hit -------------------------------------------------------------- */
function registerHit() {
  if (status.value !== 'running') return

  let bestI = -1
  let bestDist = Infinity
  for (const i of targets.value) {
    if (hitTargets.has(i)) continue
    const d = angleDiff(angleVal, slotAngle(i))
    if (d < bestDist) { bestDist = d; bestI = i }
  }
  if (bestI === -1) return

  playClick(SLOT_FREQ.YOU, 0.09, 'sine')

  if (bestDist <= HIT_WINDOW_DEG) {
    hitTargets.add(bestI)
    sessionHits.value += 1

    let kind
    if (bestDist <= PERFECT_WINDOW_DEG) {
      kind = 'good'
      loopHitsGood += 1
    } else if (bestDist <= WARN_WINDOW_DEG) {
      kind = 'warn'
      loopHitsWarn += 1
    } else {
      kind = 'warn'
      loopHitsWarn += 1
    }
    slotFeedback[bestI] = kind

    litSlot.value = bestI
    setTimeout(() => { if (litSlot.value === bestI) litSlot.value = null }, 140)

    if (waiting.value) waiting.value = false
  } else {
    slotFeedback[bestI] = 'bad'
    loopHitsBad += 1
  }
}

/* ---- keys ------------------------------------------------------------- */
function onKey(e) {
  if (e.code !== 'Space') return
  e.preventDefault()
  if (status.value === 'idle' || status.value === 'done') startCountdown()
  else registerHit()
}

/* ---- difficulty switch ----------------------------------------------- */
function setDifficulty(key) {
  if (difficulty.value === key) return
  difficulty.value = key
  status.value = 'idle'
  statusKind.value = 'idle'
  statusText.value = 'Press play to start'
  resetSession()
}

/* ---- lifecycle -------------------------------------------------------- */
onMounted(() => {
  window.addEventListener('keydown', onKey)
  rafId = requestAnimationFrame(tick)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  cancelAnimationFrame(rafId)
  if (audioCtx) audioCtx.close()
})
</script>

<template>
  <div class="exo">
    <!-- header : step 6/6 -->
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
          Step <em>6/6</em> · Timing
          <span class="exo-step-dots">
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot curr" />
          </span>
        </span>
      </div>
    </header>

    <!-- stage -->
    <div class="stage">
      <Countdown ref="countdownEl" :from="3" @done="onCountdownDone" />

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

            <div v-for="s in slots" :key="s.i"
                 class="e06-slot"
                 :class="[s.kind, { lit: litSlot === s.i }, slotFeedback[s.i] ? `fb-${slotFeedback[s.i]}` : '']"
                 :style="slotStyle(s.i)">
              <div class="e06-slot-inner">{{ s.label }}</div>
            </div>

            <!-- centre : badge status identique Exo04 -->
            <div class="e06-clock-center">
              <div v-if="status === 'running' && waiting" class="e06-clock-step">
                your turn
              </div>
              <div v-else :class="['e06-status', statusKind]">
                {{ statusText }}
              </div>
            </div>

            <div v-show="status === 'running'" class="e06-cursor-line"
                 :style="{ transform: `rotate(${angle - 180}deg)` }" />
          </div>
        </div>

        <!-- side -->
        <div class="e06-side">
          <!-- difficulté -->
          <div class="e06-block">
            <span class="mono-label">Difficulty</span>
            <div class="e06-diff-btns">
              <button
                v-for="(p, key) in PATTERNS"
                :key="key"
                type="button"
                class="e06-diff-btn"
                :class="{ active: difficulty === key, done: completedDiffs.has(key) }"
                @click="setDifficulty(key)"
              >
                {{ p.label }}
                <span class="e06-diff-tip">
                  <span class="e06-tip-row">
                    <span class="e06-tip-mode">Pause</span>
                    <span>{{ bestFor(key, 'pause') !== null
                      ? bestFor(key, 'pause') + '/' + (p.targets.length * TOTAL_LOOPS)
                      : '—' }}</span>
                  </span>
                  <span class="e06-tip-row">
                    <span class="e06-tip-mode">Loop</span>
                    <span>{{ bestFor(key, 'loop') !== null
                      ? bestFor(key, 'loop') + '/' + (p.targets.length * TOTAL_LOOPS)
                      : '—' }}</span>
                  </span>
                </span>
              </button>
            </div>
          </div>

          <!-- mode -->
          <div class="e06-block">
            <span class="mono-label">Mode</span>
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

          <!-- streak (avec new best en message) -->
          <div class="e06-block">
            <span class="mono-label">
              Streak · {{ loopCount }} / {{ TOTAL_LOOPS }} loops
            </span>
            <div class="e06-streak">
              <div class="e06-streak-num">
                <span class="x">×</span>{{ streak }}
              </div>
              <p class="e06-streak-msg">
                <template v-if="status === 'done' && isNewBest">
                  <span class="e06-new-best">★ New best score</span>
                </template>
                <template v-else-if="status === 'done'">
                  Best: {{ bestFor(difficulty, playedMode) }}/{{ totalHits }}
                </template>
                <template v-else>
                  Don't break the chain.
                  <strong>Goal: {{ TOTAL_LOOPS }} loops clean.</strong>
                </template>
              </p>
            </div>
          </div>

          <!-- historique -->
          <div class="e06-block e06-history">
            <span class="mono-label">
              History · last {{ HISTORY_MAX }} loops
            </span>
            <div class="e06-history-dots">
              <span
                v-for="i in HISTORY_MAX"
                :key="i"
                :class="['e06-hdot', history[i - 1] || 'empty']"
              />
            </div>
          </div>

          <!-- play / restart -->
          <button
            v-if="status === 'idle'"
            class="e06-play" type="button" @click="startCountdown">
            ▶ Play
          </button>
          <button
            v-else-if="status === 'done'"
            class="e06-play" type="button" @click="restart">
            ↻ Restart
          </button>
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

/* ---- stage ---- */
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
  transition: background-color var(--dur-fast),
              color var(--dur-fast),
              border-color var(--dur-fast),
              box-shadow var(--dur-fast);
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

/* feedback instantané sur slot */
.e06-slot.fb-good .e06-slot-inner {
  border-color: var(--state-good);
  color: var(--state-good);
  box-shadow: 0 0 0 4px rgba(77, 208, 140, 0.25);
}
.e06-slot.fb-warn .e06-slot-inner {
  border-color: var(--state-warn);
  color: var(--state-warn);
  box-shadow: 0 0 0 4px rgba(255, 194, 51, 0.25);
}
.e06-slot.fb-bad .e06-slot-inner {
  border-color: var(--state-bad);
  color: var(--state-bad);
  box-shadow: 0 0 0 4px rgba(255, 77, 77, 0.25);
}

/* centre */
.e06-clock-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  pointer-events: none;
}
.e06-clock-step {
  font-family: var(--font-display);
  font-size: 56px;
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--brand);
}

/* badge status — identique Exo04 .e04-status */
.e06-status {
  padding: 8px 12px;
  border-radius: 2px;
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  background: var(--brand);
  color: var(--ink-1);
}
.e06-status.good { background: var(--state-good); }
.e06-status.warn { background: var(--state-warn); }
.e06-status.bad  { background: var(--state-bad); }
.e06-status.idle { background: var(--ink-3); color: var(--fg-muted); }

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
  max-width: 420px;
}

.e06-block { display: flex; flex-direction: column; gap: 12px; }
.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

/* difficulté */
.e06-diff-btns {
  display: flex;
  border: 1px solid var(--line);
  border-radius: 4px;
  width: fit-content;
}
.e06-diff-btn {
  position: relative;
  padding: 8px 14px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
  cursor: pointer;
  transition: background-color var(--dur-fast), color var(--dur-fast);
}
.e06-diff-btn:first-child { border-radius: 3px 0 0 3px; }
.e06-diff-btn:last-child { border-right: none; border-radius: 0 3px 3px 0; }
.e06-diff-btn:hover { color: var(--fg-primary); }
.e06-diff-btn.active {
  background: var(--brand);
  color: var(--fg-on-orange);
}
.e06-diff-btn.done:not(.active)::after {
  content: '';
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--state-good);
}
.e06-diff-tip {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
  padding: 8px 10px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  color: var(--fg-secondary);
  text-transform: none;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--dur-fast);
  z-index: 5;
}
.e06-diff-btn:hover .e06-diff-tip { opacity: 1; }
.e06-tip-row { display: flex; justify-content: space-between; gap: 16px; }
.e06-tip-mode { color: var(--fg-muted); }

/* chips mode */
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

/* streak (identique Exo04) */
.e06-streak { display: flex; align-items: center; gap: 24px; }
.e06-streak-num {
  font-family: var(--font-display);
  font-size: var(--t-d2);
  line-height: var(--lh-display);
  color: var(--brand);
}
.e06-streak-num .x { font-size: var(--t-h1); }
.e06-streak-msg {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: var(--lh-body);
  color: var(--fg-muted);
}
.e06-streak-msg strong { color: var(--fg-primary); }
.e06-new-best { color: var(--brand); font-weight: 500; }

/* historique (identique Exo04) */
.e06-history {
  padding: 16px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e06-history-dots { display: flex; gap: 8px; }
.e06-hdot {
  width: 14px;
  height: 14px;
  border-radius: var(--r-pill);
  background: var(--ink-3);
  border: 1px solid var(--ink-4);
  transition: background-color var(--dur-base);
}
.e06-hdot.good { background: var(--state-good); border-color: var(--state-good); }
.e06-hdot.bad  { background: var(--state-bad);  border-color: var(--state-bad); }
.e06-hdot.empty { background: transparent; }

/* play / restart (identique Exo04 .e04-transport) */
.e06-play {
  align-self: flex-start;
  font-family: var(--font-display);
  font-size: var(--t-h3);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  padding: 12px 32px;
  background: var(--brand);
  color: var(--fg-on-orange);
  border: 2px solid var(--brand);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color var(--dur-fast);
}
.e06-play:hover { background: var(--brand-hover); }

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