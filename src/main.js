import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/styles/token.css'
import './assets/styles/general.css'

createApp(App).use(router).mount('#app')