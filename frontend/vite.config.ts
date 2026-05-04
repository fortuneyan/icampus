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
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 避免 307 重定向丢失 Authorization header
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            // 清除可能会导致重定向的响应头
            delete proxyRes.headers['location'];
          });
        }
      },
      '/deeptutor': {
        target: 'http://127.0.0.1:5183',
        changeOrigin: true
      }
    }
  }
})