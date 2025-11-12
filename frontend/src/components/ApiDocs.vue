<template>
  <div class="api-docs">
    <el-card class="header-card">
      <h1>📖 API 接口文档</h1>
      <p>OCS AI Answerer REST API 完整参考</p>
    </el-card>

    <el-collapse v-model="activeNames" class="docs-collapse">
      <!-- 答题接口 -->
      <el-collapse-item name="answer">
        <template #title>
          <div class="api-title">
            <el-tag type="success">POST</el-tag>
            <span class="api-path">/api/answer</span>
            <span class="api-desc">智能答题接口</span>
          </div>
        </template>
        <div class="api-content">
          <h3>请求参数</h3>
          <el-table :data="answerParams" border>
            <el-table-column prop="name" label="参数名" width="150" />
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.required ? 'danger' : 'info'" size="small">
                  {{ scope.row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>

          <h3>请求示例</h3>
          <el-input
            v-model="answerExample"
            type="textarea"
            :rows="12"
            readonly
            class="code-block"
          />

          <h3>响应示例</h3>
          <el-input
            v-model="answerResponse"
            type="textarea"
            :rows="8"
            readonly
            class="code-block"
          />
        </div>
      </el-collapse-item>

      <!-- 健康检查 -->
      <el-collapse-item name="health">
        <template #title>
          <div class="api-title">
            <el-tag type="primary">GET</el-tag>
            <span class="api-path">/api/health</span>
            <span class="api-desc">服务健康检查</span>
          </div>
        </template>
        <div class="api-content">
          <h3>响应示例</h3>
          <el-input
            v-model="healthResponse"
            type="textarea"
            :rows="10"
            readonly
            class="code-block"
          />
        </div>
      </el-collapse-item>

      <!-- 配置查询 -->
      <el-collapse-item name="config-get">
        <template #title>
          <div class="api-title">
            <el-tag type="primary">GET</el-tag>
            <span class="api-path">/api/config</span>
            <span class="api-desc">获取当前配置</span>
          </div>
        </template>
        <div class="api-content">
          <h3>响应示例</h3>
          <el-input
            v-model="configGetResponse"
            type="textarea"
            :rows="15"
            readonly
            class="code-block"
          />
        </div>
      </el-collapse-item>

      <!-- 配置保存 -->
      <el-collapse-item name="config-post">
        <template #title>
          <div class="api-title">
            <el-tag type="success">POST</el-tag>
            <span class="api-path">/api/config</span>
            <span class="api-desc">保存配置到.env</span>
          </div>
        </template>
        <div class="api-content">
          <h3>请求示例</h3>
          <el-input
            v-model="configPostRequest"
            type="textarea"
            :rows="8"
            readonly
            class="code-block"
          />

          <h3>响应示例</h3>
          <el-input
            v-model="configPostResponse"
            type="textarea"
            :rows="6"
            readonly
            class="code-block"
          />
        </div>
      </el-collapse-item>

      <!-- CSV数据 -->
      <el-collapse-item name="csv">
        <template #title>
          <div class="api-title">
            <el-tag type="primary">GET</el-tag>
            <span class="api-path">/api/csv</span>
            <span class="api-desc">获取CSV日志</span>
          </div>
        </template>
        <div class="api-content">
          <p>返回完整的 CSV 格式答题日志文件</p>
        </div>
      </el-collapse-item>

      <!-- 清空日志 -->
      <el-collapse-item name="csv-clear">
        <template #title>
          <div class="api-title">
            <el-tag type="danger">POST</el-tag>
            <span class="api-path">/api/csv/clear</span>
            <span class="api-desc">清空答题日志</span>
          </div>
        </template>
        <div class="api-content">
          <h3>响应示例</h3>
          <el-input
            v-model="csvClearResponse"
            type="textarea"
            :rows="3"
            readonly
            class="code-block"
          />
        </div>
      </el-collapse-item>

      <!-- 延迟测试 -->
      <el-collapse-item name="latency">
        <template #title>
          <div class="api-title">
            <el-tag type="warning">HEAD/GET</el-tag>
            <span class="api-path">/?t={timestamp}</span>
            <span class="api-desc">连接延迟测试</span>
          </div>
        </template>
        <div class="api-content">
          <p>用于测试客户端到服务器的网络延迟</p>
          <h3>请求参数</h3>
          <ul>
            <li><code>t</code> - Unix时间戳（毫秒）</li>
          </ul>
          <h3>响应头</h3>
          <ul>
            <li><code>X-Latency</code> - 计算出的延迟（毫秒）</li>
          </ul>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-card class="tips-card">
      <template #header>
        <el-icon><InfoFilled /></el-icon> 使用提示
      </template>
      <ul>
        <li>所有接口默认监听 <code>0.0.0.0:5000</code></li>
        <li>支持跨域访问 (CORS)</li>
        <li>图片支持 Base64 和 URL 两种格式</li>
        <li>答题接口自动选择最优模型（智能模式下）</li>
        <li>配置修改后需重启服务才能生效</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeNames = ref(['answer'])

const answerParams = [
  { name: 'question_type', type: 'integer', required: true, description: '题目类型：0=单选，1=多选，3=填空，4=判断' },
  { name: 'question_text', type: 'string', required: true, description: '问题内容' },
  { name: 'options', type: 'array', required: false, description: '选项列表（选择题必填）' },
  { name: 'images', type: 'array', required: false, description: '图片URL列表' }
]

const answerExample = `{
  "question_type": 0,
  "question_text": "以下哪个是Vue3的响应式API？",
  "options": [
    "ref",
    "data",
    "state",
    "props"
  ],
  "images": []
}`

const answerResponse = `[
  "以下哪个是Vue3的响应式API？",
  "ref",
  {
    "ai": true,
    "tags": ["deepseek-chat", "自动选择"],
    "model": "deepseek-chat",
    "reasoning_used": false,
    "ai_time": 1.23
  }
]`

const healthResponse = `{
  "status": "ok",
  "service": "OCS AI Answerer (Multi-Model)",
  "version": "2.2.0",
  "provider": "auto",
  "model": "deepseek-chat",
  "reasoning_enabled": false,
  "api_configured": true,
  "init_error": null
}`

const configGetResponse = `{
  "MODEL_PROVIDER": "auto",
  "AUTO_MODEL_SELECTION": "true",
  "PREFER_MODEL": "deepseek",
  "IMAGE_MODEL": "doubao",
  "DEEPSEEK_API_KEY": "sk-12345...",
  "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
  "DEEPSEEK_MODEL": "deepseek-chat",
  "ENABLE_REASONING": "false",
  "TEMPERATURE": "0.1",
  "MAX_TOKENS": "500",
  ...
}`

const configPostRequest = `{
  "MODEL_PROVIDER": "auto",
  "DEEPSEEK_API_KEY": "sk-xxxxx",
  "ENABLE_REASONING": "true",
  "TEMPERATURE": "0.2",
  ...
}`

const configPostResponse = `{
  "success": true,
  "message": "配置已成功保存到 .env 文件",
  "file": "/path/to/.env",
  "note": "请重启服务以应用新配置"
}`

const csvClearResponse = `{
  "message": "CSV日志已清空"
}`
</script>

<style scoped>
.api-docs {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
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

.docs-collapse {
  margin-bottom: 20px;
}

.api-title {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 16px;
}

.api-path {
  font-family: 'Courier New', monospace;
  font-weight: bold;
  color: #303133;
}

.dark .api-path {
  color: #e5eaf3;
}

.api-desc {
  color: #909399;
}

.dark .api-desc {
  color: #a8abb2;
}

.api-content {
  padding: 20px;
}

.api-content h3 {
  margin: 20px 0 10px 0;
  color: #409eff;
  font-size: 16px;
}

.dark .api-content h3 {
  color: #79bbff;
}

.code-block {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin-bottom: 20px;
}

.tips-card ul {
  margin: 10px 0;
  padding-left: 20px;
}

.tips-card li {
  margin: 8px 0;
  line-height: 1.6;
}

code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #e6a23c;
  font-family: 'Courier New', monospace;
}

.dark code {
  background: #262727;
  color: #e6a23c;
}
</style>
