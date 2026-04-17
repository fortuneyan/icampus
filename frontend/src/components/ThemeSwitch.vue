<template>
  <el-dropdown @command="handleThemeChange" trigger="click">
    <el-button type="primary" link>
      <el-icon size="18">
        <component :is="currentIcon" />
      </el-icon>
      <span class="theme-label">{{ themeLabel }}</span>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light" :class="{ active: themeStore.themeMode === 'light' }">
          <el-icon><Sunny /></el-icon>
          <span>明亮主题</span>
        </el-dropdown-item>
        <el-dropdown-item command="dark" :class="{ active: themeStore.themeMode === 'dark' }">
          <el-icon><Moon /></el-icon>
          <span>暗黑主题</span>
        </el-dropdown-item>
        <el-dropdown-item command="colorful" :class="{ active: themeStore.themeMode === 'colorful' }">
          <el-icon><Brush /></el-icon>
          <span>校园风格</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { Sunny, Moon, Brush } from '@element-plus/icons-vue'
import { useThemeStore, type ThemeMode } from '@/stores/theme'

const themeStore = useThemeStore()

const currentIcon = computed(() => {
  const icons: Record<ThemeMode, any> = {
    light: Sunny,
    dark: Moon,
    colorful: Brush
  }
  return icons[themeStore.themeMode]
})

const themeLabel = computed(() => {
  const labels: Record<ThemeMode, string> = {
    light: '明亮',
    dark: '暗黑',
    colorful: '校园'
  }
  return labels[themeStore.themeMode]
})

const handleThemeChange = (command: ThemeMode) => {
  themeStore.setTheme(command)
}
</script>

<style scoped lang="scss">
.theme-label {
  margin-left: 4px;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  
  &.active {
    color: var(--el-color-primary);
    font-weight: bold;
  }
}
</style>
