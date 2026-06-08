<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useProgressStore } from '@/stores/progress'
import { useBeatboxDetector } from '@/composables/useBeatboxDetector'
import { useExoNavigation } from '@/composables/useExoNavigation'
import BaseWaveform from '@/components/ui/BaseWaveform.vue'
import BaseTips from '@/components/footer/BaseTips.vue'

const router = useRouter()
const progress = useProgressStore()
const { goToNext } = useExoNavigation()
const currentSound = computed(() => progress.currentSound)

/* ---------- CONFIG ---------- */
const DEFAULT_GOAL = 21
const CONF_OK = 0.6   // ≥ : bien
const CONF_LOW = 0.3  // < : mal fait
const FEEDBACK_MS = 700
const EVAL_MS = 250   // fenêtre pour retenir la meilleure prédiction d'une tentative

const norm = (s) => String(s ?? '').trim().toLowerCase()

const goal = ref(DEFAULT_GOAL)
const current = ref(0)
const done = ref(false)

/* feedback qualitatif */
const flash = ref(null) // 'good' | 'almost' | 'bad' | 'wrong' | null
const lock = ref(false)

/* restart */
const restartOpen = ref(false)
const customGoal = ref(DEFAULT_GOAL)

const targetLabel = computed(() => currentSound.value?.label)

const { isListening, error, toggle, stop } = useBeatboxDetector({
  targetLabel,
  threshold: 0.1, // bas : on capte aussi les tentatives faibles / mauvais son
  onHit: ({ label, confidence }) => onPrediction(label, confidence),
})

/* ---------- CLASSIFICATION ----------
   On reçoit le flux brut de prédictions. Une tentative produit plusieurs
   messages (montée du son) ; on retient la meilleure confidence sur EVAL_MS
   puis on tranche une seule fois. */
let evalActive = false
let evalBest = { label: null, confidence: 0 }

function onPrediction(label, confidence) {
  if (done.value || lock.value) return

  if (!evalActive) {
    evalActive = true
    evalBest = { label, confidence }
    setTimeout(finishEval, EVAL_MS)
  } else if (confidence > evalBest.confidence) {
    evalBest = { label, confidence }
  }
}

function finishEval() {
  evalActive = false
  const { label, confidence } = evalBest

  if (norm(label) !== norm(targetLabel.value)) return setFlash('wrong')
  if (confidence < CONF_LOW) return setFlash('bad')
  if (confidence < CONF_OK) return setFlash('almost')

  // bien
  setFlash('good')
  current.value++
  if (current.value >= goal.value) {
    done.value = true
    progress.markDone('02')
    stop()
  }
}

function setFlash(kind) {
  flash.value = kind
  lock.value = true
  setTimeout(() => {
    if (done.value) return
    flash.value = null
    lock.value = false
  }, FEEDBACK_MS)
}

const feedback = computed(() => {
  switch (flash.value) {
    case 'good':   return { tone: 'good', icon: '✓', text: 'Nice!' }
    case 'almost': return { tone: 'low',  icon: '~', text: 'Almost — make it cleaner' }
    case 'bad':    return { tone: 'high', icon: '✕', text: 'Missed — try again' }
    case 'wrong':  return { tone: 'high', icon: '✕', text: 'Wrong sound' }
    default:       return { tone: 'idle', icon: '♪', text: 'Hit the sound' }
  }
})

/* ---------- PROGRESS UI ---------- */
const segs = computed(() => Array.from({ length: goal.value }, (_, i) => i < current.value))
const pad = (n) => String(n).padStart(2, '0')

/* ---------- RESTART ---------- */
function applyRestart(nextGoal) {
  goal.value = Math.min(100, Math.max(21, nextGoal))
  current.value = 0
  done.value = false
  flash.value = null
  lock.value = false
  restartOpen.value = false
  if (!isListening.value) toggle()
}
function restartDefault() { applyRestart(DEFAULT_GOAL) }
function restartCustom() { applyRestart(customGoal.value || DEFAULT_GOAL) }
function stepCustom(d) { customGoal.value = Math.min(100, Math.max(21, (customGoal.value || 21) + d)) }

function skip() {
  stop()
  goToNext()
}

