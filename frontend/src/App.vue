<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="28"><Setting /></el-icon>
          <span class="title">OCS AI Answerer</span>
        </div>
        <el-menu
          :default-active="activeRoute"
          mode="horizontal"
          :ellipsis="false"
          @select="handleMenuSelect"
          class="header-menu"
        >
          <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <span>配置管理</span>
          </el-menu-item>
          <el-menu-item index="/viewer">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据可视化</span>
          </el-menu-item>
          <el-menu-item index="/docs">
            <el-icon><Document /></el-icon>
            <span>API文档</span>
          </el-menu-item>
        </el-menu>
        <div class="status">
          <el-tag :type="serviceStatus ? 'success' : 'danger'" effect="dark">
            {{ serviceStatus ? '🟢 运行中' : '🔴 离线' }}
          </el-tag>
        </div>
      </div>
    </el-header>
    
    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
    
    <el-footer class="app-footer">
      <span>© 2025 OCS AI Answerer v2.2 | Powered by Vue3 + Element Plus</span>
    </el-footer>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const serviceStatus = ref(false)
let statusCheckInterval = null

const activeRoute = computed(() => route.path)

const handleMenuSelect = (index) => {
  router.push(index)
}

const checkServiceStatus = async () => {
  try {
    const response = await axios.head(`/?t=${Date.now()}`, { timeout: 5000 })
    serviceStatus.value = response.status === 200
  } catch (error) {
    serviceStatus.value = false
  }
}

onMounted(() => {
  checkServiceStatus()
  statusCheckInterval = setInterval(checkServiceStatus, 30000)
})

onUnmounted(() => {
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval)
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 60px;
  line-height: 60px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
}

.header-menu {
  flex: 1;
  border: none;
  margin: 0 40px;
}

.status {
  min-width: 100px;
  text-align: right;
}

.app-main {
  padding: 20px;
  overflow-y: auto;
}

.app-footer {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  text-align: center;
  height: 40px;
  line-height: 40px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
