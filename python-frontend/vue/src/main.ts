import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './pages/HomePage.vue'
import ChatPage from './pages/ChatPage.vue'
import ProjectsPage from './pages/ProjectsPage.vue'
import UploadPage from './pages/UploadPage.vue'
import PipelinePage from './pages/PipelinePage.vue'
import './styles/global.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/chat', component: ChatPage },
    { path: '/projects', component: ProjectsPage },
    { path: '/upload', component: UploadPage },
    { path: '/pipeline', component: PipelinePage },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

createApp(App).use(router).mount('#app')
