// DSP/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

const basePath = resolve(__dirname, 'frontend/extension');

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: resolve(basePath, 'dist'),
    sourcemap: true,
    rollupOptions: {
      input: {
        popup: resolve(basePath, 'popup-app/popup.html'),
        tooltips: resolve(basePath, 'src/utils/tooltips.js')
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  }
});
