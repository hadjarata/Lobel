import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

import {
  createPublicConfig,
  validateApiBaseUrl,
} from './src/config/envValidation.js';

export default defineConfig(({ mode }) => {
  const loadedEnvironment = loadEnv(mode, '.', 'VITE_');
  const environment = mode === 'test' && !loadedEnvironment.VITE_API_BASE_URL
    ? { ...loadedEnvironment, VITE_API_BASE_URL: 'http://api.test.invalid' }
    : loadedEnvironment;
  const config = createPublicConfig(environment, mode);
  const isDevelopment = mode === 'development';

  let proxy;
  if (isDevelopment) {
    const proxyTarget = validateApiBaseUrl(
      environment.VITE_DEV_BACKEND_TARGET || config.apiBaseUrl,
      'development',
    );
    proxy = Object.fromEntries(
      ['/api', '/media', '/swagger', '/admin'].map((path) => [
        path,
        { target: proxyTarget, changeOrigin: true },
      ]),
    );
  }

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      strictPort: false,
      ...(proxy ? { proxy } : {}),
    },
    preview: {
      host: true,
      port: 5173,
    },
    build: {
      target: 'es2022',
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: false,
      chunkSizeWarningLimit: 500,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
      clearMocks: true,
      include: ['src/**/*.test.{js,jsx}'],
    },
  };
});
