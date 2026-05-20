<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const phases = [
  {
    n: '01',
    name: 'Discovery',
    exos: [{ id: '01', name: 'Kick Start', state: 'start' }],
  },
  {
    n: '02',
    name: 'Imitation',
    exos: [{ id: '02', name: 'Echo Flow', state: 'todo' }],
  },
  {
    n: '03',
    name: 'Control',
    exos: [{ id: '03', name: 'Control Mode', state: 'todo' }],
  },
  {
    n: '04',
    name: 'Timing',
    exos: [
      { id: '04', name: 'Stay in Time', state: 'todo' },
      { id: '05', name: 'Rhythm Copy', state: 'todo' },
      { id: '06', name: 'Fill the Beat', state: 'todo' },
    ],
  },
]

const STATE_PILL = {
  todo: 'To do',
  next: 'Next',
  start: 'To do',
  current: 'In progress',
  done: 'Done',
}

const STATE_CTA = {
  todo: 'Later',
  next: 'Start',
  start: 'Start',
  current: 'Continue',
  done: 'Review',
}

const allExos = computed(() => phases.flatMap((p) => p.exos))
const doneCount = computed(() => allExos.value.filter((e) => e.state === 'done').length)
</script>

<template>
  <main class="home">
    <!-- TOP -->
    <section class="top">
      <div class="top-left">
        <span class="top-eyebrow">Sound · Kick</span>
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
              curr: ['start', 'next', 'current'].includes(exo.state),
            }"
          />
        </div>
      </div>
    </section>

    <!-- GRID -->
    <section class="grid">
      <div v-for="phase in phases" :key="phase.n" class="col">
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
  </main>
</template>

<style scoped>
/* Override here if your header is taller/shorter */
.home {
  --header-h: 64px;

  height: calc(100dvh - var(--header-h));
  width: 100%;
  padding: 20px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

/* ============ TOP ============ */
.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.top-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.top-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--brand);
}
.top-eyebrow::before {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--brand);
  display: inline-block;
}

.top-title {
  font-family: var(--font-display);
  font-size: 40px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  text-transform: uppercase;
  font-weight: 400;
  color: var(--fg-primary);
}
.top-title em {
  font-style: normal;
  color: var(--brand);
}

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
  font-size: 32px;
  line-height: 0.92;
  letter-spacing: -0.02em;
  color: var(--fg-primary);
}
.progress-num em {
  font-style: normal;
  color: var(--brand);
}
.progress-num .slash {
  color: var(--ink-5);
  margin: 0 4px;
}

.progress-bar {
  display: flex;
  gap: 6px;
  width: 100%;
}
.progress-bar span {
  flex: 1;
  height: 3px;
  background: var(--ink-4);
  transition: background 0.22s ease;
}
.progress-bar span.curr {
  background: var(--brand);
}
.progress-bar span.fill {
  background: var(--bone-2);
}

/* ============ GRID ============ */
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  flex: 1;
  min-height: 0;
}

/* ============ COLUMN ============ */
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
  font-size: 28px;
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

.col:has(.card:hover) .col-head {
  border-color: var(--brand);
}
.col:has(.card:hover) .col-head-num {
  color: var(--brand);
}

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

.card.start {
  border-color: var(--brand);
}
.card.start::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--brand);
}

.card:hover {
  border-color: var(--brand);
  transform: translateY(-2px);
}
.card:hover .card-no {
  color: var(--brand);
}
.card:hover .card-cta {
  border-color: var(--brand);
  color: var(--brand);
}
.card:hover .card-foot {
  border-color: var(--brand);
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
.card.start .card-no {
  color: var(--brand);
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
.card.start .state-pill {
  border-color: var(--brand);
  color: var(--brand);
}

.card-name {
  font-family: var(--font-display);
  font-size: 24px;
  line-height: 1.05;
  letter-spacing: -0.005em;
  text-transform: uppercase;
  color: var(--fg-primary);
  font-weight: 400;
}
.card.dense .card-name {
  font-size: 18px;
}

.card-spacer {
  flex: 1;
  min-height: 8px;
}

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
  transition:
    border-color 0.14s ease,
    color 0.14s ease,
    background 0.14s ease;
}
.card-cta svg {
  width: 11px;
  height: 11px;
}
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
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .top-title {
    font-size: 36px;
  }
}
@media (max-width: 640px) {
  .home {
    height: auto;
    padding: 16px 20px;
    gap: 16px;
    overflow-y: auto;
  }
  .top {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .top-right {
    align-items: flex-start;
    min-width: 0;
    width: 100%;
  }
  .top-title {
    font-size: 32px;
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>