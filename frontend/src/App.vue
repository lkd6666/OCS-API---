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
          <el-menu-item index="/models">
            <el-icon><Grid /></el-icon>
            <span>模型管理</span>
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
        <div class="header-right">
          <div class="theme-switch">
            <el-dropdown @command="handleThemeChange">
              <el-button :icon="themeIcon" circle />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="auto">
                    <el-icon><Monitor /></el-icon>
                    <span>跟随系统</span>
                    <el-icon v-if="themeMode === 'auto'" style="margin-left: 8px;"><Check /></el-icon>
                  </el-dropdown-item>
                  <el-dropdown-item command="light">
                    <el-icon><Sunny /></el-icon>
                    <span>浅色模式</span>
                    <el-icon v-if="themeMode === 'light'" style="margin-left: 8px;"><Check /></el-icon>
                  </el-dropdown-item>
                  <el-dropdown-item command="dark">
                    <el-icon><Moon /></el-icon>
                    <span>深色模式</span>
                    <el-icon v-if="themeMode === 'dark'" style="margin-left: 8px;"><Check /></el-icon>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="status">
            <el-tag :type="serviceStatus ? 'success' : 'danger'" effect="dark">
              {{ serviceStatus ? '🟢 运行中' : '🔴 离线' }}
            </el-tag>
          </div>
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
      <span>© 2025 OCS AI Answerer v2.3 | Powered by Vue3 + Element Plus</span>
    </el-footer>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Sunny, Moon, Monitor, Check } from '@element-plus/icons-vue'
import axios from 'axios'
import { 
  getThemeMode, 
  saveThemeMode, 
  getActualTheme, 
  applyTheme, 
  watchSystemTheme 
} from './utils/theme'

const router = useRouter()
const route = useRoute()
const serviceStatus = ref(false)
const themeMode = ref('auto')
const actualTheme = ref('light')
let statusCheckInterval = null
let unwatchSystemTheme = null

const activeRoute = computed(() => route.path)

const themeIcon = computed(() => {
  if (themeMode.value === 'auto') {
    return Monitor
  } else if (themeMode.value === 'light') {
    return Sunny
  } else {
    return Moon
  }
})

const handleMenuSelect = (index) => {
  router.push(index)
}

const handleThemeChange = (mode) => {
  themeMode.value = mode
  saveThemeMode(mode)
  updateTheme()
}

const updateTheme = () => {
  const theme = getActualTheme(themeMode.value)
  actualTheme.value = theme
  applyTheme(theme)
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
  // 初始化主题
  themeMode.value = getThemeMode()
  updateTheme()
  
  // 监听系统主题变化（仅在auto模式下生效）
  unwatchSystemTheme = watchSystemTheme(() => {
    if (themeMode.value === 'auto') {
      updateTheme()
    }
  })
  
  // 检查服务状态
  checkServiceStatus()
  statusCheckInterval = setInterval(checkServiceStatus, 30000)
})

onUnmounted(() => {
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval)
  }
  if (unwatchSystemTheme) {
    unwatchSystemTheme()
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: background 0.3s ease;
}

.dark .app-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.app-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 60px;
  line-height: 60px;
  transition: background 0.3s ease, box-shadow 0.3s ease;
}

.dark .app-header {
  background: #1a1a1a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
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
  transition: color 0.3s ease;
}

.dark .logo {
  color: #8b9cff;
}

.header-menu {
  flex: 1;
  border: none;
  margin: 0 40px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.theme-switch {
  display: flex;
  align-items: center;
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
  transition: background 0.3s ease;
}

.dark .app-footer {
  background: rgba(0, 0, 0, 0.3);
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
