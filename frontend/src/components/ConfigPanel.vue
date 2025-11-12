<template>
  <div class="config-panel">
    <el-card class="header-card">
      <h1>⚙️ 配置管理面板</h1>
      <p>在线管理 OCS AI Answerer 的所有配置项</p>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card" class="config-tabs">
      <!-- 首页 -->
      <el-tab-pane label="🏠 首页" name="home">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><Connection /></el-icon> 服务状态
              </template>
              <div class="status-item">
                <span>服务地址:</span>
                <el-tag>{{ apiBase }}</el-tag>
              </div>
              <div class="status-item">
                <span>当前模型:</span>
                <el-tag type="success">{{ config.MODEL_PROVIDER || 'auto' }}</el-tag>
              </div>
              <div class="status-item">
                <span>思考模式:</span>
                <el-tag :type="config.ENABLE_REASONING === 'true' ? 'success' : 'info'">
                  {{ config.ENABLE_REASONING === 'true' ? '✅ 已启用' : '❌ 未启用' }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><Link /></el-icon> 快速导航
              </template>
              <el-space direction="vertical" :fill="true" style="width: 100%">
                <el-button type="primary" @click="$router.push('/viewer')" plain>
                  <el-icon><DataAnalysis /></el-icon> 答题记录
                </el-button>
                <el-button type="success" @click="$router.push('/docs')" plain>
                  <el-icon><Document /></el-icon> API文档
                </el-button>
                <el-button type="warning" @click="testConnection" plain>
                  <el-icon><Position /></el-icon> 连接测试
                </el-button>
              </el-space>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><InfoFilled /></el-icon> 系统信息
              </template>
              <div class="status-item">
                <span>版本:</span>
                <el-tag type="info">v2.2</el-tag>
              </div>
              <div class="status-item">
                <span>监听端口:</span>
                <el-tag>{{ config.PORT || '5000' }}</el-tag>
              </div>
              <div class="status-item">
                <span>日志文件:</span>
                <el-tag>{{ config.CSV_LOG_FILE || 'ocs_answers_log.csv' }}</el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 模型配置 -->
      <el-tab-pane label="🧠 模型配置" name="model">
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="模型提供商">
            <el-select v-model="config.MODEL_PROVIDER" placeholder="请选择">
              <el-option label="自动选择 (智能路由)" value="auto" />
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="豆包 (Doubao)" value="doubao" />
            </el-select>
          </el-form-item>

          <el-divider content-position="left">DeepSeek 配置</el-divider>
          <el-form-item label="API Key">
            <el-input v-model="config.DEEPSEEK_API_KEY" type="password" show-password placeholder="sk-..." />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="config.DEEPSEEK_BASE_URL" placeholder="https://api.deepseek.com" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="config.DEEPSEEK_MODEL" placeholder="deepseek-chat" />
          </el-form-item>

          <el-divider content-position="left">豆包 (Doubao) 配置</el-divider>
          <el-form-item label="API Key">
            <el-input v-model="config.DOUBAO_API_KEY" type="password" show-password placeholder="..." />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="config.DOUBAO_BASE_URL" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
          </el-form-item>
          <el-form-item label="模型ID">
            <el-input v-model="config.DOUBAO_MODEL" placeholder="ep-..." />
          </el-form-item>

          <el-divider content-position="left">智能模型选择</el-divider>
          <el-form-item label="启用智能选择">
            <el-switch v-model="config.AUTO_MODEL_SELECTION" active-value="true" inactive-value="false" />
          </el-form-item>
          <el-form-item label="纯文本首选模型">
            <el-select v-model="config.PREFER_MODEL">
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="豆包" value="doubao" />
            </el-select>
          </el-form-item>
          <el-form-item label="图片题目模型">
            <el-select v-model="config.IMAGE_MODEL">
              <el-option label="豆包" value="doubao" />
              <el-option label="DeepSeek" value="deepseek" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 思考模式 -->
      <el-tab-pane label="💡 思考模式" name="reasoning">
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="启用深度推理">
            <el-switch v-model="config.ENABLE_REASONING" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">全局启用推理模式</el-text>
          </el-form-item>
          <el-form-item label="思考强度">
            <el-radio-group v-model="config.REASONING_EFFORT">
              <el-radio value="low">低</el-radio>
              <el-radio value="medium">中</el-radio>
              <el-radio value="high">高</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="多选题自动思考">
            <el-switch v-model="config.AUTO_REASONING_FOR_MULTIPLE" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">仅多选题启用思考</el-text>
          </el-form-item>
          <el-form-item label="图片题自动思考">
            <el-switch v-model="config.AUTO_REASONING_FOR_IMAGES" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">包含图片时启用思考</el-text>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- AI参数 -->
      <el-tab-pane label="🎛️ AI参数" name="ai">
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="温度 (Temperature)">
            <el-slider v-model.number="config.TEMPERATURE" :min="0" :max="2" :step="0.1" show-input />
          </el-form-item>
          <el-form-item label="最大Token (普通)">
            <el-input-number v-model.number="config.MAX_TOKENS" :min="100" :max="8192" :step="100" />
          </el-form-item>
          <el-form-item label="最大Token (思考)">
            <el-input-number v-model.number="config.REASONING_MAX_TOKENS" :min="1000" :max="65536" :step="1000" />
          </el-form-item>
          <el-form-item label="Top P">
            <el-slider v-model.number="config.TOP_P" :min="0" :max="1" :step="0.05" show-input />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 网络配置 -->
      <el-tab-pane label="🌐 网络配置" name="network">
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="HTTP 代理">
            <el-input v-model="config.HTTP_PROXY" placeholder="http://proxy:port" />
          </el-form-item>
          <el-form-item label="HTTPS 代理">
            <el-input v-model="config.HTTPS_PROXY" placeholder="https://proxy:port" />
          </el-form-item>
          <el-form-item label="请求超时 (秒)">
            <el-input-number v-model.number="config.TIMEOUT" :min="10" :max="3600" />
          </el-form-item>
          <el-form-item label="最大重试次数">
            <el-input-number v-model.number="config.MAX_RETRIES" :min="0" :max="10" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 系统配置 -->
      <el-tab-pane label="🔧 系统配置" name="system">
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="监听地址">
            <el-input v-model="config.HOST" placeholder="0.0.0.0" />
          </el-form-item>
          <el-form-item label="监听端口">
            <el-input-number v-model.number="config.PORT" :min="1000" :max="65535" />
          </el-form-item>
          <el-form-item label="调试模式">
            <el-switch v-model="config.DEBUG" active-value="true" inactive-value="false" />
          </el-form-item>
          <el-form-item label="日志级别">
            <el-select v-model="config.LOG_LEVEL">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
          </el-form-item>
          <el-form-item label="CSV日志文件">
            <el-input v-model="config.CSV_LOG_FILE" placeholder="ocs_answers_log.csv" />
          </el-form-item>
        </el-form>
        
        <!-- 安全设置 -->
        <el-divider content-position="left">🔐 安全设置</el-divider>
        <el-form :model="keyForm" label-width="180px" label-position="left">
          <el-alert
            title="修改访问密钥"
            type="warning"
            description="修改密钥后，所有已登录的设备需要重新输入新密钥。密钥长度至少8个字符。"
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-form-item label="当前密钥">
            <el-input
              v-model="keyForm.oldKey"
              type="password"
              placeholder="输入当前密钥"
              show-password
            />
          </el-form-item>
          <el-form-item label="新密钥">
            <el-input
              v-model="keyForm.newKey"
              type="password"
              placeholder="至少8个字符"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认新密钥">
            <el-input
              v-model="keyForm.confirmKey"
              type="password"
              placeholder="再次输入新密钥"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button type="warning" @click="updateKey" :loading="keyLoading">
              <el-icon><Lock /></el-icon> 更新密钥
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <el-card class="action-card">
      <el-space>
        <el-button type="primary" size="large" @click="saveConfig" :loading="saving">
          <el-icon><Check /></el-icon> 保存配置
        </el-button>
        <el-button type="success" size="large" @click="saveAndRestart" :loading="restarting">
          <el-icon><Refresh /></el-icon> 保存并重启
        </el-button>
        <el-button type="info" size="large" @click="loadConfig" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新配置
        </el-button>
        <el-button type="warning" size="large" @click="resetConfig">
          <el-icon><RefreshLeft /></el-icon> 重置为默认
        </el-button>
      </el-space>
    </el-card>
    
    <!-- 认证对话框（强制认证，不可关闭） -->
    <AuthDialog v-model="showAuthDialog" :closable="false" @success="onAuthSuccess" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axiosInstance from '../utils/axios'
import { hasApiKey, clearApiKey } from '../utils/auth'
import AuthDialog from './AuthDialog.vue'

// 使用认证的axios实例
const axios = axiosInstance

const activeTab = ref('home')
const loading = ref(false)
const saving = ref(false)
const restarting = ref(false)
const keyLoading = ref(false)
const showAuthDialog = ref(false)
const apiBase = window.location.origin

// 密钥表单
const keyForm = reactive({
  oldKey: '',
  newKey: '',
  confirmKey: ''
})

const config = reactive({
  MODEL_PROVIDER: 'auto',
  AUTO_MODEL_SELECTION: 'true',
  PREFER_MODEL: 'deepseek',
  IMAGE_MODEL: 'doubao',
  DEEPSEEK_API_KEY: '',
  DEEPSEEK_BASE_URL: 'https://api.deepseek.com',
  DEEPSEEK_MODEL: 'deepseek-chat',
  DOUBAO_API_KEY: '',
  DOUBAO_BASE_URL: 'https://ark.cn-beijing.volces.com/api/v3',
  DOUBAO_MODEL: '',
  ENABLE_REASONING: 'false',
  REASONING_EFFORT: 'medium',
  AUTO_REASONING_FOR_MULTIPLE: 'true',
  AUTO_REASONING_FOR_IMAGES: 'true',
  TEMPERATURE: 0.1,
  MAX_TOKENS: 500,
  REASONING_MAX_TOKENS: 4096,
  TOP_P: 0.95,
  HTTP_PROXY: '',
  HTTPS_PROXY: '',
  TIMEOUT: 180,
  MAX_RETRIES: 3,
  HOST: '0.0.0.0',
  PORT: 5000,
  DEBUG: 'false',
  LOG_LEVEL: 'INFO',
  CSV_LOG_FILE: 'ocs_answers_log.csv'
})

const loadConfig = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/config')
    Object.assign(config, response.data)
    
    // 转换数值类型
    config.TEMPERATURE = parseFloat(config.TEMPERATURE) || 0.1
    config.MAX_TOKENS = parseInt(config.MAX_TOKENS) || 500
    config.REASONING_MAX_TOKENS = parseInt(config.REASONING_MAX_TOKENS) || 4096
    config.TOP_P = parseFloat(config.TOP_P) || 0.95
    config.TIMEOUT = parseFloat(config.TIMEOUT) || 180
    config.MAX_RETRIES = parseInt(config.MAX_RETRIES) || 3
    config.PORT = parseInt(config.PORT) || 5000
    
    ElMessage.success('配置加载成功')
  } catch (error) {
    ElMessage.error('加载配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    // 转换为字符串
    const saveData = {
      ...config,
      TEMPERATURE: String(config.TEMPERATURE),
      MAX_TOKENS: String(config.MAX_TOKENS),
      REASONING_MAX_TOKENS: String(config.REASONING_MAX_TOKENS),
      TOP_P: String(config.TOP_P),
      TIMEOUT: String(config.TIMEOUT),
      MAX_RETRIES: String(config.MAX_RETRIES),
      PORT: String(config.PORT)
    }
    
    await axios.post('/api/config', saveData)
    ElMessage.success('配置保存成功！请重启服务以应用新配置')
  } catch (error) {
    ElMessage.error('保存配置失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

// 保存并重启服务器
const saveAndRestart = async () => {
  ElMessageBox.confirm(
    '此操作将保存配置并重启服务器，大约需要 3-5 秒。确定继续吗？',
    '保存并重启',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    restarting.value = true
    
    try {
      // 1. 先保存配置
      const saveData = {
        ...config,
        TEMPERATURE: String(config.TEMPERATURE),
        MAX_TOKENS: String(config.MAX_TOKENS),
        REASONING_MAX_TOKENS: String(config.REASONING_MAX_TOKENS),
        TOP_P: String(config.TOP_P),
        TIMEOUT: String(config.TIMEOUT),
        MAX_RETRIES: String(config.MAX_RETRIES),
        PORT: String(config.PORT)
      }
      
      await axios.post('/api/config', saveData)
      ElMessage.success('✅ 配置已保存')
      
      // 2. 触发重启
      await axios.post('/api/restart')
      ElMessage.info('🔄 服务器正在重启...')
      
      // 3. 轮询检测服务器状态
      let attempts = 0
      const maxAttempts = 30 // 最多尝试30次（30秒）
      
      const checkHealth = async () => {
        try {
          const response = await axios.get('/api/health', { timeout: 2000 })
          if (response.status === 200) {
            restarting.value = false
            ElMessage.success('✅ 服务器重启成功！')
            // 重新加载配置
            await loadConfig()
            return true
          }
        } catch (error) {
          // 连接失败，继续轮询
          return false
        }
      }
      
      // 等待2秒后开始轮询（给服务器时间关闭）
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const pollInterval = setInterval(async () => {
        attempts++
        
        if (attempts > maxAttempts) {
          clearInterval(pollInterval)
          restarting.value = false
          ElMessage.error('⚠️ 服务器重启超时，请手动检查')
          return
        }
        
        const isHealthy = await checkHealth()
        if (isHealthy) {
          clearInterval(pollInterval)
        } else {
          console.log(`轮询服务器状态... (${attempts}/${maxAttempts})`)
        }
      }, 1000) // 每秒检查一次
      
    } catch (error) {
      restarting.value = false
      if (error.code === 'ECONNABORTED' || error.message.includes('Network Error')) {
        // 服务器正在重启，这是预期行为
        ElMessage.info('🔄 服务器正在重启，请稍候...')
      } else {
        ElMessage.error('❌ 操作失败: ' + error.message)
      }
    }
  }).catch(() => {})
}

const resetConfig = () => {
  ElMessageBox.confirm(
    '确定要重置所有配置为默认值吗？此操作不可撤销！',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    config.MODEL_PROVIDER = 'auto'
    config.AUTO_MODEL_SELECTION = 'true'
    config.PREFER_MODEL = 'deepseek'
    config.IMAGE_MODEL = 'doubao'
    config.ENABLE_REASONING = 'false'
    config.REASONING_EFFORT = 'medium'
    config.AUTO_REASONING_FOR_MULTIPLE = 'true'
    config.AUTO_REASONING_FOR_IMAGES = 'true'
    config.TEMPERATURE = 0.1
    config.MAX_TOKENS = 500
    config.REASONING_MAX_TOKENS = 4096
    config.TOP_P = 0.95
    config.TIMEOUT = 180
    config.MAX_RETRIES = 3
    ElMessage.info('配置已重置为默认值')
  }).catch(() => {})
}

const testConnection = async () => {
  try {
    const start = Date.now()
    await axios.head(`/?t=${start}`)
    const latency = Date.now() - start
    ElMessage.success(`连接成功！延迟: ${latency}ms`)
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message)
  }
}

