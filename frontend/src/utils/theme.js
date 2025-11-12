/**
 * 主题管理工具
 */

const THEME_KEY = 'ocs_theme_mode'

/**
 * 主题模式
 * auto: 跟随系统
 * light: 浅色
 * dark: 深色
 */
export const ThemeMode = {
  AUTO: 'auto',
  LIGHT: 'light',
  DARK: 'dark'
}

/**
 * 获取系统主题偏好
 */
export function getSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

/**
 * 获取存储的主题模式
 */
export function getThemeMode() {
  return localStorage.getItem(THEME_KEY) || ThemeMode.AUTO
}

/**
 * 保存主题模式
 */
export function saveThemeMode(mode) {
  localStorage.setItem(THEME_KEY, mode)
}

/**
 * 获取实际应用的主题（考虑auto模式）
 */
export function getActualTheme(mode) {
  if (mode === ThemeMode.AUTO) {
    return getSystemTheme()
  }
  return mode
}

/**
 * 应用主题到HTML
 */
export function applyTheme(theme) {
  const html = document.documentElement
  
  if (theme === 'dark') {
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
  }
}

/**
 * 监听系统主题变化
 */
export function watchSystemTheme(callback) {
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    // 现代浏览器
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', (e) => {
        callback(e.matches ? 'dark' : 'light')
      })
    } else if (mediaQuery.addListener) {
      // 兼容旧浏览器
      mediaQuery.addListener((e) => {
        callback(e.matches ? 'dark' : 'light')
      })
    }
    
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', callback)
      } else if (mediaQuery.removeListener) {
        mediaQuery.removeListener(callback)
      }
    }
  }
  
  return () => {}
}
