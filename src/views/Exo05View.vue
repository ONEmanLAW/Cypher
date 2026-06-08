<script setup>
import { useRouter } from 'vue-router'
import Countdown from '@/components/ui/BaseCountdown.vue'
import { useProgressStore } from '@/stores/progress'
import { useBeatboxDetector } from '@/composables/useBeatboxDetector'
import { useExoNavigation } from '@/composables/useExoNavigation'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

// Footer
import BaseTips from '@/components/footer/BaseTips.vue'
import BaseReviewDemo from '@/components/footer/BaseReviewDemo.vue'
import BaseListenSound from '@/components/footer/BaseListenSound.vue'
const router = useRouter()
const progress = useProgressStore()
const { goToNext } = useExoNavigation()
const currentSound = computed(() => progress.currentSound)
const targetLabel = computed(() => currentSound.value?.label)

const completedDiffs = ref(new Set())

/* ============================================================
   EXO 05 · RHYTHM COPY — call / response
   ============================================================ */

const BAR_DIV = 4
const TOL_GOOD = 0.6
const TOL_WARN = 1.3

const PATTERNS = {
  easy: {
    label: 'Easy',
    cells: 16,
    bpm: 60,
    kicks: [2, 5, 6, 8, 12, 14]
  },
  medium: {
    label: 'Medium',
    cells: 22,
    bpm: 60,
    kicks: [2, 3, 5, 7, 8, 10, 13, 15, 17, 18, 19]
  },
  hard: {
    label: 'Hard',
    cells: 28,
    bpm: 60,
    kicks: [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 15, 16, 18, 20, 21, 23, 24, 25]
  }
}

const difficulty = ref('easy')
const teacherPattern = computed(() => PATTERNS[difficulty.value].kicks)
const bpm = computed(() => PATTERNS[difficulty.value].bpm)
const BEATS = computed(() => PATTERNS[difficulty.value].cells)

const playerHits = ref([])

const phase = ref('listen')
const teacherGuide = ref(true)
const hasHeardCall = ref(false)
const playhead = ref(0)
const isRunning = ref(false)

const beatMs = computed(() => 60000 / bpm.value)
const cellMs = computed(() => beatMs.value / 4)
const loopMs = computed(() => cellMs.value * BEATS.value)
const playheadPct = computed(() => (playhead.value / BEATS.value) * 100)

const teacherVisible = computed(
  () => !(phase.value === 'play' && !teacherGuide.value)
)
const teacherActive = computed(
  () => phase.value === 'listen' ||
        phase.value === 'compare' ||
        (phase.value === 'play' && teacherGuide.value)
)
const youActive = computed(
  () => phase.value === 'play' || phase.value === 'compare'
)

/* ---- Stepper (drivé par phase) ---- */
const STEP_ORDER = ['listen', 'play', 'compare']
const STEPS = [
  { key: 'listen',  n: 1, title: 'Listen',    desc: 'Memorize the pattern' },
  { key: 'play',    n: 2, title: 'Your turn',  desc: 'Reproduce it' },
  { key: 'compare', n: 3, title: 'Compare',    desc: 'Read your score' }
]
function stepState (key) {
  const cur = STEP_ORDER.indexOf(phase.value)
  const idx = STEP_ORDER.indexOf(key)
  return idx < cur ? 'done' : idx === cur ? 'active' : 'todo'
}

const scoredHits = computed(() => {
  const targets = teacherPattern.value.map(c => ({ cell: c, taken: false }))
  return playerHits.value.map(hit => {
    let bestIdx = -1
    let bestDist = Infinity
    targets.forEach((t, i) => {
      if (t.taken) return
      const d = Math.abs(t.cell - hit.cell)
      if (d < bestDist) { bestDist = d; bestIdx = i }
    })
    let state = 'bad'
    if (bestIdx !== -1 && bestDist <= TOL_WARN) {
      state = bestDist <= TOL_GOOD ? 'good' : 'warn'
      targets[bestIdx].taken = true
    }
    return { ...hit, state }
  })
})
const placed = computed(
  () => scoredHits.value.filter(h => h.state !== 'bad').length
)
const total = computed(() => teacherPattern.value.length)

const score = computed(() =>
  scoredHits.value.reduce((sum, h) => {
    if (h.state === 'good') return sum + 1
    if (h.state === 'warn') return sum + 0.5
    return sum
  }, 0)
)
const scoreLabel = computed(() => {
  const s = score.value
  return Number.isInteger(s) ? `${s}` : s.toFixed(1)
})
const isScorePass = computed(
  () => total.value > 0 && score.value / total.value >= 0.7
)

