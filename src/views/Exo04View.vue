<script setup>
import { useRouter } from 'vue-router'
import Countdown from '@/components/ui/BaseCountdown.vue'
import { useProgressStore } from '@/stores/progress'
import { useBeatboxDetector } from '@/composables/useBeatboxDetector'
import { useExoNavigation } from '@/composables/useExoNavigation'
import { ref, computed, onBeforeUnmount } from 'vue'

const router = useRouter()
const progress = useProgressStore()
const { goToNext } = useExoNavigation()
const currentSound = computed(() => progress.currentSound)
const targetLabel = computed(() => currentSound.value?.label)

/* ============================================================
   EXO 04 · MÉTRONOME — 8 temps orbital
   ============================================================ */

const BEATS = 8
const SIZE = 520
const CX = SIZE / 2
const CY = SIZE / 2
const RADIUS = 230
const circumference = 2 * Math.PI * RADIUS

const TOTAL_LOOPS = 8
const ACTIVE_BEATS = BEATS - 1

const PERFECT_DEG = 12
const OK_DEG = 24

const MAX_WARN = 2
const MAX_BAD = 1

function polar (deg, r = RADIUS) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}
function angleDiff (a, b) {
  const d = Math.abs(((a - b) % 360 + 360) % 360)
  return d > 180 ? 360 - d : d
}

/* ---------- état métronome ---------- */
const bpm = ref(80)
const running = ref(false)
const currentBeat = ref(-1)
const cursorPos = ref(polar(0))
const trailAngle = ref(0)

const countdownEl = ref(null)

const streak = ref(0)
const streakGoal = 8
const history = ref([])
const loopCount = ref(0)
const sessionDone = ref(false)
const bestScore = ref(null)

const tickStates = ref(Array(BEATS).fill('idle'))
const ticks = computed(() =>
  tickStates.value.map((state, i) => ({ state, pos: polar((360 / BEATS) * i) }))
)

const statusKind = ref('idle')
const statusText = ref('')

const beatMs = computed(() => 60000 / bpm.value)
const loopMs = computed(() => beatMs.value * BEATS)
const trailLen = computed(() => (trailAngle.value / 360) * circumference)

const { isListening, toggle: toggleMic, stop: stopMic } = useBeatboxDetector({
  targetLabel,
  threshold: 0.6,
  onHit: () => {
    if (running.value) registerHit()
  },
})

let audioCtx = null

function ensureCtx () {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  }
  if (audioCtx.state === 'suspended') audioCtx.resume()
  return audioCtx
}

function playTick (accent = false) {
  const ctx = ensureCtx()
  const t = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()

  osc.frequency.value = accent ? 1500 : 900
  gain.gain.setValueAtTime(0.0001, t)
  gain.gain.exponentialRampToValueAtTime(accent ? 0.6 : 0.35, t + 0.001)
  gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.05)

  osc.connect(gain).connect(ctx.destination)
  osc.start(t)
  osc.stop(t + 0.06)
}

function playKick () {
  const ctx = ensureCtx()
  const t = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()

  osc.frequency.setValueAtTime(180, t)
  osc.frequency.exponentialRampToValueAtTime(60, t + 0.1)
  gain.gain.setValueAtTime(0.5, t)
  gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.15)

  osc.connect(gain).connect(ctx.destination)
  osc.start(t)
  osc.stop(t + 0.17)
}

function loopIsValid (bad, warn) {
  if (bad > MAX_BAD || warn > MAX_WARN) return false
  if (bad >= 1 && warn >= 2) return false
  return true
}

function finishLoop () {
  for (let i = 1; i < BEATS; i++) {
    if (tickStates.value[i] === 'idle') tickStates.value[i] = 'bad'
  }
  const slice = tickStates.value.slice(1)
  const bad = slice.filter(s => s === 'bad').length
  const warn = slice.filter(s => s === 'warn').length
  const valid = loopIsValid(bad, warn)

  loopCount.value += 1
  history.value = [...history.value, valid ? 'good' : 'bad']
  streak.value = valid ? streak.value + 1 : 0

  statusKind.value = valid ? 'good' : 'bad'
  statusText.value = valid
    ? `Loop ${loopCount.value} · clean`
    : `Loop ${loopCount.value} · ${bad}x ${warn}~`
}

