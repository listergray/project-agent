import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { useUserStore } from '@/stores/modules/user'

NProgress.configure({ showSpinner: false })

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据看板', icon: 'Odometer' }
      },
      {
        path: 'system/users',
        name: 'SystemUsers',
        component: () => import('@/views/system/user/index.vue'),
        meta: { title: '用户管理', icon: 'User', group: '系统管理' }
      },
      {
        path: 'system/configs',
        name: 'SystemConfigs',
        component: () => import('@/views/system/config/index.vue'),
        meta: { title: '系统配置', icon: 'Setting', group: '系统管理' }
      },
      {
        path: 'system/logs',
        name: 'SystemLogs',
        component: () => import('@/views/system/log/index.vue'),
        meta: { title: '操作日志', icon: 'Document', group: '系统管理' }
      },
      {
        path: 'account/list',
        name: 'AccountList',
        component: () => import('@/views/account/list/index.vue'),
        meta: { title: '闲鱼账号', icon: 'Iphone', group: '闲鱼管理' }
      },
      {
        path: 'account/connect',
        name: 'AccountConnect',
        component: () => import('@/views/account/connect/index.vue'),
        meta: { title: '连接管理', icon: 'Connection', group: '闲鱼管理' }
      },
      {
        path: 'product/list',
        name: 'ProductList',
        component: () => import('@/views/product/list/index.vue'),
        meta: { title: '商品管理', icon: 'Goods', group: '店铺运营' }
      },
      {
        path: 'order/list',
        name: 'OrderList',
        component: () => import('@/views/order/list/index.vue'),
        meta: { title: '订单管理', icon: 'Tickets', group: '店铺运营' }
      },
      {
        path: 'delivery/rule',
        name: 'DeliveryRule',
        component: () => import('@/views/delivery/rule/index.vue'),
        meta: { title: '发货规则', icon: 'Promotion', group: '自动发货' }
      },
      {
        path: 'delivery/log',
        name: 'DeliveryLog',
        component: () => import('@/views/delivery/log/index.vue'),
        meta: { title: '发货记录', icon: 'List', group: '自动发货' }
      },
      {
        path: 'inventory/list',
        name: 'InventoryList',
        component: () => import('@/views/inventory/list/index.vue'),
        meta: { title: '库存管理', icon: 'Box', group: '自动发货' }
      },
      {
        path: 'reply/keyword',
        name: 'ReplyKeyword',
        component: () => import('@/views/reply/keyword/index.vue'),
        meta: { title: '关键词回复', icon: 'ChatDotRound', group: '自动回复' }
      },
      {
        path: 'reply/ai',
        name: 'ReplyAi',
        component: () => import('@/views/reply/ai/index.vue'),
        meta: { title: 'AI 配置', icon: 'MagicStick', group: '自动回复' }
      },
      {
        path: 'message/chat',
        name: 'MessageChat',
        component: () => import('@/views/message/chat/index.vue'),
        meta: { title: '在线聊天', icon: 'ChatLineRound', group: '消息管理' }
      },
      {
        path: 'notify/config',
        name: 'NotifyConfig',
        component: () => import('@/views/placeholder/index.vue'),
        meta: { title: '通知配置', icon: 'Bell', group: '消息管理' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在', public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const whiteList = ['/login', '/404']

router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - 闲鱼自动发货` : '闲鱼自动发货系统'

  const userStore = useUserStore()

  if (userStore.isLoggedIn()) {
    if (to.path === '/login') {
      next('/')
      return
    }
    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch (e) {
        await userStore.logout()
        next('/login')
        return
      }
    }
    // Token 过期检查：剩余时间少于 30 分钟时自动刷新
    const remaining = userStore.getTokenRemainingSeconds()
    if (remaining > 0 && remaining < 1800 && !sessionStorage.getItem('refreshTokenRunning')) {
      sessionStorage.setItem('refreshTokenRunning', 'true')
      try {
        await userStore.refreshToken()
      } catch (e) {
        await userStore.logout()
        next('/login')
        return
      } finally {
        sessionStorage.removeItem('refreshTokenRunning')
      }
    }
    next()
  } else {
    if (whiteList.includes(to.path) || to.meta.public) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
