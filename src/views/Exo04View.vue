<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ============================================================
   EXO 04 · MÉTRONOME — 8 temps orbital
   - carré orange tourne en continu (vitesse = BPM)
   - traînée orange derrière le curseur
   - tick audio à chaque temps (Web Audio)
   - 8 repères : idle / good / warn / bad
   - streak, historique, statut : données fixes pour l'instant
   ============================================================ */

const BEATS = 8
const SIZE = 520
const CX = SIZE / 2
const CY = SIZE / 2
const RADIUS = 230
const circumference = 2 * Math.PI * RADIUS

/* coord polaire : 0° = midi, sens horaire */
function polar (deg, r = RADIUS) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}

/* ---------- état métronome ---------- */
const bpm = ref(80)
const running = ref(false)
const currentBeat = ref(-1)
const cursorPos = ref(polar(0))
const trailAngle = ref(0)

/* ---------- données fixes (à brancher plus tard) ---------- */
const streak = ref(4)
const streakGoal = 8
const history = ref(['good', 'good', 'good', 'good', 'bad', 'empty', 'empty', 'empty'])
const statusKind = ref('bad')          // good | warn | bad | idle
const statusText = ref('Too late · −60ms')   // EN

/* 8 repères : position fixe + état */
const tickStates = ref(['good', 'good', 'good', 'warn', 'good', 'good', 'bad', 'good'])
const ticks = computed(() =>
  tickStates.value.map((state, i) => ({ state, pos: polar((360 / BEATS) * i) }))
)

/* ---------- timing ---------- */
const beatMs = computed(() => 60000 / bpm.value)
const loopMs = computed(() => beatMs.value * BEATS)
const trailLen = computed(() => (trailAngle.value / 360) * circumference)

/* ---------- audio (Web Audio, oscillateur court) ---------- */
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

/* ---------- boucle d'animation ---------- */
let rafId = null
let startTime = 0
let lastBeat = -1

function loop (now) {
  const elapsed = (now - startTime) % loopMs.value
  const beatIndex = Math.floor(elapsed / beatMs.value)

  if (beatIndex !== lastBeat) {
    lastBeat = beatIndex
    currentBeat.value = beatIndex
    playTick(beatIndex === 0)            // accent sur le 1er temps
  }

  const angle = (elapsed / loopMs.value) * 360
  trailAngle.value = angle
  cursorPos.value = polar(angle)

  rafId = requestAnimationFrame(loop)
}

