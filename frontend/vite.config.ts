import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // localhost 不能访问,原因未解决 -> 127.0.0.1
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})