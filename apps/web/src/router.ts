import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  { path: '/', name: 'dashboard', component: () => import('./views/DashboardView.vue'), meta: { title: '工作台' } },
  { path: '/projects', name: 'projects', component: () => import('./views/ProjectsView.vue'), meta: { title: '项目' } },
  { path: '/data', name: 'data', component: () => import('./views/CatalogsView.vue'), meta: { title: '数据连接' } },
  {
    path: '/models',
    name: 'models',
    component: () => import('./views/KnowledgeNetworksView.vue'),
    meta: { title: '业务对象模型' },
  },
  {
    path: '/capabilities',
    name: 'capabilities',
    component: () => import('./views/CapabilitiesView.vue'),
    meta: { title: 'Agent 能力' },
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