const bestScores = ref({})
const playedMode = ref('guided')

function modeOf (guide) { return guide ? 'guided' : 'blind' }
function bestKey (diff, mode) { return `${diff}-${mode}` }
function bestFor (diff, mode) {
  return bestScores.value[bestKey(diff, mode)] ?? null
}

const isNewBest = ref(false)

function saveBest () {
  const key = bestKey(difficulty.value, playedMode.value)
  const prev = bestScores.value[key] ?? -1
  isNewBest.value = score.value > prev
  if (isNewBest.value) {
    bestScores.value = { ...bestScores.value, [key]: score.value }
  }
}

const { isListening, toggle: toggleMic, stop: stopMic } = useBeatboxDetector({
  targetLabel,
  threshold: 0.6,
  onHit: () => {
    if (phase.value !== 'play' || !isRunning.value) return
    playerHits.value.push({ cell: playhead.value })
    playKick()
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

function playKick () {
  const ctx = ensureCtx()
  const t = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()

  osc.frequency.setValueAtTime(160, t)
  osc.frequency.exponentialRampToValueAtTime(50, t + 0.12)
  gain.gain.setValueAtTime(0.6, t)
  gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.18)

  osc.connect(gain).connect(ctx.destination)
  osc.start(t)
  osc.stop(t + 0.2)
}

let rafId = null
let startTime = 0
let lastCell = -1

function loop (now) {
  const elapsed = now - startTime

  if (elapsed >= loopMs.value) {
    finishRun()
    return
  }

  playhead.value = (elapsed / loopMs.value) * BEATS.value
  const cell = Math.floor(playhead.value)

  if (cell !== lastCell) {
    lastCell = cell
    const soundOn = phase.value === 'listen' ||
                    (phase.value === 'play' && teacherGuide.value)
    if (soundOn && teacherPattern.value.includes(cell)) playKick()
  }

  rafId = requestAnimationFrame(loop)
}

function startRun () {
  ensureCtx()
  cancelAnimationFrame(rafId)
  playhead.value = 0
  lastCell = -1
  isRunning.value = true
  startTime = performance.now()
  rafId = requestAnimationFrame(loop)
}

function finishRun () {
  cancelAnimationFrame(rafId)
  rafId = null
  isRunning.value = false
  playhead.value = 0
  if (phase.value === 'listen') hasHeardCall.value = true
  if (phase.value === 'play') {
    phase.value = 'compare'
    saveBest()
    completedDiffs.value.add(difficulty.value)
    if (
      completedDiffs.value.has('easy') &&
      completedDiffs.value.has('medium') &&
      completedDiffs.value.has('hard')
    ) {
      progress.markDone('05')
    }
  }
}

function playCall () {
  phase.value = 'listen'
  startRun()
}

const countdownEl = ref(null)

/* ---- Confirmation avant "Your turn" ---- */
const confirmOpen = ref(false)

function requestYourTurn () { confirmOpen.value = true }
function cancelConfirm ()  { confirmOpen.value = false }
function confirmStart () {
  confirmOpen.value = false
  startYourTurn()
}

function startYourTurn () {
  playerHits.value = []
  playedMode.value = modeOf(teacherGuide.value)
  phase.value = 'play'
  countdownEl.value.start()
}

function retry () {
  playerHits.value = []
  phase.value = 'listen'
}

function setDifficulty (key) {
  if (difficulty.value === key) return
  cancelAnimationFrame(rafId)
  countdownEl.value?.stop()
  confirmOpen.value = false
  isRunning.value = false
  difficulty.value = key
  playerHits.value = []
  playhead.value = 0
  hasHeardCall.value = false
  teacherGuide.value = true
  phase.value = 'listen'
}

function skip () {
  stopMic()
  goToNext()
}

function onKeydown (e) {
  if (e.code !== 'Space') return
  e.preventDefault()
  if (phase.value !== 'play' || !isRunning.value) return
  playerHits.value.push({ cell: playhead.value })
  playKick()
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  // Micro actif par défaut (déclenche la demande de permission au montage)
  if (!isListening.value) toggleMic()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  cancelAnimationFrame(rafId)
  stopMic()
  if (audioCtx) audioCtx.close()
})

function cellLeft (cell) {
  return `${(cell / BEATS.value) * 100}%`
}
const displayedHits = computed(() =>
  phase.value === 'compare' ? scoredHits.value
    : playerHits.value.map(h => ({ ...h, state: 'live' }))
)
const callLabel = computed(() =>
  hasHeardCall.value ? '↻ Replay the call' : '▶ Play the call'
)
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
        <div class="kicker">Exo 05 · Academy</div>
        <div class="name">Rhythm Copy</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Step <em>5/6</em> · Timing
          <span class="exo-step-dots">
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot done" />
            <span class="exo-step-dot curr" />
            <span class="exo-step-dot" />
          </span>
        </span>
      </div>
    </header>

    <!-- stage -->
    <div class="stage">
      <Countdown ref="countdownEl" :from="3" @done="startRun" />

      <div class="stage-pad">
        <!-- topbar -->
        <div class="e05-topbar">
          <!-- STEPPER mis en valeur -->
          <ol class="e05-steps">
            <li
              v-for="s in STEPS"
              :key="s.key"
              class="e05-step-item"
              :class="stepState(s.key)"
            >
              <span class="e05-step-num">{{ s.n }}</span>
              <span class="e05-step-body">
                <span class="e05-step-title">{{ s.title }}</span>
                <span class="e05-step-desc">{{ s.desc }}</span>
              </span>
            </li>
          </ol>

          <div class="e05-diff">
            <span class="mono-label">Difficulty</span>
            <div class="e05-diff-btns">
              <button
                v-for="(p, key) in PATTERNS"
                :key="key"
                type="button"
                class="e05-diff-btn"
                :class="{ active: difficulty === key }"
                @click="setDifficulty(key)"
              >
                {{ p.label }}
                <span class="e05-diff-tip">
                  <span class="e05-tip-row">
                    <span class="e05-tip-mode">Guided</span>
                    <span>{{ bestFor(key, 'guided') !== null
                      ? bestFor(key, 'guided') + '/' + p.kicks.length
                      : '—' }}</span>
                  </span>
                  <span class="e05-tip-row">
                    <span class="e05-tip-mode">Blind</span>
                    <span>{{ bestFor(key, 'blind') !== null
                      ? bestFor(key, 'blind') + '/' + p.kicks.length
                      : '—' }}</span>
                  </span>
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- timelines -->
        <div class="e05-timelines">
          <!-- PROF -->
          <div class="e05-track">
            <span class="e05-track-label" :class="{ active: teacherActive }">
              ● Teacher · Target phrase
            </span>
            <div class="e05-grid" :style="{ '--cells': BEATS }">
              <span
                v-for="n in BEATS"
                :key="'tg' + n"
                class="e05-cell"
                :class="{ bar: (n - 1) % BAR_DIV === 0 }"
              />
              <template v-if="teacherVisible">
                <div
                  v-for="cell in teacherPattern"
                  :key="'tk' + cell"
                  class="e05-kick teacher"
                  :style="{ left: cellLeft(cell) }"
                />
              </template>
              <div v-else class="e05-track-hidden">
                Teacher guide hidden — play by ear
              </div>
              <div
                v-if="isRunning && teacherActive"
                class="e05-playhead"
                :style="{ left: playheadPct + '%' }"
              />
            </div>
          </div>

          <!-- YOU -->
          <div class="e05-track">
            <span class="e05-track-label" :class="{ active: youActive }">
              ● You · Response
            </span>
            <div class="e05-grid" :style="{ '--cells': BEATS }">
              <span
                v-for="n in BEATS"
                :key="'yg' + n"
                class="e05-cell"
                :class="{ bar: (n - 1) % BAR_DIV === 0 }"
              />
              <div
                v-for="(hit, i) in displayedHits"
                :key="'yk' + i"
                class="e05-kick"
                :class="hit.state"
                :style="{ left: cellLeft(hit.cell) }"
              />
              <div
                v-if="isRunning && phase === 'play'"
                class="e05-playhead"
                :style="{ left: playheadPct + '%' }"
              />
            </div>
          </div>
        </div>

        <!-- panneau bas -->
        <div class="e05-panel">
          <template v-if="phase === 'listen'">
            <div class="e05-panel-info">
              <span class="e05-panel-head">
                <span class="e05-panel-num">1</span>
                <span class="e05-panel-step-title">Listen</span>
              </span>
              <p class="e05-panel-text">
                Play the call and memorize the kick pattern.
              </p>
            </div>
            <div class="e05-panel-actions">
              <button
                type="button"
                class="e05-guide"
                :class="{ off: !teacherGuide }"
                :disabled="!hasHeardCall"
                @click="teacherGuide = !teacherGuide"
              >
                <span class="e05-guide-dot" />
                Teacher guide · {{ teacherGuide ? 'ON' : 'OFF' }}
              </button>
              <button class="footer-btn" type="button" @click="playCall">
                {{ callLabel }}
              </button>
              <button
                class="footer-cta"
                type="button"
                :disabled="!hasHeardCall"
                @click="requestYourTurn"
              >
                ▶ Your turn
              </button>
            </div>
          </template>

          <template v-else-if="phase === 'play'">
            <div class="e05-panel-info">
              <span class="e05-panel-head">
                <span class="e05-panel-num">2</span>
                <span class="e05-panel-step-title">Your turn</span>
              </span>
              <p class="e05-panel-text">
                Make the <em>{{ currentSound?.name }}</em> sound on every beat.
                {{ teacherGuide
                    ? 'The teacher line guides you.'
                    : 'Teacher line hidden — trust your ear.' }}
              </p>
            </div>
            <div class="e05-panel-actions">
              <span class="e05-live">● Recording</span>
            </div>
          </template>

          <template v-else>
            <div class="e05-panel-info">
              <span class="e05-panel-head">
                <span class="e05-panel-num">3</span>
                <span class="e05-panel-step-title">Compare</span>
              </span>
              <div class="e05-feedback">
                <span class="placed" :class="{ pass: isScorePass }">
                  {{ scoreLabel }}
                </span>
                <span class="e05-feedback-total">/ {{ total }}</span>
                <span class="e05-feedback-text">
                  score · {{ playedMode === 'guided' ? 'guided' : 'blind' }}
                </span>
              </div>
              <p class="e05-panel-text">
                <span v-if="isNewBest" class="e05-new-best">
                  ★ New best score ({{ playedMode }})
                </span>
                <span v-else>
                  Best {{ playedMode }} on {{ PATTERNS[difficulty].label }}:
                  {{ bestFor(difficulty, playedMode) }}/{{ total }}
                </span>
              </p>
            </div>
            <div class="e05-panel-actions">
              <button class="footer-btn" type="button" @click="retry">
                ↻ Try again
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- CONFIRMATION avant Your turn -->
      <div v-if="confirmOpen" class="e05-confirm-backdrop">
        <div class="e05-confirm">
          <div>
            <span class="mono-label">Step 2 · Your turn</span>
            <h3 class="e05-confirm-title">Ready?</h3>
          </div>

          <div class="e05-confirm-rows">
            <div class="e05-confirm-row">
              <span class="e05-confirm-row-label">
                <b>Teacher guide</b>
                <span>{{ teacherGuide ? 'Pattern shown' : 'Play by ear' }}</span>
              </span>
              <button
                class="e05-guide"
                :class="{ off: !teacherGuide }"
                type="button"
                @click="teacherGuide = !teacherGuide"
              >
                <span class="e05-guide-dot" />
                {{ teacherGuide ? 'ON' : 'OFF' }}
              </button>
            </div>
          </div>

          <div class="e05-confirm-actions">
            <button class="footer-btn" type="button" @click="cancelConfirm">Cancel</button>
            <button class="footer-cta" type="button" @click="confirmStart">▶ Start</button>
          </div>
        </div>
      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <BaseReviewDemo />
        <BaseListenSound />
        <BaseTips />
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
  gap: 32px;
  padding: 32px 40px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

.e05-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

/* ---- STEPPER ---- */
.e05-steps { display: flex; list-style: none; margin: 0; padding: 0; }
.e05-step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: var(--ink-3);
  border: 1px solid var(--line);
  border-right: none;
  opacity: 0.5;
  transition: opacity var(--dur-base), background-color var(--dur-base);
}
.e05-step-item:first-child { border-radius: 4px 0 0 4px; }
.e05-step-item:last-child  { border-right: 1px solid var(--line); border-radius: 0 4px 4px 0; }

