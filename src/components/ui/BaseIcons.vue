<script setup>
defineProps({
  icon: { type: [Object, Function], required: true },
  size: { type: Number, default: 24 },
})
</script>

<template>
  <component :is="icon" :size="size" :stroke-width="1.5" />
</template>