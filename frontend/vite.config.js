import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/log_event': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000'
    }
  }
})
