<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DocumentCopy, ChatLineRound, Star, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const username = computed(() => localStorage.getItem('username') || '用户')
const hideLayout = computed(() => route.meta.hideLayout)
const activeMenu = computed(() => route.path)

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<template>
  <!-- 登录页不显示导航 -->
  <router-view v-if="hideLayout" />

  <!-- 主布局 -->
  <el-container v-else class="app-layout">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="header-left">
        <h1 class="logo">📰 新语</h1>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        :ellipsis="false"
        router
        class="header-menu"
      >
        <el-menu-item index="/">
          <el-icon><DocumentCopy /></el-icon>
          <span>新闻列表</span>
        </el-menu-item>
        <el-menu-item index="/recommend">
          <el-icon><Star /></el-icon>
          <span>个性推荐</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatLineRound /></el-icon>
          <span>智能对话</span>
        </el-menu-item>
      </el-menu>
      <div class="header-right">
        <span class="welcome-text">👋 {{ username }}</span>
        <el-button type="danger" text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page-transition" mode="out-in">
          <keep-alive :include="['NewsList', 'Recommend']">
            <component :is="Component" />
          </keep-alive>
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: transparent !important; /* 让 global css 的伪元素透过来 */
}
#app {
  min-height: 100vh;
  background-color: transparent !important;
}
</style>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: transparent;
}
.app-header {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 0 32px;
  height: 64px !important;
  border-bottom: 1px solid var(--ina-border-light);
  box-shadow: 0 4px 12px -8px rgba(0, 102, 255, 0.15);
  z-index: 100;
}
.header-left {
  display: flex;
  align-items: center;
  margin-right: 48px;
}
.logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--ina-primary);
  white-space: nowrap;
  letter-spacing: -0.5px;
}
.header-menu {
  flex: 1;
  /* Element Plus Menu CSS Variables */
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--ina-text-2);
  --el-menu-active-color: var(--ina-primary);
  --el-menu-hover-text-color: var(--ina-text);
  --el-menu-hover-bg-color: var(--ina-bg);
}

/* scoped 样式默认不会穿透到 el-menu 的内部结构，这里用 :deep 处理 */
:deep(.header-menu.el-menu--horizontal) {
  border-bottom: none;
}
:deep(.header-menu .el-menu-item) {
  border-bottom: 2px solid transparent;
  font-size: 15px;
  font-weight: 500;
  height: 64px;
  line-height: 64px;
  margin: 0 8px;
  padding: 0 16px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
:deep(.header-menu .el-menu-item:hover) {
  background-color: rgba(37, 99, 235, 0.05) !important;
  color: var(--ina-primary) !important;
  transform: translateY(-2px);
}
:deep(.header-menu .el-menu-item:active) {
  transform: scale(0.95);
}
:deep(.header-menu .el-menu-item.is-active) {
  color: var(--ina-primary) !important;
  background: rgba(37, 99, 235, 0.08) !important;
  border-bottom: none !important;
  font-weight: 600;
}

:deep(.header-menu .el-menu-item .el-icon) {
  color: inherit;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  white-space: nowrap;
}
.welcome-text {
  color: var(--ina-text-2);
  font-size: 14px;
  font-weight: 500;
}
.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: transparent;
}
</style>