// 更新访问密钥
const updateKey = async () => {
  // 验证表单
  if (!keyForm.oldKey) {
    ElMessage.warning('请输入当前密钥')
    return
  }
  if (!keyForm.newKey) {
    ElMessage.warning('请输入新密钥')
    return
  }
  if (keyForm.newKey.length < 8) {
    ElMessage.warning('新密钥长度至少8个字符')
    return
  }
  if (keyForm.newKey !== keyForm.confirmKey) {
    ElMessage.warning('两次输入的新密钥不一致')
    return
  }
  
  keyLoading.value = true
  try {
    const response = await axios.post('/api/auth/update-key', {
      old_key: keyForm.oldKey,
      new_key: keyForm.newKey
    })
    
    if (response.data.success) {
      ElMessage.success('✅ 密钥更新成功！请使用新密钥重新登录')
      
      // 清除表单
      keyForm.oldKey = ''
      keyForm.newKey = ''
      keyForm.confirmKey = ''
      
      // 清除本地存储的密钥
      clearApiKey()
      
      // 3秒后刷新页面
      setTimeout(() => {
        window.location.reload()
      }, 3000)
    } else {
      ElMessage.error('❌ ' + (response.data.error || '更新失败'))
    }
  } catch (error) {
    console.error('更新密钥失败:', error)
    ElMessage.error('❌ 更新失败: ' + (error.response?.data?.error || error.message))
  } finally {
    keyLoading.value = false
  }
}

// 认证成功处理
const onAuthSuccess = (apiKey) => {
  console.log('认证成功，重新加载配置')
  loadConfig()
}

// 监听全局认证事件
const handleAuthRequired = () => {
  showAuthDialog.value = true
}

onMounted(() => {
  // 检查是否有API密钥
  if (!hasApiKey()) {
    showAuthDialog.value = true
  } else {
    loadConfig()
  }
  
  // 监听认证事件
  window.addEventListener('auth-required', handleAuthRequired)
})

onUnmounted(() => {
  window.removeEventListener('auth-required', handleAuthRequired)
})
</script>

<style scoped>
.config-panel {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-card h1 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.dark .header-card h1 {
  color: #79bbff;
}

.header-card p {
  margin: 0;
  color: #909399;
}

.dark .header-card p {
  color: #a8abb2;
}

.config-tabs {
  margin-bottom: 20px;
}

.action-card {
  text-align: center;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.dark .status-item {
  border-bottom-color: #414243;
}

.status-item:last-child {
  border-bottom: none;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>
