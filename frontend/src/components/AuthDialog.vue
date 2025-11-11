<template>
  <el-dialog
    v-model="visible"
    title="🔐 访问密钥验证"
    width="600px"
    :close-on-click-modal="closable"
    :close-on-press-escape="closable"
    :show-close="closable"
  >
    <el-form :model="form" label-width="80px">
      <el-alert
        title="需要访问密钥"
        type="warning"
        description="请输入服务器生成的访问密钥以继续使用。密钥已在服务器启动时显示在控制台。"
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <el-form-item label="访问密钥">
        <el-input
          v-model="form.apiKey"
          type="password"
          placeholder="请输入64位访问密钥"
          show-password
          @keyup.enter="submitKey"
        />
      </el-form-item>
      
      <el-form-item v-if="errorMessage">
        <el-alert
          :title="errorMessage"
          type="error"
          :closable="false"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <!-- 导航链接（始终显示） -->
        <div style="flex: 1; text-align: left;">
          <el-text type="info" size="small" style="display: block; margin-bottom: 8px;">
            {{ closable ? '💡 提示：您可以先访问其他页面' : '💡 提示：配置页面需要密钥，其他页面可直接访问' }}
          </el-text>
          <el-link type="primary" href="/" style="margin-right: 15px;">🏠 首页</el-link>
          <el-link type="primary" href="/viewer" style="margin-right: 15px;">📊 数据可视化</el-link>
          <el-link type="primary" href="/api">� API文档</el-link>
        </div>
        
        <!-- 验证按钮 -->
        <el-button type="primary" @click="submitKey" :loading="loading" style="margin-left: 20px;">
          验证并继续
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { saveApiKey } from '../utils/auth'

const props = defineProps({
  modelValue: Boolean,
  closable: {
    type: Boolean,
    default: false  // 默认不可关闭（强制认证）
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const form = ref({
  apiKey: ''
})
const loading = ref(false)
const errorMessage = ref('')

const submitKey = async () => {
  if (!form.value.apiKey) {
    errorMessage.value = '请输入访问密钥'
    return
  }
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    // 验证密钥
    const response = await axios.post('/api/auth/verify', {
      api_key: form.value.apiKey
    })
    
    if (response.data.valid) {
      // 保存密钥
      saveApiKey(form.value.apiKey)
      
      // 通知父组件
      emit('success', form.value.apiKey)
      emit('update:modelValue', false)
      
      ElMessage.success('✅ 验证成功！')
    } else {
      errorMessage.value = response.data.error || '密钥无效'
    }
  } catch (error) {
    console.error('验证失败:', error)
    if (error.response?.status === 429) {
      errorMessage.value = '错误次数过多，请稍后重试'
    } else {
      errorMessage.value = error.response?.data?.error || '验证失败，请检查密钥是否正确'
    }
  } finally {
    loading.value = false
  }
}

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})
</script>

<style scoped>
:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
}

:deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
}
</style>
