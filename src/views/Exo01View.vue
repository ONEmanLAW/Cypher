<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import BaseWaveform from '@/components/ui/BaseWaveform.vue'
import { useProgressStore } from '@/stores/progress'
import { useBeatboxDetector } from '@/composables/useBeatboxDetector'
import { useExoNavigation } from '@/composables/useExoNavigation'

// Footer
import BaseTips from '@/components/footer/BaseTips.vue'
import BaseListenSound from '@/components/footer/BaseListenSound.vue'

const router = useRouter()
const progress = useProgressStore()
const { goToNext } = useExoNavigation()
const currentSound = computed(() => progress.currentSound)

const norm = (s) => String(s ?? '').trim().toLowerCase()
const targetLabel = computed(() => currentSound.value?.label)

/* ============================================================
   PHASES — mappées sur le temps réel de la vidéo (9:56 = 596s)
   ============================================================ */
const phases = ref([
  { name: 'Intro',       start: 0,    end: 23,   essai: false },
  { name: 'Benefits',    start: 23,   end: 50,   essai: false },
  { name: 'Steps',       start: 50,   end: 300,  essai: false },
  { name: 'Pro Tips',    start: 302,  end: 456,  essai: false },
  { name: 'Practice',    start: 456,  end: 527,  essai: false },
  { name: 'Try 1',       start: 527,  end: 543,  essai: true  },
  { name: 'Try 2',       start: 543,  end: 546,  essai: true  },
  { name: 'Try 3',       start: 546,  end: 550,  essai: true  },
  { name: 'Try 4',       start: 550,  end: 555,  essai: true  },
  { name: 'Try 5',       start: 555,  end: 590,  essai: true  },
  { name: 'Conclusion',  start: 590,  end: 596,  essai: false },
])

const VIDEO_SRC = '/videos/kick-drum-demo.mp4'

/* ============================================================
   STATE
   ============================================================ */
const videoRef = ref(null)
const containerRef = ref(null)

const currentTime = ref(0)
const duration = ref(596)
const isPlaying = ref(false)
const hasStarted = ref(false)
const isFullscreen = ref(false)
const volume = ref(0.8)
const muted = ref(false)
const showVolume = ref(false)

const visitedPhases = ref(new Set([0]))
const validatedTries = ref(new Set())
const activeTryIdx = ref(null)
const tryFeedback = ref(null)   // 'good' | null

/* ---------- FEEDBACK / SCORE ---------- */
const score = ref(0)            // 0..100 — score de la TENTATIVE en cours (remplacé à chaque nouveau son)

/* ============================================================
   GESTION DU SCORE PAR TENTATIVE
   - burst   : suite de prédictions rapprochées = 1 tentative → on garde le pic
   - silence > SILENCE_GAP : la tentative est terminée
   - un nouveau son remplace le score précédent
   - après DISPLAY_HOLD, le score se reset à 0
   ============================================================ */
const SILENCE_GAP = 500     // ms — sépare deux tentatives
const DISPLAY_HOLD = 3000   // ms — durée d'affichage avant reset

let burstTimer = null       // actif = on est encore dans la même tentative
let clearTimer = null       // hold d'affichage avant reset

function clearScoreTimers() {
  if (burstTimer) { clearTimeout(burstTimer); burstTimer = null }
  if (clearTimer) { clearTimeout(clearTimer); clearTimer = null }
}

function resetScore() {
  clearScoreTimers()
  score.value = 0
  tryFeedback.value = null
}

/* ============================================================
   DÉTECTION — même composable que l'exo 02
   ============================================================ */
const { isListening, error, toggle, stop } = useBeatboxDetector({
  targetLabel,
  threshold: 0.1, // bas : on capte aussi les tentatives faibles / mauvais son
  onHit: ({ label, confidence }) => onPrediction(label, confidence),
})

function onPrediction(label, confidence) {
  // n'évalue que pendant un try actif
  if (activeTryIdx.value === null) return
  // on ne traite que le bon son
  if (norm(label) !== norm(targetLabel.value)) return

  const pct = Math.round(confidence * 100)

  // un nouveau son annule le reset d'affichage en attente
  if (clearTimer) { clearTimeout(clearTimer); clearTimer = null }

  if (!burstTimer) {
    // nouvelle tentative → on REMPLACE l'ancien score
    score.value = pct
  } else {
    // même tentative → on garde le pic
    if (pct > score.value) score.value = pct
    clearTimeout(burstTimer)
  }

  // feedback aligné sur la tentative en cours
  tryFeedback.value = score.value >= 70 ? 'good' : null

  // fin de tentative après un silence, puis hold d'affichage
  burstTimer = setTimeout(() => {
    burstTimer = null
    clearTimer = setTimeout(() => {
      score.value = 0
      tryFeedback.value = null
      clearTimer = null
    }, DISPLAY_HOLD)
  }, SILENCE_GAP)
}