onMounted(() => {
  if (!currentSound.value) return router.replace('/')
  if (!isListening.value) toggle() // mic activé par défaut
})
onBeforeUnmount(stop)
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
        <div class="kicker">Exo 02 · Academy</div>
        <div class="name">Echo Flow</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Step <em>2/6</em> · Imitation
          <span class="exo-step-dots">
            <span class="exo-step-dot done" />
            <span class="exo-step-dot curr" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
            <span class="exo-step-dot" />
          </span>
        </span>
      </div>
    </header>

    <!-- stage -->
    <div class="stage">
      <div class="stage-pad">
        <div class="e02-center">
          <div class="mono-label" style="letter-spacing: 0.4em">
            — Make the sound · <em>{{ currentSound?.name }}</em> —
          </div>

          <div class="e02-counter">
            <span class="cur">{{ pad(current) }}</span>
            <span class="sep">/</span>
            <span class="tgt">{{ pad(goal) }}</span>
          </div>

          <div class="e02-bar">
            <div
              v-for="(on, i) in segs"
              :key="i"
              :class="['e02-bar-seg', { fill: on }]"
            />
          </div>

          <div class="e02-feedback">
            <div class="e02-wave">
              <BaseWaveform :bar-count="48" />
            </div>

            <!-- DONE : pill + restart (DA exo03) -->
            <template v-if="done">
              <div class="e02-feedback-row">
                <div class="e02-feedback-pill done">
                  <span class="e02-feedback-icon">★</span>
                  Exercise completed
                </div>
                <button class="e02-restart-btn" type="button" @click="restartOpen = !restartOpen">
                  ↻ Restart
                </button>
              </div>

              <div v-if="restartOpen" class="e02-modal">
                <div class="e02-modal-backdrop" @click="restartOpen = false" />
                <div class="e02-restart-panel">
                  <div class="e02-restart-title">Choose your goal</div>
                  <div class="e02-restart-opts">
                    <button class="e02-opt default" type="button" @click="restartDefault">
                      <span class="e02-opt-tag">Default program</span>
                      <span class="e02-opt-big">{{ DEFAULT_GOAL }}</span>
                      <span class="e02-opt-unit">reps</span>
                    </button>

                    <div class="e02-opt custom">
                      <span class="e02-opt-tag">Custom goal</span>
                      <div class="e02-opt-row">
                        <button class="e02-step-btn" type="button" @click="stepCustom(-1)">−</button>
                        <input
                          class="e02-goal-input"
                          type="number"
                          min="21"
                          max="100"
                          v-model.number="customGoal"
                        />
                        <button class="e02-step-btn" type="button" @click="stepCustom(1)">+</button>
                        <button class="e02-opt-go" type="button" @click="restartCustom">Go →</button>
                      </div>
                      <span class="e02-opt-hint">min 21 · max 100</span>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- ERROR -->
            <div v-else-if="error" class="e02-feedback-pill high">
              <span class="e02-feedback-icon">⚠</span>
              {{ error }}
            </div>

            <!-- MIC OFF -->
            <div v-else-if="!isListening" class="e02-feedback-pill idle">
              <span class="e02-feedback-icon">♪</span>
              Activate the mic
            </div>

            <!-- ACTIVE -->
            <div v-else class="e02-feedback-pill" :class="feedback.tone">
              <span class="e02-feedback-icon">{{ feedback.icon }}</span>
              {{ feedback.text }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Review the demo</button>
        <button class="footer-btn" type="button">♪ Listen to the sound</button>
        <BaseTips />
      </div>
      <div class="exo-footer-actions">
        <button
          class="footer-mic"
          :class="{ active: isListening }"
          type="button"
          @click="toggle"
        >
          <span class="dot" />
          {{ isListening ? 'Mic on' : 'Mic off' }}
        </button>
        <button class="footer-cta" type="button" @click="skip">
          Skip →
        </button>
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

/* header */
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

/* stage */
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

/* center */
.e02-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}
.e02-counter {
  display: flex;
  align-items: baseline;
  font-family: var(--font-display);
  font-size: var(--t-counter);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  font-feature-settings: 'tnum' 1;
}
.e02-counter .cur { color: var(--brand); }
.e02-counter .sep { color: var(--ink-5); padding: 0 4px; }
.e02-counter .tgt { color: var(--ink-6); }

