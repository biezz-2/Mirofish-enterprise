import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue App Error]', err, info)
}

app.use(router)
app.use(i18n)

app.mount('#app')
