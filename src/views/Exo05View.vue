<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ============================================================
   EXO 05 · RHYTHM COPY — call / response, kick only
   ------------------------------------------------------------
   Flow pédagogique :
   1. LISTEN  — la ligne prof défile avec le son (Play the call)
   2. SETUP   — le joueur règle "Teacher guide" ON / OFF
   3. PLAY    — les 2 lignes défilent, le joueur tape Espace
                pour poser un kick. Si guide OFF, la ligne prof
                est masquée pendant qu'il joue (à l'oreille).
   4. COMPARE — la ligne prof réapparaît, on compare et on note.
   ============================================================ */

const BAR_DIV = 4         // séparateur de mesure : tous les N de la subdivision

/* tolérance de placement (en cellules) — resserrée si grille fine */
const TOL_GOOD = 0.6
const TOL_WARN = 1.3

/* ---------- patterns par difficulté ----------
   chaque difficulté a SA grille (cells) et SON nombre de kicks.
   - cells : nombre de cellules de la timeline
   - bpm   : vitesse → moins de cells = curseur plus rapide à parcourir
   - kicks : index de cellule de chaque kick (à ajuster librement)
   NB : positions régulières par défaut, à régler à l'oreille. */
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
/* BEATS = nombre de cellules, propre à chaque difficulté */
const BEATS = computed(() => PATTERNS[difficulty.value].cells)

/* ---------- réponse JOUEUR : positions posées { cell } ---------- */
const playerHits = ref([])

/* ---------- état ---------- */
const phase = ref('listen')        // listen | play | compare
const teacherGuide = ref(true)     // visuel du prof pendant la phase play
const hasHeardCall = ref(false)
const playhead = ref(0)
const isRunning = ref(false)

/* durée : 1 cellule = 1 double-croche. moins de cellules → timeline
   plus courte → curseur plus rapide à parcourir d'un bout à l'autre. */
const beatMs = computed(() => 60000 / bpm.value)
const cellMs = computed(() => beatMs.value / 4)        // 4 cellules par temps
const loopMs = computed(() => cellMs.value * BEATS.value)
const playheadPct = computed(() => (playhead.value / BEATS.value) * 100)

/* la ligne prof est visible sauf en phase play avec guide coupé */
const teacherVisible = computed(
  () => !(phase.value === 'play' && !teacherGuide.value)
)
/* labels orange : prof actif en listen + compare + play(guidé) */
const teacherActive = computed(
  () => phase.value === 'listen' ||
        phase.value === 'compare' ||
        (phase.value === 'play' && teacherGuide.value)
)
const youActive = computed(
  () => phase.value === 'play' || phase.value === 'compare'
)

/* ---------- évaluation des kicks joueur (phase compare) ----------
   chaque kick prof ne peut être validé qu'UNE fois → score plafonné.
   on associe à chaque kick prof le hit joueur le plus proche dispo. */
const scoredHits = computed(() => {
  const targets = teacherPattern.value.map(c => ({ cell: c, taken: false }))
  // hits triés : on traite les plus proches d'une cible en premier
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
      targets[bestIdx].taken = true   // cible consommée
    }
    return { ...hit, state }
  })
})
const placed = computed(
  () => scoredHits.value.filter(h => h.state !== 'bad').length
)
const total = computed(() => teacherPattern.value.length)

/* score chiffré : vert = 1 point, jaune = 0,5 point */
const score = computed(() =>
  scoredHits.value.reduce((sum, h) => {
    if (h.state === 'good') return sum + 1
    if (h.state === 'warn') return sum + 0.5
    return sum
  }, 0)
)
/* affichage : entier sans décimale inutile (3 / 3.5) */
const scoreLabel = computed(() => {
  const s = score.value
  return Number.isInteger(s) ? `${s}` : s.toFixed(1)
})
/* réussite : score vert si ≥ 70% du total, gris sinon */
const isScorePass = computed(
  () => total.value > 0 && score.value / total.value >= 0.7
)

/* ---------- meilleur score par difficulté + mode (en mémoire) ----------
   non persistant : remis à zéro au rechargement de la page.
   2 scores par difficulté : 'guided' (repère prof) et 'blind' (à l'aveugle).
   clé = `${difficulté}-${mode}` ex: 'easy-guided'. */
const bestScores = ref({})

/* mode du run en cours, figé au lancement (teacherGuide peut bouger après) */
const playedMode = ref('guided')

function modeOf (guide) { return guide ? 'guided' : 'blind' }
function bestKey (diff, mode) { return `${diff}-${mode}` }

/* best score d'une difficulté pour un mode donné */
function bestFor (diff, mode) {
  return bestScores.value[bestKey(diff, mode)] ?? null
}

/* vrai si le dernier score a battu le record (figé à la fin du run) */
const isNewBest = ref(false)

/* enregistre le score courant s'il bat le record (difficulté + mode joué) */
function saveBest () {
  const key = bestKey(difficulty.value, playedMode.value)
  const prev = bestScores.value[key] ?? -1
  isNewBest.value = score.value > prev
  if (isNewBest.value) {
    bestScores.value = { ...bestScores.value, [key]: score.value }
  }
}

/* ---------- audio ---------- */
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

/* ---------- boucle de lecture (une seule passe) ---------- */
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
    // son du prof : en listen toujours, en play seulement si guide ON
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
    saveBest()                 // enregistre le record une fois noté
  }
}

/* ---------- actions ---------- */
function playCall () {
  phase.value = 'listen'
  startRun()
}

/* compte à rebours 3·2·1 avant la phase de jeu */
const countdown = ref(0)       // 0 = inactif, sinon 3 → 2 → 1
let countdownTimer = null