.e02-bar { display: flex; gap: 4px; width: 720px; max-width: 80vw; }
.e02-bar-seg {
  flex: 1;
  height: 14px;
  background: var(--ink-3);
  transition: background-color var(--dur-base);
}
.e02-bar-seg.fill { background: var(--brand); }

.e02-feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-height: 60px;
}
.e02-wave { width: 280px; }

/* ---------- FEEDBACK PILL (DA exo03) ---------- */
.e02-feedback-row { display: flex; align-items: center; gap: 12px; }
.e02-feedback-pill {
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
.e02-feedback-icon { font-size: 13px; }
.e02-feedback-pill.idle { background: var(--ink-3); color: var(--fg-muted); border-color: var(--line); }
.e02-feedback-pill.low  { background: var(--orange-900); color: var(--orange-200); border-color: var(--orange-700); }
.e02-feedback-pill.high { background: var(--state-bad); color: var(--ink-0); }
.e02-feedback-pill.good { background: var(--state-good); color: var(--ink-0); animation: hit-pop var(--dur-stage) var(--ease-bounce); }
.e02-feedback-pill.done { background: var(--brand); color: var(--fg-on-orange); animation: hit-pop var(--dur-stage) var(--ease-bounce); }
@keyframes hit-pop { 0% { transform: scale(0.7); } 45% { transform: scale(1.12); } 100% { transform: scale(1); } }

/* ---------- RESTART (DA exo03) ---------- */
.e02-restart-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--fg-primary);
  border: 2px solid var(--brand);
  padding: 10px 24px;
  border-radius: 2px;
  font-family: var(--font-display);
  font-size: 16px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--dur-fast), color var(--dur-fast);
}
.e02-restart-btn:hover { background: var(--brand); color: var(--fg-on-orange); }

.e02-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.e02-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(5, 5, 6, 0.72);
  backdrop-filter: blur(3px);
}
.e02-restart-panel {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  border: 1px solid var(--line);
  background: var(--surface-card);
  box-shadow: var(--shadow-stage);
  min-width: 460px;
  max-width: 90vw;
  animation: hit-pop var(--dur-base) var(--ease-out-snap);
}
.e02-restart-title {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e02-restart-opts { display: flex; gap: 12px; }

.e02-opt {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 18px;
  background: var(--ink-3);
  border: 1px solid var(--line);
  border-radius: 2px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--dur-fast), background var(--dur-fast);
}
button.e02-opt:hover { border-color: var(--brand); }
.e02-opt.custom { cursor: default; justify-content: space-between; }
.e02-opt-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e02-opt-big {
  font-family: var(--font-display);
  font-size: 64px;
  line-height: 0.9;
  letter-spacing: var(--ls-display);
  color: var(--brand);
}
.e02-opt-unit {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-secondary);
}
.e02-opt-hint {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e02-opt-row { display: flex; align-items: center; gap: 6px; }
.e02-step-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--line);
  color: var(--fg-primary);
  font-family: var(--font-mono);
  font-size: 16px;
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.e02-step-btn:hover { border-color: var(--brand); color: var(--brand); }
.e02-goal-input {
  width: 52px;
  height: 30px;
  text-align: center;
  background: var(--ink-1);
  border: 1px solid var(--line);
  color: var(--fg-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  -moz-appearance: textfield;
}
.e02-goal-input::-webkit-outer-spin-button,
.e02-goal-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.e02-opt-go {
  height: 30px;
  margin-left: 4px;
  padding: 0 14px;
  background: var(--brand);
  border: none;
  color: var(--fg-on-orange);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--dur-fast);
}
.e02-opt-go:hover { background: var(--brand-hover); }

@media (max-width: 640px) {
  .e02-restart-panel { min-width: 0; width: 100%; }
  .e02-restart-opts { flex-direction: column; }
}

/* footer */
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
.footer-mic.active {
  color: var(--fg-primary);
  border-color: var(--state-good);
}
.footer-mic.active .dot {
  background: var(--state-good);
  box-shadow: 0 0 8px 0 var(--state-good);
  animation: mic-pulse 1.2s ease-in-out infinite;
}
@keyframes mic-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
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