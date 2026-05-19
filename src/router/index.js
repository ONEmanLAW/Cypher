import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import Exo02View from '@/views/Exo02View.vue'
import Exo04View from '@/views/Exo04View.vue'
import Exo05View from '@/views/Exo05View.vue'
import Exo06View from '@/views/Exo06View.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/exo-02', name: 'exo02', component: Exo02View },
    { path: '/exo-04', name: 'exo04', component: Exo04View },
    { path: '/exo-05', name: 'exo05', component: Exo05View },
    { path: '/exo-06', name: 'exo06', component: Exo06View },
  ],
})

export default router