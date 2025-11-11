#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCS脚本智能答题API - 多模型支持版本
支持：DeepSeek、豆包(Doubao)等多个大语言模型
支持：思考模式、自定义配置
"""

from flask import Flask, request, jsonify, make_response, redirect, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from dotenv import load_dotenv
import re
import time
import csv
from datetime import datetime
import base64
from io import BytesIO
import secrets
import hashlib
import json
from functools import wraps
from collections import defaultdict

# 加载环境变量
load_dotenv()

# ==================== 配置区域 ====================

# 模型配置
MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'deepseek')  # deepseek, doubao 或 auto（智能选择）
MODEL_NAME = os.getenv('MODEL_NAME', 'deepseek-chat')     # 模型名称

# 智能模型选择配置
AUTO_MODEL_SELECTION = os.getenv('AUTO_MODEL_SELECTION', 'true').lower() == 'true'  # 是否启用智能选择
PREFER_MODEL = os.getenv('PREFER_MODEL', 'deepseek')  # 纯文本题目首选模型
IMAGE_MODEL = os.getenv('IMAGE_MODEL', 'doubao')       # 图片题目使用的模型

# DeepSeek配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')  # deepseek-chat 或 deepseek-reasoner

# 豆包配置
DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
DOUBAO_BASE_URL = os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
DOUBAO_MODEL = os.getenv('DOUBAO_MODEL', 'doubao-seed-1-6-251015')

# 思考模式配置
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'
REASONING_EFFORT = os.getenv('REASONING_EFFORT', 'medium')  # low, medium, high
AUTO_REASONING_FOR_MULTIPLE = os.getenv('AUTO_REASONING_FOR_MULTIPLE', 'true').lower() == 'true'
AUTO_REASONING_FOR_IMAGES = os.getenv('AUTO_REASONING_FOR_IMAGES', 'true').lower() == 'true'  # 带图片题目自动启用深度思考

# AI参数配置
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.1'))

# max_tokens 限制:
# - deepseek-chat: [1, 8192] (最大8K)
# - deepseek-reasoner: [1, 65536] (最大64K)
# 普通模式的 max_tokens（默认500）
MAX_TOKENS_RAW = int(os.getenv('MAX_TOKENS', '500'))
MAX_TOKENS = max(1, min(8192, MAX_TOKENS_RAW))  # 默认限制到8K（deepseek-chat的限制）

# 思考模式的 max_tokens（默认4096，可以更大以支持复杂推理）
REASONING_MAX_TOKENS_RAW = int(os.getenv('REASONING_MAX_TOKENS', '4096'))
REASONING_MAX_TOKENS = max(1, min(65536, REASONING_MAX_TOKENS_RAW))  # 限制到64K（deepseek-reasoner的限制）

TOP_P = float(os.getenv('TOP_P', '0.95'))

# 网络配置
HTTP_PROXY = os.getenv('HTTP_PROXY', '')
HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')
TIMEOUT = float(os.getenv('TIMEOUT', '1200.0'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# 服务配置
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 安全配置
SECRET_KEY_FILE = os.getenv('SECRET_KEY_FILE', '.secret_key')  # 密钥文件路径
RATE_LIMIT_ATTEMPTS = int(os.getenv('RATE_LIMIT_ATTEMPTS', '5'))  # 允许的连续错误次数
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '300'))  # 限流时间窗口（秒）

# ==================== 配置区域结束 ====================

# 配置日志（必须在SecurityManager之前初始化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 安全认证系统 ====================

class SecurityManager:
    """安全管理器：处理密钥认证和限流"""
    
    def __init__(self, key_file=SECRET_KEY_FILE):
        self.key_file = key_file
        self.secret_key_hash = None
        self.failed_attempts = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]
        self.rate_limit_attempts = RATE_LIMIT_ATTEMPTS
        self.rate_limit_window = RATE_LIMIT_WINDOW
        
        # 初始化密钥
        self._init_secret_key()
    
    def _init_secret_key(self):
        """初始化密钥：如果不存在则生成，否则加载"""
        if os.path.exists(self.key_file):
            # 加载现有密钥
            try:
                with open(self.key_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.secret_key_hash = data.get('key_hash')
                    logger.info(f"✅ 已加载现有访问密钥")
            except Exception as e:
                logger.error(f"❌ 加载密钥失败: {e}，将生成新密钥")
                self._generate_new_key()
        else:
            # 首次启动，生成新密钥
            self._generate_new_key()
    
    def _generate_new_key(self):
        """生成新的64位随机密钥"""
        # 生成64位随机hex字符串（256位熵）
        raw_key = secrets.token_hex(32)  # 32字节 = 64个hex字符
        
        # 存储密钥的SHA256哈希值
        self.secret_key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # 保存到文件
        try:
            with open(self.key_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'key_hash': self.secret_key_hash,
                    'created_at': datetime.now().isoformat(),
                    'raw_key': raw_key  # 仅首次生成时保存明文密钥
                }, f, indent=2)
            
            logger.info("=" * 80)
            logger.info("🔐 首次启动：已生成访问密钥")
            logger.info("=" * 80)
            logger.info(f"   访问密钥: {raw_key}")
            logger.info("=" * 80)
            logger.info(f"⚠️  请妥善保管此密钥！")
            logger.info(f"   - 密钥已保存到: {self.key_file}")
            logger.info(f"   - 访问配置页面和敏感接口需要此密钥")
            logger.info(f"   - 可在配置页面修改密钥")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"❌ 保存密钥失败: {e}")
    
    def verify_key(self, provided_key: str) -> bool:
        """验证提供的密钥是否正确"""
        if not provided_key:
            return False
        
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        return provided_hash == self.secret_key_hash
    
    def update_key(self, old_key: str, new_key: str) -> Tuple[bool, str]:
        """更新密钥"""
        # 验证旧密钥
        if not self.verify_key(old_key):
            return False, "旧密钥错误"
        
        # 验证新密钥格式（至少8字符，像普通密码）
        if len(new_key) < 8:
            return False, "新密钥长度至少8字符"
        
        # 生成新密钥的哈希
        new_hash = hashlib.sha256(new_key.encode()).hexdigest()
        
        # 保存新密钥
        try:
            with open(self.key_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'key_hash': new_hash,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
            
            self.secret_key_hash = new_hash
            logger.info("✅ 访问密钥已更新")
            return True, "密钥更新成功"
        except Exception as e:
            logger.error(f"❌ 更新密钥失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """检查IP是否被限流"""
        now = time.time()
        
        # 清理过期的失败记录
        self.failed_attempts[ip] = [
            ts for ts in self.failed_attempts[ip]
            if now - ts < self.rate_limit_window
        ]
        
        # 检查是否超过限制
        if len(self.failed_attempts[ip]) >= self.rate_limit_attempts:
            remaining_time = int(self.rate_limit_window - (now - self.failed_attempts[ip][0]))
            return False, f"错误次数过多，请{remaining_time}秒后重试"
        
        return True, ""
    
    def record_failed_attempt(self, ip: str):
        """记录失败的认证尝试"""
        self.failed_attempts[ip].append(time.time())
    
    def clear_failed_attempts(self, ip: str):
        """清除失败记录（认证成功后调用）"""
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]

# 全局安全管理器
security_manager = SecurityManager()

def require_auth(f):
    """装饰器：要求API密钥认证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # 检查限流
        allowed, message = security_manager.check_rate_limit(client_ip)
        if not allowed:
            return jsonify({"error": message, "code": "RATE_LIMITED"}), 429
        
        # 从请求头或查询参数获取密钥
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            security_manager.record_failed_attempt(client_ip)
            return jsonify({"error": "缺少API密钥", "code": "MISSING_KEY"}), 401
        
        # 验证密钥
        if not security_manager.verify_key(api_key):
            security_manager.record_failed_attempt(client_ip)
            return jsonify({"error": "API密钥无效", "code": "INVALID_KEY"}), 403
        
        # 认证成功，清除失败记录
        security_manager.clear_failed_attempts(client_ip)
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== 安全认证系统结束 ====================

app = Flask(__name__)
CORS(app)

# 题型映射
QUESTION_TYPES = {
    0: "single",
    1: "multiple",
    3: "completion",
    4: "judgement"
}


