import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { hideLayout: true }
    },
    {
      path: '/',
      name: 'news',
      component: () => import('../views/NewsList.vue'),
      meta: { title: '新闻列表' }
    },
    {
      path: '/news/:id',
      name: 'newsDetail',
      component: () => import('../views/NewsDetail.vue'),
      meta: { title: '新闻详情' }
    },
    {
      path: '/recommend',
      name: 'recommend',
      component: () => import('../views/Recommend.vue'),
      meta: { title: '个性推荐' }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/Chat.vue'),
      meta: { title: '智能对话' }
    }
  ]
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'login' && !token) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router