/* ============================================================
   COMPUTED
   ============================================================ */
const currentPhaseIdx = computed(() =>
  phases.value.findIndex(p => currentTime.value >= p.start && currentTime.value < p.end)
)

const phasesWithLayout = computed(() =>
  phases.value.map((p, i) => {
    // largeur proportionnelle au temps, mais bornée pour rester lisible
    const raw = ((p.end - p.start) / duration.value) * 100
    const width = p.essai
      ? 0                       // les try ne s'étirent pas : largeur fixe
      : Math.max(raw, 8)        // les phases longues : min 8%
    let state = 'todo'
    if (visitedPhases.value.has(i)) state = 'done'
    if (i === currentPhaseIdx.value) state = 'curr'
    const validated = validatedTries.value.has(i)
    return { ...p, width, state, validated, idx: i }
  })
)

const triesPhases = computed(() => phases.value.filter(p => p.essai))
const totalTries = computed(() => triesPhases.value.length)
const doneTries = computed(() => validatedTries.value.size)

const fmtTime = (s) => {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

/* ============================================================
   VIDEO CONTROLS
   ============================================================ */
function togglePlay() {
  if (!videoRef.value) return
  if (videoRef.value.paused) videoRef.value.play()
  else videoRef.value.pause()
}

function startVideo() {
  if (!videoRef.value) return
  hasStarted.value = true
  videoRef.value.play()
}

function onTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime

  const idx = currentPhaseIdx.value
  if (idx !== -1) visitedPhases.value.add(idx)

  // arrêt fiable : 1er try non validé dont le start est dépassé
  if (activeTryIdx.value === null) {
    const tIdx = phases.value.findIndex(
      (p, i) => p.essai && !validatedTries.value.has(i) && currentTime.value >= p.start
    )
    if (tIdx !== -1) triggerTryStop(tIdx)
  }
}

function onLoadedMetadata() {
  if (videoRef.value) duration.value = videoRef.value.duration
}

function onPlay() { isPlaying.value = true }
function onPause() { isPlaying.value = false }

function onVideoEnded() {
  isPlaying.value = false
  progress.markDone('01')
}

function setVolume(v) {
  volume.value = v
  if (videoRef.value) videoRef.value.volume = v
  muted.value = v === 0
}

function toggleMute() {
  muted.value = !muted.value
  if (videoRef.value) videoRef.value.muted = muted.value
}

/* ============================================================
   FULLSCREEN — faux fullscreen CSS (pas de conflit avec F navigateur)
   ============================================================ */
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

/* ============================================================
   TRY FLOW
   ============================================================ */
function triggerTryStop(idx) {
  if (videoRef.value) videoRef.value.pause()
  activeTryIdx.value = idx
  resetScore()
  if (!isListening.value) toggle()   // on s'assure que le micro écoute
}

function continueAfterTry() {
  if (activeTryIdx.value === null) return
  validatedTries.value.add(activeTryIdx.value)
  activeTryIdx.value = null
  resetScore()
  if (videoRef.value) videoRef.value.play()
}

/* ============================================================
   TIMELINE NAVIGATION — toutes les phases sont navigables
   ============================================================ */
function goToPhase(idx) {
  if (!videoRef.value) return
  hasStarted.value = true
  videoRef.value.currentTime = phases.value[idx].start
  const phase = phases.value[idx]
  if (phase.essai) {
    triggerTryStop(idx)
  } else {
    activeTryIdx.value = null
    resetScore()
    videoRef.value.play()
  }
}

