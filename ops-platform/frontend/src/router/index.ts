import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/test-api',
        name: 'TestApi',
        component: () => import('@/views/TestApi.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        component: () => import('@/layouts/MainLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                redirect: '/dashboard'
            },
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/Dashboard.vue')
            },
            {
                path: 'resources',
                name: 'Resources',
                component: () => import('@/views/Resources/ResourceList.vue')
            },
            {
                path: 'monitoring',
                name: 'Monitoring',
                component: () => import('@/views/Monitoring/MonitoringDashboard.vue')
            },
            {
                path: 'alerts',
                name: 'Alerts',
                component: () => import('@/views/Alerts/AlertList.vue')
            },
            {
                path: 'alerts/rules',
                name: 'AlertRules',
                component: () => import('@/views/Alerts/AlertRules.vue')
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')

    if (to.meta.requiresAuth && !token) {
        next('/login')
    } else if (to.path === '/login' && token) {
        next('/dashboard')
    } else {
        next()
    }
})

export default router