function startLoop () {
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

/* ---------- contrôles ---------- */
function toggleRun () {
  ensureCtx()                            // débloque l'audio sur geste utilisateur
  running.value = !running.value
  running.value ? startLoop() : stopLoop()
}

function changeBpm (delta) {
  bpm.value = Math.min(200, Math.max(40, bpm.value + delta))
}

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  if (audioCtx) audioCtx.close()
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
      <div class="stage-pad">
        <div class="e04-grid">
          <!-- orbite -->
          <div class="e04-orbit">
            <svg :width="SIZE" :height="SIZE" class="e04-orbit-svg">
              <!-- anneau de base -->
              <circle :cx="CX" :cy="CY" :r="RADIUS"
                      fill="none" stroke="var(--line)" stroke-width="2" />
              <!-- anneau interne pointillé -->
              <circle :cx="CX" :cy="CY" :r="RADIUS - 28"
                      fill="none" stroke="var(--ink-4)" stroke-width="1"
                      stroke-dasharray="2 6" />
              <!-- traînée orange du curseur -->
              <circle :cx="CX" :cy="CY" :r="RADIUS"
                      fill="none" stroke="var(--brand)" stroke-width="3"
                      stroke-linecap="round"
                      :stroke-dasharray="`${trailLen} ${circumference}`"
                      :transform="`rotate(-90 ${CX} ${CY})`"
                      class="e04-trail" />
            </svg>

            <!-- 8 repères -->
            <div
              v-for="(tick, i) in ticks"
              :key="i"
              :class="['e04-tick', tick.state, { active: running && currentBeat === i }]"
              :style="{ left: tick.pos.x + 'px', top: tick.pos.y + 'px' }"
            />

            <!-- curseur carré orange -->
            <div
              class="e04-cursor"
              :style="{ left: cursorPos.x + 'px', top: cursorPos.y + 'px' }"
            />

            <!-- centre -->
            <div class="e04-center">
              <div class="e04-bpm">{{ bpm }}</div>
              <div class="mono-label">BPM</div>
              <div :class="['e04-status', statusKind]">{{ statusText }}</div>
            </div>
          </div>

          <!-- panneau latéral -->
          <div class="e04-side">
            <!-- streak -->
            <div class="e04-block">
              <span class="mono-label">Streak</span>
              <div class="e04-streak">
                <div class="e04-streak-num"><span class="x">×</span>{{ streak }}</div>
                <p class="e04-streak-msg">
                  Keep going, don't break the chain.
                  <strong>Goal: {{ streakGoal }} loops in a row.</strong>
                </p>
              </div>
            </div>

            <!-- historique -->
            <div class="e04-block e04-history">
              <span class="mono-label">
                History · last {{ history.length }} loops
              </span>
              <div class="e04-history-dots">
                <span
                  v-for="(h, i) in history"
                  :key="i"
                  :class="['e04-hdot', h]"
                />
              </div>
            </div>

            <!-- tempo -->
            <div class="e04-block">
              <span class="mono-label">Tempo</span>
              <div class="e04-tempo">
                <button class="e04-tempo-btn" type="button" @click="changeBpm(-5)">−</button>
                <span class="e04-tempo-val">{{ bpm }}</span>
                <span class="e04-tempo-unit">bpm</span>
                <button class="e04-tempo-btn" type="button" @click="changeBpm(5)">+</button>
              </div>
            </div>

            <!-- transport -->
            <button
              :class="['e04-transport', { running }]"
              type="button"
              @click="toggleRun"
            >
              {{ running ? 'Stop' : 'Play' }}
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

/* ===== header (identique Exo02) ===== */
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
.stage { flex: 1; display: flex; min-height: 0; }
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

/* ===== orbite ===== */
.e04-orbit { position: relative; width: 520px; height: 520px; }
.e04-orbit-svg { position: absolute; inset: 0; pointer-events: none; }
.e04-trail { filter: drop-shadow(0 0 6px rgba(255, 107, 26, 0.5)); }

/* repère de temps */
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
              box-shadow var(--dur-fast) var(--ease-out-snap);
}
.e04-tick.good { background: var(--state-good); border-color: var(--state-good); }
.e04-tick.warn { background: var(--state-warn); border-color: var(--state-warn); }
.e04-tick.bad  { background: var(--state-bad);  border-color: var(--state-bad); }
.e04-tick.active {
  transform: scale(1.4);
  box-shadow: var(--shadow-glow);
}

/* curseur carré orange */
.e04-cursor {
  position: absolute;
  width: 26px;
  height: 26px;
  margin-left: -13px;
  margin-top: -13px;
  background: var(--brand);
  box-shadow: var(--shadow-glow);
}

/* centre */
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

/* ===== panneau latéral ===== */
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

/* streak */
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

/* historique */
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
}
.e04-hdot.good { background: var(--state-good); border-color: var(--state-good); }
.e04-hdot.bad  { background: var(--state-bad);  border-color: var(--state-bad); }
.e04-hdot.empty { background: transparent; }

/* tempo */
.e04-tempo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.e04-tempo-val {
  flex: 1;
  text-align: center;
  font-family: var(--font-display);
  font-size: var(--t-h2);
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
  transition: border-color var(--dur-fast);
}
.e04-tempo-btn:hover { border-color: var(--brand); }

/* transport */
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
  transition: background-color var(--dur-fast);
}
.e04-transport:hover { background: var(--brand-hover); }
.e04-transport.running { background: var(--ink-3); color: var(--fg-primary); }

/* ===== footer (identique Exo02 + bloc info central) ===== */
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