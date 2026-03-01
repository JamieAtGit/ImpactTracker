// Vite build configuration for all frontend surfaces (website + extension bundles).
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        website: resolve(__dirname, 'website/index.html'),
        popup: resolve(__dirname, 'extension/src/popup/index.html'),
        background: resolve(__dirname, 'extension/src/utils/background.js'),
        content: resolve(__dirname, 'extension/src/content/tooltip.js'),
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
});
