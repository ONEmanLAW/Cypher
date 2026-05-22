<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useProgressStore } from '@/stores/progress'

const router = useRouter()
const progress = useProgressStore()

const phases = [
  {
    n: '01',
    name: 'Discovery',
    exos: [
      { id: '01', name: 'Kick Start', desc: 'Find your first sound.' },
    ],
  },
  {
    n: '02',
    name: 'Imitation',
    exos: [
      { id: '02', name: 'Echo Flow', desc: 'Copy what you hear.' },
    ],
  },
  {
    n: '03',
    name: 'Control',
    exos: [
      { id: '03', name: 'Control Mode', desc: 'Master your dynamics.' },
    ],
  },
  {
    n: '04',
    name: 'Timing',
    exos: [
      { id: '04', name: 'Stay in Time', desc: 'Lock onto the tempo.' },
      { id: '05', name: 'Rhythm Copy', desc: 'Repeat short patterns.' },
      { id: '06', name: 'Fill the Beat', desc: 'Add sounds on cue.' },
    ],
  },
]

const STATE_PILL = {
  todo: 'To do',
  start: 'To do',
  current: 'In progress',
  done: 'Done',
}

const STATE_CTA = {
  todo: 'Later',
  start: 'Start',
  current: 'Continue',
  done: 'Review',
}

const resolvedPhases = computed(() => {
  const flat = phases.flatMap((p) => p.exos.map((e) => e.id))
  const firstUndoneId = flat.find((id) => progress.getState(id) !== 'done')

  return phases.map((p) => ({
    ...p,
    exos: p.exos.map((e) => {
      const raw = progress.getState(e.id)
      let state = raw
      if (raw !== 'done' && e.id === firstUndoneId) state = 'start'
      return { ...e, state }
    }),
  }))
})

const allExos = computed(() => resolvedPhases.value.flatMap((p) => p.exos))
const doneCount = computed(() => progress.doneCount)

function goBack() {
  router.back()
}
</script>

<template>
  <main class="home">
    <!-- HEADER -->
    <header class="nav">
      <div class="nav-left">
        <button class="nav-back" type="button" @click="goBack" aria-label="Back">
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path
              d="M6.5 1.5L3 5l3.5 3.5"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="square"
            />
          </svg>
          <span>Back</span>
        </button>
      </div>

      <RouterLink to="/" class="nav-logo">
        <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <path
            d="M14 2.5 A11.5 11.5 0 1 1 14 25.5 A11.5 11.5 0 1 1 14 2.5 Z M14 2.5 L14 6.5"
            stroke="var(--brand)"
            stroke-width="2.5"
            fill="none"
          />
          <circle cx="14" cy="14" r="3" fill="var(--brand)" />
        </svg>
        <span>Cypher</span>
      </RouterLink>

      <div class="nav-right">
        <button class="icon-btn" type="button" aria-label="Settings">
          <svg viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.5" />
            <path
              d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
              stroke="currentColor"
              stroke-width="1.5"
            />
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
      <!-- TOP -->
      <section class="top">
        <div class="top-left">
          <h1 class="top-title">Choose your <em>training.</em></h1>
        </div>

        <div class="top-right">
          <span class="progress-label">Progress</span>
          <div class="progress-num">
            <em>{{ doneCount }}</em><span class="slash">/</span>{{ allExos.length }}
          </div>
          <div class="progress-bar">
            <span
              v-for="exo in allExos"
              :key="exo.id"
              :class="{
                fill: exo.state === 'done',
                curr: exo.state === 'current',
              }"
            />
          </div>
        </div>
      </section>

      <!-- GRID -->
      <section class="grid">
        <div v-for="phase in resolvedPhases" :key="phase.n" class="col">
          <div class="col-head">
            <span class="col-head-num">{{ phase.n }}</span>
            <span class="col-head-name">{{ phase.name }}</span>
          </div>

          <div class="col-body">
            <RouterLink
              v-for="exo in phase.exos"
              :key="exo.id"
              :to="`/exo-${exo.id}`"
              class="card"
              :class="[exo.state, { dense: phase.exos.length > 1 }]"
            >
              <div class="card-top">
                <span class="card-no">exo · {{ exo.id }}</span>
                <span class="state-pill">{{ STATE_PILL[exo.state] }}</span>
              </div>

              <div class="card-name">{{ exo.name }}</div>
              <p class="card-desc">{{ exo.desc }}</p>

              <div class="card-spacer" />

              <div class="card-foot">
                <span class="card-cta">
                  <span>{{ STATE_CTA[exo.state] }}</span>
                  <svg viewBox="0 0 12 12" fill="none">
                    <path
                      d="M2 6h8m-3-3 3 3-3 3"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="square"
                    />
                  </svg>
                </span>
              </div>
            </RouterLink>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.home {
  height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
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
.nav-left { display: flex; align-items: center; }
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
  padding: 18px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.top-left { display: flex; flex-direction: column; gap: 6px; }
.top-title {
  font-family: var(--font-display);
  font-size: 36px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  text-transform: uppercase;
  font-weight: 400;
  color: var(--fg-primary);
  margin: 0;
}
.top-title em { font-style: normal; color: var(--brand); }

.top-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 200px;
}
.progress-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-muted);
}
.progress-num {
  font-family: var(--font-display);
  font-size: 30px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  color: var(--fg-primary);
}
.progress-num em { font-style: normal; color: var(--brand); }
.progress-num .slash { color: var(--ink-5); margin: 0 4px; }

