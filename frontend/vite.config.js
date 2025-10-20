import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      react({
        // Enable fast refresh
        fastRefresh: !isProduction,
      }),
    ],
    server: {
      port: 3002,
      host: 'localhost',
      open: false, // Don't auto-open browser
      cors: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
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
      // Reduce bundle size
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            icons: ['lucide-react'],
            utils: ['axios', 'clsx'],
          },
        },
      },
      // Build optimizations
      minify: isProduction ? 'terser' : false,
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
        },
      } : {},
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
    // Development optimizations
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom', 'axios'],
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
