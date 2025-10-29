import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const isProduction = mode === 'production'
  const isAnalyze = mode === 'analyze'
  
  return {
    plugins: [
      react({
        // Enable fast refresh for development
        fastRefresh: !isProduction,
        // Enable automatic JSX runtime
        jsxRuntime: 'automatic',
      }),
      // Bundle analyzer for production builds
      ...(isAnalyze ? [
        visualizer({
          filename: 'dist/bundle-analysis.html',
          open: true,
          gzipSize: true,
          brotliSize: true,
        })
      ] : []),
    ],
    server: {
      port: 3002,
      host: 'localhost',
      open: false, // Don't auto-open browser
      cors: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          secure: false,
          ws: true, // Enable WebSocket proxying
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err)
            })
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url)
            })
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url)
            })
          },
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: !isProduction,
      // COMPLETELY DISABLE ALL CHUNK SPLITTING to prevent initialization order issues
      rollupOptions: {
        output: {
          // FORCE everything into a single bundle to prevent dependency order problems
          manualChunks: () => 'vendor', // Force all code into single chunk
          
          // Simple file naming
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash][extname]'
        },
      },
      // Conservative build settings to prevent initialization errors
      minify: isProduction ? 'esbuild' : false,
      // Remove Terser options completely since we're using esbuild
      // Target older ES version for better compatibility
      target: 'es2018',
      // Disable CSS code splitting temporarily to prevent dependency issues
      cssCodeSplit: false,
      // Report bundle size
      reportCompressedSize: false, // Disable to speed up builds
      // Increase chunk size warning limit
      chunkSizeWarningLimit: 2000,
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
        '@components': resolve(__dirname, './src/components'),
        '@pages': resolve(__dirname, './src/pages'),
        '@services': resolve(__dirname, './src/services'),
        '@config': resolve(__dirname, './src/config'),
        '@context': resolve(__dirname, './src/context'),
      },
    },
    // Simplified development optimizations to prevent circular dependencies
    optimizeDeps: {
      include: [
        'react', 
        'react-dom', 
        'react-router-dom', 
        'axios'
      ],
      // Force pre-bundling of problematic packages
      force: true
    },
    // CSS configuration
    css: {
      devSourcemap: !isProduction,
    },
    // Define global constants
    define: {
      __DEV__: !isProduction,
    },
  }
})
