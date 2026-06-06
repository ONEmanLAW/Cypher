<!-- views/ModeSelectView.vue -->
<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useProgressStore, SECTIONS } from '@/stores/progress'

const router = useRouter()
const progress = useProgressStore()

/* ---- progression Académie (réelle, dérivée du store) ---- */
const totalSounds = computed(() =>
  SECTIONS.reduce((sum, s) => sum + s.soundCount, 0)
)
const doneSounds = computed(() =>
  SECTIONS.reduce(
    (sum, s) => sum + s.soundIds.filter((id) => progress.soundState(id) === 'done').length,
    0
  )
)
const academyProgress = computed(() =>
  totalSounds.value ? doneSounds.value / totalSounds.value : 0
)

/* première section débloquée non terminée → "section · …" */
const currentSectionName = computed(() => {
  const s =
    SECTIONS.find((sec) => sec.unlocked && progress.sectionDoneCount(sec.id) < sec.soundCount) ||
    SECTIONS[0]
  return s.name.toLowerCase()
})

/* ---- campagne : placeholder tant que non implémentée ---- */
const campaignLevel = 3
const campaignTotal = 10
const campaignProgress = campaignLevel / campaignTotal

function enterAcademy() {
  router.push('/sections')
}
</script>

<template>
  <main class="mode">
    <!-- HEADER (identique aux autres vues) -->
    <header class="nav">
      <div class="nav-left" />

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
      <h1 class="title">Two spaces.<br />Two intentions.</h1>

      <div class="tiles">
        <!-- ============ ACADEMY ============ -->
        <button class="tile dark" type="button" @click="enterAcademy">
          <div class="tile-title">ACADEMY</div>
          <div class="tile-hook">learn the sounds,<br />one by one.</div>

          <div class="tile-foot">
            <div class="foot-num-wrap">
              <div class="foot-label">global progress</div>
              <div class="foot-num">
                <em>{{ doneSounds }}</em><span class="sep">/{{ totalSounds }}</span>
                <span class="unit">sounds</span>
              </div>
            </div>
            <div class="foot-gauge">
              <div class="foot-track">
                <div class="foot-fill" :style="{ width: academyProgress * 100 + '%' }" />
              </div>
              <div class="foot-bottom">section · {{ currentSectionName }}</div>
            </div>
          </div>
        </button>

        <!-- ============ CAMPAIGN (non cliquable) ============ -->
        <div class="tile light disabled" aria-disabled="true">
          <div class="tile-title">CAMPAIGN</div>
          <div class="tile-hook">put them into practice.<br />play for real.</div>

          <div class="tile-foot">
            <div class="foot-num-wrap">
              <div class="foot-label">level reached</div>
              <div class="foot-num">
                <em>{{ campaignLevel }}</em><span class="sep">/{{ campaignTotal }}</span>
                <span class="unit">battles</span>
              </div>
            </div>
            <div class="foot-gauge">
              <div class="foot-track">
                <div class="foot-fill" :style="{ width: campaignProgress * 100 + '%' }" />
              </div>
              <div class="foot-bottom">next · level {{ campaignLevel + 1 }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.mode {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--surface-stage);
  color: var(--fg-primary);
}

/* ============ NAV (aligné sur SectionSelectView) ============ */
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
  width: 100%;
  max-width: var(--container);
  margin: 0 auto;
  padding: var(--s-12) var(--s-8) var(--s-16);
  display: flex;
  flex-direction: column;
}
.title {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: clamp(40px, 5vw, var(--t-d3));
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  color: var(--fg-primary);
  margin: 0 0 var(--s-10);
}

/* ============ TILES ============ */
.tiles {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--s-6);
}
@media (max-width: 760px) {
  .tiles { grid-template-columns: 1fr; }
}

.tile {
  all: unset;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: clamp(360px, 52vh, 480px);
  padding: var(--s-8);
  cursor: pointer;
  transition: transform var(--dur-fast) var(--ease-out-snap),
              box-shadow var(--dur-base) var(--ease-out-snap),
              border-color var(--dur-base) var(--ease-out-snap);
}
.tile.dark {
  background: var(--ink-2);
  color: var(--fg-primary);
  border: var(--bw-hair) solid var(--ink-2);
}
.tile.light {
  background: var(--surface-inverse);
  color: var(--fg-on-light);
  border: var(--bw-hair) solid var(--surface-inverse);
}
.tile.dark:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
  border-color: var(--orange-500);
}
.tile.dark:active { transform: translateY(0); box-shadow: var(--shadow-press); }
.tile.disabled { cursor: default; }

/* ---- titre ---- */
.tile-title {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: clamp(52px, 6.5vw, 88px);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  text-transform: uppercase;
}
.tile.dark .tile-title  { color: var(--bone-2); }
.tile.light .tile-title { color: var(--ink-1); }

/* ---- hook ---- */
.tile-hook {
  margin-top: var(--s-4);
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: var(--t-h4);
  line-height: var(--lh-snug);
}
.tile.dark .tile-hook  { color: var(--ink-9); }
.tile.light .tile-hook { color: var(--ink-7); }

/* ---- footer ---- */
.tile-foot {
  margin-top: auto;
  display: flex;
  align-items: flex-end;
  gap: var(--s-8);
  padding-top: var(--s-5);
  border-top: var(--bw-hair) solid;
}
.tile.dark .tile-foot  { border-top-color: var(--ink-4); }
.tile.light .tile-foot { border-top-color: var(--bone-4); }

.foot-num-wrap { flex-shrink: 0; }
.foot-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: var(--t-micro);
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  opacity: 0.65;
  margin-bottom: var(--s-2);
}
.foot-num { display: flex; align-items: baseline; gap: 2px; }
.foot-num em {
  font-family: var(--font-display);
  font-style: normal;
  font-size: var(--t-h1);
  line-height: 1;
  color: var(--brand);
}
.foot-num .sep {
  font-family: var(--font-display);
  font-size: var(--t-h1);
  line-height: 1;
  opacity: 0.45;
}
.foot-num .unit {
  font-family: var(--font-mono);
  font-size: var(--t-body-sm);
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  opacity: 0.6;
  margin-left: var(--s-3);
}

.foot-gauge { flex: 1; min-width: 0; }
.foot-track {
  height: var(--bw-md);
  overflow: hidden;
}
.tile.dark .foot-track  { background: var(--ink-4); }
.tile.light .foot-track { background: var(--bone-4); }
.foot-fill {
  height: 100%;
  transition: width var(--dur-slow) var(--ease-out-soft);
}
.tile.dark .foot-fill  { background: var(--orange-500); }
.tile.light .foot-fill { background: var(--ink-1); }

.foot-bottom {
  margin-top: var(--s-3);
  font-family: var(--font-mono);
  font-size: var(--t-meta);
  letter-spacing: var(--ls-mono);
  text-transform: uppercase;
  opacity: 0.6;
}
</style>