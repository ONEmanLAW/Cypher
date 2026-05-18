<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  // hauteurs des barres, valeurs 0 -> 1. Si absent : animation de démo
  levels: { type: Array, default: null },
  barCount: { type: Number, default: 80 },
})

const fake = ref([])

onMounted(() => {
  if (props.levels) return // vrai son fourni -> pas de démo
  fake.value = Array.from(
    { length: props.barCount },
    () => 0.2 + Math.random() * 0.8,
  )
})
</script>

<template>
  <div class="bars">
    <span
      v-for="(h, i) in (levels ?? fake)"
      :key="i"
      class="bar"
      :style="{
        height: `${h * 100}%`,
        animationDelay: `${(i % 10) * 0.08}s`,
      }"
    />
  </div>
</template>

<style scoped>
.bars {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  gap: 3px;
}

.bar {
  width: 4px;
  background: var(--orange-500);
  transform-origin: center;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scaleY(0.3); opacity: 0.7; }
  50%      { transform: scaleY(1);   opacity: 1; }
}
</style>