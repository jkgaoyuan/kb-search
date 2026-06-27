import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/LayoutView.vue'),
    redirect: '/search',
    children: [
      {
        path: '/search',
        name: 'Search',
        component: () => import('@/views/SearchView.vue'),
        meta: { title: '搜索' }
      },
      {
        path: '/document/:id',
        name: 'DocumentDetail',
        component: () => import('@/views/DocumentDetailView.vue'),
        meta: { title: '文档详情' }
      },
      {
        path: '/upload',
        name: 'Upload',
        component: () => import('@/views/UploadView.vue'),
        meta: { title: '上传文档', requiresAuth: true }
      },
      {
        path: '/categories',
        name: 'Categories',
        component: () => import('@/views/CategoryView.vue'),
        meta: { title: '分类浏览' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
