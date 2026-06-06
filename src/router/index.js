import { createRouter, createWebHistory } from 'vue-router'
import { useProgressStore } from '@/stores/progress'

import ModeSelectView from '@/views/ModeSelectView.vue'
import SectionSelectView from '@/views/SectionSelectView.vue'
import SoundSelectView from '@/views/SoundSelectView.vue'
import ExercisesView from '@/views/ExercisesView.vue'
import Exo01View from '@/views/Exo01View.vue'
import Exo02View from '@/views/Exo02View.vue'
import Exo03View from '@/views/Exo03View.vue'
import Exo04View from '@/views/Exo04View.vue'
import Exo05View from '@/views/Exo05View.vue'
import Exo06View from '@/views/Exo06View.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',          name: 'mode-select',    component: ModeSelectView },
    { path: '/sections',  name: 'section-select', component: SectionSelectView },
    { path: '/sounds',    name: 'sound-select',   component: SoundSelectView },
    { path: '/exercises', name: 'exercises',      component: ExercisesView },
    { path: '/exo-01',    name: 'exo01',          component: Exo01View },
    { path: '/exo-02',    name: 'exo02',          component: Exo02View },
    { path: '/exo-03',    name: 'exo03',          component: Exo03View },
    { path: '/exo-04',    name: 'exo04',          component: Exo04View },
    { path: '/exo-05',    name: 'exo05',          component: Exo05View },
    { path: '/exo-06',    name: 'exo06',          component: Exo06View },
  ],
})

/* Écrans de sélection libres ; les exos exigent un son sélectionné */
const OPEN_PATHS = new Set(['/', '/sections', '/sounds'])

router.beforeEach((to) => {
  if (OPEN_PATHS.has(to.path)) return true
  const progress = useProgressStore()
  if (!progress.currentSoundId) return { path: '/sounds' }
  return true
})

export default router