.e05-step-num {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 999px;
  border: var(--bw-thin) solid var(--line-strong);
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--fg-muted);
}
.e05-step-body { display: flex; flex-direction: column; gap: 2px; }
.e05-step-title {
  font-family: var(--font-display);
  font-size: 18px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-secondary);
}
.e05-step-desc {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}

.e05-step-item.done { opacity: 1; }
.e05-step-item.done .e05-step-num {
  background: var(--orange-700);
  border-color: var(--orange-700);
  color: var(--fg-on-orange);
}
.e05-step-item.active {
  opacity: 1;
  background: var(--brand);
  border-color: var(--brand);
  box-shadow: var(--shadow-glow);
  z-index: 1;
}
.e05-step-item.active .e05-step-num {
  background: var(--fg-on-orange);
  border-color: var(--fg-on-orange);
  color: var(--brand);
}
.e05-step-item.active .e05-step-title,
.e05-step-item.active .e05-step-desc { color: var(--fg-on-orange); }

.e05-diff {
  display: flex;
  align-items: center;
  gap: 12px;
}
.e05-diff-btns {
  display: flex;
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e05-diff-btn {
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
.e05-diff-btn:first-child { border-radius: 3px 0 0 3px; }
.e05-diff-btn:last-child { border-right: none; border-radius: 0 3px 3px 0; }
.e05-diff-btn:hover { color: var(--fg-primary); }
.e05-diff-btn.active {
  background: var(--brand);
  color: var(--fg-on-orange);
}

.e05-diff-tip {
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
.e05-diff-btn:hover .e05-diff-tip { opacity: 1; }
.e05-tip-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.e05-tip-mode { color: var(--fg-muted); }

.e05-timelines { display: flex; flex-direction: column; gap: 24px; }
.e05-track { display: flex; flex-direction: column; gap: 8px; }

.e05-track-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
  transition: color var(--dur-base);
}
.e05-track-label.active { color: var(--brand); }

.e05-grid {
  position: relative;
  display: flex;
  height: 72px;
  border: 1px solid var(--line);
  background: var(--surface-card);
  --cells: 32;
}
.e05-cell {
  flex: 1;
  border-right: 1px solid var(--ink-3);
}
.e05-cell:last-child { border-right: none; }
.e05-cell.bar { border-right-color: var(--ink-4); }

.e05-kick {
  position: absolute;
  top: 50%;
  width: calc(100% / var(--cells) * 0.7);
  height: 26px;
  transform: translate(-50%, -50%);
  margin-left: calc(100% / var(--cells) / 2);
  border-radius: 2px;
  background: var(--bone-2);
}
.e05-kick.teacher { background: var(--bone-2); }
.e05-kick.live { background: var(--brand); }
.e05-kick.good { background: var(--state-good); }
.e05-kick.warn { background: var(--state-warn); }
.e05-kick.bad  { background: var(--state-bad); }

.e05-track-hidden {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-disabled);
}

.e05-playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--brand);
  box-shadow: 0 0 8px 0 var(--brand);
}

