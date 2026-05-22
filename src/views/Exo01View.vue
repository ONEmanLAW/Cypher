<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import BaseWaveform from '@/components/ui/BaseWaveform.vue'
import { useProgressStore } from '@/stores/progress'

const router = useRouter()
const progress = useProgressStore()
const currentSound = computed(() => progress.currentSound)

/* ============================================================
   PHASES — mappées sur le temps réel de la vidéo (51s)
   ============================================================ */
const phases = ref([
  { name: 'Intro',     start: 0,    end: 8,    essai: false },
  { name: 'Demo',      start: 8,    end: 18,   essai: false },
  { name: 'Technique', start: 18,   end: 28,   essai: false },
  { name: 'Try 1',     start: 28,   end: 34,   essai: true  },
  { name: 'Try 2',     start: 34,   end: 40,   essai: true  },
  { name: 'Try 3',     start: 40,   end: 46,   essai: true  },
  { name: 'Recap',     start: 46,   end: 51,   essai: false },
])

const VIDEO_SRC = '/videos/kick-drum-demo.mov'

/* ============================================================
   STATE
   ============================================================ */
const videoRef = ref(null)
const containerRef = ref(null)

const currentTime = ref(0)
const duration = ref(51)
const isPlaying = ref(false)
const hasStarted = ref(false)
const isFullscreen = ref(false)
const volume = ref(0.8)
const muted = ref(false)
const showVolume = ref(false)

const visitedPhases = ref(new Set([0]))
const validatedTries = ref(new Set())
const activeTryIdx = ref(null)
const tryFeedback = ref(null)

/* ============================================================
   COMPUTED
   ============================================================ */
const currentPhaseIdx = computed(() =>
  phases.value.findIndex(p => currentTime.value >= p.start && currentTime.value < p.end)
)

const phasesWithLayout = computed(() =>
  phases.value.map((p, i) => {
    const width = ((p.end - p.start) / duration.value) * 100
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

  const phase = phases.value[idx]
  if (phase && phase.essai && !validatedTries.value.has(idx) && activeTryIdx.value !== idx) {
    triggerTryStop(idx)
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
   FULLSCREEN
   ============================================================ */
async function toggleFullscreen() {
  if (!containerRef.value) return
  if (!document.fullscreenElement) {
    await containerRef.value.requestFullscreen()
  } else {
    await document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

/* ============================================================
   TRY FLOW
   ============================================================ */
async function exitFullscreenIfNeeded() {
  if (document.fullscreenElement) {
    try {
      await document.exitFullscreen()
    } catch (e) {
      console.warn('exitFullscreen failed:', e)
    }
  }
}

async function triggerTryStop(idx) {
  await exitFullscreenIfNeeded()
  if (videoRef.value) videoRef.value.pause()
  activeTryIdx.value = idx
  tryFeedback.value = null
}

function validateTry() {
  if (activeTryIdx.value === null) return
  validatedTries.value.add(activeTryIdx.value)
  tryFeedback.value = 'good'
}

function continueAfterTry() {
  if (activeTryIdx.value === null) return
  validatedTries.value.add(activeTryIdx.value)
  activeTryIdx.value = null
  tryFeedback.value = null
  if (videoRef.value) videoRef.value.play()
}

/* ============================================================
   TIMELINE NAVIGATION
   ============================================================ */
function goToPhase(idx) {
  if (!visitedPhases.value.has(idx)) return
  if (!videoRef.value) return
  videoRef.value.currentTime = phases.value[idx].start
  const phase = phases.value[idx]
  if (phase.essai) {
    triggerTryStop(idx)
  } else {
    activeTryIdx.value = null
    videoRef.value.play()
  }
}

/* ============================================================
   LIFECYCLE
   ============================================================ */
onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
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
              :class="['e01-phase', p.state, { locked: !visitedPhases.has(p.idx), essai: p.essai }]"
              :style="{ flexBasis: p.width + '%' }"
              :disabled="!visitedPhases.has(p.idx)"
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
            <div class="e01-essai-title">Do the kick sound</div>
          </div>
          <div class="e01-essai-wave">
            <BaseWaveform :bar-count="56" />
          </div>
          <div class="e01-essai-actions">
            <div v-if="tryFeedback === 'good'" class="e01-feedback good">Pretty good</div>
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
.e01-video.fullscreen { border: none; }
.e01-video-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  cursor: pointer;
}

/* ===== Big play overlay (avant le premier lancement) ===== */
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

/* ===== Volume control · fix hover gap ===== */
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
  /* padding-bottom crée l'espace visuel SANS trou hover */
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
}
.e01-phase {
  position: relative;
  background: var(--ink-2);
  border: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--dur-fast), background-color var(--dur-fast);
  min-width: 0;
}
.e01-phase:hover:not(:disabled) { border-color: var(--line-hover); }
.e01-phase.locked,
.e01-phase:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.e01-phase.done { border-color: var(--line); }
.e01-phase.curr {
  background: var(--brand);
  border-color: var(--brand);
}
.e01-phase.curr .e01-phase-name,
.e01-phase.curr .e01-phase-time { color: var(--fg-on-orange); }

.e01-phase-name {
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
  line-height: 1;
  margin-bottom: 4px;
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
  background: var(--bone-0);
  box-shadow: 0 0 8px 0 var(--bone-0);
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
.e01-feedback {
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  padding: 6px 12px;
  border-radius: 2px;
}
.e01-feedback.good {
  background: var(--state-good);
  color: var(--ink-0);
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
  cursor: pointer;
  transition: background-color var(--dur-fast);
}
.footer-cta:hover { background: var(--brand-hover); }
</style>