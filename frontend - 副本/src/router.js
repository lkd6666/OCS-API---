import { createRouter, createWebHistory } from 'vue-router'
import ConfigPanel from './components/ConfigPanel.vue'
import DataViewer from './components/DataViewer.vue'
import ApiDocs from './components/ApiDocs.vue'

const routes = [
  {
    path: '/',
    redirect: '/config'
  },
  {
    path: '/config',
    name: 'Config',
    component: ConfigPanel,
    meta: { title: '配置管理', icon: 'Setting' }
  },
  {
    path: '/viewer',
    name: 'Viewer',
    component: DataViewer,
    meta: { title: '数据可视化', icon: 'DataAnalysis' }
  },
  {
    path: '/docs',
    name: 'Docs',
    component: ApiDocs,
    meta: { title: 'API文档', icon: 'Document' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
