// frontend/extension/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: resolve(__dirname, 'dist'),
    sourcemap: true,
    rollupOptions: {
      input: {
        // Entry for the popup.html
        popup: resolve(__dirname, 'popup.html'),

        // ✅ Combined content script entry
        content: resolve(__dirname, 'src/content/content-entry.js')
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        manualChunks: undefined,
        preserveModules: false,
        dir: resolve(__dirname, 'dist')
      }
    }
  }
});
