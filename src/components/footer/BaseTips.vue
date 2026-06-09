<!-- components/ui/BaseTips.vue -->
<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useProgressStore } from '@/stores/progress'

/* ============================================================
   EXPLICATIONS DES EXERCICES — universel, indexé par numéro 1→6
   theme  = nom du concept (affiché en petit)
   title  = vrai nom de l'exo (affiché en gros). null → fallback theme.
   ============================================================ */
const EXERCISE_TIPS = {
  1: {
    num: 'Exercise 1',
    theme: 'Discovery',
    title: 'Kick Start',
    goal: 'A step by step video that breaks the sound down. It pauses at key moments so you can try it yourself, and you move at your own pace.',
    steps: [
      'Play the video and follow the breakdown of the sound.',
      'At each checkpoint the video pauses so you can try what you just heard.',
      'Make the sound: live feedback tells you whether it sounds right or not.',
      'When you feel ready, resume the video yourself. You decide when to move on.',
      'Use the timeline to jump back to any moment and replay a step as often as you want.',
    ],
    watch: [],
  },
  2: {
    num: 'Exercise 2',
    theme: 'Imitation',
    title: 'Echo Flow',
    goal: 'Reproduce the correct sound a set number of times. The mic counts every valid hit.',
    steps: [
      'Make sur the mic is on (green dot means it is listening).',
      'Make the target sound: each recognized hit raises the counter.',
      'Reach the goal to clear the exercise.',
      'Once cleared, you can set your own target (21 to 100) to keep chaining the sound and push further.'
    ],
    watch: [
      'A wrong sound or noise will not count, so articulate the target sound clearly.',
      'Leave a short gap between hits so each one is detected.',
    ],
  },
  3: {
    num: 'Exercise 3',
    theme: 'Control',
    title: 'Control Mode',
    goal: 'Control your sound\'s intensity. You aim for a target zone that slides from soft to loud.',
    steps: [
      'Make sur the mic is on (green dot means it is listening).',
      'Make the sound while aiming for the displayed target zone (soft to loud).',
      'Your intensity peak is compared to the target: too low, too high, or perfect.',
      'Clear each level to finish.',
    ],
    watch: [
      'Too loud reads as "high", too quiet reads as "low": volume matters, not just the sound.',
      'Keep a steady intensity across the whole hit.',
    ],
  },
  4: {
    num: 'Exercise 4',
    theme: 'Timing',
    title: 'Stay In Time',
    goal: 'Place your sound on the beat. A metronome sets the tempo, you hit right on time.',
    steps: [
      'Make sur the mic is on (green dot means it is listening).',
      'Get ready and make the target sound on every beat, following the click.',
      'The closer you are to the beat, the better the result (hit / perfect).',
    ],
    watch: [
      'Timing comes first here: stay steady rather than fast.',
      'Anticipate the sound slightly to land right on the click.',
    ],
  },
  5: {
    num: 'Exercise 5',
    theme: 'Timing',
    title: 'Rhythm Copy',
    goal: 'Call and response: a rhythmic pattern is played, you reproduce it exactly.',
    steps: [
      'Listen to the pattern all the way through (the "call" phase).',
      'On your turn, reproduce the exact same sequence of sounds and timing.',
      'The sequence is valid if both order and rhythm match.',
      'Pick the difficulty to make the patterns harder and raise the challenge.',
    ],
    watch: [
      'Memorize the rhythm before you start, do not rush.',
      'Respect the rests in the pattern, they are part of it.',
    ],
  },
  6: {
    num: 'Exercise 6',
    theme: 'Timing',
    title: 'Fill the Beat',
    goal: 'Fill the groove: on an existing loop, place your sounds in the missing spots.',
    steps: [
      'Listen to the backing loop to spot the gaps to fill.',
      'Turn on the mic and place the target sound on every open slot.',
      'Stay on the loop: sound and timing both count.',
      'For more challenge, switch to loop mode: the metronome never stops so you keep placing the sound non stop.',
      'You can also raise the difficulty to add more sounds to hit within the loop.',
    ],
    watch: [
      'Stay locked to the loop, do not drift into freestyle.',
      'Combine what you learned: right sound, right intensity, right timing.',
    ],
  },
}

const progress = useProgressStore()
const route = useRoute()
const open = ref(false)
const tab = ref('exo')         // 'exo' | 'sound'

const tipsUrl = computed(() => progress.currentSound?.tips || null)
const soundName = computed(() => progress.currentSound?.name || '')

/* route.name = 'exo01'…'exo06' → 1…6 */
const exoId = computed(() => {
  const n = parseInt(String(route.name).replace('exo', ''), 10)
  return n && EXERCISE_TIPS[n] ? n : null
})
const exo = computed(() => (exoId.value ? EXERCISE_TIPS[exoId.value] : null))

const canOpen = computed(() => !!exo.value || !!tipsUrl.value)

function show() {
  if (!canOpen.value) return
  tab.value = exo.value ? 'exo' : 'sound'   // priorité à l'explication exo
  open.value = true
}
function close() {
  open.value = false
}

