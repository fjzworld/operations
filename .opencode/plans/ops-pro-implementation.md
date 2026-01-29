# OpsPro Design System Implementation Plan

This document contains the exact code changes required to implement the "OpsPro" Dark OLED design system.

## 1. Global Styles & Variables

**Target File:** `src/assets/main.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600&family=Fira+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
  /* --- OpsPro Design System: Dark OLED Theme --- */
  
  /* Backgrounds */
  --bg-app: #020617;       /* Deepest Black/Blue (Slate 950) */
  --bg-surface: #0F172A;   /* Sidebar/Nav (Slate 900) */
  --bg-card: #1E293B;      /* Cards/Elevated (Slate 800) */
  --bg-element: #334155;   /* Inputs/Borders (Slate 700) */

  /* Text */
  --text-primary: #F8FAFC; /* High Contrast (Slate 50) */
  --text-secondary: #94A3B8; /* Muted (Slate 400) */
  --text-muted: #64748B;   /* Disabled/Subtle (Slate 500) */

  /* Accents */
  --color-primary: #38bdf8; /* Sky 400 - UI Interaction */
  --color-success: #22C55E; /* Green 500 - OpsPro Signature CTA/Status */
  --color-warning: #eab308;
  --color-danger: #ef4444;

  /* Borders */
  --border-color: #1e293b;

  /* --- Element Plus Overrides (Mapping to OpsPro) --- */
  --el-bg-color: var(--bg-app);
  --el-bg-color-page: var(--bg-app);
  --el-bg-color-overlay: var(--bg-card);
  
  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-secondary);
  --el-text-color-secondary: var(--text-muted);
  
  --el-border-color: var(--border-color);
  --el-border-color-light: var(--bg-element);
  --el-border-color-lighter: var(--bg-card);
  
  --el-color-primary: var(--color-primary);
  --el-color-success: var(--color-success);
  
  /* Menu Overrides */
  --el-menu-bg-color: var(--bg-surface);
  --el-menu-text-color: var(--text-secondary);
  --el-menu-active-color: var(--color-primary);
  --el-menu-hover-bg-color: var(--bg-card);
  --el-menu-border-color: transparent;
}

/* Global Reset */
html, body {
  background-color: var(--bg-app);
  color: var(--text-primary);
  font-family: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin: 0;
  padding: 0;
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* Typography Utilities */
code, pre, .font-mono {
  font-family: 'Fira Code', monospace;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--bg-app);
}
::-webkit-scrollbar-thumb {
  background: var(--bg-element);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Visual Effects */
.text-glow {
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

.card-base {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.card-base:hover {
  border-color: var(--bg-element);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.cursor-pointer {
  cursor: pointer;
}
```

## 2. Element Plus Dark Mode

**Target File:** `src/main.ts`

**Change:** Import dark theme vars.

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// Add this line:
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

## 3. Layout Refactoring

**Target File:** `src/layouts/MainLayout.vue`

**Changes:** Use CSS variables, remove hardcoded styles, add transparency.

```vue
<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2 class="text-glow">OpsPro</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="custom-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/resources">
          <el-icon><Box /></el-icon>
          <span>资源管理</span>
        </el-menu-item>
        <el-menu-item index="/monitoring">
          <el-icon><Monitor /></el-icon>
          <span>监控中心</span>
        </el-menu-item>
        <el-sub-menu index="/alerts">
          <template #title>
            <el-icon><Bell /></el-icon>
            <span>告警管理</span>
          </template>
          <el-menu-item index="/alerts">告警列表</el-menu-item>
          <el-menu-item index="/alerts/rules">告警规则</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-content">
          <span class="title">{{ pageTitle }}</span>
          <div class="user-info">
            <el-dropdown @command="handleCommand">
              <span class="user-name">
                <el-icon><User /></el-icon>
                {{ authStore.user?.username || 'User' }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { DataLine, Monitor, Bell, User, Box } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': '仪表盘',
    '/resources': '资源管理',
    '/monitoring': '监控中心',
    '/alerts': '告警列表',
    '/alerts/rules': '告警规则'
  }
  return titles[route.path] || '运维平台'
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background-color: var(--bg-app);
}

.sidebar {
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-surface);
}

.logo h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.5px;
}

/* Menu Customization */
.custom-menu {
  border-right: none;
  background-color: transparent;
}

:deep(.el-menu-item) {
  border-left: 3px solid transparent;
}

:deep(.el-menu-item.is-active) {
  background-color: var(--bg-card);
  border-left-color: var(--color-success);
}

.header {
  background-color: rgba(2, 6, 23, 0.8); /* Semi-transparent bg-app */
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  height: 64px;
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.user-name:hover {
  background-color: var(--bg-element);
  color: var(--text-primary);
}

.main-content {
  padding: 24px;
  background-color: var(--bg-app);
  overflow-y: auto;
}

/* Page Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```