.e05-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  border-top: 1px solid var(--line);
  padding-top: 24px;
  min-height: 72px;
}
.e05-panel-info { display: flex; flex-direction: column; gap: 8px; }
.e05-panel-head {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.e05-panel-num {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--brand);
  color: var(--fg-on-orange);
  font-family: var(--font-display);
  font-size: 15px;
  line-height: 1;
}
.e05-panel-step-title {
  font-family: var(--font-display);
  font-size: var(--t-h3);
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}
.e05-panel-text {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--fg-secondary);
}
.e05-panel-text em { font-style: normal; color: var(--brand); }
.e05-panel-text kbd {
  font-family: var(--font-mono);
  font-size: 11px;
  background: var(--ink-3);
  border: 1px solid var(--line);
  border-radius: 2px;
  padding: 2px 6px;
}
.e05-panel-actions { display: flex; align-items: center; gap: 12px; }

.e05-feedback {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: var(--font-display);
  text-transform: uppercase;
}
.e05-feedback .placed {
  font-size: var(--t-h1);
  letter-spacing: var(--ls-tight);
  color: var(--fg-muted);
  transition: color var(--dur-base);
}
.e05-feedback .placed.pass { color: var(--state-good); }
.e05-feedback-total {
  font-size: var(--t-h3);
  color: var(--fg-muted);
}
.e05-feedback-text {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  color: var(--fg-muted);
}
.e05-new-best { color: var(--brand); }

