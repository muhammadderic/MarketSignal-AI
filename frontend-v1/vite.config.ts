import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

/**
 * Vite configuration for the MarketSignal AI SPA.
 *
 * The dev server proxies all `/api/v1/...` calls to the local FastAPI backend so
 * the React SPA never communicates directly with third-party services
 * (ARC-001). The default backend binding is 127.0.0.1:8000 per AS-001 R-006.
 */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
