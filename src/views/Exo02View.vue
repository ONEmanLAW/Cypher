<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const target = 10
const current = 7
const segs = Array.from({ length: target }, (_, i) => i < current)
const objectifs = ['×1', '×3', '×5', '×10', '×20']

// barres waveform : hauteur de base déterministe + délai pour l'anim
let s = 31
const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280 }
const waveBars = Array.from({ length: 48 }, (_, i) => ({
  base: Math.round((0.2 + rnd() * 0.8) * 48),
  delay: (i * 40) % 1200,
}))
</script>

<template>
  <div class="exo">
    <!-- header -->
    <header class="exo-header">
      <div class="exo-header-side">
        <button class="exo-back" type="button" @click="router.push('/')">
          ← Retour
        </button>
        <span class="exo-header-num">Son · <em>Kick Drum</em></span>
      </div>
      <div class="exo-header-title">
        <div class="kicker">Exo 02 · Académie</div>
        <div class="name">Écho · Série d'habitudes</div>
      </div>
      <div class="exo-header-side right">
        <span class="exo-step">
          Étape <em>2/4</em> · Imitation
          <span class="exo-step-dots">
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
        <!-- objectif -->
        <div class="e02-objectif-row">
          <span class="mono-label">Objectif</span>
          <div class="chip-row">
            <button
              v-for="v in objectifs"
              :key="v"
              :class="['chip', { active: v === '×10' }]"
              type="button"
            >
              {{ v }}
            </button>
          </div>
          <div style="flex: 1" />
          <span class="mono-label">Tentative <em>01</em></span>
        </div>

        <!-- compteur + jauge + feedback -->
        <div class="e02-center">
          <div class="mono-label" style="letter-spacing: 0.4em">— Répète le son —</div>
          <div class="e02-counter">
            <span class="cur">07</span>
            <span class="sep">/</span>
            <span class="tgt">10</span>
          </div>
          <div class="e02-bar">
            <div
              v-for="(on, i) in segs"
              :key="i"
              :class="['e02-bar-seg', { fill: on }]"
            />
          </div>
          <div class="e02-feedback">
            <div class="waveform">
              <span
                v-for="(b, i) in waveBars"
                :key="i"
                :style="{ height: b.base + 'px', animationDelay: b.delay + 'ms' }"
              />
            </div>
            <div class="e02-streak-badge">Good streak · ×5 d'affilée</div>
          </div>
        </div>
      </div>
    </div>

    <!-- footer -->
    <footer class="exo-footer">
      <div class="exo-footer-actions">
        <button class="footer-btn" type="button">↺ Revoir la démo</button>
        <button class="footer-btn" type="button">♪ Écouter le son</button>
        <button class="footer-btn" type="button">ⓘ Tips</button>
      </div>
      <div class="exo-footer-info">session · <em>kick drum</em> · <em>×10</em></div>
      <div class="exo-footer-actions">
        <span class="footer-mic"><span class="dot" /> Mic on</span>
        <button class="footer-cta" type="button">Passer →</button>
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

/* header */
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
}
.exo-header-title .name {
  font-family: var(--font-display);
  font-size: 24px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  line-height: var(--lh-tight);
  margin-top: 2px;
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

/* stage */
.stage { flex: 1; display: flex; min-height: 0; }
.stage-pad {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 32px 40px;
}

/* objectif row */
.e02-objectif-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.mono-label {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.mono-label em { font-style: normal; color: var(--fg-primary); }
.chip-row { display: flex; gap: 8px; }
.chip {
  background: transparent;
  color: var(--fg-secondary);
  border: 1px solid var(--line);
  padding: 4px 12px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  transition: border-color var(--dur-fast), color var(--dur-fast), background-color var(--dur-fast);
}
.chip:hover { border-color: var(--line-strong); color: var(--fg-primary); }
.chip.active {
  background: var(--brand);
  color: var(--fg-on-orange);
  border-color: var(--brand);
}

/* center */
.e02-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}
.e02-counter {
  display: flex;
  align-items: baseline;
  font-family: var(--font-display);
  font-size: var(--t-counter);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  font-feature-settings: 'tnum' 1;
}
.e02-counter .cur { color: var(--brand); }
.e02-counter .sep { color: var(--ink-5); padding: 0 4px; }
.e02-counter .tgt { color: var(--ink-6); }

.e02-bar { display: flex; gap: 4px; width: 560px; max-width: 80vw; }
.e02-bar-seg {
  flex: 1;
  height: 14px;
  background: var(--ink-3);
  transition: background-color var(--dur-base);
}
.e02-bar-seg.fill { background: var(--brand); }

.e02-feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* waveform animée */
.waveform { display: flex; align-items: center; gap: 2px; height: 48px; }
.waveform span {
  width: 3px;
  background: var(--brand);
  border-radius: 999px;
  transform-origin: center;
  animation: wave 1s ease-in-out infinite alternate;
}
@keyframes wave {
  from { transform: scaleY(0.3); }
  to   { transform: scaleY(1); }
}

/* badge streak qui pulse */
.e02-streak-badge {
  background: var(--state-good);
  color: var(--ink-0);
  padding: 8px 16px;
  border-radius: 2px;
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  animation: pulse 1.6s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.04); }
}

/* footer */
.exo-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid var(--line);
  flex-shrink: 0;
}
.exo-footer-actions { display: flex; gap: 8px; align-items: center; }
.exo-footer-info {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.exo-footer-info em { font-style: normal; color: var(--fg-primary); }
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