.e05-live {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--brand);
  animation: e05-pulse 1.2s ease-in-out infinite;
}
@keyframes e05-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.4; }
}

.e05-guide {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-secondary);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.e05-guide:hover:not(:disabled) { border-color: var(--brand); }
.e05-guide:disabled { opacity: 0.4; cursor: not-allowed; }
.e05-guide-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--state-good);
}
.e05-guide.off { color: var(--fg-muted); }
.e05-guide.off .e05-guide-dot { background: var(--ink-6); }

/* ---- CONFIRMATION OVERLAY ---- */
.e05-confirm-backdrop {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  background: rgba(5, 5, 6, 0.72);
  backdrop-filter: blur(2px);
}
.e05-confirm {
  width: min(420px, 90%);
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-stage);
}
.e05-confirm-title {
  margin: 6px 0 0;
  font-family: var(--font-display);
  font-size: var(--t-h2);
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
}
.e05-confirm-rows { display: flex; flex-direction: column; gap: 10px; }
.e05-confirm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e05-confirm-row-label { display: flex; flex-direction: column; gap: 3px; }
.e05-confirm-row-label b {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 14px;
  color: var(--fg-primary);
}
.e05-confirm-row-label span {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e05-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

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
.footer-cta:disabled { opacity: 0.4; cursor: not-allowed; }
</style>