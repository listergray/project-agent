import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// scripts/ → openplan → third_party → repo root → public/openplan
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../public/openplan')
const spa = path.join(root, 'index.html')
const destDir = path.join(root, 'editor')

if (!fs.existsSync(spa)) {
  console.error('OpenPlan SPA index missing:', spa)
  process.exit(1)
}

fs.mkdirSync(destDir, { recursive: true })
fs.copyFileSync(spa, path.join(destDir, 'index.html'))
console.log('Wrote', path.join(destDir, 'index.html'))