function onKey(e) {
  if (e.key === 'Escape') close()
}
watch(open, (v) => {
  if (v) window.addEventListener('keydown', onKey)
  else window.removeEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <button
    class="tips-btn"
    type="button"
    :disabled="!canOpen"
    @click="show"
  >
    ⓘ Tips
  </button>

  <Teleport to="body">
    <div v-if="open" class="tips-backdrop" @click.self="close">
      <div class="tips-panel">
        <header class="tips-head">
          <div class="tips-head-text">
            <span class="tips-kicker">Tips · {{ soundName }}</span>
            <span class="tips-title">How to nail it</span>
          </div>
          <button class="tips-close" type="button" aria-label="Close" @click="close">✕</button>
        </header>

        <!-- Onglets -->
        <nav class="tips-tabs">
          <button
            class="tips-tab"
            :class="{ 'is-active': tab === 'exo' }"
            :disabled="!exo"
            type="button"
            @click="tab = 'exo'"
          >
            How it works
          </button>
          <button
            class="tips-tab"
            :class="{ 'is-active': tab === 'sound' }"
            :disabled="!tipsUrl"
            type="button"
            @click="tab = 'sound'"
          >
            Sound tips
          </button>
        </nav>

        <!-- Onglet explication exo -->
        <div v-if="tab === 'exo'" class="tips-body tips-body--exo">
          <div v-if="exo" class="exo">
            <span class="exo-kicker">{{ exo.num }} · {{ exo.theme }}</span>
            <h2 class="exo-title">{{ exo.title || exo.theme }}</h2>

            <p v-if="exo.goal" class="exo-goal">{{ exo.goal }}</p>

            <ol v-if="exo.steps?.length" class="exo-steps">
              <li v-for="(s, i) in exo.steps" :key="i">{{ s }}</li>
            </ol>

            <div v-if="exo.watch?.length" class="exo-watch">
              <span class="exo-watch-label">Watch out</span>
              <ul>
                <li v-for="(w, i) in exo.watch" :key="i">{{ w }}</li>
              </ul>
            </div>
          </div>
          <p v-else class="exo-empty">No tips for this exercise.</p>
        </div>

        <!-- Onglet PDF du son -->
        <div v-else class="tips-body tips-body--frame">
          <iframe v-if="tipsUrl" :src="tipsUrl" class="tips-frame" title="Sound tips" />
        </div>

        <footer v-if="tab === 'sound' && tipsUrl" class="tips-foot">
          <a class="tips-open" :href="tipsUrl" target="_blank" rel="noopener">Open ↗</a>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* bouton */
.tips-btn {
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
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.tips-btn:hover:not(:disabled) { border-color: var(--brand); color: var(--fg-primary); }
.tips-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* overlay */
.tips-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(5, 5, 6, 0.72);
  backdrop-filter: blur(3px);
}
.tips-panel {
  display: flex;
  flex-direction: column;
  width: min(900px, 92vw);
  height: min(860px, 88vh);
  background: var(--surface-raised);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-stage);
  animation: tips-pop var(--dur-base) var(--ease-out-snap);
}
@keyframes tips-pop {
  0% { transform: scale(0.96); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.tips-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.tips-head-text { display: flex; flex-direction: column; gap: 4px; }
.tips-kicker {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--brand);
}
.tips-title {
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}
.tips-close {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--fg-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.tips-close:hover { border-color: var(--brand); color: var(--brand); }

/* onglets */
.tips-tabs {
  display: flex;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.tips-tab {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 12px 16px;
  color: var(--fg-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  cursor: pointer;
  transition: color var(--dur-fast), border-color var(--dur-fast);
}
.tips-tab:hover:not(:disabled) { color: var(--fg-primary); }
.tips-tab.is-active { color: var(--fg-primary); border-bottom-color: var(--brand); }
.tips-tab:disabled { opacity: 0.3; cursor: not-allowed; }

/* corps */
.tips-body { flex: 1; min-height: 0; }
.tips-body--frame { background: var(--ink-0); }
.tips-body--exo { overflow-y: auto; padding: 28px 32px; }

/* explication exo */
.exo { display: flex; flex-direction: column; gap: 16px; }
.exo-kicker {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--brand);
}
.exo-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 32px;
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}
.exo-goal {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 18px;
  line-height: var(--lh-body);
  color: var(--fg-secondary);
}
.exo-steps {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-family: var(--font-ui);
  font-size: 16px;
  line-height: var(--lh-body);
  color: var(--fg-secondary);
}
.exo-steps li::marker { color: var(--brand); font-family: var(--font-mono); }

.exo-watch {
  border-left: 2px solid var(--state-warn);
  padding: 4px 0 4px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.exo-watch-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--state-warn);
}
.exo-watch ul {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: var(--lh-body);
  color: var(--fg-muted);
}
.exo-empty {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--fg-muted);
}

/* frame PDF */
.tips-frame { width: 100%; height: 100%; border: none; display: block; }

/* footer (uniquement onglet son) */
.tips-foot {
  display: flex;
  justify-content: flex-end;
  padding: 12px 20px;
  border-top: 1px solid var(--line);
  flex-shrink: 0;
}
.tips-open {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-secondary);
  text-decoration: none;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 7px 12px;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.tips-open:hover { border-color: var(--brand); color: var(--fg-primary); }
</style>