<template>
  <el-container class="main-layout">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>运维平台</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/resources">
          <el-icon><Server /></el-icon>
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
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { DataLine, Server, Monitor, Bell, User } from '@element-plus/icons-vue'

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
}

.sidebar {
  background-color: #304156;
  overflow-y: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #434a50;
}

.logo h2 {
  font-size: 20px;
  margin: 0;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 18px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-name {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-name:hover {
  background-color: #f5f7fa;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
