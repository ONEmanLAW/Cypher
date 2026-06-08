<!-- components/footer/BaseListenSound.vue -->
<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useProgressStore } from '@/stores/progress'

const progress = useProgressStore()

const soundUrl = computed(() => progress.currentSound?.sound || null)
const playing = ref(false)

let audio = null

function play() {
  if (!soundUrl.value) return
  if (!audio) {
    audio = new Audio(soundUrl.value)
    audio.addEventListener('ended', () => { playing.value = false })
  }
  audio.currentTime = 0       // rejoue depuis le début à chaque clic
  audio.play()
  playing.value = true
}

/* si on change de son courant, on recrée l'élément audio */
watch(soundUrl, () => {
  if (audio) { audio.pause(); audio = null }
  playing.value = false
})

onBeforeUnmount(() => {
  if (audio) { audio.pause(); audio = null }
})
</script>

<template>
  <button
    class="footer-btn"
    :class="{ playing }"
    type="button"
    :disabled="!soundUrl"
    @click="play"
  >
    <!-- repos : note · lecture : égaliseur animé -->
    <span v-if="!playing" class="note">♪</span>
    <span v-else class="eq">
      <span></span><span></span><span></span>
    </span>
    Listen to the sound
  </button>
</template>

<style scoped>
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
.footer-btn:hover:not(:disabled) { border-color: var(--brand); color: var(--fg-primary); }
.footer-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.footer-btn.playing { border-color: var(--brand); color: var(--brand); }

.note { font-size: 13px; line-height: 1; }

/* égaliseur : 3 barres animées pendant la lecture */
.eq {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 11px;
}
.eq span {
  width: 2px;
  height: 4px;
  background: currentColor;
  transform-origin: bottom;
  animation: eq-bounce 0.7s var(--ease-out-soft) infinite;
}
.eq span:nth-child(2) { animation-delay: 0.15s; }
.eq span:nth-child(3) { animation-delay: 0.3s; }

@keyframes eq-bounce {
  0%, 100% { height: 4px; }
  50%      { height: 11px; }
}

@media (prefers-reduced-motion: reduce) {
  .eq span { animation: none; height: 8px; }
}
</style>