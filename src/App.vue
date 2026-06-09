<script setup>
import VinylOverlay from '@/components/VinylOverlay.vue'
import PanelOverlay from '@/components/PanelOverlay.vue'
</script>

<template>
  <RouterView v-slot="{ Component }">
    <Transition name="page">
      <component :is="Component" :key="$route.path" />
    </Transition>
  </RouterView>

  <VinylOverlay />
  <PanelOverlay />
</template>