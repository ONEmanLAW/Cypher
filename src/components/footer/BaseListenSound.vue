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
    ♪ Listen to the sound
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
</style>