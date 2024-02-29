import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

/* Layout */
import Layout from '@/layout'

/**
 * Note: sub-menu only appear when route children.length >= 1
 * Detail see: https://panjiachen.github.io/vue-element-admin-site/guide/essentials/router-and-nav.html
 *
 * hidden: true                   if set true, item will not show in the sidebar(default is false)
 * alwaysShow: true               if set true, will always show the root menu
 *                                if not set alwaysShow, when item has more than one children route,
 *                                it will becomes nested mode, otherwise not show the root menu
 * redirect: noRedirect           if set noRedirect will no redirect in the breadcrumb
 * name:'router-name'             the name is used by <keep-alive> (must set!!!)
 * meta : {
    roles: ['admin','editor']    control the page roles (you can set multiple roles)
    title: 'title'               the name show in sidebar and breadcrumb (recommend set)
    icon: 'svg-name'             the icon show in the sidebar
    breadcrumb: false            if set false, the item will hidden in breadcrumb(default is true)
    activeMenu: '/example/list'  if set path, the sidebar will highlight the path you set
  }
 */

/**
 * constantRoutes
 * a base page that does not have permission requirements
 * all roles can be accessed
 */
export const constantRoutes = [

  {
    path: '/login',
    component: () => import('@/views/login/index'),
    hidden: true
  },

  {
    path: '/404',
    component: () => import('@/views/404'),
    hidden: true
  },

  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [{
      path: 'dashboard',
      name: '首页',
      component: () => import('@/views/dashboard/index'),
      meta: { title: '首页', icon: 'dashboard' }
    }]
  },

  {
    path: '/stock',
    component: Layout,
    redirect: '/stock/stock',
    name: '股票期货',
    meta: { title: '股票期货', icon: 'example' },
    children: [
      {
        path: 'stock',
        name: 'Stock',
        component: () => import('@/views/stock/index'),
        meta: { title: '条件筛选', icon: 'table' }
      },
      {
        path: 'shape',
        name: '形态结果',
        component: () => import('@/views/shape/index'),
        meta: { title: '形态结果', icon: 'table' }
      },
      {
        path: 'audit',
        name: '交易清单审核',
        component: () => import('@/views/audit/index'),
        meta: { title: '交易清单审核', icon: 'table' }
      },
      {
        path: 'audit_manual',
        name: '手动交易清单',
        component: () => import('@/views/audit_manual/index'),
        meta: { title: '手动交易清单', icon: 'table' }
      }

    ]
  },

  {
    path: '/system',
    component: Layout,
    redirect: '/passwd',
    children: [{
      path: 'passwd',
      name: '修改密码',
      component: () => import('@/views/passwd/pwd'),
      meta: { title: '修改密码', icon: 'dashboard' }
    }]
  },
  {
    path: '/direction_for_use',
    component: Layout,
    redirect: '/direction_for_use',
    meta: { title: '使用说明', icon: 'dashboard' },
    children: [{
      path: 'indicators_show',
      component: () => import('@/views/indicators_show'), // Parent router-view
      name: 'indicators_show',
      meta: { title: '指标说明', icon: 'example' },
      children: [
        {
          path: 'fundamentals',
          component: () => import('@/views/indicators_show/fundamentals'),
          name: 'fundamentals',
          meta: { title: '基本面指标' },
          children: [
            {
              path: 'net_profit',
              component: () => import('@/views/indicators_show/fundamentals/net_profit'),
              name: 'net_profit',
              meta: { title: '净利润' }
            },
            {
              path: 'pe_ratio',
              component: () => import('@/views/indicators_show/fundamentals/pe_ratio'),
              name: 'pe_ratio',
              meta: { title: '市盈率' }
            }
          ]
        },
        {
          path: 'technical',
          component: () => import('@/views/indicators_show/technical'),
          name: 'technical',
          meta: { title: '技术面指标' },
          children: [
            {
              path: 'break_history_high',
              component: () => import('@/views/indicators_show/technical/break_history_high'),
              name: 'break_history_high',
              meta: { title: '突破历史高点' }
            },
            {
              path: 'break_history_ma',
              component: () => import('@/views/indicators_show/technical/break_history_ma'),
              name: 'break_history_ma',
              meta: { title: '突破日均线' }
            }
          ]
        }
      ]
    }]
  },

  // 404 page must be placed at the end !!!
  { path: '*', redirect: '/404', hidden: true }
]

const createRouter = () => new Router({
  // mode: 'history', // require service support
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

// Detail see: https://github.com/vuejs/vue-router/issues/1234#issuecomment-357941465
export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher // reset router
}

export default router