class ModelClient:
    """统一的模型客户端（支持智能模型选择）"""
    
    def __init__(self, provider: str = MODEL_PROVIDER):
        """
        初始化模型客户端
        
        Args:
            provider: 模型提供商 (deepseek/doubao/auto)
        """
        self.provider = provider.lower()
        self.enable_reasoning = ENABLE_REASONING
        self.reasoning_effort = REASONING_EFFORT
        self.auto_reasoning_for_multiple = AUTO_REASONING_FOR_MULTIPLE
        self.auto_reasoning_for_images = AUTO_REASONING_FOR_IMAGES
        
        # 智能模式相关
        self.is_auto_mode = (self.provider == 'auto')
        self.prefer_model = PREFER_MODEL.lower()
        self.image_model = IMAGE_MODEL.lower()
        
        # 存储多个客户端（用于auto模式）
        self.clients = {}
        self.models = {}
        
        # 配置HTTP客户端（代理、超时等）
        import httpx
        
        # 设置超时
        try:
            timeout = httpx.Timeout(TIMEOUT, connect=10.0)
        except Exception:
            # 兼容旧版本httpx
            timeout = TIMEOUT
        
        # 创建httpx客户端（最简方式，避免版本兼容问题）
        if HTTP_PROXY or HTTPS_PROXY:
            # 有代理时配置代理
            proxies = HTTPS_PROXY if HTTPS_PROXY else HTTP_PROXY
            logger.info(f"✅ 已配置代理: {proxies}")
            try:
                http_client = httpx.Client(timeout=timeout, proxies=proxies)
            except TypeError:
                # 如果httpx版本不支持proxies参数，使用环境变量方式
                import os
                if HTTPS_PROXY:
                    os.environ['HTTPS_PROXY'] = HTTPS_PROXY
                if HTTP_PROXY:
                    os.environ['HTTP_PROXY'] = HTTP_PROXY
                http_client = httpx.Client(timeout=timeout)
        else:
            # 无代理时直接创建
            http_client = httpx.Client(timeout=timeout)
        
        # 根据provider初始化对应的客户端
        if self.provider == 'auto':
            # 智能模式：初始化所有已配置的客户端
            logger.info("🤖 启用智能模型选择模式")
            
            # 尝试初始化DeepSeek
            if DEEPSEEK_API_KEY:
                try:
                    self.clients['deepseek'] = OpenAI(
                        api_key=DEEPSEEK_API_KEY,
                        base_url=DEEPSEEK_BASE_URL,
                        http_client=http_client,
                        max_retries=MAX_RETRIES
                    )
                    self.models['deepseek'] = DEEPSEEK_MODEL
                    logger.info("✅ DeepSeek客户端已就绪")
                except Exception as e:
                    logger.warning(f"⚠️  DeepSeek初始化失败: {str(e)}")
            else:
                logger.warning("⚠️  DeepSeek API密钥未配置，纯文本题目可能无法使用")
            
            # 尝试初始化豆包
            if DOUBAO_API_KEY and DOUBAO_MODEL:
                try:
                    self.clients['doubao'] = OpenAI(
                        api_key=DOUBAO_API_KEY,
                        base_url=DOUBAO_BASE_URL,
                        http_client=http_client,
                        max_retries=MAX_RETRIES
                    )
                    self.models['doubao'] = DOUBAO_MODEL
                    logger.info("✅ 豆包客户端已就绪")
                except Exception as e:
                    logger.warning(f"⚠️  豆包初始化失败: {str(e)}")
            else:
                logger.warning("⚠️  豆包 API密钥或模型ID未配置，图片题目可能无法使用")
            
            if not self.clients:
                raise ValueError("智能模式需要至少配置一个模型的API密钥（DeepSeek或豆包）")
            
            # 设置默认客户端和模型（用于显示）
            if self.prefer_model in self.clients:
                self.client = self.clients[self.prefer_model]
                self.model = self.models[self.prefer_model]
            else:
                # 使用第一个可用的客户端
                first_provider = list(self.clients.keys())[0]
                self.client = self.clients[first_provider]
                self.model = self.models[first_provider]
            
            logger.info(f"✅ 智能模式已启用 - 已配置 {len(self.clients)} 个模型")
            logger.info(f"   默认首选: {self.prefer_model} (纯文本)")
            logger.info(f"   图片模型: {self.image_model}")
            
        elif self.provider == 'deepseek':
            if not DEEPSEEK_API_KEY:
                logger.warning("⚠️  DeepSeek API密钥未配置")
            
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
                http_client=http_client,
                max_retries=MAX_RETRIES
            )
            
            # 如果启用思考模式，使用deepseek-reasoner
            if self.enable_reasoning:
                self.model = 'deepseek-reasoner'
                logger.info("✅ DeepSeek思考模式已启用（最大64K tokens）")
            else:
                self.model = DEEPSEEK_MODEL
                logger.info("✅ DeepSeek普通模式（最大8K tokens）")
            
        elif self.provider == 'doubao':
            if not DOUBAO_API_KEY:
                logger.warning("⚠️  豆包 API密钥未配置")
            
            self.client = OpenAI(
                api_key=DOUBAO_API_KEY,
                base_url=DOUBAO_BASE_URL,
                http_client=http_client,
                max_retries=MAX_RETRIES
            )
            self.model = DOUBAO_MODEL
            
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
        
        if not self.is_auto_mode:
            logger.info(f"✅ 已初始化 {self.provider} 客户端，模型: {self.model}, 超时: {TIMEOUT}秒, 最大重试: {MAX_RETRIES}次")
    
    def download_image_as_base64(self, image_url: str) -> Optional[str]:
        """
        下载图片并转换为base64格式（使用伪装请求头）
        
        Args:
            image_url: 图片URL
            
        Returns:
            base64编码的data URI，格式: data:image/xxx;base64,xxxxx
            如果下载失败返回None
        """
        try:
            import httpx
            
            # 伪装成浏览器的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://mooc1.chaoxing.com/',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            # 创建HTTP客户端（带超时）
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                logger.info(f"📥 下载图片: {image_url}")
                response = client.get(image_url, headers=headers)
                response.raise_for_status()
                
                # 获取图片内容
                image_data = response.content
                
                # 根据Content-Type判断图片类型
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                if 'image/' not in content_type:
                    content_type = 'image/jpeg'  # 默认JPEG
                
                # 转换为base64
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_uri = f"data:{content_type};base64,{base64_data}"
                
                logger.info(f"✅ 图片下载成功，大小: {len(image_data)} bytes")
                return data_uri
                
        except Exception as e:
            logger.error(f"❌ 图片下载失败: {image_url}")
            logger.error(f"   错误: {str(e)}")
            return None
    
    def chat(self, prompt: str, force_reasoning: bool = False, image_urls: List[str] = None) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, int]]]:
        """
        调用模型进行对话（带重试机制，支持智能模型选择）
        
        Args:
            prompt: 提示词
            force_reasoning: 是否强制启用思考模式（用于多选题等）
            image_urls: 图片URL列表（仅豆包支持）
        
        Returns:
            (推理过程, 最终答案, token使用量) 或 (None, 答案, token使用量)
            token使用量格式: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        """
        # 确定是否使用思考模式
        use_reasoning = self.enable_reasoning or force_reasoning
        
        # 智能选择模型（如果启用）
        if self.is_auto_mode:
            selected_provider, selected_client, selected_model = self._select_model(image_urls)
            if not selected_client:
                return None, None, None
        else:
            selected_provider = self.provider
            selected_client = self.client
            selected_model = self.model
        
        # 根据是否使用思考模式选择模型和max_tokens限制
        if selected_provider == 'deepseek':
            if use_reasoning and not self.enable_reasoning:
                # 临时启用思考模式，需要切换到reasoner模型
                actual_model = 'deepseek-reasoner'
                # 使用思考模式专用的 max_tokens（支持更大的输出）
                max_tokens_limit = REASONING_MAX_TOKENS
                logger.debug(f"思考模式使用 max_tokens: {max_tokens_limit}")
            elif self.enable_reasoning:
                # 全局启用思考模式
                actual_model = selected_model
                max_tokens_limit = REASONING_MAX_TOKENS
                logger.debug(f"思考模式使用 max_tokens: {max_tokens_limit}")
            else:
                # 普通模式
                actual_model = selected_model
                max_tokens_limit = MAX_TOKENS
        else:
            # 豆包模型
            actual_model = selected_model
            if use_reasoning:
                # 豆包的思考模式也使用更大的 token
                max_tokens_limit = REASONING_MAX_TOKENS
                logger.debug(f"豆包思考模式使用 max_tokens: {max_tokens_limit}")
            else:
                max_tokens_limit = MAX_TOKENS
        
        # 构建消息（支持动态切换：首次尝试使用图片，失败后降级为纯文本）
        # 注意：在智能模式下，selected_provider 已经确定，所以用它判断而不是 self.provider
        use_images = selected_provider == 'doubao' and image_urls
        
        # 如果需要使用图片，先下载并转换为base64
        base64_images = []
        if use_images and image_urls:
            logger.info(f"🔄 开始下载 {len(image_urls)} 张图片...")
            for img_url in image_urls:
                base64_data = self.download_image_as_base64(img_url)
                if base64_data:
                    base64_images.append(base64_data)
                else:
                    logger.warning(f"⚠️  跳过无法下载的图片: {img_url}")
            
            if not base64_images:
                logger.warning("⚠️  所有图片下载失败，将使用纯文本模式")
                use_images = False
            else:
                logger.info(f"✅ 成功下载 {len(base64_images)}/{len(image_urls)} 张图片")
        
        # 构建消息的函数
        def build_messages(use_image_urls: bool):
            if use_image_urls and selected_provider == 'doubao' and base64_images:
                # 豆包支持图片输入（多模态）- 使用base64格式
                user_content = []
                # 先添加图片（使用base64格式）
                for base64_data in base64_images:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": base64_data}  # 直接使用data URI
                    })
                # 再添加文本
                user_content.append({"type": "text", "text": prompt})
                
                return [
                    {"role": "system", "content": "你是一个专业、严谨的答题助手。你必须根据题目、图片和选项给出准确的答案，严格按照要求的格式输出，不要有任何多余的内容。"},
                    {"role": "user", "content": user_content}
                ]
            else:
                # 纯文本格式（DeepSeek或无图片）
                if image_urls and selected_provider == 'deepseek':
                    logger.warning("⚠️  DeepSeek不支持图片输入，已忽略图片")
                return [
                    {"role": "system", "content": "你是一个专业、严谨的答题助手。你必须根据题目和选项给出准确的答案，严格按照要求的格式输出，不要有任何多余的内容。"},
                    {"role": "user", "content": prompt}
                ]
        
        # 构建请求参数
        request_params = {
            "model": actual_model,
            "messages": build_messages(use_images),
            "temperature": TEMPERATURE,
            "max_tokens": max_tokens_limit,
            "top_p": TOP_P,
            "stream": False
        }
        
        # 豆包模型支持reasoning_effort
        if selected_provider == 'doubao' and use_reasoning:
            request_params["reasoning_effort"] = self.reasoning_effort
        
        reasoning_status = "（思考模式）" if use_reasoning else ""
        image_status = f"，{len(base64_images)}张图片(base64)" if use_images and base64_images else ""
        auto_status = "🤖智能选择-" if self.is_auto_mode else ""
        logger.info(f"调用{auto_status}{selected_provider}模型 - {actual_model}{reasoning_status}{image_status}")
        
        # 重试机制
        last_error = None
        retry_without_images = False  # 标记是否应该不使用图片重试
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 如果之前检测到图片URL问题，使用纯文本模式
                if retry_without_images:
                    request_params["messages"] = build_messages(False)
                    logger.info("🔄 使用纯文本模式重试（不使用图片）")
                
                # 调用API（使用选定的客户端）
                response = selected_client.chat.completions.create(**request_params)
                
                # 提取推理过程和答案
                reasoning_content = None
                if hasattr(response.choices[0].message, 'reasoning_content'):
                    reasoning_content = response.choices[0].message.reasoning_content
                    if reasoning_content:
                        logger.info(f"推理过程: {reasoning_content[:100]}...")
                
                answer = response.choices[0].message.content.strip()
                logger.info(f"模型返回答案: {answer}")
                
                # 提取token使用量
                usage_info = None
                if hasattr(response, 'usage'):
                    usage_info = {
                        'prompt_tokens': response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                        'completion_tokens': response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                        'total_tokens': response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                    }
                    logger.info(f"💰 Token使用量: 输入={usage_info['prompt_tokens']}, 输出={usage_info['completion_tokens']}, 总计={usage_info['total_tokens']}")
                else:
                    logger.warning("⚠️  响应中没有usage信息，token用量将记录为0")
                    usage_info = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                
                return reasoning_content, answer, usage_info
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                error_type = type(e).__name__
                
                # 记录详细错误信息
                logger.error(f"API调用失败 (尝试 {attempt}/{MAX_RETRIES}): {error_type}: {error_msg[:300]}")
                
                # 检查是否是参数错误（400），这种错误重试也没用
                is_param_error = (
                    "400" in error_msg or 
                    "Invalid" in error_msg or 
                    "invalid_request_error" in error_msg.lower() or
                    "max_tokens" in error_msg.lower()
                )
                
                if is_param_error:
                    logger.error(f"参数错误（无需重试）: {error_msg}")
                    print(f"\n❌ API参数错误: {error_msg[:200]}")
                    if "max_tokens" in error_msg.lower():
                        print("💡 提示: max_tokens必须在[1, 8192]范围内，已自动限制")
                    return None, None, None
                
                # 检查是否是图片相关的错误（即使使用了base64，也可能因为图片过大或格式问题失败）
                # 如果使用了图片且出现连接/超时错误，且是第一次尝试，尝试不使用图片重试
                is_image_error = (
                    "connection" in error_msg.lower() or
                    "Connection" in error_type or
                    "timeout" in error_msg.lower() or
                    "image" in error_msg.lower() or
                    "base64" in error_msg.lower()
                ) and base64_images  # 只有在实际使用了图片时才考虑是图片问题
                
                # 如果是图片相关错误，且是第一次尝试，标记为不使用图片重试
                if is_image_error and attempt == 1 and selected_provider == 'doubao' and base64_images and not retry_without_images:
                    logger.warning(f"⚠️  检测到可能的图片处理问题")
                    logger.warning(f"   错误类型: {error_type}")
                    logger.warning(f"   已发送 {len(base64_images)} 张base64图片")
                    logger.warning(f"   可能原因: 1) 图片过大 2) 图片格式不支持 3) 网络连接问题")
                    print(f"\n⚠️  检测到图片处理问题，将尝试不使用图片重试...")
                    print(f"   错误类型: {error_type}")
                    print(f"   图片数量: {len(base64_images)} 张")
                    
                    # 标记为不使用图片重试
                    retry_without_images = True
                    # 继续重试，但这次不使用图片
                    continue
                
                # 如果是最后一次尝试，直接返回失败
                if attempt >= MAX_RETRIES:
                    logger.error(f"模型调用失败 (已重试{MAX_RETRIES}次): {error_msg}")
                    print(f"\n⚠️  网络错误，已重试 {MAX_RETRIES} 次")
                    print(f"错误类型: {error_type}")
                    print(f"错误信息: {error_msg[:200]}")
                    if "Connection" in error_msg or "timeout" in error_msg.lower():
                        print("💡 提示: 检查网络连接或配置HTTP_PROXY/HTTPS_PROXY环境变量")
                        if image_urls:
                            print("💡 提示: 图片URL可能无法访问，已尝试不使用图片")
                    return None, None, None
                
                # 等待后重试（仅对网络错误）
                wait_time = min(2 ** attempt, 10)  # 指数退避，最多10秒
                logger.warning(f"模型调用失败 (第{attempt}次尝试)，{wait_time}秒后重试: {error_msg[:100]}")
                print(f"⚠️  请求失败，{wait_time}秒后重试 ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait_time)
        
        # 理论上不会执行到这里
        logger.error(f"模型调用失败: {last_error}")
        return None, None, None
    
    def _select_model(self, image_urls: List[str] = None) -> Tuple[str, Optional[Any], Optional[str]]:
        """
        智能选择模型
        
        Args:
            image_urls: 图片URL列表
        
        Returns:
            (provider, client, model) 或 (provider, None, None)
        """
        has_images = image_urls and len(image_urls) > 0
        
        if has_images:
            # 有图片：优先使用豆包
            if self.image_model in self.clients:
                logger.info(f"💡 智能选择: 检测到图片，使用 {self.image_model}")
                return self.image_model, self.clients[self.image_model], self.models[self.image_model]
            else:
                # 豆包未配置，尝试降级
                logger.warning(f"⚠️  {self.image_model} 未配置，但题目包含图片")
                
                # 尝试使用已配置的其他模型
                if self.clients:
                    fallback_provider = list(self.clients.keys())[0]
                    logger.warning(f"⚠️  降级使用 {fallback_provider}（该模型可能不支持图片）")
                    print(f"\n⚠️  警告: {self.image_model} 未配置，降级使用 {fallback_provider}")
                    print(f"   该模型可能不支持图片输入，答题准确率可能降低")
                    print(f"   建议配置 {self.image_model.upper()}_API_KEY 以获得最佳效果\n")
                    return fallback_provider, self.clients[fallback_provider], self.models[fallback_provider]
                else:
                    logger.error("❌ 没有可用的模型客户端")
                    print("\n❌ 错误: 没有可用的模型客户端")
                    print("   请至少配置一个模型的API密钥\n")
                    return 'none', None, None
        else:
            # 无图片：优先使用首选模型（通常是DeepSeek，成本更低）
            if self.prefer_model in self.clients:
                logger.info(f"💡 智能选择: 纯文本题目，使用 {self.prefer_model}（成本更低）")
                return self.prefer_model, self.clients[self.prefer_model], self.models[self.prefer_model]
            else:
                # 首选模型未配置，使用其他可用模型
                if self.clients:
                    fallback_provider = list(self.clients.keys())[0]
                    logger.info(f"💡 {self.prefer_model} 未配置，使用 {fallback_provider}")
                    return fallback_provider, self.clients[fallback_provider], self.models[fallback_provider]
                else:
                    logger.error("❌ 没有可用的模型客户端")
                    print("\n❌ 错误: 没有可用的模型客户端")
                    print("   请至少配置一个模型的API密钥\n")
                    return 'none', None, None


class PromptBuilder:
    """智能Prompt构建器"""
    
    @staticmethod
    def build_prompt(question: str, options: List[str], q_type: str) -> str:
        """根据题型构建prompt"""
        
        if q_type == "single":
            return PromptBuilder._build_single_choice_prompt(question, options)
        elif q_type == "multiple":
            return PromptBuilder._build_multiple_choice_prompt(question, options)
        elif q_type == "judgement":
            return PromptBuilder._build_judgement_prompt(question, options)
        elif q_type == "completion":
            return PromptBuilder._build_completion_prompt(question)
        else:
            return PromptBuilder._build_default_prompt(question, options)
    
    @staticmethod
    def _build_single_choice_prompt(question: str, options: List[str]) -> str:
        """构建单选题prompt"""
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】单选题（只能选择一个正确答案）

【题目】
{question}

【选项】
{options_text}

【回答要求】
1. 仔细分析题目和所有选项
2. 只选择一个最正确的答案
3. 必须从给定的选项中选择，不能自己编造
4. 回答格式：直接输出选项内容，不要包含A、B、C等标识符
5. 只输出答案内容，不要有任何解释、分析或额外文字

【示例】
如果正确答案是选项"北京"，则只输出：北京

现在请回答上述题目："""

    @staticmethod
    def _build_multiple_choice_prompt(question: str, options: List[str]) -> str:
        """构建多选题prompt"""
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】多选题（可能有多个正确答案）

【题目】
{question}

【选项】
{options_text}

【回答要求】
1. 仔细分析题目，找出所有正确的选项
2. 多选题通常有2个或以上的正确答案
3. 必须从给定的选项中选择，不能自己编造
4. 多个答案之间用井号#分隔
5. 回答格式：选项1#选项2#选项3（不要包含A、B、C等标识符）
6. 只输出答案内容，不要有任何解释、分析或额外文字

【示例】
如果正确答案是"北京"和"上海"两个选项，则输出：北京#上海

现在请回答上述题目："""

    @staticmethod
    def _build_judgement_prompt(question: str, options: List[str]) -> str:
        """构建判断题prompt"""
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】判断题（判断对错/是否）

【题目】
{question}

【可选答案】
{chr(10).join(options) if options else "正确 / 错误"}

【回答要求】
1. 仔细分析题目陈述是否正确
2. 必须从给定的选项中选择（如：正确/错误、对/错、是/否、√/×等）
3. 只输出一个判断结果
4. 不要有任何解释、分析或额外文字

【示例】
如果题目陈述正确，且选项中有"正确"，则输出：正确

现在请判断上述题目："""

    @staticmethod
    def _build_completion_prompt(question: str) -> str:
        """构建填空题prompt"""
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】填空题

【题目】
{question}

【回答要求】
1. 仔细理解题目要求
2. 给出准确、简洁的答案
3. 如果有多个空，答案之间用井号#分隔
4. 答案要具体、准确，避免模糊表述
5. 只输出答案内容，不要有序号、解释或额外文字

【示例】
- 单空题：如果答案是"北京"，则输出：北京
- 多空题：如果答案是"氢"和"氧"，则输出：氢#氧

现在请回答上述填空题："""

    @staticmethod
    def _build_default_prompt(question: str, options: List[str]) -> str:
        """构建默认prompt"""
        options_text = "\n".join([f"- {opt}" for opt in options]) if options else "无固定选项"
        
        return f"""请回答以下问题：

【题目】
{question}

【选项】
{options_text}

【要求】
1. 给出准确的答案
2. 如果有多个答案，用#分隔
3. 只输出答案，不要解释

请回答："""


class AnswerProcessor:
    """答案处理器 - 保守清洗，优先匹配原始答案"""
    
    @staticmethod
    def _clean_answer(text: str) -> str:
        """
        轻度清洗，只移除明显的格式标记
        不进行内容修改，避免误删正确答案
        """
        if not text:
            return ""
        
        # 只移除行首的常见前缀（不影响答案内容）
        text = re.sub(r'^(答案[是为：:]*|正确答案[是为：:]*|选择[：:]*)', '', text)
        text = text.strip()
        
        # 只移除markdown的格式符号（不是内容）
        text = re.sub(r'[*`_]', '', text)
        text = text.strip()
        
        # 只移除行首的选项标识（如 "A. "），但不影响答案本身
        text = re.sub(r'^[A-Z][.、)]\s*', '', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _match_option(answer: str, option: str) -> bool:
        """
        智能匹配答案和选项
        优先精确匹配，再模糊匹配
        """
        answer = answer.strip()
        option = option.strip()
        
        if not answer or not option:
            return False
        
        # 精确匹配（忽略大小写和空格）
        if answer.lower() == option.lower():
            return True
        
        # 包含匹配
        if answer.lower() in option.lower() or option.lower() in answer.lower():
            return True
        
        # 去除标点符号后匹配
        answer_clean = re.sub(r'[。，、；：！？\s]', '', answer)
        option_clean = re.sub(r'[。，、；：！？\s]', '', option)
        if answer_clean.lower() == option_clean.lower():
            return True
        
        return False
    
    @staticmethod
    def process_answer(raw_answer: str, q_type: str, options: List[str]) -> str:
        """
        处理和清洗答案 - 保守策略，优先保留原始答案
        """
        if not raw_answer:
            return ""
        
        raw_answer = raw_answer.strip()
        
        # 根据题型处理
        if q_type == "single":
            return AnswerProcessor._process_single_choice(raw_answer, options)
        elif q_type == "multiple":
            return AnswerProcessor._process_multiple_choice(raw_answer, options)
        elif q_type == "judgement":
            return AnswerProcessor._process_judgement(raw_answer, options)
        elif q_type == "completion":
            # 填空题只做轻度清洗，保留原始答案
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
        else:
            # 其他题型只做轻度清洗
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_single_choice(raw_answer: str, options: List[str]) -> str:
        """处理单选题答案 - 优先使用原始答案匹配"""
        if not options:
            # 没有选项，只做轻度清洗
            return AnswerProcessor._clean_answer(raw_answer)
        
        # 第一步：尝试用原始答案直接匹配
        for option in options:
            if AnswerProcessor._match_option(raw_answer, option):
                return option.strip()
        
        # 第二步：轻度清洗后再匹配
        cleaned = AnswerProcessor._clean_answer(raw_answer)
        if cleaned != raw_answer:  # 如果清洗有变化
            for option in options:
                if AnswerProcessor._match_option(cleaned, option):
                    return option.strip()
        
        # 第三步：如果还是匹配不到，返回清洗后的答案
        # 这样至少保留了可能的正确答案，而不是空字符串
        return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_multiple_choice(raw_answer: str, options: List[str]) -> str:
        """处理多选题答案 - 优先使用原始答案匹配"""
        if not options:
            return AnswerProcessor._clean_answer(raw_answer)
        
        # 分割答案（支持多种分隔符）
        raw_answers = re.split(r'[#;；、\n]', raw_answer)
        matched_options = []
        
        # 第一步：用原始答案匹配
        for raw_ans in raw_answers:
            raw_ans = raw_ans.strip()
            if not raw_ans:
                continue
            
            for option in options:
                if AnswerProcessor._match_option(raw_ans, option):
                    option_clean = option.strip()
                    if option_clean not in matched_options:
                        matched_options.append(option_clean)
                    break
        
        # 第二步：如果匹配到了，直接返回
        if matched_options:
            return "#".join(matched_options)
        
        # 第三步：尝试清洗后再匹配
        cleaned_answers = [AnswerProcessor._clean_answer(ans) for ans in raw_answers if ans.strip()]
        for cleaned_ans in cleaned_answers:
            for option in options:
                if AnswerProcessor._match_option(cleaned_ans, option):
                    option_clean = option.strip()
                    if option_clean not in matched_options:
                        matched_options.append(option_clean)
                    break
        
        # 第四步：返回匹配结果或清洗后的原始答案
        if matched_options:
            return "#".join(matched_options)
        else:
            # 如果匹配不到，返回清洗后的答案（保留可能的正确答案）
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_judgement(raw_answer: str, options: List[str]) -> str:
        """处理判断题答案 - 保守策略"""
        if not options:
            return AnswerProcessor._clean_answer(raw_answer)
        
        raw_answer_lower = raw_answer.lower()
        
        # 第一步：直接匹配选项
        for option in options:
            if AnswerProcessor._match_option(raw_answer, option):
                return option.strip()
        
        # 第二步：清洗后匹配
        cleaned = AnswerProcessor._clean_answer(raw_answer)
        if cleaned != raw_answer:
            for option in options:
                if AnswerProcessor._match_option(cleaned, option):
                    return option.strip()
        
        # 第三步：语义匹配（保守）
        # 只在不匹配的情况下才进行语义判断
        cleaned_lower = cleaned.lower()
        
        # 判断"正确"倾向
        positive_words = ['正确', '对', 'true', '√', '是', 'yes', '成立']
        negative_words = ['错误', '错', 'false', '×', '否', 'no', '不成立']
        
        has_positive = any(word in cleaned_lower for word in positive_words)
        has_negative = any(word in cleaned_lower for word in negative_words)
        
        # 只在明确有倾向且没有匹配到选项时才使用
        if has_positive and not has_negative:
            for opt in options:
                opt_lower = opt.lower()
                if any(word in opt_lower for word in positive_words):
                    return opt.strip()
            # 如果选项中没有明确的正向词，返回第一个选项（通常判断题第一个是"正确"）
            return options[0].strip() if len(options) > 0 else cleaned
        
        if has_negative and not has_positive:
            for opt in options:
                opt_lower = opt.lower()
                if any(word in opt_lower for word in negative_words):
                    return opt.strip()
            # 如果选项中没有明确的负向词，返回第二个选项（通常判断题第二个是"错误"）
            return options[1].strip() if len(options) > 1 else cleaned
        
        # 无法判断，返回清洗后的原始答案
        return cleaned if cleaned else raw_answer


# 创建全局模型客户端
model_client = None
init_error = None

try:
    # 检查必需的配置
    if MODEL_PROVIDER == 'auto':
        # 智能模式：需要至少配置一个模型
        if not DEEPSEEK_API_KEY and not DOUBAO_API_KEY:
            init_error = "智能模式需要至少配置一个模型的API密钥（DEEPSEEK_API_KEY 或 DOUBAO_API_KEY）"
            logger.error(init_error)
        else:
            model_client = ModelClient(MODEL_PROVIDER)
            logger.info(f"✅ 智能模型选择已启用 - 已配置 {len(model_client.clients)} 个模型")
    elif MODEL_PROVIDER == 'deepseek':
        if not DEEPSEEK_API_KEY:
            init_error = "DeepSeek API密钥未配置，请在.env文件中设置 DEEPSEEK_API_KEY"
            logger.error(init_error)
        else:
            model_client = ModelClient(MODEL_PROVIDER)
            logger.info(f"✅ 模型客户端初始化成功: {MODEL_PROVIDER} - {model_client.model}")
    elif MODEL_PROVIDER == 'doubao':
        if not DOUBAO_API_KEY:
            init_error = "豆包 API密钥未配置，请在.env文件中设置 DOUBAO_API_KEY"
            logger.error(init_error)
        elif not DOUBAO_MODEL:
            init_error = "豆包 模型ID未配置，请在.env文件中设置 DOUBAO_MODEL"
            logger.error(init_error)
        else:
            model_client = ModelClient(MODEL_PROVIDER)
            logger.info(f"✅ 模型客户端初始化成功: {MODEL_PROVIDER} - {model_client.model}")
    else:
        init_error = f"不支持的模型提供商: {MODEL_PROVIDER}（支持: deepseek, doubao, auto）"
        logger.error(init_error)
except Exception as e:
    init_error = f"初始化模型客户端失败: {str(e)}"
    logger.error(init_error, exc_info=True)
    model_client = None


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.1f}秒"


def check_and_fix_csv_header(csv_file: str, correct_headers: List[str]) -> bool:
    """
    检查并修复CSV文件表头
    
    Args:
        csv_file: CSV文件路径
        correct_headers: 正确的表头列表
    
    Returns:
        True表示表头正确或已修复，False表示修复失败
    """
    if not os.path.exists(csv_file):
        # 文件不存在，无需修复
        return True
    
    try:
        # 读取当前表头
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            current_headers = next(reader, None)
            if current_headers is None:
                # 空文件，无需修复
                return True
            
            # 检查表头是否正确
            if current_headers == correct_headers:
                # 表头正确，无需修复
                return True
            
            # 表头不正确，需要修复
            logger.warning(f"⚠️  CSV文件表头不正确，当前列数: {len(current_headers)}, 正确列数: {len(correct_headers)}")
            logger.info("🔧 开始自动修复CSV文件表头...")
            
            # 读取所有数据
            f.seek(0)
            reader = csv.reader(f)
            rows = list(reader)
        
        # 备份原文件
        backup_file = csv_file + '.backup'
        import shutil
        shutil.copy2(csv_file, backup_file)
        logger.info(f"📋 已备份到: {backup_file}")
        
        # 修复数据
        fixed_rows = [correct_headers]  # 新表头
        
        for i, row in enumerate(rows[1:], start=2):  # 跳过旧表头
            # 如果行的列数少于新表头，补充默认值
            if len(row) < len(correct_headers):
                missing_cols = len(correct_headers) - len(row)
                # 补充默认值：0, 0, 0, 0.000000, ''
                row.extend(['0'] * (missing_cols - 1) + [''])
            elif len(row) > len(correct_headers):
                # 如果列数过多，截断
                row = row[:len(correct_headers)]
            fixed_rows.append(row)
        
        # 写入修复后的文件
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(fixed_rows)
        
        logger.info(f"✅ CSV文件表头修复完成，共处理 {len(fixed_rows)-1} 行数据")
        return True
        
    except Exception as e:
        logger.error(f"❌ CSV文件表头修复失败: {str(e)}")
        return False


def save_to_csv(question: str, options: List[str], q_type: str, raw_answer: str, 
                reasoning: Optional[str], processed_answer: str, ai_time: float, 
                total_time: float, model_name: str, reasoning_used: bool,
                prompt_tokens: int = 0, completion_tokens: int = 0, provider: str = ''):
    """
    保存答题记录到CSV文件
    
    Args:
        question: 题目
        options: 选项列表
        q_type: 题型
        raw_answer: AI原始回答
        reasoning: 思考过程（如果有）
        processed_answer: 处理后的答案
        ai_time: AI答题耗时（秒）
        total_time: 总耗时（秒）
        model_name: 模型名称
        reasoning_used: 是否使用了思考模式
        prompt_tokens: 输入token数
        completion_tokens: 输出token数
        provider: 模型提供商 (deepseek/doubao)
    """
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # CSV表头
    headers = [
        '时间戳', '题型', '题目', '选项', '原始回答', '思考过程', 
        '处理后答案', 'AI耗时(秒)', '总耗时(秒)', '模型', '思考模式',
        '输入Token', '输出Token', '总Token', '费用(元)', '提供商'
    ]
    
    # 检查并修复CSV文件表头（如果需要）
    if os.path.exists(csv_file):
        check_and_fix_csv_header(csv_file, headers)
    
    # 检查文件是否存在，如果不存在则创建并写入表头
    file_exists = os.path.exists(csv_file)
    
    try:
        # 使用UTF-8 BOM编码，确保Excel可以正确显示中文
        with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            
            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writerow(headers)
            
            # 准备数据
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            options_str = ' | '.join(options) if options else ''
            reasoning_str = reasoning if reasoning else ''
            
            # 计算费用（基于DeepSeek和豆包的官方价格）
            # DeepSeek: 输入缓存命中0.2元/百万tokens，缓存未命中2元/百万tokens，输出3元/百万tokens
            # 豆包-Seed-1.6: 推理输入0.8元/百万tokens，推理输出2元/百万tokens
            # 注意：这里假设缓存未命中（实际应该根据缓存状态判断）
            cost = 0.0
            if provider.lower() == 'deepseek':
                # DeepSeek价格（假设缓存未命中）
                input_cost = (prompt_tokens / 1000000) * 2.0  # 2元/百万tokens
                output_cost = (completion_tokens / 1000000) * 3.0  # 3元/百万tokens
                cost = input_cost + output_cost
            elif provider.lower() == 'doubao':
                # 豆包-Seed-1.6 官方价格
                input_cost = (prompt_tokens / 1000000) * 0.8  # 0.8元/百万tokens
                output_cost = (completion_tokens / 1000000) * 2.0  # 2元/百万tokens
                cost = input_cost + output_cost
            else:
                # 未知提供商，使用默认价格（参考DeepSeek）
                input_cost = (prompt_tokens / 1000000) * 2.0
                output_cost = (completion_tokens / 1000000) * 3.0
                cost = input_cost + output_cost
            
            total_tokens = prompt_tokens + completion_tokens
            
            # 写入数据行（所有字段都会被正确转义）
            row = [
                timestamp,
                q_type,
                question,
                options_str,
                raw_answer,
                reasoning_str,
                processed_answer,
                f"{ai_time:.2f}",
                f"{total_time:.2f}",
                model_name,
                '是' if reasoning_used else '否',
                str(prompt_tokens),
                str(completion_tokens),
                str(total_tokens),
                f"{cost:.6f}",
                provider.upper() if provider else ''
            ]
            
            writer.writerow(row)
            logger.debug(f"CSV记录已保存: {len(row)}个字段，思考过程长度: {len(reasoning_str)}")
            
    except Exception as e:
        # CSV记录失败不影响答题流程，只记录日志
        logger.warning(f"保存CSV记录失败: {str(e)}", exc_info=True)


@app.route('/api/answer', methods=['POST'])
def answer_question():
    """答题接口"""
    start_time = time.time()
    
    try:
        if not model_client:
            error_msg = init_error or "模型客户端未初始化，请检查配置"
            print(f"\n❌ {error_msg}")
            print("="*80 + "\n")
            return jsonify({
                "success": False,
                "error": error_msg,
                "hint": "请检查.env文件中的API密钥配置"
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        question = data.get('question', '').strip()
        options = data.get('options', [])
        type_num = data.get('type', 0)
        images = data.get('images', [])  # 图片URL列表
        
        if not question:
            return jsonify({"success": False, "error": "题目不能为空"}), 400
        
        q_type = QUESTION_TYPES.get(type_num, "single")
        q_type_name = {"single": "单选题", "multiple": "多选题", "judgement": "判断题", "completion": "填空题"}.get(q_type, "未知题型")
        
        # 处理选项：支持多种格式
        if isinstance(options, str):
            # 如果是字符串，按换行符分割（OCS脚本传递的格式）
            options = [opt.strip() for opt in options.split('\n') if opt.strip()]
        elif isinstance(options, list):
            # 如果是列表，清理每个选项
            options = [str(opt).strip() for opt in options if opt]
        else:
            # 其他格式转为空列表
            options = []
        
        # 提取题目中的图片URL
        image_urls = []
        
        # 清理URL的函数（去除扩展名后可能附加的字符）
        def clean_url(url):
            """清理URL，去除扩展名后可能附加的字符"""
            url = str(url).strip()
            # 找到最后一个图片扩展名的位置
            match = re.search(r'\.(jpg|jpeg|png|gif|bmp|webp)', url, re.IGNORECASE)
            if match:
                # 只保留到扩展名结束（包括扩展名）
                end_pos = match.end()
                return url[:end_pos]
            return url
        
        if images and isinstance(images, list):
            image_urls = [clean_url(img) for img in images if img]
        
        # 从题目文本中提取图片URL（支持常见图片格式）
        # 使用非贪婪匹配，确保在遇到图片扩展名后立即停止
        # 匹配URL中的合法字符，但使用非贪婪模式避免匹配过多
        img_pattern = r'(https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+?\.(?:jpg|jpeg|png|gif|bmp|webp))'
        found_images = re.findall(img_pattern, question, re.IGNORECASE)
        
        # 清理提取的URL
        found_images = [clean_url(url) for url in found_images]
        
        if found_images:
            logger.info(f"📷 从题目中检测到 {len(found_images)} 张图片")
        image_urls.extend(found_images)
        
        # 从选项中提取图片URL
        found_images_in_options = []
        if options:
            options_text = ' '.join(str(opt) for opt in options)
            found_images_in_options = re.findall(img_pattern, options_text, re.IGNORECASE)
            found_images_in_options = [clean_url(url) for url in found_images_in_options]
            if found_images_in_options:
                logger.info(f"📷 从选项中检测到 {len(found_images_in_options)} 张图片")
                image_urls.extend(found_images_in_options)
        
        image_urls = list(dict.fromkeys(image_urls))  # 去重
        
        # 过滤掉明显的图标URL（通常不是题目内容）
        # 例如：icon/video.png, icon/audio.png, icons/ 等
        filtered_image_urls = []
        icon_keywords = ['/icon/', '/icons/', '/icon.', 'icon/', 'video.png', 'audio.png', 'play.png', 'pause.png']
        
        for img_url in image_urls:
            # 跳过明显的图标URL
            img_url_lower = img_url.lower()
            is_icon = any(keyword in img_url_lower for keyword in icon_keywords)
            
            if is_icon:
                logger.debug(f"跳过图标URL: {img_url}")
                continue
            
            filtered_image_urls.append(img_url)
        
        image_urls = filtered_image_urls
        
        # 记录图片检测结果
        total_found = len(found_images) + len(found_images_in_options) + len([img for img in (images or []) if img])
        if total_found > 0:
            logger.info(f"📷 图片检测结果: 题干{len(found_images)}张, 选项{len(found_images_in_options)}张, API传入{len(images or [])}张, 过滤后{len(image_urls)}张")
        
        # 如果过滤后没有图片，记录日志
        if len(image_urls) == 0 and total_found > 0:
            logger.debug("所有图片URL已被过滤（可能都是图标），使用纯文本模式")
        
        # 控制台输出题目信息
        print("\n" + "="*80)
        print(f"📝 【{q_type_name}】")
        print(f"题目: {question}")
        if options:
            print(f"选项: {' | '.join(options)}")
        if image_urls:
            print(f"📷 检测到图片: {len(image_urls)}张")
            if found_images_in_options and len(found_images_in_options) > 0:
                print(f"   ⚠️  选项中有图片，将自动使用豆包模型")
            for i, img_url in enumerate(image_urls, 1):
                print(f"   {i}. {img_url}")
        print("="*80)
        
        # 构建prompt
        prompt = PromptBuilder.build_prompt(question, options, q_type)
        
        # 多选题自动启用思考模式
        force_reasoning = False
        reasoning_reasons = []
        
        if q_type == "multiple" and model_client.auto_reasoning_for_multiple:
            force_reasoning = True
            reasoning_reasons.append("多选题")
        
        # 带图片题目自动启用思考模式
        if image_urls and model_client.auto_reasoning_for_images:
            force_reasoning = True
            reasoning_reasons.append("图片题")
        
        if force_reasoning and reasoning_reasons:
            print(f"🧠 {' + '.join(reasoning_reasons)}自动启用深度思考模式")
        
        # 调用模型（计时）
        ai_start = time.time()
        reasoning, raw_answer, usage_info = model_client.chat(
            prompt, 
            force_reasoning=force_reasoning,
            image_urls=image_urls if image_urls else None
        )
        ai_time = time.time() - ai_start
        
        if not raw_answer:
            print(f"❌ 答题失败: AI未返回答案")
            return jsonify({"success": False, "error": "AI答题失败"}), 500
        
        # 提取token使用量
        prompt_tokens = 0
        completion_tokens = 0
        if usage_info:
            prompt_tokens = usage_info.get('prompt_tokens', 0)
            completion_tokens = usage_info.get('completion_tokens', 0)
        
        # 处理答案
        processed_answer = AnswerProcessor.process_answer(raw_answer, q_type, options)
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 控制台输出答案和耗时
        print(f"\n🤖 AI原始回答: {raw_answer}")
        print(f"✅ 处理后答案: {processed_answer}")
        print(f"⏱️  模型答题用时: {format_time(ai_time)}")
        print(f"⏱️  总处理用时: {format_time(total_time)}")
        print("="*80 + "\n")
        
        # 记录到CSV文件
        # 确定实际使用的模型名称
        if model_client.is_auto_mode:
            # 智能模式：从响应中获取实际使用的模型
            actual_provider = model_client._select_model(image_urls if image_urls else None)[0]
            if actual_provider in model_client.models:
                model_name = model_client.models[actual_provider]
            else:
                model_name = "auto-unknown"
        else:
            model_name = model_client.model if not force_reasoning else ('deepseek-reasoner' if model_client.provider == 'deepseek' else model_client.model)
        
        reasoning_used = force_reasoning or model_client.enable_reasoning
        
        # 确定提供商
        actual_provider = ''
        if model_client.is_auto_mode:
            actual_provider = model_client._select_model(image_urls if image_urls else None)[0]
        else:
            actual_provider = model_client.provider
        
        save_to_csv(
            question=question,
            options=options,
            q_type=q_type_name,
            raw_answer=raw_answer,
            reasoning=reasoning,
            processed_answer=processed_answer,
            ai_time=ai_time,
            total_time=total_time,
            model_name=model_name,
            reasoning_used=reasoning_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider=actual_provider
        )
        
        # 构建响应（OCS脚本格式：返回[题目, 答案, extra_data]）
        # extra_data格式：{ai: true, tags: [{text, title, color}]}
        # 注意：OCS脚本会在ai=true时自动添加"AI"标签（蓝色）
        # 所以我们只需要添加额外的标签来区分思考/非思考模式
        
        # 构建标签
        tags = []
        
        # 思考模式：添加"深度思考"标签（紫色），OCS会自动添加"AI"标签（蓝色）
        if force_reasoning or model_client.enable_reasoning:
            tags.append({
                "text": "深度思考",
                "title": "使用深度思考模式生成，答案更准确",
                "color": "purple"  # OCS支持的颜色：blue, green, red, yellow, gray, purple, orange
            })
            # 如果是多选题自动启用的思考模式
            if force_reasoning:
                tags.append({
                    "text": "自动思考",
                    "title": "多选题自动启用深度思考",
                    "color": "orange"
                })
        # 普通模式：不添加标签，OCS脚本会自动添加"AI"标签（蓝色）
        
        # 模型标签
        if model_client.is_auto_mode:
            # 智能模式：显示实际使用的模型
            actual_provider = model_client._select_model(image_urls if image_urls else None)[0]
            display_provider = actual_provider.upper()
            if actual_provider in model_client.models:
                display_model = model_client.models[actual_provider]
            else:
                display_model = "unknown"
            
            # 添加智能选择标签
            tags.append({
                "text": "智能选择",
                "title": "根据题目内容自动选择最合适的模型",
                "color": "blue"
            })
            tags.append({
                "text": display_provider,
                "title": f"实际使用: {display_model}",
                "color": "green"
            })
            model_name = display_model
        else:
            model_name = model_client.model if not force_reasoning else ('deepseek-reasoner' if model_client.provider == 'deepseek' else model_client.model)
            tags.append({
                "text": model_client.provider.upper(),
                "title": f"模型: {model_name}",
                "color": "green"
            })
        
        # OCS脚本期望的格式：[题目, 答案, extra_data]
        # ai=true 会让OCS自动添加"AI"标签
        # 计算总token数
        total_tokens = prompt_tokens + completion_tokens
        
        ocs_format = [
            question,
            processed_answer,
            {
                "ai": True,  # OCS会自动添加"AI"标签
                "tags": tags,  # 我们添加的额外标签（深度思考、模型等）
                "model": model_name,
                "provider": model_client.provider,
                "reasoning_used": force_reasoning or model_client.enable_reasoning,
                "ai_time": round(ai_time, 2),
                "total_time": round(total_time, 2),
                # Token使用量（从API响应中提取）
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }
        ]
        
        # 返回兼容格式（同时支持OCS格式和原始格式）
        response_provider = model_client.provider
        if model_client.is_auto_mode:
            actual_provider = model_client._select_model(image_urls if image_urls else None)[0]
            response_provider = f"auto({actual_provider})"
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": processed_answer,
            "type": q_type,
            "raw_answer": raw_answer,
            "model": model_name,
            "provider": response_provider,
            "reasoning_used": force_reasoning or model_client.enable_reasoning,
            "ai_time": round(ai_time, 2),
            "total_time": round(total_time, 2),
            # Token使用量（从API响应中提取）
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            # OCS脚本直接使用的格式
            "ocs_format": ocs_format
        })
    
    except Exception as e:
        error_time = time.time() - start_time
        print(f"\n❌ 错误: {str(e)}")
        print(f"⏱️  处理用时: {format_time(error_time)}")
        print("="*80 + "\n")
        logger.error(f"处理请求错误: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"服务器错误: {str(e)}"}), 500


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok" if model_client else "error",
        "service": "OCS AI Answerer (Multi-Model)",
        "version": "2.2.0",
        "provider": MODEL_PROVIDER,
        "model": model_client.model if model_client else "未配置",
        "reasoning_enabled": ENABLE_REASONING,
        "api_configured": bool(
            (MODEL_PROVIDER == 'deepseek' and DEEPSEEK_API_KEY) or
            (MODEL_PROVIDER == 'doubao' and DOUBAO_API_KEY)
        ),
        "init_error": init_error if not model_client else None
    })


