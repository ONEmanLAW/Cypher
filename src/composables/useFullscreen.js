import { ref, onMounted, onUnmounted } from 'vue'

export function useFullscreen({ hotkey = null } = {}) {
  const isFullscreen = ref(false)

  const sync = () => { isFullscreen.value = !!document.fullscreenElement }
  const enter = (el = document.documentElement) => el.requestFullscreen?.()
  const exit  = () => document.exitFullscreen?.()
  const toggle = (el) => (document.fullscreenElement ? exit() : enter(el))

  const onKey = (e) => {
    if (hotkey && e.key.toLowerCase() === hotkey.toLowerCase()) {
      // évite de déclencher quand on tape dans un champ
      const t = e.target
      if (t?.tagName === 'INPUT' || t?.tagName === 'TEXTAREA' || t?.isContentEditable) return
      e.preventDefault()
      toggle()
    }
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', sync)
    if (hotkey) window.addEventListener('keydown', onKey)
  })
  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', sync)
    if (hotkey) window.removeEventListener('keydown', onKey)
  })

  return { isFullscreen, enter, exit, toggle }
}