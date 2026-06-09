import { ref } from 'vue'

const active = ref(false)
const phase = ref('idle') // 'idle' | 'cover' | 'reveal'

const wait = (ms) => new Promise((r) => setTimeout(r, ms))

export function useVinylTransition(router) {
  async function go(to) {
    active.value = true
    phase.value = 'cover'
    await wait(420)
    phase.value = 'reveal'
    if (router) await router.push(to)
    await wait(420)
    active.value = false
    phase.value = 'idle'
  }
  return { active, phase, go }
}