<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useProgressStore, SECTIONS } from '@/stores/progress'
import { useVinylTransition } from '@/composables/useVinylTransition'

const router = useRouter()
const progress = useProgressStore()
const { go } = useVinylTransition(router)

const sections = computed(() => {
  let prevDone = true // 1ʳᵉ section toujours ouverte

  return SECTIONS.map((s) => {
    const masteredSounds = progress.sectionDoneCount(s.id)
    const startedExos = s.soundIds.reduce((n, id) => n + progress.doneCountFor(id), 0)
    const isComplete = s.soundCount > 0 && masteredSounds === s.soundCount

    const unlocked = prevDone
    let state
    if (!unlocked) state = 'locked'
    else if (isComplete) state = 'done'        // terminé → sombre
    else if (startedExos > 0) state = 'current' // commencé → orange
    else state = 'avail'                        // dispo, non touché → blanc

    prevDone = isComplete // la suivante n'ouvre que si celle-ci est finie

    return {
      ...s,
      state,
      clickable: unlocked && s.soundIds.length > 0,
      done: masteredSounds,
      total: s.soundCount,
    }
  })
})

const completedCount = computed(() => sections.value.filter((s) => s.state === 'done').length)
const totalCount = SECTIONS.length

const STATE_PILL = {
  done:    'Done',
  current: 'In progress',
  avail:   'Available',
  locked:  'Locked',
}

/* Pilote la vitesse du vinyle sans saut : on change le playbackRate de
   l'animation en cours, qui continue depuis l'angle courant. */
function setVinylSpeed(e, rate) {
  if (e.currentTarget.disabled) return
  const anim = e.currentTarget.querySelector('.vinyl')?.getAnimations?.()[0]
  if (anim) anim.playbackRate = rate
}

function selectSection(s) {
  if (!s.clickable) return
  progress.setCurrentSection(s.id)
  go('/sounds')
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <main class="select">
    <!-- HEADER -->
    <header class="nav">
      <div class="nav-left">
        <button class="nav-back" type="button" @click="goBack">
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M6.5 1.5L3 5l3.5 3.5" stroke="currentColor"
                  stroke-width="1.5" stroke-linecap="square" />
          </svg>
          <span>Back</span>
        </button>
      </div>

      <RouterLink to="/" class="nav-logo">
        <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
          <path d="M14 2.5 A11.5 11.5 0 1 1 14 25.5 A11.5 11.5 0 1 1 14 2.5 Z M14 2.5 L14 6.5"
                stroke="var(--brand)" stroke-width="2.5" fill="none" />
          <circle cx="14" cy="14" r="3" fill="var(--brand)" />
        </svg>
        <span>Cypher</span>
      </RouterLink>

      <div class="nav-right">
        <button class="icon-btn" type="button" aria-label="Settings">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.5" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
                  stroke="currentColor" stroke-width="1.5" />
          </svg>
        </button>
        <button class="icon-btn" type="button" aria-label="Profile">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5" />
            <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke="currentColor" stroke-width="1.5" />
          </svg>
        </button>
      </div>
    </header>

    <!-- BODY -->
    <div class="body">
      <section class="top">
        <div class="top-left">
          <h1 class="top-title">Choose your <em>section.</em></h1>
          <p class="top-sub">8 chapters to become a beatboxer.</p>
        </div>

        <div class="counter">
          <span class="counter-label">Sections completed</span>
          <div class="counter-num">
            <em>{{ completedCount }}</em><span class="slash">/</span>{{ totalCount }}
          </div>
        </div>
      </section>

      <section class="grid-wrap">
        <section class="grid">
          <button
            v-for="s in sections"
            :key="s.id"
            type="button"
            class="card"
            :class="[s.state]"
            :disabled="!s.clickable"
            @click="selectSection(s)"
            @mouseenter="setVinylSpeed($event, 3.2)"
            @mouseleave="setVinylSpeed($event, 1)"
          >
            <!-- VINYLE -->
            <div class="vinyl">
              <div class="vinyl-grooves" />
              <div class="vinyl-shine" />
              <div class="vinyl-center"><div class="vinyl-hole" /></div>
            </div>

            <!-- PILL -->
            <div class="card-pill-wrap">
              <span class="pill" :class="s.state">
                <svg v-if="s.state === 'locked'" class="pill-lock" viewBox="0 0 24 24" fill="none">
                  <rect x="5" y="11" width="14" height="9" rx="1" stroke="currentColor" stroke-width="2.5" />
                  <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2.5" />
                </svg>
                <span v-else class="pill-dot" />
                {{ STATE_PILL[s.state] }}
              </span>
            </div>

            <!-- TEXTE -->
            <div class="card-text">
              <div class="card-num">Section · {{ s.number }}</div>
              <div class="card-name">{{ s.name }}</div>
            </div>

            <!-- FOOTER -->
            <div class="card-foot">
              <div class="card-exos">
                <span class="card-exos-label">Sounds · {{ s.done }}/{{ s.total }}</span>
                <div class="card-bars">
                  <span v-for="i in s.total" :key="i" :class="{ fill: i <= s.done }" />
                </div>
              </div>
            </div>
          </button>
        </section>
      </section>
    </div>
  </main>
</template>

<style scoped>
.select {
  height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-stage);
  overflow: hidden;
}