@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """获取当前配置（需要认证）- 返回完整密钥"""
    # 返回所有环境变量配置（用于配置面板）
    config = {
        # 模型提供商配置
        "MODEL_PROVIDER": MODEL_PROVIDER,
        "AUTO_MODEL_SELECTION": str(model_client.is_auto_mode if model_client else False).lower(),
        "PREFER_MODEL": getattr(model_client, 'prefer_model', '') if model_client else '',
        "IMAGE_MODEL": getattr(model_client, 'image_model', '') if model_client else '',
        
        # DeepSeek 配置 - 返回完整密钥
        "DEEPSEEK_API_KEY": DEEPSEEK_API_KEY,
        "DEEPSEEK_BASE_URL": os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        "DEEPSEEK_MODEL": os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        
        # 豆包配置 - 返回完整密钥
        "DOUBAO_API_KEY": DOUBAO_API_KEY,
        "DOUBAO_BASE_URL": os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
        "DOUBAO_MODEL": os.getenv('DOUBAO_MODEL', ''),
        
        # 思考模式配置
        "ENABLE_REASONING": str(ENABLE_REASONING).lower(),
        "REASONING_EFFORT": REASONING_EFFORT,
        "AUTO_REASONING_FOR_MULTIPLE": str(AUTO_REASONING_FOR_MULTIPLE).lower(),
        "AUTO_REASONING_FOR_IMAGES": str(AUTO_REASONING_FOR_IMAGES).lower(),
        
        # AI 参数配置
        "TEMPERATURE": str(TEMPERATURE),
        "MAX_TOKENS": str(MAX_TOKENS),
        "REASONING_MAX_TOKENS": str(os.getenv('REASONING_MAX_TOKENS', '4096')),
        "TOP_P": str(os.getenv('TOP_P', '1.0')),
        
        # 网络配置
        "HTTP_PROXY": os.getenv('HTTP_PROXY', ''),
        "HTTPS_PROXY": os.getenv('HTTPS_PROXY', ''),
        "TIMEOUT": str(os.getenv('TIMEOUT', '1200')),
        "MAX_RETRIES": str(os.getenv('MAX_RETRIES', '3')),
        
        # 系统配置
        "HOST": HOST,
        "PORT": str(PORT),
        "DEBUG": str(os.getenv('DEBUG', 'false')).lower(),
        "CSV_LOG_FILE": os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv'),
        "LOG_LEVEL": os.getenv('LOG_LEVEL', 'INFO'),
    }
    
    # 添加运行时信息（用于状态显示）
    config["_runtime"] = {
        "model": model_client.model if model_client else None,
        "auto_mode": model_client.is_auto_mode if model_client else False,
        "available_models": list(model_client.clients.keys()) if model_client and model_client.is_auto_mode else [],
        "deepseek_configured": "deepseek" in model_client.clients if model_client and model_client.is_auto_mode else bool(DEEPSEEK_API_KEY),
        "doubao_configured": "doubao" in model_client.clients if model_client and model_client.is_auto_mode else bool(DOUBAO_API_KEY)
    }
    
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
@require_auth
def save_config():
    """保存配置到 .env 文件（需要认证）- 匹配修改而非覆盖"""
    try:
        config_data = request.get_json()
        if not config_data:
            return jsonify({"error": "无效的配置数据"}), 400
        
        # .env 文件路径
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # 读取现有的 .env 文件内容（逐行）
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 创建配置键到新值的映射
        updated_keys = set()
        
        # 逐行处理，匹配并修改
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # 保留注释和空行
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            # 解析配置行
            if '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                
                # 如果这个key在更新数据中，替换它
                if key in config_data:
                    value = config_data[key]
                    # 处理空值
                    if value == '' or value is None:
                        new_lines.append(f"{key}=\n")
                    else:
                        new_lines.append(f"{key}={value}\n")
                    updated_keys.add(key)
                else:
                    # 保留原有配置
                    new_lines.append(line)
            else:
                # 保留格式不正确的行
                new_lines.append(line)
        
        # 添加新的配置项（如果有）
        new_keys = set(config_data.keys()) - updated_keys
        if new_keys:
            new_lines.append("\n# 新增配置项\n")
            for key in sorted(new_keys):
                value = config_data[key]
                if value == '' or value is None:
                    new_lines.append(f"{key}=\n")
                else:
                    new_lines.append(f"{key}={value}\n")
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info(f"配置已保存到 {env_file}，更新了 {len(updated_keys)} 个配置项，新增了 {len(new_keys)} 个配置项")
        return jsonify({
            "success": True,
            "message": "配置已成功保存到 .env 文件",
            "file": env_file,
            "updated": len(updated_keys),
            "added": len(new_keys),
            "note": "请重启服务以应用新配置"
        })
        
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return jsonify({"error": f"保存配置失败: {str(e)}"}), 500


