import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Helper: allow overriding API target via env while defaulting to local dev server or docker service name.
const API_TARGET = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // Proxy API calls during development so the frontend can use relative paths (/api/v1/...)
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        // FastAPI mounted at /api/v1; we keep /api prefix so axios calls to /api/v1 pass through untouched.
        // If deploying behind a different ingress path, adjust rewrite accordingly.
        // rewrite: (path) => path.replace(/^\/api/, '/api')
      },
    },
  },
})
