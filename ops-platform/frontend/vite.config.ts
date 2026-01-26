import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        proxy: {
            '/api': {
                // Use localhost for browser access, backend for Docker network
                target: process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path
            }
        }
    }
})
