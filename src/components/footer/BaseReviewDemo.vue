<!-- components/footer/BaseReviewDemo.vue -->
<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const confirmOpen = ref(false)

function ask() { confirmOpen.value = true }
function cancel() { confirmOpen.value = false }
function confirm() {
  confirmOpen.value = false
  router.push({ name: 'exo01' })
}

/* Escape ferme la confirmation */
function onKey(e) { if (e.key === 'Escape') cancel() }
watch(confirmOpen, (v) => {
  if (v) window.addEventListener('keydown', onKey)
  else window.removeEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <button class="footer-btn" type="button" @click="ask">
    ↺ Review the demo
  </button>

  <Teleport to="body">
    <div v-if="confirmOpen" class="rv-backdrop" @click.self="cancel">
      <div class="rv-confirm">
        <div>
          <span class="rv-kicker">Review the demo</span>
          <h3 class="rv-title">Leave this exercise?</h3>
        </div>

        <div class="rv-rows">
          <div class="rv-row">
            <span class="rv-row-label">
              <b>Current progress</b>
              <span>Won't be saved</span>
            </span>
            <span class="rv-badge">Exo · demo</span>
          </div>
        </div>

        <div class="rv-actions">
          <button class="footer-btn" type="button" @click="cancel">Cancel</button>
          <button class="footer-cta" type="button" @click="confirm">↺ Review</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* bouton — DA de .footer-btn (composant autonome) */
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
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.footer-btn:hover { border-color: var(--brand); color: var(--fg-primary); }

/* overlay de confirmation */
.rv-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(5, 5, 6, 0.72);
  backdrop-filter: blur(2px);
}
.rv-confirm {
  width: min(420px, 90%);
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-stage);
  animation: rv-pop var(--dur-base) var(--ease-out-snap);
}
@keyframes rv-pop {
  0% { transform: scale(0.96); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.rv-kicker {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--fg-muted);
}
.rv-title {
  margin: 6px 0 0;
  font-family: var(--font-display);
  font-size: var(--t-h2);
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--fg-primary);
}

.rv-rows { display: flex; flex-direction: column; gap: 10px; }
.rv-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.rv-row-label { display: flex; flex-direction: column; gap: 3px; }
.rv-row-label b {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 14px;
  color: var(--fg-primary);
}
.rv-row-label span {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--ls-label);
  text-transform: uppercase;
  color: var(--state-bad);
}
.rv-badge {
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: var(--ls-tight);
  text-transform: uppercase;
  color: var(--brand);
  padding: 4px 12px;
  border: 1px solid var(--brand);
  border-radius: 4px;
}

.rv-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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