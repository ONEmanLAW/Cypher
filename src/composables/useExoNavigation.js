import { useRouter, useRoute } from 'vue-router'

const ORDER = ['exo01', 'exo02', 'exo03', 'exo04', 'exo05', 'exo06']

export function useExoNavigation() {
  const router = useRouter()
  const route = useRoute()

  function goToNext() {
    const idx = ORDER.indexOf(route.name)
    const nextName = idx === -1 || idx === ORDER.length - 1
      ? ORDER[0]
      : ORDER[idx + 1]
    router.push({ name: nextName })
  }

  return { goToNext }
}