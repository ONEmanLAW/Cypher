<!-- views/CampaignView.vue -->
<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()

/* ---------------------------------------------------------------
   Placeholder — campagne pas encore branchée au store.
   Tout est verrouillé après le niveau 1.
   --------------------------------------------------------------- */
const RAW_SECTIONS = [
  {
    id: 'fundamentals', number: '01', title: 'Fundamentals', tag: 'current',
    levels: [
      { n: 1, name: 'First Beat',  state: 'current' },
      { n: 2, name: 'Two-Step',    state: 'locked' },
      { n: 3, name: 'Hi-Hat Roll', state: 'locked' },
      { n: 4, name: 'Clean Snare', state: 'locked' },
    ],
  },
  {
    id: 'battle', number: '02', title: 'Battle rounds', tag: 'locked',
    levels: [
      { n: 5, name: 'Bass Drop',   state: 'locked' },
      { n: 6, name: 'Double Kick', state: 'locked' },
      { n: 7, name: 'Crowd Check', state: 'locked' },
    ],
  },
  {
    id: 'champ', number: '03', title: 'Championship', tag: 'locked',
    levels: [
      { n: 8,  name: 'Semi-Final',    state: 'locked' },
      { n: 9,  name: 'Final',         state: 'locked' },
      { n: 10, name: 'Grand Beatbox', state: 'locked' },
    ],
  },
]

/* serpentin : alternance gauche/droite continue entre sections */
let i = 0
const sections = RAW_SECTIONS.map((sec) => ({
  ...sec,
  levels: sec.levels.map((l) => ({ ...l, side: i++ % 2 === 0 ? 'l' : 'r' })),
}))

const allLevels = computed(() => sections.flatMap((s) => s.levels))
const total = computed(() => allLevels.value.length)
const reached = computed(() => allLevels.value.filter((l) => l.state === 'done').length)

/* section courante = celle qui contient le niveau "current" */
const currentSection = computed(
  () => sections.find((s) => s.levels.some((l) => l.state === 'current')) || sections[0]
)

function goBack() {
  router.push('/')
}
</script>

<template>
  <main class="campaign">
    <!-- HEADER (aligné sur SectionSelectView) -->
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

    <!-- SCROLLER -->
    <div class="scroll">
      <div class="inner">
        <!-- TOP (typo identique à la sélection) -->
        <section class="top">
          <div class="top-left">
            <h1 class="top-title">The <em>campaign.</em></h1>
            <p class="top-sub">Put your sounds into practice. Play for real.</p>
          </div>
          <div class="counter">
            <span class="counter-label">Levels reached</span>
            <div class="counter-num">
              <em>{{ reached }}</em><span class="slash">/</span>{{ total }}
            </div>
          </div>
        </section>

        <!-- BANNER compact : nom de section seul -->
        <section class="banner">
          <span class="banner-label">Current section</span>
          <span class="banner-name">{{ currentSection.title }}</span>
        </section>

        <!-- MAP -->
        <section class="map">
          <div class="spine" />

          <template v-for="sec in sections" :key="sec.id">
            <div class="sec" :class="{ locked: sec.tag === 'locked' }">
              <span class="sec-line" />
              <div class="sec-mid">
                <div class="sec-eyebrow">
                  Section · {{ sec.number }}
                  <span class="tag" :class="sec.tag">{{ sec.tag }}</span>
                </div>
                <div class="sec-title">{{ sec.title }}</div>
              </div>
              <span class="sec-line" />
            </div>

            <div
              v-for="l in sec.levels"
              :key="l.n"
              class="row"
              :class="l.side === 'l' ? 'row--l' : 'row--r'"
            >
              <span class="connector" />
              <div class="node" :class="l.state">
                <span class="num" v-if="l.state !== 'locked'">{{ l.n }}</span>
                <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <rect x="5" y="11" width="14" height="9" rx="1"
                        stroke="currentColor" stroke-width="2" />
                  <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2" />
                </svg>

                <div class="label">
                  <div class="label-no">Level · {{ String(l.n).padStart(2, '0') }}</div>
                  <div class="label-name">{{ l.name }}</div>
                </div>

                <span class="start" v-if="l.state === 'current'">Start</span>
              </div>
            </div>
          </template>

          <div class="foot">— more rounds coming soon —</div>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }

.campaign {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--surface-stage);
  color: var(--fg-primary);
}

/* ============ NAV (copie SectionSelectView) ============ */
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

/* ============ SCROLLER + scrollbar DA ============ */
.scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  scrollbar-width: thin;
  scrollbar-color: var(--ink-4) var(--ink-1);
}
.scroll::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: var(--grain-overlay);
  opacity: 0.28;
  mix-blend-mode: overlay;
  pointer-events: none;
  z-index: 5;
}
.scroll::-webkit-scrollbar { width: 12px; }
.scroll::-webkit-scrollbar-track {
  background: var(--ink-1);
  border-left: 1px solid var(--ink-4);
}
.scroll::-webkit-scrollbar-thumb {
  background: var(--ink-4);
  border: 3px solid var(--ink-1);
}
.scroll::-webkit-scrollbar-thumb:hover { background: var(--orange-500); }
.scroll::-webkit-scrollbar-thumb:active { background: var(--orange-600); }

.inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 32px 96px;
}

/* ============ TOP (typo = sélection) ============ */
.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
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

/* ============ BANNER compact ============ */
.banner {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding: 12px 18px;
  background: var(--surface-card);
  border: 1px solid var(--ink-4);
  border-left: 4px solid var(--orange-500);
}
.banner-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--fg-muted);
}
.banner-name {
  font-family: var(--font-display);
  font-size: 24px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--bone-2);
}

/* ============ MAP — spine + serpentin ============ */
.map {
  position: relative;
  max-width: 600px;
  margin: 48px auto 0;
}
.spine {
  position: absolute;
  top: 0; bottom: 80px;
  left: 50%;
  width: 2px;
  transform: translateX(-1px);
  background: repeating-linear-gradient(
    to bottom,
    var(--ink-4) 0 8px,
    transparent 8px 16px
  );
  z-index: 0;
}

/* en-tête de section */
.sec {
  position: relative;
  display: flex;
  align-items: center;
  gap: 28px;
  margin: 40px 0 24px;
  z-index: 2;
}
.sec-line { flex: 1; height: 1px; background: var(--ink-4); }
.sec.locked .sec-line { background: none; border-top: 1px dashed var(--ink-5); }
.sec-mid {
  text-align: center;
  background: var(--ink-1);
  padding: 2px 22px;
}
.sec-eyebrow {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.26em;
  text-transform: uppercase;
  color: var(--fg-muted);
  margin-bottom: 7px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}
.sec-eyebrow .tag {
  border: 1px solid currentColor;
  padding: 2px 6px;
  letter-spacing: 0.18em;
}
.sec-eyebrow .tag.current { color: var(--orange-500); border-color: var(--orange-500); }
.sec-eyebrow .tag.locked  { color: var(--ink-6); }
.sec-title {
  font-family: var(--font-display);
  font-size: 30px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--bone-2);
}
.sec.locked .sec-eyebrow,
.sec.locked .sec-title { color: var(--ink-6); }

/* rangée niveau */
.row {
  position: relative;
  height: 168px;
  z-index: 1;
}
.connector {
  position: absolute;
  top: 50%;
  height: 2px;
  background: var(--ink-4);
  transform: translateY(-1px);
  z-index: 0;
}
.row--l .connector { left: 25%; right: 50%; }
.row--r .connector { left: 50%; right: 25%; }

/* nœud */
.node {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  line-height: 1;
  z-index: 2;
}
.row--l .node { left: 25%; }
.row--r .node { left: 75%; }

.node.done {
  width: 84px; height: 84px;
  background: var(--bone-2);
  color: var(--ink-0);
  font-size: 40px;
  box-shadow: 4px 4px 0 var(--ink-0);
}
.node.current {
  width: 120px; height: 120px;
  background: var(--orange-500);
  color: var(--ink-0);
  font-size: 56px;
  box-shadow: 0 0 0 2px var(--orange-500), 0 0 40px 2px rgba(255,107,26,0.45);
  animation: cmpPulse 2.6s var(--ease-out-soft) infinite;
  cursor: pointer;
}
.node.locked {
  width: 80px; height: 80px;
  background: transparent;
  border: 2px dashed var(--ink-6);
  color: var(--ink-7);
}
@keyframes cmpPulse {
  0%, 100% { box-shadow: 0 0 0 2px var(--orange-500), 0 0 0 0 rgba(255,107,26,0.5); }
  50%      { box-shadow: 0 0 0 2px var(--orange-500), 0 0 0 20px rgba(255,107,26,0); }
}
.num { display: block; padding-top: 4px; }

/* étiquette sous le nœud */
.label {
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%);
  margin-top: 14px;
  width: 200px;
  text-align: center;
  pointer-events: none;
}
.label-no {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
  margin-bottom: 5px;
}
.label-name {
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--bone-2);
}
.node.current .label-no { color: var(--orange-500); }
.node.locked .label-no,
.node.locked .label-name { color: var(--ink-6); }

/* tag START sur le nœud courant */
.start {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 12px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--ink-1);
  background: var(--accent-lime);
  padding: 5px 9px;
  white-space: nowrap;
}

.foot {
  text-align: center;
  margin-top: 48px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--ink-6);
}

@media (prefers-reduced-motion: reduce) {
  .node.current { animation: none; }
}

@media (max-width: 760px) {
  .top { flex-direction: column; align-items: flex-start; gap: 16px; }
  .counter { align-items: flex-start; }
  .top-title { font-size: 38px; }
}
</style>