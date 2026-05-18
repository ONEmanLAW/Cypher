<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <main class="home">
    <RouterLink to="/exo-01" class="btn">Exo 01</RouterLink>
    <RouterLink to="/exo-02" class="btn">Exo 02</RouterLink>
    <RouterLink to="/exo-03" class="btn">Exo 03</RouterLink>
    <RouterLink to="/exo-04" class="btn">Exo 04</RouterLink>
    <RouterLink to="/exo-05" class="btn">Exo 05</RouterLink>
    <RouterLink to="/exo-06" class="btn">Exo 06</RouterLink>
  </main>
</template>

<style scoped>
.home {
  height: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 24px;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-card);
  border: 1px solid var(--line);
  color: var(--fg-primary);
  font-family: var(--font-display);
  font-size: 24px;
  text-transform: uppercase;
}

.btn:hover {
  border-color: var(--brand);
  color: var(--brand);
}
</style>