onBeforeUnmount(() => {
  clearScoreTimers()
  stop()
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
        <div class="kicker">Exo 01 · Academy</div>
        <div class="name">Kick Start</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Step <em>1/6</em> · Discovery
          <span class="exo-step-dots">
            <span class="exo-step-dot curr" />
            <span class="exo-step-dot" />
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
      <div class="e01-stage">

        <!-- VIDEO -->
        <div ref="containerRef" class="e01-video" :class="{ fullscreen: isFullscreen }">
          <video
            ref="videoRef"
            class="e01-video-el"
            :src="VIDEO_SRC"
            @timeupdate="onTimeUpdate"
            @loadedmetadata="onLoadedMetadata"
            @play="onPlay"
            @pause="onPause"
            @ended="onVideoEnded"
            @click="hasStarted && togglePlay()"
            playsinline
          />

          <!-- big play overlay (before first start) -->
          <div v-if="!hasStarted" class="e01-video-overlay" @click="startVideo">
            <button class="e01-big-play" type="button" aria-label="Start video">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="6,4 20,12 6,20"/>
              </svg>
            </button>
            <div class="e01-big-play-label">Start the demo</div>
          </div>

          <!-- bottom-left: timer + tag -->
          <div class="e01-video-caption">
            <span class="pill">{{ isPlaying ? '▶' : '❚❚' }} {{ fmtTime(currentTime) }}</span>
            <span>Demo · Kick Drum video</span>
          </div>

          <!-- bottom-right: custom controls -->
          <div class="e01-controls">
            <div class="ctrl-volume" @mouseenter="showVolume = true" @mouseleave="showVolume = false">
              <button class="e01-icon-btn" type="button" @click="toggleMute" aria-label="Volume">
                <svg v-if="!muted && volume > 0.5" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/></svg>
                <svg v-else-if="!muted && volume > 0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 010 7.07"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4V5z"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
              </button>
              <div class="vol-popover" v-show="showVolume">
                <input
                  type="range" min="0" max="1" step="0.05"
                  :value="muted ? 0 : volume"
                  @input="setVolume(parseFloat($event.target.value))"
                  class="vol-slider"
                />
              </div>
            </div>

            <button
              class="e01-icon-btn primary"
              type="button"
              @click="togglePlay"
              :disabled="activeTryIdx !== null || !hasStarted"
              aria-label="Play/Pause"
            >
              <svg v-if="isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14"/><rect x="14" y="5" width="4" height="14"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="6,4 20,12 6,20"/></svg>
            </button>

            <button
              class="e01-icon-btn"
              type="button"
              @click="toggleFullscreen"
              :disabled="activeTryIdx !== null"
              aria-label="Fullscreen"
            >
              <svg v-if="!isFullscreen" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3v6H3M15 3v6h6M9 21v-6H3M15 21v-6h6"/></svg>
            </button>
          </div>
        </div>

        <!-- TIMELINE -->
        <div class="e01-timeline-block">
          <div class="e01-timeline-label">
            <span>Timeline</span>
            <span>{{ fmtTime(currentTime) }} / {{ fmtTime(duration) }}</span>
          </div>
          <div class="e01-phases">
            <button
              v-for="p in phasesWithLayout"
              :key="p.idx"
              :class="['e01-phase', p.state, { essai: p.essai }]"
              :style="p.essai
                ? { flex: '0 0 auto' }
                : { flex: '1 1 ' + p.width + '%' }"
              type="button"
              @click="goToPhase(p.idx)"
            >
              <div class="e01-phase-name">{{ p.name }}</div>
              <div class="e01-phase-time">{{ fmtTime(p.start) }}</div>
              <div
                v-if="p.essai"
                :class="['e01-phase-dot', p.validated ? 'done' : p.state]"
              />
            </button>
          </div>
        </div>

        <!-- ESSAI PANEL -->
        <div v-if="activeTryIdx !== null" class="e01-essai-panel">
          <div class="e01-essai-block">
            <div class="e01-essai-label">Your turn</div>
            <div class="e01-essai-title">Do the {{ currentSound?.name }} sound</div>
          </div>
          <div class="e01-essai-wave">
            <BaseWaveform :bar-count="56" />
          </div>
          <div class="e01-essai-actions">
            <div class="e01-score">
              <div
                class="e01-score-num"
                :class="{ good: score >= 70, mid: score >= 40 && score < 70 }"
              >
                {{ score }}<span>%</span>
              </div>
              <div class="e01-score-label">
                <template v-if="error">⚠ {{ error }}</template>
                <template v-else-if="!isListening">mic off</template>
                <template v-else>{{ currentSound?.name }}</template>
              </div>
            </div>
            <button class="footer-cta" type="button" @click="continueAfterTry">
              Continue →
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <BaseListenSound />
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
        <button class="footer-cta" type="button" @click="goToNext">Skip →</button>
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
  transition: border-color var(--dur-fast), color var(--dur-fast);
  cursor: pointer;
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
.exo-step-dot.curr { background: var(--orange-500); }

.stage { flex: 1; display: flex; min-height: 0; }
.e01-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 24px;
  gap: 12px;
  min-height: 0;
}

.e01-video {
  position: relative;
  flex: 1;
  min-height: 0;
  background: var(--ink-0);
  border: 1px solid var(--line);
  overflow: hidden;
}
.e01-video.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border: none;
}
.e01-video-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  cursor: pointer;
}