@app.route('/api/restart', methods=['POST'])
@require_auth
def restart_server():
    """重启服务器（需要认证）"""
    try:
        import sys
        import os
        import threading
        import subprocess
        
        def do_restart():
            """延迟重启以便响应返回"""
            import time
            time.sleep(1)  # 等待响应返回
            logger.info("正在重启服务器...")
            
            # 检测是否为 PyInstaller 打包环境
            if getattr(sys, 'frozen', False):
                # 打包后的 exe 环境
                executable = sys.executable  # exe 文件路径
                logger.info(f"检测到打包环境，重启 exe: {executable}")
                
                # 直接启动新的 exe 进程
                if os.name == 'nt':  # Windows
                    subprocess.Popen([executable], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # Linux/Mac
                    subprocess.Popen([executable])
                
                # 退出当前进程
                os._exit(0)
            else:
                # 普通 Python 脚本环境
                python = sys.executable
                script = os.path.abspath(__file__)
                logger.info(f"检测到脚本环境，重启: {python} {script}")
                
                if os.name == 'nt':  # Windows
                    subprocess.Popen([python, script], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os._exit(0)
                else:  # Linux/Mac
                    os.execv(python, [python, script])
        
        # 在后台线程中执行重启
        threading.Thread(target=do_restart, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message": "服务器将在 1 秒后重启"
        })
        
    except Exception as e:
        logger.error(f"重启服务器失败: {str(e)}")
        return jsonify({"error": f"重启失败: {str(e)}"}), 500


@app.route('/api/csv/stats', methods=['GET'])
def get_csv_stats():
    """获取CSV统计数据（支持筛选）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # 获取筛选参数
    search = request.args.get('search', '')
    question_type = request.args.get('type', '')
    reasoning = request.args.get('reasoning', '')
    date_filter = request.args.get('date', 'all')
    custom_date = request.args.get('custom_date', '')
    
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": "CSV文件不存在"}), 404
        
        # 读取并解析CSV
        import csv as csv_module
        stats = {
            'total': 0,
            'avgTime': 0,
            'reasoningCount': 0,
            'totalTime': 0,
            'totalCost': 0,
            'totalTokens': 0,
            'inputTokens': 0,
            'outputTokens': 0,
            'typeCounts': {},
            'timeRanges': {'0-2秒': 0, '2-5秒': 0, '5-10秒': 0, '10秒以上': 0},
            'reasoningCounts': {'思考模式': 0, '普通模式': 0},
            'dailyCounts': {}
        }
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv_module.DictReader(f)
            total_ai_time = 0
            
            for row in reader:
                # 应用筛选
                row_text = '|'.join(row.values()).lower()
                if search and search.lower() not in row_text:
                    continue
                if question_type and row.get('题型', '') != question_type:
                    continue
                if reasoning and row.get('思考模式', '') != reasoning:
                    continue
                # TODO: 日期筛选
                
                # 统计
                stats['total'] += 1
                
                # AI耗时
                ai_time = float(row.get('AI耗时(秒)', 0) or 0)
                total_ai_time += ai_time
                
                # 总耗时
                stats['totalTime'] += float(row.get('总耗时(秒)', 0) or 0)
                
                # 费用
                stats['totalCost'] += float(row.get('费用(元)', 0) or 0)
                
                # Token统计
                stats['totalTokens'] += int(row.get('总Token', 0) or 0)
                stats['inputTokens'] += int(row.get('输入Token', 0) or 0)
                stats['outputTokens'] += int(row.get('输出Token', 0) or 0)
                
                # 思考模式
                if row.get('思考模式', '') == '是':
                    stats['reasoningCount'] += 1
                    stats['reasoningCounts']['思考模式'] += 1
                else:
                    stats['reasoningCounts']['普通模式'] += 1
                
                # 题型分布
                q_type = row.get('题型', '未知')
                stats['typeCounts'][q_type] = stats['typeCounts'].get(q_type, 0) + 1
                
                # 耗时分布
                if ai_time <= 2:
                    stats['timeRanges']['0-2秒'] += 1
                elif ai_time <= 5:
                    stats['timeRanges']['2-5秒'] += 1
                elif ai_time <= 10:
                    stats['timeRanges']['5-10秒'] += 1
                else:
                    stats['timeRanges']['10秒以上'] += 1
                
                # 每日答题量
                timestamp = row.get('时间戳', '')
                if timestamp:
                    date = timestamp.split(' ')[0]
                    stats['dailyCounts'][date] = stats['dailyCounts'].get(date, 0) + 1
        
        # 计算平均值
        if stats['total'] > 0:
            stats['avgTime'] = total_ai_time / stats['total']
            stats['totalTime'] = stats['totalTime'] / 60  # 转换为分钟
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({"error": f"获取统计数据失败: {str(e)}"}), 500


@app.route('/api/csv', methods=['GET'])
def get_csv():
    """获取CSV日志文件（返回JSON格式，支持分页和筛选，时间倒序）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # 获取分页参数
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size', type=int)
    export_all = request.args.get('export', '') == 'true'  # 是否导出全部数据
    
    # 获取筛选参数
    search = request.args.get('search', '')
    question_type = request.args.get('type', '')
    reasoning = request.args.get('reasoning', '')
    date_filter = request.args.get('date', 'all')
    custom_date = request.args.get('custom_date', '')
    
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": "CSV文件不存在"}), 404
        
        # 使用DictReader解析CSV为字典列表
        all_data = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 应用筛选
                if search and search.lower() not in str(row).lower():
                    continue
                if question_type and row.get('题型', '') != question_type:
                    continue
                if reasoning:
                    if reasoning == '思考模式':
                        if row.get('思考模式', '否') == '否':
                            continue
                    elif reasoning == '普通模式':
                        if row.get('思考模式', '否') != '否':
                            continue
                
                # 日期筛选
                if date_filter != 'all':
                    timestamp = row.get('时间戳', '')
                    if timestamp:
                        try:
                            from datetime import datetime, timedelta
                            record_date = datetime.strptime(timestamp.split()[0], '%Y-%m-%d')
                            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                            
                            if date_filter == 'today':
                                if record_date.date() != today.date():
                                    continue
                            elif date_filter == 'week':
                                week_ago = today - timedelta(days=7)
                                if record_date < week_ago:
                                    continue
                            elif date_filter == 'month':
                                month_ago = today - timedelta(days=30)
                                if record_date < month_ago:
                                    continue
                            elif date_filter == 'custom' and custom_date:
                                date_range = custom_date.split(',')
                                if len(date_range) == 2:
                                    start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
                                    end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
                                    if not (start_date <= record_date <= end_date):
                                        continue
                        except:
                            pass
                
                all_data.append(row)
        
        # 按时间戳倒序排序（最新的在前面）
        all_data.sort(key=lambda x: x.get('时间戳', ''), reverse=True)
        
        total = len(all_data)
        
        # 如果是导出全部数据
        if export_all:
            return jsonify({
                "data": all_data,
                "total": total
            })
        
        # 如果没有分页参数，返回全部数据
        if page is None or page_size is None:
            return jsonify({
                "data": all_data,
                "total": total
            })
        
        # 分页处理
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        
        if start >= total or start < 0:
            paginated_data = []
        else:
            paginated_data = all_data[start:end]
        
        return jsonify({
            "data": paginated_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        })
        
    except Exception as e:
        logger.error(f"读取CSV文件失败: {str(e)}")
        return jsonify({"error": f"读取CSV文件失败: {str(e)}"}), 500


@app.route('/api/csv/clear', methods=['POST'])
@require_auth
def clear_csv():
    """清空CSV日志文件（保留表头，需要认证）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    try:
        # CSV表头
        headers = [
            '时间戳', '题型', '题目', '选项', '原始回答', '思考过程', 
            '处理后答案', 'AI耗时(秒)', '总耗时(秒)', '模型', '思考模式',
            '输入Token', '输出Token', '总Token', '费用(元)', '提供商'
        ]
        
        # 写入空文件（只保留表头）
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        logger.info(f"CSV文件已清空: {csv_file}")
        return jsonify({
            "success": True,
            "message": "CSV文件已清空（保留表头）",
            "file": csv_file
        })
    except Exception as e:
        logger.error(f"清空CSV文件失败: {str(e)}")
        return jsonify({"success": False, "error": f"清空CSV文件失败: {str(e)}"}), 500


# ==================== 安全认证API ====================

@app.route('/api/auth/verify', methods=['POST'])
def verify_auth():
    """验证API密钥是否有效"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({"valid": False, "error": "缺少API密钥"}), 400
        
        # 验证密钥
        is_valid = security_manager.verify_key(api_key)
        
        if is_valid:
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "error": "密钥无效"}), 403
    except Exception as e:
        logger.error(f"验证密钥失败: {str(e)}")
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route('/api/auth/update-key', methods=['POST'])
@require_auth
def update_secret_key():
    """更新访问密钥（需要旧密钥认证）"""
    try:
        data = request.get_json()
        old_key = data.get('old_key', '')
        new_key = data.get('new_key', '')
        
        if not old_key or not new_key:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        # 更新密钥
        success, message = security_manager.update_key(old_key, new_key)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"更新密钥失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """获取认证状态（不需要密钥，用于检查是否启用了认证）"""
    return jsonify({
        "auth_enabled": True,
        "message": "此服务需要API密钥才能访问敏感接口"
    })


# ==================== Vue SPA 静态文件服务 ====================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供Vue打包后的静态资源"""
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist', 'assets')
    return send_from_directory(dist_dir, filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    """
    服务 Vue SPA 应用
    - 如果请求的是 API 路径，跳过（由其他路由处理）
    - 如果请求有时间戳参数 (?t=...)，作为延迟测试
    - 否则返回 Vue 应用的 index.html
    """
    # API 路径已经被上面的路由处理，这里不应该被触发
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    
    # 延迟测试（向后兼容旧的 OCS 脚本）
    timestamp = request.args.get('t', None)
    if timestamp and request.method in ['HEAD', 'GET']:
        response = make_response('', 200)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['X-Service'] = 'OCS AI Answerer'
        response.headers['X-Version'] = '3.0.0'
        
        try:
            client_timestamp = int(timestamp) / 1000
            server_timestamp = time.time()
            latency = (server_timestamp - client_timestamp) * 1000
            response.headers['X-Latency'] = f"{latency:.2f}ms"
        except (ValueError, TypeError):
            pass
        
        if request.method == 'GET':
            response.set_data('OK')
        
        return response
    
    # 服务 Vue SPA
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    index_file = os.path.join(dist_dir, 'index.html')
    
    # 如果 dist 目录不存在，提示需要构建前端
    if not os.path.exists(dist_dir) or not os.path.exists(index_file):
        return jsonify({
            "error": "前端应用未构建",
            "message": "请先构建前端应用：cd frontend && npm install && npm run build",
            "note": "或者使用旧版HTML界面，访问 /config_legacy"
        }), 503
    
    # 返回 Vue 应用的 index.html
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"加载Vue应用失败: {str(e)}")
        return jsonify({"error": f"加载前端应用失败: {str(e)}"}), 500


