import { ref } from 'vue'

const active = ref(false)
const phase = ref('idle') // 'idle' | 'cover' | 'reveal'
const origin = ref(null)  // rect de la tuile cliquée

const wait = (ms) => new Promise((r) => setTimeout(r, ms))

export function usePanelTransition(router) {
  async function enterPanel(to, el, label = '') {
    const r = el.getBoundingClientRect()
    origin.value = { top: r.top, left: r.left, width: r.width, height: r.height, label }
    active.value = true
    phase.value = 'cover'
    await wait(440)
    phase.value = 'reveal'
    if (router) await router.push(to)
    await wait(640)
    active.value = false
    phase.value = 'idle'
    origin.value = null
  }
  return { active, phase, origin, enterPanel }
}