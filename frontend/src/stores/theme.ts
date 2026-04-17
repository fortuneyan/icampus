import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'colorful'

export const useThemeStore = defineStore('theme', () => {
  // 当前主题模式
  const themeMode = ref<ThemeMode>('colorful')
  
  // 从 localStorage 读取保存的主题
  const savedTheme = localStorage.getItem('theme-mode') as ThemeMode
  if (savedTheme && ['light', 'dark', 'colorful'].includes(savedTheme)) {
    themeMode.value = savedTheme
  }
  
  // 是否为暗黑模式
  const isDark = computed(() => themeMode.value === 'dark')
  
  // 是否为彩色校园风格
  const isColorful = computed(() => themeMode.value === 'colorful')
  
  // 设置主题
  const setTheme = (mode: ThemeMode) => {
    themeMode.value = mode
    localStorage.setItem('theme-mode', mode)
    applyTheme(mode)
  }
  
  // 应用主题到 DOM
  const applyTheme = (mode: ThemeMode) => {
    const html = document.documentElement
    
    // 移除所有主题类
    html.classList.remove('dark-theme', 'colorful-theme')
    
    // 添加对应主题类
    if (mode === 'dark') {
      html.classList.add('dark-theme')
    } else if (mode === 'colorful') {
      html.classList.add('colorful-theme')
    }
    
    // 设置 Element Plus 的暗黑模式
    if (mode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }
  
  // 初始化主题
  const initTheme = () => {
    applyTheme(themeMode.value)
  }
  
  // 监听主题变化
  watch(themeMode, (newMode) => {
    applyTheme(newMode)
  })
  
  return {
    themeMode,
    isDark,
    isColorful,
    setTheme,
    initTheme
  }
})
