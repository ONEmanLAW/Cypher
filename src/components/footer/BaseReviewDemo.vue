<!-- components/footer/BaseReviewDemo.vue -->
<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function reviewDemo() {
  router.push('/exo-01')
}
</script>

<template>
  <button class="footer-btn" type="button" @click="reviewDemo">
    ↺ Review the demo
  </button>
</template>

<style scoped>
/* réplique la DA de .footer-btn (composant autonome) */
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
</style>