function resetTicks () {
  tickStates.value = Array(BEATS).fill('idle')
}

function finishSession () {
  const score = history.value.filter(h => h === 'good').length
  if (bestScore.value === null || score > bestScore.value) {
    bestScore.value = score
  }
  running.value = false
  sessionDone.value = true
  stopLoop()
  statusKind.value = score >= 6 ? 'good' : 'bad'
  statusText.value = `Score ${score} / ${TOTAL_LOOPS}`
  progress.markDone('04')
}

let rafId = null
let startTime = 0
let lastBeat = -1

function loop (now) {
  const elapsed = (now - startTime) % loopMs.value
  const beatIndex = Math.floor(elapsed / beatMs.value)

  if (beatIndex !== lastBeat) {
    if (beatIndex < lastBeat) {
      finishLoop()
      if (loopCount.value >= TOTAL_LOOPS) {
        finishSession()
        return
      }
      resetTicks()
    }
    lastBeat = beatIndex
    currentBeat.value = beatIndex
    playTick(beatIndex === 0)
  }

  const angle = (elapsed / loopMs.value) * 360
  trailAngle.value = angle
  cursorPos.value = polar(angle)

  rafId = requestAnimationFrame(loop)
}

function startLoop () {
  resetTicks()
  loopCount.value = 0
  streak.value = 0
  history.value = []
  sessionDone.value = false
  statusKind.value = 'idle'
  statusText.value = ''
  startTime = performance.now()
  lastBeat = -1
  rafId = requestAnimationFrame(loop)
}

function stopLoop () {
  cancelAnimationFrame(rafId)
  rafId = null
  currentBeat.value = -1
  trailAngle.value = 0
  cursorPos.value = polar(0)
}

function registerHit () {
  playKick()
  const cursorDeg = trailAngle.value

  let bestIdx = -1
  let bestDist = Infinity
  for (let i = 1; i < BEATS; i++) {
    const d = angleDiff(cursorDeg, (360 / BEATS) * i)
    if (d < bestDist) { bestDist = d; bestIdx = i }
  }
  if (bestIdx !== -1 && tickStates.value[bestIdx] === 'idle') {
    let state = 'bad'
    if (bestDist <= PERFECT_DEG) state = 'good'
    else if (bestDist <= OK_DEG) state = 'warn'
    tickStates.value[bestIdx] = state
  }
}

function onKeydown (e) {
  if (e.code !== 'Space') return
  e.preventDefault()
  if (!running.value) return
  registerHit()
}

function toggleRun () {
  ensureCtx()
  if (running.value) {
    running.value = false
    stopLoop()
  } else {
    countdownEl.value.start()
  }
}

function onCountdownDone () {
  running.value = true
  startLoop()
}

function changeBpm (delta) {
  bpm.value = Math.min(180, Math.max(60, bpm.value + delta))
}

function skip () {
  stopMic()
  goToNext()
}

window.addEventListener('keydown', onKeydown)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  cancelAnimationFrame(rafId)
  stopMic()
  if (audioCtx) audioCtx.close()
})
</script>

