import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0',      // Required for Docker
        port: 5173,           // Default port
        watch: {
            usePolling: true, // Required for Windows (WSL2) hot-reloading
        },
    },
    build: {
        target: 'es2015',
        minify: 'terser',
        cssMinify: true,
        reportCompressedSize: true,
        emptyOutDir: true,
        chunkSizeWarningLimit: 1000,
        assetsInlineLimit: 4096,
        rollupOptions: {
            output: {
                manualChunks: {
                    'react-vendor': ['react', 'react-dom', 'react-router-dom'],
                    'chart-vendor': ['recharts'],
                    'state-vendor': ['zustand', 'axios'],

                }
            }
        },
        terserOptions: {
            compress: {
                drop_console: false, // Enabled for debugging
                drop_debugger: false
            }
        }
    },
    optimizeDeps: {
        include: ['immer'],
    },
    css: {
        modules: {
            localsConvention: 'camelCase',
            generateScopedName: '[name]__[local]___[hash:base64:5]',
        }
    }
})
