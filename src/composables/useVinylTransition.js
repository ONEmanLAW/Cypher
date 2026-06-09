import { ref } from 'vue'

// refs module-level → partagées entre l'overlay (App.vue) et les vues
const active = ref(false)
const phase = ref('idle') // 'idle' | 'cover' | 'reveal'

const wait = (ms) => new Promise((r) => setTimeout(r, ms))

export function useVinylTransition(router) {
  async function go(to) {
    active.value = true
    phase.value = 'cover'
    await wait(420) // le disque couvre l'écran
    if (router) await router.push(to) // swap de route caché derrière
    phase.value = 'reveal'
    await wait(420) // le disque se retire
    active.value = false
    phase.value = 'idle'
  }

  return { active, phase, go }
}