/* ============ NAV ============ */
.nav {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid var(--line);
  background: var(--ink-0);
  flex-shrink: 0;
}
.nav-left { display: flex; align-items: center; gap: 16px; }
.nav-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-primary);
  background: transparent;
  cursor: pointer;
  transition: border-color 0.14s ease, color 0.14s ease;
}
.nav-back:hover { border-color: var(--brand); color: var(--brand); }

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--fg-primary);
  text-decoration: none;
}

.nav-right { display: flex; justify-content: flex-end; gap: 8px; }
.icon-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--line);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-primary);
  background: transparent;
  cursor: pointer;
  transition: border-color 0.14s ease, color 0.14s ease;
}
.icon-btn:hover { border-color: var(--brand); color: var(--brand); }
.icon-btn svg { width: 14px; height: 14px; }

/* ============ BODY ============ */
.body {
  flex: 1;
  min-height: 0;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.top-title {
  font-family: var(--font-display);
  font-size: 56px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  text-transform: uppercase;
  font-weight: 400;
  color: var(--fg-primary);
  margin: 0;
}
.top-title em { font-style: normal; color: var(--brand); }
.top-sub {
  margin: 8px 0 0;
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--fg-muted);
}

.counter {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 200px;
}
.counter-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-muted);
}
.counter-num {
  font-family: var(--font-display);
  font-size: 40px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  color: var(--fg-primary);
}
.counter-num em { font-style: normal; color: var(--brand); }
.counter-num .slash { color: var(--ink-5); margin: 0 4px; }

/* ============ GRID (4 colonnes) ============ */
.grid-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;
}

/* ============ CARD ============ */
.card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 24px;
  text-align: left;
  background: var(--ink-2);
  border: 1px solid var(--line);
  color: var(--fg-primary);
  cursor: pointer;
  overflow: hidden;
  height: clamp(230px, 33vh, 300px);
  transition:
    border-color var(--dur-base) var(--ease-out-snap),
    transform var(--dur-base) var(--ease-out-snap),
    background-color var(--dur-base) var(--ease-out-snap);
}
.card:disabled { cursor: not-allowed; }

.card.avail {
  background: var(--bone-2);
  color: var(--ink-1);
  border-color: var(--bone-4);
}
.card.done {
  background: var(--ink-2);
  color: var(--fg-primary);
}
.card.current {
  background: var(--brand);
  color: var(--fg-on-orange);
  border-color: var(--brand);
}

/* --- Carte verrouillée : éteinte, vinyle figé --- */
.card.locked {
  background: var(--ink-2);
  color: var(--fg-muted);
  border-color: var(--line);
}
.card.locked .card-name { color: var(--ink-6); }
.card.locked .card-num  { opacity: 0.45; }
.card.locked .vinyl {
  opacity: 0.2;
  filter: grayscale(1);
  animation: none; /* pas de rotation tant que verrouillé */
}
.card.locked .card-foot { border-top-color: var(--ink-4); opacity: 0.6; }

.card:not(:disabled):hover {
  border-color: var(--brand);
  transform: translateY(-2px);
}

/* ============ PILL ============ */
.card-pill-wrap {
  position: relative;
  z-index: 3;
  display: flex;
  justify-content: flex-start;
  margin-bottom: 16px;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border: 1px solid currentColor;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
}
.pill-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
}
.pill-lock { width: 9px; height: 9px; }
.pill.done,
.pill.current {
  background: var(--ink-0);
  color: var(--fg-primary);
  border-color: var(--ink-0);
}
.pill.done .pill-dot    { background: var(--state-good); }
.pill.current .pill-dot { background: var(--brand); }
.pill.avail {
  background: transparent;
  color: var(--ink-1);
  border-color: var(--ink-1);
}
.pill.locked {
  background: transparent;
  color: var(--fg-muted);
  border-color: var(--line);
}