# ==================== 旧版HTML页面路由(向后兼容) ====================

@app.route('/config_legacy', methods=['GET'])
def config_panel_legacy():
    """配置管理面板 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'config_panel.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "配置面板文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载配置面板失败: {str(e)}")
        return jsonify({"error": f"加载配置面板失败: {str(e)}"}), 500


@app.route('/viewer_legacy', methods=['GET'])
def viewer_legacy():
    """答题记录可视化页面 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'ocs_answers_viewer.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 修改HTML中的fetch路径，使其指向Flask API
            html_content = html_content.replace(
                "fetch('ocs_answers_log.csv')",
                "fetch('/api/csv')"
            )
            html_content = html_content.replace(
                'fetch("ocs_answers_log.csv")',
                'fetch("/api/csv")'
            )
            html_content = html_content.replace(
                '<script src="chart.js.min.js"></script>',
                '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'
            )
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "可视化页面文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载可视化页面失败: {str(e)}")
        return jsonify({"error": f"加载可视化页面失败: {str(e)}"}), 500


@app.route('/docs_legacy', methods=['GET'])
def api_docs_legacy():
    """API文档页面 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'api_docs.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "API文档文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载API文档失败: {str(e)}")
        return jsonify({"error": f"加载API文档失败: {str(e)}"}), 500


if __name__ == '__main__':
    # 显示模型信息
    if model_client and model_client.is_auto_mode:
        model_info = f"AUTO (智能选择)"
        models_list = ", ".join(model_client.clients.keys())
        model_detail = f"已配置: {models_list}"
    elif model_client:
        model_info = f"{MODEL_PROVIDER.upper()} - {model_client.model}"
        model_detail = "固定模式"
    else:
        model_info = "未配置"
        model_detail = ""
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║       OCS智能答题API服务 - 多模型支持版本 v2.2          ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  � Vue3 前端: http://{HOST}:{PORT}/                    
    ║  📊 数据可视化: http://{HOST}:{PORT}/viewer             
    ║  📖 API文档: http://{HOST}:{PORT}/docs                  
    ╠═══════════════════════════════════════════════════════════╣
    ║  接口地址: http://{HOST}:{PORT}/api/answer              
    ║  健康检查: http://{HOST}:{PORT}/api/health              
    ║  配置查询: http://{HOST}:{PORT}/api/config              
    ║  CSV数据: http://{HOST}:{PORT}/api/csv                  
    ║  延迟测试: http://{HOST}:{PORT}/?t=时间戳 (HEAD/GET)    
    ╠═══════════════════════════════════════════════════════════╣
    ║  当前模式: {model_info:<48s}║
    ║  {'  ' + model_detail if model_detail else '':<60s}║
    ║  思考模式: {'✅ 已启用' if ENABLE_REASONING else '❌ 未启用':<40s}║
    ║  多选题思考: {'✅ 自动启用' if AUTO_REASONING_FOR_MULTIPLE else '❌ 关闭':<38s}║
    ║  图片题思考: {'✅ 自动启用' if AUTO_REASONING_FOR_IMAGES else '❌ 关闭':<38s}║
    ║  支持题型: 单选、多选、判断、填空                        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  💡 旧版HTML: http://{HOST}:{PORT}/config_legacy         
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if not model_client:
        print("\n" + "="*80)
        print("❌ 模型客户端初始化失败")
        if init_error:
            print(f"错误信息: {init_error}")
        print("\n💡 解决方案:")
        if MODEL_PROVIDER == 'auto':
            print("   智能模式需要至少配置一个模型:")
            print("   1. 创建或编辑 .env 文件")
            print("   2. 设置 MODEL_PROVIDER=auto")
            print("   3. 配置至少一个模型的API密钥:")
            print("      - DEEPSEEK_API_KEY=your_key (获取: https://platform.deepseek.com/api_keys)")
            print("      - DOUBAO_API_KEY=your_key + DOUBAO_MODEL=your_endpoint_id")
            print("        (获取: https://console.volcengine.com/ark)")
            print("   4. 建议配置两个模型以获得最佳效果")
        elif MODEL_PROVIDER == 'deepseek':
            print("   1. 创建或编辑 .env 文件")
            print("   2. 设置 DEEPSEEK_API_KEY=your_api_key")
            print("   3. 获取API密钥: https://platform.deepseek.com/api_keys")
        elif MODEL_PROVIDER == 'doubao':
            print("   1. 创建或编辑 .env 文件")
            print("   2. 设置 DOUBAO_API_KEY=your_api_key")
            print("   3. 设置 DOUBAO_MODEL=your_endpoint_id")
            print("   4. 获取API密钥: https://console.volcengine.com/ark")
        print("="*80 + "\n")
    else:
        if model_client.is_auto_mode:
            print("✅ 智能模型选择已启用！\n")
            print("💡 工作原理:")
            print(f"   📷 有图片 → 自动使用 {model_client.image_model}")
            print(f"   📄 纯文本 → 自动使用 {model_client.prefer_model} (成本更低)")
            print(f"   🔧 已配置模型: {', '.join(model_client.clients.keys())}\n")
        else:
            print("✅ 服务启动成功！\n")
    
    # 检查前端是否已构建
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    if not os.path.exists(dist_dir):
        print("⚠️  警告: 前端应用未构建")
        print("   访问 Web 界面需要先构建前端：")
        print("   执行: build_frontend.bat")
        print("   或访问旧版界面: http://{}:{}/config_legacy\n".format(HOST, PORT))
    
    app.run(host=HOST, port=PORT, debug=DEBUG)