function startYourTurn () {
  playerHits.value = []
  playedMode.value = modeOf(teacherGuide.value)   // fige le mode du run
  phase.value = 'play'
  countdown.value = 3

  clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      startRun()               // le curseur démarre après le "1"
    }
  }, 700)
}

function retry () {
  playerHits.value = []
  phase.value = 'listen'
}

/* changer de difficulté : reset complet de l'exercice */
function setDifficulty (key) {
  if (difficulty.value === key) return
  cancelAnimationFrame(rafId)
  clearInterval(countdownTimer)
  countdown.value = 0
  isRunning.value = false
  difficulty.value = key
  playerHits.value = []
  playhead.value = 0
  hasHeardCall.value = false
  teacherGuide.value = true
  phase.value = 'listen'
}

/* ---------- input joueur : Espace pose un kick au playhead ---------- */
function onKeydown (e) {
  if (e.code !== 'Space') return
  e.preventDefault()
  if (phase.value !== 'play' || !isRunning.value) return
  playerHits.value.push({ cell: playhead.value })
  playKick()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  cancelAnimationFrame(rafId)
  clearInterval(countdownTimer)
  if (audioCtx) audioCtx.close()
})

/* ---------- helpers d'affichage ---------- */
function cellLeft (cell) {
  return `${(cell / BEATS.value) * 100}%`
}
/* kicks joueur : bruts pendant play, notés en compare */
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
        <button class="exo-back" type="button" @click="router.push('/')">
          ← Back
        </button>
        <span class="exo-header-num">Sound · <em>Kick Drum</em></span>
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
      <!-- compte à rebours avant la phase de jeu -->
      <div v-if="countdown > 0" class="e05-countdown">
        <div class="e05-countdown-num" :key="countdown">{{ countdown }}</div>
        <div class="e05-countdown-label">Get ready</div>
      </div>

      <div class="stage-pad">
        <!-- mode tabs + difficulté -->
        <div class="e05-topbar">
          <div class="e05-modes">
            <span class="e05-mode" :class="{ active: phase === 'listen' }">1 · Listen</span>
            <span class="e05-mode-arrow">→</span>
            <span class="e05-mode" :class="{ active: phase === 'play' }">2 · Your turn</span>
            <span class="e05-mode-arrow">→</span>
            <span class="e05-mode" :class="{ active: phase === 'compare' }">3 · Compare</span>
          </div>

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
                <!-- best scores au survol : 2 modes -->
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
              <!-- ligne prof masquée si guide coupé pendant play -->
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

        <!-- panneau bas selon la phase -->
        <div class="e05-panel">
          <!-- LISTEN -->
          <template v-if="phase === 'listen'">
            <div class="e05-panel-info">
              <span class="mono-label">Step 1 · Listen</span>
              <p class="e05-panel-text">
                Play the call and memorize the kick pattern.
              </p>
            </div>
            <div class="e05-panel-actions">
              <!-- réglage guide visuel, dispo avant de jouer -->
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
                @click="startYourTurn"
              >
                ▶ Your turn
              </button>
            </div>
          </template>

          <!-- PLAY -->
          <template v-else-if="phase === 'play'">
            <div class="e05-panel-info">
              <span class="mono-label">Step 2 · Your turn</span>
              <p class="e05-panel-text">
                Hit <kbd>Space</kbd> on every kick.
                {{ teacherGuide
                    ? 'The teacher line guides you.'
                    : 'Teacher line hidden — trust your ear.' }}
              </p>
            </div>
            <div class="e05-panel-actions">
              <span class="e05-live">● Recording</span>
            </div>
          </template>

          <!-- COMPARE -->
          <template v-else>
            <div class="e05-panel-info">
              <span class="mono-label">Step 3 · Compare</span>
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
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Review the demo</button>
        <button class="footer-btn" type="button" @click="playKick">
          ♪ Listen to the sound
        </button>
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

/* ===== header (identique Exo02/04) ===== */
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

/* ===== stage ===== */
.stage { flex: 1; display: flex; min-height: 0; position: relative; }

/* ===== compte à rebours 3·2·1 ===== */
.e05-countdown {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(11, 11, 12, 0.82);
}
.e05-countdown-num {
  font-family: var(--font-display);
  font-size: var(--t-counter);
  line-height: 1;
  color: var(--brand);
  text-shadow: 0 0 40px rgba(255, 107, 26, 0.6);
  animation: e05-count-pop 0.7s var(--ease-out-snap);
}
.e05-countdown-label {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-tag);
  text-transform: uppercase;
  color: var(--fg-muted);
}
@keyframes e05-count-pop {
  0%   { transform: scale(0.4); opacity: 0; }
  35%  { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
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

/* ===== topbar : modes + difficulté ===== */
.e05-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

/* ===== mode tabs ===== */
.e05-modes { display: flex; align-items: center; gap: 12px; }
.e05-mode {
  padding: 8px 14px;
  background: var(--ink-3);
  border: 1px solid var(--line);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.e05-mode.active {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--fg-on-orange);
}
.e05-mode-arrow { color: var(--fg-muted); }

/* sélecteur de difficulté */
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

/* tooltip best score (au survol) */
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

/* ===== timelines ===== */
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

/* grille : bordures uniformes 1px partout
   --cells = nombre de cellules (synchronisé avec BEATS côté JS) */
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

/* kick : cube compact, centré dans sa cellule */
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

/* message ligne prof masquée */
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

/* curseur de lecture */
.e05-playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--brand);
  box-shadow: 0 0 8px 0 var(--brand);
}

/* ===== panneau bas ===== */
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
.e05-panel-text {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--fg-secondary);
}
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

/* indicateur d'enregistrement */
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

/* toggle guide visuel */
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

/* ===== footer (identique Exo02/04) ===== */
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
.footer-cta:disabled { opacity: 0.4; cursor: not-allowed; }
</style>