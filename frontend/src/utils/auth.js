/**
 * 认证工具 - 管理API密钥
 */

const API_KEY_STORAGE = 'ocs_api_key'

/**
 * 保存API密钥到本地存储
 */
export function saveApiKey(key) {
  if (key) {
    localStorage.setItem(API_KEY_STORAGE, key)
  }
}

/**
 * 获取存储的API密钥
 */
export function getApiKey() {
  return localStorage.getItem(API_KEY_STORAGE) || ''
}

/**
 * 清除API密钥
 */
export function clearApiKey() {
  localStorage.removeItem(API_KEY_STORAGE)
}

/**
 * 检查是否已有密钥
 */
export function hasApiKey() {
  return !!getApiKey()
}
