import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/global.css'
import './styles/tokens.css'
import lazyLoad from './directives/lazyLoad'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 注册全局懒加载指令
app.directive('lazy', lazyLoad)

app.mount('#app')
