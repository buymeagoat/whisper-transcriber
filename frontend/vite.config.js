import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

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
      '/admin/stats': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
      '/transcripts': 'http://localhost:8000'
    }
  },
  build: {
    // Output directory
    outDir: 'dist',
    
    // Generate source maps for debugging
    sourcemap: false,
    
    // Enable minification
    minify: 'terser',
    
    // Terser options for advanced minification
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
        drop_debugger: true, // Remove debugger statements
        pure_funcs: ['console.log', 'console.warn', 'console.error'] // Remove specific console methods
      },
      mangle: {
        safari10: true  // Fix Safari 10+ issues
      }
    },
    
    // Code splitting configuration
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      },
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // React and related libraries
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          
          // UI and utility libraries
          'ui-vendor': [
            '@hookform/resolvers',
            'react-hook-form'
          ],
          
          // Split large components into separate chunks
          'pages': [
            './src/pages/UploadPage.jsx',
            './src/pages/JobsPage.jsx',
            './src/pages/ResultsPage.jsx'
          ],
          
          // API and services
          'services': [
            './src/api/index.js',
            './src/services/errorHandler.js'
          ]
        },
        
        // Naming pattern for chunks
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? 
            chunkInfo.facadeModuleId.split('/').pop().replace('.jsx', '').replace('.js', '') : 
            'chunk';
          return `assets/js/[name]-[hash].js`;
        },
        
        // Naming pattern for entry files
        entryFileNames: 'assets/js/[name]-[hash].js',
        
        // Naming pattern for assets
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name.split('.').pop();
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/css/i.test(extType)) {
            return `assets/css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        }
      }
    },
    
    // Chunk size warning limit (500kb)
    chunkSizeWarningLimit: 500,
    
    // Target modern browsers for better optimization
    target: ['es2020', 'chrome80', 'firefox78', 'safari13']
  },
  
  // Optimization settings
  optimizeDeps: {
    // Pre-bundle dependencies for faster dev startup
    include: [
      'react',
      'react-dom',
      'react-router-dom'
    ]
  },
  
  // Resolve configuration
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@pages': resolve(__dirname, 'src/pages'),
      '@services': resolve(__dirname, 'src/services'),
      '@utils': resolve(__dirname, 'src/utils')
    }
  }
});
