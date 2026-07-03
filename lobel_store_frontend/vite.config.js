import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendTarget = process.env.VITE_DEV_BACKEND_TARGET || 'http://127.0.0.1:8000';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/media': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/swagger': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    port: 5173,
  },
});
