import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// Production-only Vite configuration
export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic',
    })
  ],
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: () => 'vendor',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      },
    },
    minify: 'esbuild',
    target: 'es2018',
    cssCodeSplit: false,
    chunkSizeWarningLimit: 2000,
  },
  resolve: {
    alias: {
      '@': resolve(import.meta.dirname, './src'),
      '@components': resolve(import.meta.dirname, './src/components'),
      '@pages': resolve(import.meta.dirname, './src/pages'),
      '@services': resolve(import.meta.dirname, './src/services'),
      '@config': resolve(import.meta.dirname, './src/config'),
      '@context': resolve(import.meta.dirname, './src/context'),
    },
  },
  optimizeDeps: {
    include: [
      'react', 
      'react-dom', 
      'react-router-dom', 
      'axios'
    ],
  },
  define: {
    __DEV__: false,
  },
  preview: {
    port: 3002,
    host: true
  }
})