<template>
  <div class="exo">
    <!-- header -->
    <header class="exo-header">
      <div class="exo-header-side">
        <button class="exo-back" type="button" @click="router.push('/exercises')">
          ← Back
        </button>
        <span v-if="currentSound" class="exo-header-num">
          Sound · <em>{{ currentSound.name }}</em>
        </span>
      </div>
      <div class="exo-header-title">
        <div class="kicker">Exo 04 · Academy</div>
        <div class="name">Stay In Time</div>
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
      <Countdown ref="countdownEl" :from="3" @done="onCountdownDone" />

      <div class="stage-pad">
        <div class="e04-grid">
          <!-- orbite -->
          <div class="e04-orbit">
            <svg :width="SIZE" :height="SIZE" class="e04-orbit-svg">
              <circle :cx="CX" :cy="CY" :r="RADIUS"
                      fill="none" stroke="var(--line)" stroke-width="2" />
              <circle :cx="CX" :cy="CY" :r="RADIUS - 28"
                      fill="none" stroke="var(--ink-4)" stroke-width="1"
                      stroke-dasharray="2 6" />
              <circle :cx="CX" :cy="CY" :r="RADIUS"
                      fill="none" stroke="var(--brand)" stroke-width="3"
                      stroke-linecap="round"
                      :stroke-dasharray="`${trailLen} ${circumference}`"
                      :transform="`rotate(-90 ${CX} ${CY})`"
                      class="e04-trail" />
            </svg>

            <div
              v-for="(tick, i) in ticks"
              :key="i"
              :class="['e04-tick', tick.state, { active: running && currentBeat === i }]"
              :style="{ left: tick.pos.x + 'px', top: tick.pos.y + 'px' }"
            />

            <div
              class="e04-cursor"
              :style="{ left: cursorPos.x + 'px', top: cursorPos.y + 'px' }"
            />

            <div class="e04-center">
              <div class="e04-bpm">{{ bpm }}</div>
              <div class="mono-label">BPM</div>
              <div v-if="statusText" :class="['e04-status', statusKind]">{{ statusText }}</div>
            </div>
          </div>

          <!-- panneau latéral -->
          <div class="e04-side">
            <div class="e04-block">
              <span class="mono-label">
                Streak · {{ loopCount }} / {{ TOTAL_LOOPS }} loops
              </span>
              <div class="e04-streak">
                <div class="e04-streak-num e04-has-tip">
                  <span class="x">×</span>{{ streak }}
                  <span class="e04-tip">
                    <span class="e04-tip-row">
                      <span class="e04-tip-label">Best score</span>
                      <span>{{ bestScore !== null
                        ? bestScore + '/' + TOTAL_LOOPS : '—' }}</span>
                    </span>
                  </span>
                </div>
                <p class="e04-streak-msg">
                  Don't break the chain.
                  <strong>Goal: {{ streakGoal }} loops clean.</strong>
                </p>
              </div>
            </div>

            <div class="e04-block e04-history">
              <span class="mono-label">
                History · last {{ TOTAL_LOOPS }} loops
              </span>
              <div class="e04-history-dots">
                <span
                  v-for="i in TOTAL_LOOPS"
                  :key="i"
                  :class="['e04-hdot', history[i - 1] || 'empty']"
                />
              </div>
            </div>

            <div class="e04-block">
              <span class="mono-label">Tempo</span>
              <div class="e04-tempo">
                <button class="e04-tempo-btn" type="button"
                        :disabled="running" @click="changeBpm(-5)">−</button>
                <div class="e04-tempo-display">
                  <span class="e04-tempo-val">{{ bpm }}</span>
                  <span class="e04-tempo-unit">bpm</span>
                </div>
                <button class="e04-tempo-btn" type="button"
                        :disabled="running" @click="changeBpm(5)">+</button>
              </div>
            </div>

            <button
              :class="['e04-transport', { running }]"
              type="button"
              @click="toggleRun"
            >
              {{ running ? 'Stop' : (sessionDone ? 'Play again' : 'Play') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Review the demo</button>
        <button class="footer-btn" type="button" @click="playTick(false)">
          ♪ Listen to the sound
        </button>
        <button class="footer-btn" type="button">ⓘ Tips</button>
      </div>
      <div class="exo-footer-actions">
        <button
          class="footer-mic"
          :class="{ active: isListening }"
          type="button"
          @click="toggleMic"
        >
          <span class="dot" />
          {{ isListening ? 'Mic on' : 'Mic off' }}
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

.stage { flex: 1; display: flex; min-height: 0; position: relative; }
.stage-pad {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 32px 40px;
}

.e04-grid {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 64px;
  width: 100%;
}

.e04-orbit { position: relative; width: 520px; height: 520px; }
.e04-orbit-svg { position: absolute; inset: 0; pointer-events: none; }
.e04-trail { filter: drop-shadow(0 0 6px rgba(255, 107, 26, 0.5)); }

.e04-tick {
  position: absolute;
  width: 18px;
  height: 18px;
  margin-left: -9px;
  margin-top: -9px;
  border-radius: var(--r-pill);
  background: var(--ink-2);
  border: var(--bw-md) solid var(--bone-0);
  transform: scale(1);
  transition: transform var(--dur-flash) var(--ease-out-snap),
              box-shadow var(--dur-fast) var(--ease-out-snap),
              background-color var(--dur-fast);
}
.e04-tick.good { background: var(--state-good); border-color: var(--state-good); }
.e04-tick.warn { background: var(--state-warn); border-color: var(--state-warn); }
.e04-tick.bad  { background: var(--state-bad);  border-color: var(--state-bad); }
.e04-tick.active {
  transform: scale(1.4);
  box-shadow: var(--shadow-glow);
}

.e04-cursor {
  position: absolute;
  width: 26px;
  height: 26px;
  margin-left: -13px;
  margin-top: -13px;
  background: var(--brand);
  box-shadow: var(--shadow-glow);
}

.e04-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.e04-bpm {
  font-family: var(--font-display);
  font-size: var(--t-counter-sm);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  font-feature-settings: 'tnum' 1;
}
.e04-status {
  margin-top: 12px;
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
.e04-status.good { background: var(--state-good); }
.e04-status.warn { background: var(--state-warn); }
.e04-status.bad  { background: var(--state-bad); }
.e04-status.idle { background: var(--ink-3); color: var(--fg-muted); }

.e04-side {
  display: flex;
  flex-direction: column;
  gap: 32px;
  max-width: 420px;
}
.e04-block { display: flex; flex-direction: column; gap: 12px; }

.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

.e04-streak { display: flex; align-items: center; gap: 24px; }
.e04-streak-num {
  font-family: var(--font-display);
  font-size: var(--t-d2);
  line-height: var(--lh-display);
  color: var(--brand);
}
.e04-streak-num .x { font-size: var(--t-h1); }
.e04-streak-msg {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: var(--lh-body);
  color: var(--fg-muted);
}
.e04-streak-msg strong { color: var(--fg-primary); }

.e04-has-tip { position: relative; cursor: default; }
.e04-tip {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
  padding: 8px 10px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  color: var(--fg-secondary);
  text-transform: uppercase;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--dur-fast);
  z-index: 5;
}
.e04-has-tip:hover .e04-tip { opacity: 1; }
.e04-tip-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.e04-tip-label { color: var(--fg-muted); }

.e04-history {
  padding: 16px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e04-history-dots { display: flex; gap: 8px; }
.e04-hdot {
  width: 14px;
  height: 14px;
  border-radius: var(--r-pill);
  background: var(--ink-3);
  border: 1px solid var(--ink-4);
  transition: background-color var(--dur-base);
}
.e04-hdot.good { background: var(--state-good); border-color: var(--state-good); }
.e04-hdot.bad  { background: var(--state-bad);  border-color: var(--state-bad); }
.e04-hdot.empty { background: transparent; }

.e04-tempo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e04-tempo-display {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.e04-tempo-val {
  font-family: var(--font-display);
  font-size: var(--t-h2);
  line-height: 1;
}
.e04-tempo-unit {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e04-tempo-btn {
  width: 40px;
  height: 40px;
  font-family: var(--font-display);
  font-size: var(--t-h3);
  background: var(--ink-3);
  color: var(--fg-primary);
  border: 1px solid var(--line);
  border-radius: 4px;
  cursor: pointer;
  transition: border-color var(--dur-fast);
}
.e04-tempo-btn:hover:not(:disabled) { border-color: var(--brand); }
.e04-tempo-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.e04-transport {
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
.e04-transport:hover { background: var(--brand-hover); }
.e04-transport.running { background: var(--ink-3); color: var(--fg-primary); }

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
  color: var(--fg-muted);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.footer-mic .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--ink-6);
  transition: background var(--dur-fast), box-shadow var(--dur-fast);
}
.footer-mic.active { color: var(--fg-primary); border-color: var(--state-good); }
.footer-mic.active .dot {
  background: var(--state-good);
  box-shadow: 0 0 8px 0 var(--state-good);
  animation: mic-pulse 1.2s ease-in-out infinite;
}
@keyframes mic-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

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