/* ============ NUM ============ */
.card-num {
  position: relative;
  z-index: 2;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 6px;
}
.card.current .card-num { opacity: 0.85; }

/* ============ VINYLE ============ */
.vinyl {
  position: absolute;
  top: 50%;
  right: -35%;
  width: 75%;
  aspect-ratio: 1 / 1;
  border-radius: 999px;
  background: var(--ink-0);
  pointer-events: none;
  z-index: 0;
  transform: translateY(-50%);
  animation: vinyl-spin 8s linear infinite;
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.04),
    inset 0 0 40px rgba(0,0,0,0.6);
}
@keyframes vinyl-spin {
  from { transform: translateY(-50%) rotate(0deg); }
  to   { transform: translateY(-50%) rotate(360deg); }
}
/* La vitesse est gérée via playbackRate en JS (pas de saut). */

.vinyl-grooves {
  position: absolute;
  inset: 6%;
  border-radius: 999px;
  background:
    repeating-radial-gradient(circle at center,
      rgba(255,255,255,0.07) 0,
      rgba(255,255,255,0.07) 1px,
      transparent 1px,
      transparent 6px);
}
.vinyl-shine {
  position: absolute;
  inset: 6%;
  border-radius: 999px;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    rgba(255,255,255,0.12) 30deg,
    transparent 80deg,
    transparent 180deg,
    rgba(255,255,255,0.06) 210deg,
    transparent 260deg,
    transparent 360deg
  );
  mix-blend-mode: screen;
  pointer-events: none;
}
.vinyl-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 32%;
  aspect-ratio: 1 / 1;
  transform: translate(-50%, -50%);
  border-radius: 999px;
  background: var(--bone-2);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    inset 0 0 0 1px rgba(0,0,0,0.15),
    0 0 0 1px rgba(0,0,0,0.3);
}
.vinyl-hole {
  width: 12%;
  aspect-ratio: 1 / 1;
  border-radius: 999px;
  background: var(--bone-0);
  box-shadow:
    0 0 0 2px var(--ink-0),
    0 0 0 3px rgba(0,0,0,0.6);
}

/* === Variante orange (en cours) === */
.card.current .vinyl-center {
  background: var(--ink-0);
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.1),
    0 0 0 1px rgba(255,255,255,0.15);
}
.card.current .vinyl-hole {
  background: var(--brand);
  box-shadow:
    0 0 0 2px var(--ink-0),
    0 0 0 3px rgba(0,0,0,0.6);
}

/* === Variante blanche (non commencé) === */
.card.avail .vinyl-center {
  background: var(--ink-1);
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.08),
    0 0 0 1px rgba(255,255,255,0.1);
}
.card.avail .vinyl-hole {
  background: var(--bone-0);
  box-shadow:
    0 0 0 2px var(--ink-0),
    0 0 0 3px rgba(255,255,255,0.1);
}

/* ============ TEXTE ============ */
.card-text {
  position: relative;
  z-index: 2;
  margin-top: auto;
  max-width: 60%;
}
.card-name {
  font-family: var(--font-display);
  font-size: 30px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
}

/* ============ FOOTER ============ */
.card-foot {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 16px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid currentColor;
  max-width: 60%;
}
.card.current .card-foot { border-top-color: rgba(11,11,12,0.3); }
.card.avail .card-foot { border-top-color: var(--ink-1); opacity: 0.85; }
.card.done .card-foot { border-top-color: var(--ink-4); }

.card-exos { display: flex; flex-direction: column; gap: 6px; }
.card-exos-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: inherit;
  opacity: 0.75;
}
.card-bars { display: flex; gap: 4px; }
.card-bars span {
  width: 14px;
  height: 12px;
  border: 1px solid currentColor;
  background: transparent;
}
.card-bars span.fill { background: currentColor; }

/* ============ RESPONSIVE ============ */
@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .top-title { font-size: 44px; }
  .card { height: clamp(240px, 36vh, 320px); }
}
@media (max-width: 640px) {
  .select { height: auto; overflow: visible; }
  .body { overflow: visible; }
  .grid-wrap { align-items: stretch; }
  .top { flex-direction: column; align-items: flex-start; gap: 16px; }
  .counter { align-items: flex-start; }
  .grid { grid-template-columns: 1fr; }
  .card { height: auto; min-height: 240px; }
  .top-title { font-size: 32px; }
  .vinyl { width: 70%; right: -30%; }
}
</style>