<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useProgressStore, SOUNDS } from '@/stores/progress'

const router = useRouter()
const progress = useProgressStore()

const sounds = computed(() =>
  SOUNDS.map((s) => ({
    ...s,
    exos: progress.doneCountFor(s.id),
    total: progress.allIds.length,
    state: s.unlocked ? progress.soundState(s.id) : 'locked',
  }))
)

const unlockedCount = computed(() => SOUNDS.filter((s) => s.unlocked).length)
const totalCount = computed(() => SOUNDS.length)

const STATE_PILL = {
  done:    'Done',
  current: 'In progress',
  avail:   'Available',
  locked:  'Locked',
}

const STATE_CTA = {
  current: 'Continue',
  avail:   'Start',
}

function selectSound(sound) {
  if (!sound.unlocked) return
  progress.setCurrentSound(sound.id)
  router.push('/exercises')
}

function goBack() {
  router.back()
}
</script>

<template>
  <main class="select">
    <!-- HEADER (identique à ExercisesView) -->
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
          <h1 class="top-title">Choose your <em>sound.</em></h1>
          <p class="top-sub">the basic sounds every beatboxer needs.</p>
        </div>

        <div class="counter">
          <span class="counter-label">Sounds unlocked</span>
          <div class="counter-num">
            <em>{{ unlockedCount }}</em><span class="slash">/</span>{{ totalCount }}
          </div>
        </div>
      </section>

      <section class="grid">
        <button
          v-for="s in sounds"
          :key="s.id"
          type="button"
          class="card"
          :class="[s.state]"
          :disabled="!s.unlocked"
          @click="selectSound(s)"
        >
          <!-- pill état (en haut à droite) -->
          <div class="card-pill-wrap">
            <span class="pill" :class="s.state">
              <span class="pill-dot" />
              {{ STATE_PILL[s.state] }}
            </span>
          </div>

          <!-- vinyle (à droite, partiellement coupé) -->
          <div class="vinyl-wrap">
            <div class="vinyl">
              <div class="vinyl-grooves" />
              <div class="vinyl-center" />
            </div>
          </div>

          <!-- nom + sous-titre -->
          <div class="card-text">
            <div class="card-name">{{ s.name }}</div>
            <div class="card-sub">{{ s.sub }}</div>
          </div>

          <!-- footer -->
          <div class="card-foot">
            <div class="card-exos">
              <span class="card-exos-label">Exos · {{ s.exos }}/{{ s.total }}</span>
              <div class="card-bars">
                <span v-for="i in s.total" :key="i"
                      :class="{ fill: i <= s.exos }" />
              </div>
            </div>

            <span v-if="STATE_CTA[s.state]" class="card-cta">
              <span>{{ STATE_CTA[s.state] }}</span>
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                <path d="M2 6h8m-3-3 3 3-3 3"
                      stroke="currentColor" stroke-width="1.5" stroke-linecap="square" />
              </svg>
            </span>
          </div>
        </button>
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

/* ============ NAV (identique ExercisesView) ============ */
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

/* ============ GRID ============ */
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  flex: 1;
  min-height: 0;
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
  min-height: 0;
  transition:
    border-color var(--dur-base) var(--ease-out-snap),
    transform var(--dur-base) var(--ease-out-snap),
    background-color var(--dur-base) var(--ease-out-snap);
}

.card:disabled,
.card.locked { cursor: not-allowed; }

/* États */
.card.avail,
.card.locked {
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

.card:not(:disabled):hover {
  border-color: var(--brand);
  transform: translateY(-2px);
}
.card.locked { opacity: 0.55; }

/* ============ PILL EN HAUT ============ */
.card-pill-wrap {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
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
.pill.done,
.pill.current {
  background: var(--ink-0);
  color: var(--fg-primary);
  border-color: var(--ink-0);
}
.pill.done .pill-dot { background: var(--state-good); }
.pill.current .pill-dot { background: var(--brand); }
.pill.avail,
.pill.locked {
  background: transparent;
  color: var(--ink-1);
  border-color: var(--ink-1);
}

/* ============ VINYLE (à droite, partiellement coupé comme la maquette) ============ */
.vinyl-wrap {
  position: absolute;
  top: 40%;
  right: -90px;
  transform: translateY(-50%);
  width: 260px;
  height: 260px;
  pointer-events: none;
  z-index: 1;
}
.vinyl {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 999px;
  background: var(--ink-0);
  transition: box-shadow var(--dur-base);
}

/* Rotation au hover */
.card:not(:disabled):hover .vinyl {
  animation: spin 4s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Grooves : cercles concentriques très subtils */
.vinyl-grooves {
  position: absolute;
  inset: 12px;
  border-radius: 999px;
  background:
    repeating-radial-gradient(circle at center,
      rgba(255,255,255,0.04) 0,
      rgba(255,255,255,0.04) 1px,
      transparent 1px,
      transparent 7px);
}
/* Étiquette centrale (le label du vinyle) */
.vinyl-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 90px;
  height: 90px;
  margin: -45px 0 0 -45px;
  border-radius: 999px;
  background: var(--bone-2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.vinyl-center::after {
  content: '';
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: var(--ink-0);
}

/* current : étiquette du vinyle en sombre, trou orange */
.card.current .vinyl-center { background: var(--ink-0); }
.card.current .vinyl-center::after { background: var(--brand); }

/* avail/locked : vinyle reste sombre, étiquette sombre */
.card.avail .vinyl,
.card.locked .vinyl { background: var(--ink-0); }
.card.avail .vinyl-center,
.card.locked .vinyl-center { background: var(--ink-1); }
.card.avail .vinyl-center::after,
.card.locked .vinyl-center::after { background: var(--ink-0); }

/* ============ TEXTE ============ */
.card-text {
  position: relative;
  z-index: 2;
  margin-top: auto;
  max-width: 60%;
}
.card-name {
  font-family: var(--font-display);
  font-size: 36px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.card-sub {
  font-family: var(--font-ui);
  font-style: italic;
  font-size: 13px;
  color: var(--fg-muted);
  line-height: 1.4;
}
.card.avail .card-sub,
.card.locked .card-sub { color: var(--ink-6); }
.card.current .card-sub { color: rgba(11,11,12,0.75); }

/* ============ FOOTER ============ */
.card-foot {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid currentColor;
}
.card.current .card-foot { border-top-color: rgba(11,11,12,0.3); }
.card.avail .card-foot,
.card.locked .card-foot { border-top-color: var(--ink-1); opacity: 0.85; }
.card.done .card-foot { border-top-color: var(--ink-4); }

.card-exos {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card-exos-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: inherit;
  opacity: 0.75;
}
.card-bars {
  display: flex;
  gap: 4px;
}
.card-bars span {
  width: 14px;
  height: 12px;
  border: 1px solid currentColor;
  background: transparent;
}
.card-bars span.fill {
  background: currentColor;
}

.card-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid currentColor;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
}

/* ============ RESPONSIVE ============ */
@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .top-title { font-size: 44px; }
}
@media (max-width: 640px) {
  .select { height: auto; overflow-y: auto; }
  .body { overflow: visible; }
  .top { flex-direction: column; align-items: flex-start; gap: 16px; }
  .counter { align-items: flex-start; }
  .grid { grid-template-columns: 1fr; }
  .top-title { font-size: 32px; }
}
</style>