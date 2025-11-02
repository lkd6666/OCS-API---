# OCS智能答题API - 多模型支持版本

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![DeepSeek](https://img.shields.io/badge/DeepSeek-AI-orange.svg)
![Doubao](https://img.shields.io/badge/Doubao-AI-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![AI Maintained](https://img.shields.io/badge/Maintained%20by-AI-00D9FF.svg)

一个专为[OCS网课助手](https://docs.ocsjs.com/)设计的智能答题API，支持DeepSeek、豆包等多个大语言模型，提供强大的AI答题能力。

> 📌 **关于 OCS**
> 
> [OCS (Online Course Script)](https://docs.ocsjs.com/) 是一款功能强大的网课助手脚本，支持超星学习通、智慧树、职教云等多个平台。本项目为 OCS 提供 AI 智能答题能力。
> 
> - 🌐 官方网站：https://docs.ocsjs.com/
> - 📦 脚本安装：https://docs.ocsjs.com/docs/work
> - 💬 交流社区：https://docs.ocsjs.com/

---

> 🤖 **AI 驱动开发**
> 
> 本项目由 AI 辅助设计、开发和维护，代表了人工智能在软件工程领域的实践应用。
> 
> - 💡 **智能设计**：AI 参与架构设计和功能规划
> - 🔧 **代码生成**：核心代码由 AI 协助编写和优化
> - 📝 **文档维护**：技术文档由 AI 自动生成和更新
> - 🐛 **问题诊断**：AI 协助分析和修复问题
> 
> 这种开发模式确保了代码质量、快速迭代和持续优化。

---

</div>

## ✨ 特性

### 🤖 AI驱动
- **多模型支持**：DeepSeek、豆包(Doubao)等多个大语言模型
- **思考模式**：支持DeepSeek Reasoner和豆包深度思考模式
- **多选题智能**：多选题自动启用深度思考，提高准确率
- **智能理解**：强大的自然语言理解能力

### 🎯 题型支持
- ✅ 单选题（Single Choice）
- ✅ 多选题（Multiple Choice） - 自动深度思考
- ✅ 判断题（True/False）
- ✅ 填空题（Completion）

### 🖼️ 多模态支持
- **图片识别**：豆包模型支持图片+文本混合输入
- **自动提取**：从题目中自动提取图片URL
- **智能降级**：图片访问失败时自动切换纯文本模式

### 📊 数据记录
- **CSV日志**：记录每道题的详细信息（题目、选项、答案、思考过程、耗时等）
- **可视化界面**：内置HTML可视化页面，图表展示答题数据
- **数据统计**：题型分布、思考模式使用、平均耗时等

### 🔧 其他特性
- 📝 **精准Prompt**：针对不同题型优化的提示词工程
- 🔄 **智能清洗**：答案格式化和匹配优化
- 🚀 **即插即用**：完美对接OCS脚本题库配置
- 🔁 **重试机制**：网络错误自动重试，支持代理配置
- ⚙️ **灵活配置**：所有参数通过环境变量配置
- 🏷️ **标签展示**：在OCS中显示AI、深度思考、模型等标签

## 📋 目录

- [快速开始](#快速开始)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [配置OCS脚本](#配置ocs脚本)
- [API文档](#api文档)
- [功能介绍](#功能介绍)
- [常见问题](#常见问题)
- [功能规划](#功能规划)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.template` 为 `.env` 并编辑：

```bash
# Windows
copy env.template .env

# Linux/Mac
cp env.template .env
```

### 🔑 获取API密钥

#### DeepSeek（推荐，性价比高）

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 [API密钥页面](https://platform.deepseek.com/api_keys)
4. 点击"创建API密钥"
5. 复制生成的密钥（格式：`sk-xxxxxx...`）
6. 粘贴到 `.env` 文件的 `DEEPSEEK_API_KEY`

#### 豆包（可选，支持图片）

1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
2. 注册/登录账号
3. 开通"豆包大模型"服务
4. 创建推理接入点，获取：
   - API密钥（填入 `DOUBAO_API_KEY`）
   - 接入点ID（填入 `DOUBAO_MODEL`）

### 📝 编辑配置文件

编辑 `.env` 文件，填入API密钥：

```env
# 选择模型提供商：deepseek、doubao 或 auto（智能选择）
MODEL_PROVIDER=auto  # 推荐使用auto模式

# DeepSeek配置（纯文本题目，成本低）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key  # 👈 填入你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 豆包配置（图片题目，支持多模态）
DOUBAO_API_KEY=your-doubao-api-key         # 👈 填入你的密钥
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-251015        # 👈 填入你的接入点ID

# 思考模式（推荐配置）
ENABLE_REASONING=false
AUTO_REASONING_FOR_MULTIPLE=true  # 多选题自动启用
```


### 3. 启动服务

```bash
python ocs_ai_answerer_advanced.py
```

看到以下输出表示启动成功：

```
╔═══════════════════════════════════════════════════════════╗
║       OCS智能答题API服务 - 多模型支持版本 v2.0          ║
╠═══════════════════════════════════════════════════════════╣
║  接口地址: http://localhost:5000/api/answer              
║  健康检查: http://localhost:5000/api/health              
║  配置查询: http://localhost:5000/api/config              
║  CSV数据: http://localhost:5000/api/csv                  
║  可视化页面: http://localhost:5000/viewer                
║  延迟测试: http://localhost:5000/?t=时间戳 (HEAD/GET)    
╠═══════════════════════════════════════════════════════════╣
║  当前模型: DEEPSEEK - deepseek-chat                     ║
║  思考模式: ❌ 未启用                                   ║
║  多选题思考: ✅ 自动启用                              ║
║  支持题型: 单选、多选、判断、填空                        ║
╚═══════════════════════════════════════════════════════════╝

✅ 服务启动成功！可以开始答题了
```

### 4. 配置OCS脚本

#### 方式一：安装OCS脚本（推荐）

如果还未安装 OCS 脚本，请先安装：

1. **安装脚本管理器**（推荐脚本猫）
   - Chrome/Edge：安装 [脚本猫(ScriptCat)](https://scriptcat.org/) 或 [Tampermonkey](https://www.tampermonkey.net/)
   - Firefox：安装 [脚本猫](https://scriptcat.org/) 或 [Tampermonkey](https://addons.mozilla.org/firefox/addon/tampermonkey/)
   - Safari：安装 [Userscripts](https://apps.apple.com/app/userscripts/id1463298887)
   
   > 💡 **推荐使用脚本猫**：国内开发，速度快，功能强大，更适合国内网络环境

2. **安装 OCS 脚本**
   - 访问 [OCS 官网](https://docs.ocsjs.com/docs/work)
   - 或直接在脚本管理器中添加本项目的 `ocs.user.js` 文件（包含标签兼容性优化）

3. **配置题库**
   - 在OCS脚本的"通用-全局设置-题库配置"中
   - 导入 `ocs_config.json` 文件

> 💡 **推荐使用项目提供的 `ocs.user.js`**
> 
> 本项目的 `ocs.user.js` 已针对 AI 答题功能进行优化，包含：
> - ✅ 支持 `purple` 和 `orange` 标签颜色（深度思考、自动思考标识）
> - ✅ 更好的 AI 答题标签显示
> - ✅ 完整的题库超时配置（3分钟）
> 
> **安装方法：**
> 1. 打开脚本管理器（脚本猫或Tampermonkey）
> 2. 点击"添加新脚本"或"新建脚本"
> 3. 将 `ocs.user.js` 的内容粘贴进去
> 4. 保存并启用
> 
> 或者直接从文件安装：
> 1. 下载项目中的 `ocs.user.js` 文件
> 2. 在脚本管理器中选择"从本地安装"
> 3. 选择下载的 `ocs.user.js` 文件

#### 方式二：仅配置题库（已安装OCS用户）

如果已经安装了 OCS 脚本，只需导入题库配置即可。

## 📦 安装步骤

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- DeepSeek 或 豆包 API密钥

### 详细安装

1. **克隆或下载项目**

```bash
git clone https://github.com/lkd6666/OCS-API---.git
cd OCS-API---
```

2. **创建虚拟环境（推荐）**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖包**

```bash
pip install -r requirements.txt
```

依赖包列表（`requirements.txt`）：
```
flask>=3.0.0
flask-cors>=4.0.0
openai>=1.12.0
python-dotenv>=1.0.0
httpx>=0.26.0
requests>=2.31.0
```

4. **配置环境变量**

```bash
# 复制模板
cp env.template .env

# 编辑配置
# Windows: notepad .env
# Linux/Mac: nano .env
```

5. **启动服务**

```bash
python ocs_ai_answerer_advanced.py
```

## ⚙️ 配置说明

### 🔑 API密钥获取（详细步骤）

#### 方案一：只配置 DeepSeek（推荐新手）

**优点**：成本低、配置简单、适合纯文本题目

1. **注册DeepSeek账号**
   - 访问：https://platform.deepseek.com/
   - 使用邮箱或手机号注册

2. **创建API密钥**
   - 登录后进入：https://platform.deepseek.com/api_keys
   - 点击"创建API密钥"按钮
   - 复制生成的密钥（以 `sk-` 开头）

3. **配置 .env 文件**
   ```env
   MODEL_PROVIDER=deepseek
   DEEPSEEK_API_KEY=sk-your-key-here  # 粘贴你的密钥
   ```

#### 方案二：配置 DeepSeek + 豆包（推荐进阶）

**优点**：智能选择、支持图片、效果最优

1. **获取DeepSeek密钥**（同上）

2. **获取豆包密钥和模型ID**
   - 访问：https://console.volcengine.com/ark
   - 注册/登录火山引擎账号
   - 开通"豆包大模型"服务
   - 创建推理接入点（Inference Endpoint）
   - 获取两个信息：
     * API密钥（API Key）
     * 接入点ID（Endpoint ID）

3. **配置 .env 文件**
   ```env
   MODEL_PROVIDER=auto              # 智能选择模式
   DEEPSEEK_API_KEY=sk-xxxxx       # DeepSeek密钥
   DOUBAO_API_KEY=xxxxx            # 豆包密钥
   DOUBAO_MODEL=doubao-seed-xxx    # 豆包接入点ID
   ```

### 环境变量详解

#### 模型配置

```env
# 模型提供商（deepseek、doubao 或 auto）
MODEL_PROVIDER=auto  # auto=智能选择（推荐）

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxx           # DeepSeek API密钥 👈 必填
DEEPSEEK_BASE_URL=https://api.deepseek.com  # API地址
DEEPSEEK_MODEL=deepseek-chat        # 模型名称

# 豆包配置
DOUBAO_API_KEY=xxxxx                # 豆包API密钥 👈 可选
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-251015 # 推理接入点ID 👈 可选
```

#### 思考模式配置

```env
# 全局启用思考模式（false=普通模式，true=思考模式）
ENABLE_REASONING=false

# 多选题自动启用深度思考（推荐开启）
AUTO_REASONING_FOR_MULTIPLE=true

# 豆包思考强度（low/medium/high）
REASONING_EFFORT=medium
```

**思考模式说明：**
- **普通模式**：快速响应，适合简单题目，使用 `MAX_TOKENS`
- **思考模式**：深度推理，答案更准确但耗时更长，使用 `REASONING_MAX_TOKENS`
- **多选题自动思考**：仅对多选题启用，平衡速度和准确率

> 💡 **为什么需要单独配置思考模式的 token？**
> 
> 思考模式（如 deepseek-reasoner）需要输出详细的推理过程，比普通模式需要更多的 token。如果设置太小，可能导致推理过程被截断，影响答案质量。推荐配置：
> - `MAX_TOKENS=500`（普通模式，节省成本）
> - `REASONING_MAX_TOKENS=4096`（思考模式，确保完整推理）

#### AI参数配置

```env
TEMPERATURE=0.1               # 温度参数 (0-2)，越低越稳定
MAX_TOKENS=500               # 普通模式最大输出token数
REASONING_MAX_TOKENS=4096    # 思考模式最大输出token数
TOP_P=0.95                   # 核采样参数
```

**参数详解：**

| 参数 | 范围 | 推荐值 | 作用说明 |
|------|------|--------|----------|
| **TEMPERATURE** | 0.0-2.0 | 0.1 | **控制答案的随机性和创造性**<br>• 0.0-0.3：确定性高，适合答题（推荐）<br>• 0.4-0.7：平衡，适合对话<br>• 0.8-2.0：创造性高，答案多样但可能不准确 |
| **MAX_TOKENS** | 1-8192 | 500 | **普通模式的最大输出长度**<br>• 填空题：200-300 足够<br>• 选择题：300-500 合适<br>• 复杂题目：可增加到 1000+<br>• deepseek-chat 最大：8192 |
| **REASONING_MAX_TOKENS** | 1-65536 | 4096 | **思考模式的最大输出长度**<br>• 简单思考：2000-4000<br>• 中等复杂：4096-8000（推荐）<br>• 复杂推理：8000-16000<br>• deepseek-reasoner 最大：65536 |
| **TOP_P** | 0.0-1.0 | 0.95 | **核采样，控制词汇选择范围**<br>• 0.9-1.0：词汇丰富，表达多样（推荐）<br>• 0.5-0.8：更保守，重复性增加<br>• 0.1-0.4：非常保守，可能过于机械 |

**答题场景推荐配置：**

```env
# 🎯 追求准确率（推荐）
TEMPERATURE=0.1               # 低温度，减少随机性
MAX_TOKENS=500               # 普通模式输出长度
REASONING_MAX_TOKENS=4096    # 思考模式输出长度
TOP_P=0.95                   # 保持自然表达

# ⚡ 追求速度
TEMPERATURE=0.05             # 更低温度，更快决策
MAX_TOKENS=300              # 限制输出长度
REASONING_MAX_TOKENS=2000   # 思考模式也限制
TOP_P=0.9                   # 略微降低

# 🔬 复杂题目 / 深度思考
TEMPERATURE=0.15             # 略高温度，更多思考
MAX_TOKENS=1000             # 更长的输出空间
REASONING_MAX_TOKENS=8192   # 思考模式大幅增加
TOP_P=0.95                  # 保持多样性

# 🧠 极限推理（适合超难题目）
TEMPERATURE=0.1              # 保持稳定
MAX_TOKENS=1000             
REASONING_MAX_TOKENS=16384  # 给思考模式最大空间
TOP_P=0.95
```

**参数组合效果：**

- **TEMPERATURE ↓ + TOP_P ↑**：准确但自然（最佳）
- **TEMPERATURE ↓ + TOP_P ↓**：准确但机械
- **TEMPERATURE ↑ + TOP_P ↑**：多样但不稳定
- **TEMPERATURE ↑ + TOP_P ↓**：不推荐（容易出错）

#### 网络配置

```env
HTTP_PROXY=             # HTTP代理（可选）
HTTPS_PROXY=            # HTTPS代理（可选）
TIMEOUT=1200.0          # 请求超时时间（秒）
MAX_RETRIES=3           # 最大重试次数
```

#### 服务配置

```env
HOST=0.0.0.0            # 监听地址
PORT=5000               # 监听端口
DEBUG=False             # 调试模式
CSV_LOG_FILE=ocs_answers_log.csv  # CSV日志文件路径
```

## 🔧 配置OCS脚本

### 前置要求

确保已安装 OCS 脚本。如果还没有安装，请参考 [快速开始 - 第4步](#4-配置ocs脚本)。

> 💡 **提示**：推荐使用本项目提供的 `ocs.user.js`，已包含 AI 答题的标签兼容性优化。

### 导入配置文件

1. 打开OCS脚本悬浮窗
2. 进入"通用" → "全局设置"
3. 找到"题库配置"，点击"点击配置"
4. 选择"自定义配置"
5. 将 `ocs_config.json` 的内容粘贴到文本框
6. 点击"解析并保存"

### 配置文件内容（`ocs_config.json`）

```json
{
  "name": "AI智能答题",
  "url": "http://localhost:5000/api/answer",
  "method": "post",
  "type": "fetch",
  "contentType": "json",
  "homepage": "https://github.com/yourname/ocs-ai-answerer",
  "headers": {
    "Content-Type": "application/json"
  },
  "data": {
    "question": "${title}",
    "options": {
      "handler": "return (env)=>env.options?.split('\\n')"
    },
    "type": {
      "handler": "return (env)=> env.type === 'single' ? 0 : env.type === 'multiple' ? 1 : env.type === 'completion' ? 3 : env.type === 'judgement' ? 4 : 0"
    },
    "images": {
      "handler": "return (env)=> { const imgPattern = /https?:\\/\\/[^\\s]+\\.(?:jpg|jpeg|png|gif|bmp|webp)/gi; return env.title?.match(imgPattern) || []; }"
    }
  },
  "handler": "return (res)=>res.success && res.ocs_format ? [res.ocs_format] : []"
}
```

### 验证配置

配置成功后，进入任意作业/考试页面，OCS应该显示：

> ✅ 当前有1个可用题库：AI智能答题

### OCS 脚本标签兼容性

如果使用官方原版 OCS 脚本，可能不支持 `purple` 和 `orange` 标签颜色。建议：

1. **使用项目提供的 `ocs.user.js`**（推荐）
   - 已包含所有标签颜色支持
   - 题库超时设置为3分钟
   - 完美兼容 AI 答题功能

2. **或修改现有 OCS 脚本**
   - 在 OCS 脚本中添加以下 CSS（搜索 `.search-result-answer-tag` 部分）：
   ```css
   .search-result-answer-tag.purple {
     background-color: #9b59b6;
     color: white;
   }
   .search-result-answer-tag.orange {
     background-color: #e67e22;
     color: white;
   }
   ```

### 标签说明

使用本项目的 AI 答题时，会显示以下标签：

| 标签 | 颜色 | 说明 |
|------|------|------|
| AI | 🔵 蓝色 | OCS自动添加，表示AI答题 |
| 深度思考 | 🟣 紫色 | 使用思考模式（需兼容脚本）|
| 自动思考 | 🟠 橙色 | 多选题自动启用思考（需兼容脚本）|
| 智能选择 | 🔵 蓝色 | 智能模型选择模式 |
| DEEPSEEK/DOUBAO | 🟢 绿色 | 实际使用的模型 |

## 📚 API文档

### 1. 答题接口

#### 请求

```http
POST /api/answer
Content-Type: application/json

{
  "question": "中国的首都是哪里？",
  "options": ["北京", "上海", "广州", "深圳"],
  "type": 0,
  "images": []
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 题目内容 |
| options | array | 否 | 选项列表（填空题可为空）|
| type | integer | 是 | 题型：0=单选, 1=多选, 3=填空, 4=判断 |
| images | array | 否 | 图片URL列表（仅豆包支持）|

#### 响应

```json
{
  "success": true,
  "question": "中国的首都是哪里？",
  "answer": "北京",
  "type": "single",
  "raw_answer": "北京",
  "model": "deepseek-chat",
  "provider": "deepseek",
  "reasoning_used": false,
  "ai_time": 1.23,
  "total_time": 1.25,
  "ocs_format": [
    "中国的首都是哪里？",
    "北京",
    {
      "ai": true,
      "tags": [
        {"text": "DEEPSEEK", "title": "模型: deepseek-chat", "color": "green"}
      ],
      "model": "deepseek-chat",
      "provider": "deepseek",
      "reasoning_used": false,
      "ai_time": 1.23,
      "total_time": 1.25
    }
  ]
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| question | string | 题目（回显）|
| answer | string | 处理后的答案 |
| type | string | 题型名称 |
| raw_answer | string | AI原始返回 |
| model | string | 使用的模型 |
| provider | string | 模型提供商 |
| reasoning_used | boolean | 是否使用思考模式 |
| ai_time | float | AI答题耗时（秒）|
| total_time | float | 总处理耗时（秒）|
| ocs_format | array | OCS脚本格式数据 |

### 2. 健康检查接口

```http
GET /api/health

Response:
{
  "status": "ok",
  "service": "OCS AI Answerer (Multi-Model)",
  "version": "2.0.0",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "reasoning_enabled": false,
  "api_configured": true
}
```

### 3. 配置查询接口

```http
GET /api/config

Response:
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "reasoning_enabled": false,
  "auto_reasoning_for_multiple": true,
  "reasoning_effort": null,
  "temperature": 0.1,
  "max_tokens": 500
}
```

### 4. CSV数据接口

```http
GET /api/csv
# 获取CSV日志文件

POST /api/csv/clear
# 清空CSV日志（保留表头）
```

### 5. 可视化页面

```http
GET /viewer
# 访问答题记录可视化界面
```

### 6. 延迟测试接口

```http
HEAD /?t=<timestamp>
GET /?t=<timestamp>
# OCS脚本用于测试连接延迟
```

## 🎯 功能介绍

### 1. 多模型支持

支持DeepSeek和豆包两个模型，可通过环境变量切换：

```env
MODEL_PROVIDER=deepseek  # 或 doubao
```

#### DeepSeek
- **普通模式**：`deepseek-chat`，最大8K tokens
- **思考模式**：`deepseek-reasoner`，最大64K tokens
- **特点**：响应快速，性价比高

#### 豆包（Doubao）
- **模型**：自定义推理接入点
- **思考强度**：可配置 low/medium/high
- **特点**：支持图片输入，多模态理解

### 2. 思考模式

#### 自动启用策略
- **多选题**：自动启用深度思考（可配置）
- **单选/判断/填空**：使用普通模式（除非全局启用）

#### 标签展示
在OCS界面中会显示：
- 🔵 **AI** - OCS自动添加
- 🟣 **深度思考** - 使用思考模式时显示
- 🟡 **自动思考** - 多选题自动启用时显示
- 🟢 **DEEPSEEK/DOUBAO** - 模型标识

### 3. 图片支持（豆包）

#### 自动提取
从题目文本中自动提取图片URL：
- 支持格式：jpg, jpeg, png, gif, bmp, webp
- 自动去重

#### 智能过滤
过滤无关图标URL：
- `/icon/`, `/icons/`
- `video.png`, `audio.png`
- `play.png`, `pause.png`

#### 自动降级
- 首次尝试使用图片
- 如果图片访问失败，自动切换纯文本模式
- 确保答题流程不中断

### 4. CSV日志记录

自动记录每道题的详细信息：

| 字段 | 说明 |
|------|------|
| 时间戳 | 答题时间 |
| 题型 | 单选/多选/判断/填空 |
| 题目 | 完整题目文本 |
| 选项 | 所有选项（用 \| 分隔）|
| 原始回答 | AI原始返回的答案 |
| 思考过程 | 推理过程（如果有）|
| 处理后答案 | 清洗后的最终答案 |
| AI耗时(秒) | AI调用耗时 |
| 总耗时(秒) | 总处理耗时 |
| 模型 | 使用的模型 |
| 思考模式 | 是/否 |

### 5. 数据可视化

访问 `http://localhost:5000/viewer` 查看：

- 📊 **题型分布**：饼图显示各题型数量
- 📈 **思考模式使用**：思考vs普通模式统计
- ⏱️ **平均耗时**：AI耗时和总耗时对比
- 📋 **详细列表**：可搜索、过滤的题目列表
- 🔍 **详情查看**：点击题目查看完整信息

功能：
- 搜索题目/答案
- 按题型过滤
- 按思考模式过滤
- 导出数据
- 清空数据

## 🧪 测试示例

### 使用curl测试

```bash
# 单选题
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "世界上最高的山峰是？",
    "options": ["泰山", "珠穆朗玛峰", "华山", "黄山"],
    "type": 0
  }'

# 多选题（自动启用深度思考）
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "以下哪些是Python的特点？",
    "options": ["简洁", "高效", "跨平台", "开源"],
    "type": 1
  }'

# 带图片的题目（豆包）
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "图片中是什么动物？ http://example.com/image.jpg",
    "options": ["猫", "狗", "鸟", "鱼"],
    "type": 0,
    "images": ["http://example.com/image.jpg"]
  }'
```

### 使用Python测试

```python
import requests

url = "http://localhost:5000/api/answer"

# 测试单选题
response = requests.post(url, json={
    "question": "1+1等于几？",
    "options": ["1", "2", "3", "4"],
    "type": 0
})

print(response.json())
# Output: {"success": true, "answer": "2", ...}
```

## ❓ 常见问题

### Q1: 如何选择模型？

**当前版本（v2.0）：**

手动选择模型：
```env
MODEL_PROVIDER=deepseek  # 或 doubao
```

**DeepSeek** 适合：
- ✅ 预算有限
- ✅ 纯文本题目
- ✅ 需要快速响应

**豆包** 适合：
- ✅ 有图片的题目
- ✅ 需要多模态理解
- ✅ 追求更高准确率

**未来版本（规划中）：**

智能自动选择：
```env
MODEL_PROVIDER=auto  # 根据题目内容自动选择
```
- 📷 有图片 → 自动使用豆包
- 📝 纯文本 → 自动使用DeepSeek
- 💰 自动优化成本和效率

详见：[功能规划](#功能规划)

### Q2: 思考模式应该启用吗？

推荐配置：
```env
ENABLE_REASONING=false              # 全局不启用（节省成本）
AUTO_REASONING_FOR_MULTIPLE=true    # 多选题自动启用（提高准确率）
```

**全局启用思考模式**会：
- ✅ 显著提高答案准确率
- ❌ 增加API调用耗时
- ❌ 增加API调用成本

### Q3: API返回"Connection error"

可能原因：
1. **网络问题**：检查网络连接
2. **代理配置**：如需代理，配置 `HTTP_PROXY`/`HTTPS_PROXY`
3. **图片URL问题**（豆包）：
   - 图片URL需要认证
   - 图片URL无法从豆包服务器访问
   - 会自动降级为纯文本模式

解决方案：
```env
# 配置代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# 增加超时时间
TIMEOUT=120.0

# 增加重试次数
MAX_RETRIES=5
```

### Q4: 图片题目无法识别

**检查清单：**
1. 确认使用豆包模型：`MODEL_PROVIDER=doubao`
2. 检查图片URL是否可访问
3. 查看控制台是否显示"📷 图片"
4. 检查是否被过滤为图标URL

**DeepSeek不支持图片**，会自动忽略图片URL。

### Q5: 答案格式不正确

查看控制台输出：
```
🤖 AI原始回答: 北京#上海
✅ 处理后答案: 北京#上海
```

如果原始回答正确但处理后答案错误，可能需要调整 `AnswerProcessor` 类。

### Q6: CSV日志文件太大

清空日志文件：
```bash
# 方法1：通过API
curl -X POST http://localhost:5000/api/csv/clear

# 方法2：通过可视化页面
访问 http://localhost:5000/viewer
点击"清空数据"按钮

# 方法3：手动删除
rm ocs_answers_log.csv  # Linux/Mac
del ocs_answers_log.csv  # Windows
```

### Q7: 如何提高答题准确率？

**策略：**
1. **启用思考模式**：`ENABLE_REASONING=true`
2. **多选题自动思考**：`AUTO_REASONING_FOR_MULTIPLE=true`（默认）
3. **降低温度**：`TEMPERATURE=0.05`（更保守）
4. **使用豆包**：图片题目准确率更高
5. **优化Prompt**：根据学科调整Prompt

### Q8: 服务器部署

使用 gunicorn（生产环境）：

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务（4个worker）
gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app &
```

使用 systemd（Linux开机自启）：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/ocs-ai.service
```

```ini
[Unit]
Description=OCS AI Answerer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ocs-ai-answerer
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start ocs-ai
sudo systemctl enable ocs-ai  # 开机自启
```

### Q9: 网络代理配置

```env
# 配置HTTP代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# 或使用socks5代理
HTTP_PROXY=socks5://127.0.0.1:1080
HTTPS_PROXY=socks5://127.0.0.1:1080
```

### Q10: API密钥安全

**不要：**
- ❌ 将真实密钥提交到Git仓库
- ❌ 在公开代码中硬编码密钥
- ❌ 分享包含密钥的`.env`文件

**应该：**
- ✅ 使用`.env`文件存储密钥
- ✅ 将`.env`添加到`.gitignore`
- ✅ 使用环境变量或密钥管理服务（生产环境）
- ✅ 定期轮换API密钥

## 🔒 安全建议

1. **密钥管理**
   - 不要泄露API密钥
   - 使用环境变量存储
   - 定期轮换密钥

2. **访问控制**
   - 限制API访问IP
   - 添加认证机制（如API Token）
   - 使用HTTPS加密通信

3. **日志安全**
   - 定期清理敏感日志
   - 不要记录API密钥
   - 控制日志文件权限

## 🚀 功能规划

### 计划中的功能

#### 🤖 智能模型选择（即将推出）
根据题目内容自动选择最合适的模型：

**工作原理：**
- 📷 **有图片** → 自动使用豆包（支持多模态）
- 📝 **纯文本** → 自动使用DeepSeek（成本更低、速度更快）
- 💡 **智能切换** → 无需手动配置，自动优化成本和效率

**配置方式：**
```env
MODEL_PROVIDER=auto  # 启用智能选择模式

# 配置两个模型的API密钥
DEEPSEEK_API_KEY=sk-xxxxx
DOUBAO_API_KEY=xxxxx
DOUBAO_MODEL=doubao-seed-1-6-251015

# 智能选择策略
AUTO_MODEL_SELECTION=true        # 启用自动模型选择
PREFER_MODEL=deepseek            # 默认首选模型（无图片时）
IMAGE_MODEL=doubao               # 图片题目使用的模型
```

**预期效果：**
- ✅ 降低成本：纯文本题目使用成本更低的DeepSeek
- ✅ 提高准确率：图片题目使用支持多模态的豆包
- ✅ 自动优化：无需手动切换，系统智能判断
- ✅ 灵活配置：可自定义选择策略

#### 📊 其他计划功能
- 🔍 **题目相似度检测**：避免重复答题
- 💾 **答案缓存机制**：相同题目直接返回缓存答案
- 📈 **答题统计报告**：生成详细的答题分析报告
- 🔔 **错误预警**：自动检测可能的错误答案
- 🌐 **Web管理界面**：图形化配置和管理界面

## 📝 更新日志

### v2.0.0 (2025-11-02)
- ✨ 支持多模型（DeepSeek + 豆包）
- 🧠 支持思考模式（深度推理）
- 🖼️ 支持图片输入（豆包多模态）
- 📊 CSV日志记录功能
- 📈 HTML可视化界面
- ⚙️ 环境变量配置
- 🔄 智能降级机制
- 🏷️ OCS标签展示

### v1.0.0 (2024-11-01)
- ✨ 初始版本发布
- 🎯 支持4种题型（单选/多选/判断/填空）
- 🤖 集成DeepSeek AI
- 📝 优化的Prompt工程
- 🔄 智能答案处理

## 📄 License

MIT License

Copyright (c) 2024-2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

> 🤖 **AI 参与声明**
> 
> 本项目的设计、开发和维护过程中大量使用了人工智能技术。AI 作为开发工具，协助完成了代码编写、文档生成、问题诊断等工作。所有 AI 生成的内容都经过审核和测试，确保质量和可用性。

## 🤝 贡献

欢迎提交Issue和Pull Request！

> 💡 **关于 AI 维护**
> 
> 本项目采用 AI 辅助开发模式：
> - ✅ Issue 响应：AI 会参与问题分析和解答
> - ✅ 代码审查：AI 协助进行代码质量检查
> - ✅ 功能开发：AI 参与新功能的设计和实现
> - ✅ 文档更新：AI 自动维护技术文档
> 
> 人类开发者依然负责最终决策和代码审核。

## 📧 联系方式

- 项目主页：https://github.com/lkd6666/OCS-API---
- 问题反馈：https://github.com/lkd6666/OCS-API---/issues
- OCS 官网：https://docs.ocsjs.com/
- OCS 文档：https://docs.ocsjs.com/docs/work

---

<div align="center">

⭐ 如果这个项目对你有帮助，请给个star支持一下！⭐

**主要特性**
🤖 多模型 | 🧠 深度思考 | 🖼️ 图片识别 | 📊 数据可视化

**规划功能**
🎯 智能模型选择 | 💾 答案缓存 | 📈 统计报告 | 🌐 Web管理

---

**开发模式**
🤖 AI 辅助开发 | 💡 智能设计 | 🔧 自动优化 | 📝 文档自动生成

*本项目展示了 AI 在软件开发领域的创新应用*

</div>