.progress-bar { display: flex; gap: 6px; width: 100%; }
.progress-bar span {
  flex: 1;
  height: 3px;
  background: var(--ink-4);
  transition: background 0.22s ease;
}
.progress-bar span.curr { background: var(--brand); }
.progress-bar span.fill { background: var(--bone-2); }

/* ============ GRID ============ */
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  flex: 1;
  min-height: 0;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}
.col-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
  transition: border-color 0.22s ease;
  flex-shrink: 0;
}
.col-head-num {
  font-family: var(--font-display);
  font-size: 26px;
  line-height: 1;
  color: var(--ink-6);
  transition: color 0.22s ease;
}
.col-head-name {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--fg-primary);
}
.col-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.col:has(.card:hover) .col-head { border-color: var(--brand); }
.col:has(.card:hover) .col-head-num { color: var(--brand); }

/* ============ CARD ============ */
.card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--surface-card);
  border: 1px solid var(--line);
  padding: 14px;
  text-decoration: none;
  color: inherit;
  flex: 1;
  min-height: 0;
  transition:
    border-color 0.22s cubic-bezier(0.2, 0.9, 0.25, 1),
    transform 0.22s cubic-bezier(0.2, 0.9, 0.25, 1);
  overflow: hidden;
}

.card:hover {
  border-color: var(--brand);
  transform: translateY(-2px);
}
.card:hover .card-no { color: var(--brand); }
.card:hover .card-cta { border-color: var(--brand); color: var(--brand); }
.card:hover .card-foot { border-color: var(--brand); }

.card.done .card-no,
.card.done .state-pill {
  color: var(--state-good, #4DD08C);
}
.card.done .state-pill {
  border-color: var(--state-good, #4DD08C);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.card-no {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-muted);
  transition: color 0.22s ease;
}

.state-pill {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  padding: 3px 7px;
  border: 1px solid var(--line);
  color: var(--fg-muted);
}

.card-name {
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1.05;
  letter-spacing: -0.005em;
  text-transform: uppercase;
  color: var(--fg-primary);
  font-weight: 400;
}
.card.dense .card-name { font-size: 17px; }

.card-desc {
  margin: 6px 0 0;
  font-family: var(--font-ui);
  font-size: 12px;
  line-height: 1.4;
  color: var(--fg-muted);
  letter-spacing: -0.005em;
}
.card.dense .card-desc { font-size: 11px; }

.card-spacer { flex: 1; min-height: 8px; }

.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  transition: border-color 0.22s ease;
  flex-shrink: 0;
}

.card-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 11px;
  border: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-primary);
  transition: border-color 0.14s ease, color 0.14s ease, background 0.14s ease;
}
.card-cta svg { width: 11px; height: 11px; }

.card.start .card-cta {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--ink-0);
}
.card.start:hover .card-cta {
  background: var(--orange-400);
  border-color: var(--orange-400);
  color: var(--ink-0);
}

/* ============ RESPONSIVE ============ */
@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .top-title { font-size: 32px; }
}
@media (max-width: 640px) {
  .home { height: auto; overflow-y: auto; }
  .body { overflow: visible; gap: 16px; }
  .top { flex-direction: column; align-items: flex-start; gap: 16px; }
  .top-right { align-items: flex-start; min-width: 0; width: 100%; }
  .top-title { font-size: 30px; }
  .grid { grid-template-columns: 1fr; }
}
</style>