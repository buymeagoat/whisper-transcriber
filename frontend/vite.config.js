import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
    base: '/static/',
    server: {
    host: process.env.VITE_DEV_HOST || "localhost",
    port: parseInt(process.env.VITE_DEV_PORT || "5173"),
    proxy: {
      '/log_event': 'http://192.168.1.52:8000',
      '/jobs': 'http://192.168.1.52:8000',
      '/audio': 'http://192.168.1.52:8000',
      '^/admin/(files|reset|download-all)$': 'http://192.168.1.52:8000',
      '/admin/stats': 'http://192.168.1.52:8000',
      '/logs': 'http://192.168.1.52:8000',
      '/uploads': 'http://192.168.1.52:8000',
      '/transcripts': 'http://192.168.1.52:8000'
    }
  }
});
