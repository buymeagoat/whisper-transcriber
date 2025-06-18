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
      '/log_event': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/audio': 'http://localhost:8000',
      '^/admin/(files|reset|download-all)$': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
      '/transcripts': 'http://localhost:8000'
    }
  }
});
