// copy-static.js
import { copyFileSync, existsSync, mkdirSync } from 'fs';
import { resolve } from 'path';

const base = resolve('./'); // current dir = frontend/extension
const dist = resolve(base, 'dist');

const filesToCopy = [
  'manifest.json',
  'material_insights.json',
  'src/styles/tooltip.css',
  'src/styles/overlay.css',
  'src/overlay.js',
  'src/overlayTest.js',
  'src/background.js',
  'src/leaf-indicator.js',
  'src/persistent-overlay.js',
  'icon16.png',
  'icon32.png',
  'icon48.png',
  'icon128.png'
];

for (const file of filesToCopy) {
  const source = resolve(base, file);
  const destination = resolve(dist, file.includes('/') ? file.split('/').pop() : file);

  if (!existsSync(source)) {
    console.warn(`⚠️ Skipped: ${file} (not found)`);
    continue;
  }

  try {
    mkdirSync(dist, { recursive: true });
    copyFileSync(source, destination);
    console.log(`✅ Copied: ${file}`);
  } catch (err) {
    console.error(`❌ Failed to copy: ${file}`, err);
  }
}