.e01-video-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: rgba(5, 5, 6, 0.65);
  backdrop-filter: blur(2px);
  cursor: pointer;
  z-index: 2;
  transition: background-color var(--dur-base);
}
.e01-video-overlay:hover { background: rgba(5, 5, 6, 0.55); }

.e01-big-play {
  width: 96px;
  height: 96px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--brand);
  color: var(--fg-on-orange);
  border: none;
  border-radius: 999px;
  cursor: pointer;
  transition: transform var(--dur-fast) var(--ease-spring), background-color var(--dur-fast);
  box-shadow: var(--shadow-glow);
}
.e01-big-play:hover {
  background: var(--brand-hover);
  transform: scale(1.06);
}
.e01-big-play svg { transform: translateX(3px); }

.e01-big-play-label {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-primary);
}

.e01-video-caption {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-primary);
  z-index: 1;
}
.pill {
  background: var(--brand);
  color: var(--fg-on-orange);
  padding: 4px 8px;
  border-radius: 2px;
  font-weight: 500;
}

.e01-controls {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 6px;
  align-items: center;
  z-index: 1;
}
.e01-icon-btn {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(11, 11, 12, 0.7);
  backdrop-filter: blur(8px);
  color: var(--fg-primary);
  border: 1px solid var(--line);
  border-radius: 4px;
  cursor: pointer;
  transition: border-color var(--dur-fast), background-color var(--dur-fast);
}
.e01-icon-btn:hover { border-color: var(--brand); }
.e01-icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}
.e01-icon-btn.primary {
  width: 48px;
  height: 48px;
  background: var(--brand);
  color: var(--fg-on-orange);
  border-color: var(--brand);
}
.e01-icon-btn.primary:hover { background: var(--brand-hover); }

.ctrl-volume { position: relative; }

.vol-popover {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(11, 11, 12, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid var(--line);
  padding: 12px 8px;
  border-radius: 4px;
  margin-bottom: 0;
  padding-bottom: 16px;
}
.vol-slider {
  writing-mode: vertical-lr;
  direction: rtl;
  width: 4px;
  height: 80px;
  appearance: none;
  background: var(--ink-4);
  cursor: pointer;
}
.vol-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--brand);
  border-radius: 999px;
}
.vol-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: var(--brand);
  border-radius: 999px;
  border: none;
}

.e01-timeline-block { flex-shrink: 0; }
.e01-timeline-label {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
  margin-bottom: 8px;
}
.e01-timeline-label em { font-style: normal; color: var(--fg-primary); }

.e01-phases {
  display: flex;
  gap: 4px;
  width: 100%;
  overflow-x: auto;
}
.e01-phase {
  position: relative;
  background: var(--ink-2);
  border: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--dur-fast), background-color var(--dur-fast);
  min-width: 72px;
}
.e01-phase:hover { border-color: var(--line-hover); }
.e01-phase.done { border-color: var(--line); }

.e01-phase.curr {
  border-color: var(--brand);
  box-shadow: inset 0 0 0 1px var(--brand);
  background: var(--ink-2);
}
.e01-phase.curr .e01-phase-name { color: var(--brand); }

.e01-phase.essai {
  flex: 0 0 auto !important;
  min-width: 64px;
  white-space: nowrap;
}

.e01-phase-name {
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
  line-height: 1;
  margin-bottom: 4px;
  white-space: nowrap;
}
.e01-phase-time {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-mono);
  color: var(--fg-muted);
}
.e01-phase-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--ink-5);
}
.e01-phase-dot.done { background: var(--state-good); }
.e01-phase-dot.curr {
  background: var(--brand);
  box-shadow: 0 0 8px 0 var(--brand);
}

.e01-essai-panel {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 24px;
  align-items: center;
  padding: 16px 20px;
  background: var(--ink-2);
  border: 1px solid var(--brand);
  flex-shrink: 0;
}
.e01-essai-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--brand);
  margin-bottom: 6px;
}
.e01-essai-title {
  font-family: var(--font-display);
  font-size: 22px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
  line-height: var(--lh-tight);
}
.e01-essai-wave {
  width: 280px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.e01-essai-wave :deep(.bars) {
  width: 100%;
  height: 100%;
  justify-content: center;
}
.e01-essai-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.e01-score { text-align: center; min-width: 90px; }
.e01-score-num {
  font-family: var(--font-display);
  font-size: 40px;
  line-height: 1;
  color: var(--state-bad);
  transition: color var(--dur-base);
}
.e01-score-num.mid { color: var(--state-warn); }
.e01-score-num.good { color: var(--state-good); }
.e01-score-num span { font-size: 18px; margin-left: 2px; }
.e01-score-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
  margin-top: 4px;
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