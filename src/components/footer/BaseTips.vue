<!-- components/ui/BaseTips.vue -->
<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useProgressStore } from '@/stores/progress'

const progress = useProgressStore()
const open = ref(false)

const tipsUrl = computed(() => progress.currentSound?.tips || null)
const soundName = computed(() => progress.currentSound?.name || '')

function show() {
  if (!tipsUrl.value) return
  open.value = true
}
function close() {
  open.value = false
}

/* Escape ferme la fiche */
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
    :disabled="!tipsUrl"
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
          <div class="tips-head-actions">
            <a class="tips-open" :href="tipsUrl" target="_blank" rel="noopener">Open ↗</a>
            <button class="tips-close" type="button" aria-label="Close" @click="close">✕</button>
          </div>
        </header>

        <div class="tips-body">
          <iframe :src="tipsUrl" class="tips-frame" title="Tips" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* bouton — réplique la DA de .footer-btn (composant autonome) */
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
.tips-head-actions { display: flex; align-items: center; gap: 8px; }
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

.tips-body { flex: 1; min-height: 0; background: var(--ink-0); }
.tips-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>