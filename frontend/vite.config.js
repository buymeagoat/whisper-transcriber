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
      // Advanced bundle optimization
      rollupOptions: {
        output: {
          // Enhanced chunk splitting strategy
          manualChunks: (id) => {
            // Vendor chunks
            if (id.includes('node_modules')) {
              // React ecosystem
              if (id.includes('react') || id.includes('react-dom')) {
                return 'react-vendor'
              }
              // Routing
              if (id.includes('react-router')) {
                return 'router-vendor'
              }
              // Icons (potentially large)
              if (id.includes('lucide-react')) {
                return 'icons-vendor'
              }
              // HTTP client
              if (id.includes('axios')) {
                return 'http-vendor'
              }
              // CSS utilities
              if (id.includes('clsx') || id.includes('class-variance-authority')) {
                return 'utils-vendor'
              }
              // Other third-party libraries
              return 'vendor'
            }
            
            // Application chunks by route/feature
            if (id.includes('/pages/admin/')) {
              return 'admin-pages'
            }
            if (id.includes('/pages/auth/')) {
              return 'auth-pages'
            }
            if (id.includes('/components/admin/')) {
              return 'admin-components'
            }
            if (id.includes('/services/')) {
              return 'services'
            }
          },
          // Optimize chunk file names
          chunkFileNames: (chunkInfo) => {
            const facadeModuleId = chunkInfo.facadeModuleId
              ? chunkInfo.facadeModuleId.split('/').pop().replace(/\.[^/.]+$/, '')
              : 'chunk'
            return `assets/[name]-[hash].js`
          },
          // Optimize asset file names
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/\.(css)$/.test(assetInfo.name)) {
              return `assets/css/[name]-[hash][extname]`
            }
            if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
              return `assets/images/[name]-[hash][extname]`
            }
            return `assets/[name]-[hash][extname]`
          }
        },
      },
      // Enhanced build optimizations
      minify: isProduction ? 'terser' : false,
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          // Remove unused code
          dead_code: true,
          // Remove unused variables
          unused: true,
          // Inline functions when beneficial
          inline: true,
          // Reduce function calls
          reduce_funcs: true,
          // Collapse single-use variables
          collapse_vars: true,
          // Optimize sequences
          sequences: true,
        },
        mangle: {
          // Mangle function and variable names
          toplevel: true,
        },
        format: {
          // Remove comments
          comments: false,
        },
      } : {},
      // Target modern browsers for smaller bundles
      target: 'es2020',
      // Optimize CSS
      cssCodeSplit: true,
      // Report bundle size
      reportCompressedSize: true,
      // Chunk size warning limit
      chunkSizeWarningLimit: 1000,
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
