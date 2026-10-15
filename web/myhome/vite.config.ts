import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

/** Serve OpenPlan SPA for extensionless /openplan/* routes (e.g. /openplan/editor). */
function openplanSpaFallback(): Plugin {
  const spaHtml = path.resolve(rootDir, 'public/openplan/index.html')

  function rewrite(url: string | undefined) {
    if (!url) return null
    const [pathname, query = ''] = url.split('?')
    if (!pathname.startsWith('/openplan')) return null
    if (pathname.includes('.')) return null
    if (pathname.startsWith('/openplan/models')) return null
    if (pathname.startsWith('/openplan/textures')) return null
    if (pathname.startsWith('/openplan/_app')) return null
    const q = query ? `?${query}` : ''
    return `/openplan/index.html${q}`
  }

  return {
    name: 'openplan-spa-fallback',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const nextUrl = rewrite(req.url)
        if (nextUrl) req.url = nextUrl
        next()
      })
    },
    configurePreviewServer(server) {
      server.middlewares.use((req, _res, next) => {
        const nextUrl = rewrite(req.url)
        if (nextUrl) req.url = nextUrl
        next()
      })
    },
    closeBundle() {
      if (!fs.existsSync(spaHtml)) return
      const dir = path.resolve(rootDir, 'public/openplan/editor')
      fs.mkdirSync(dir, { recursive: true })
      fs.copyFileSync(spaHtml, path.join(dir, 'index.html'))
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), openplanSpaFallback()],
  server: {
    // OpenPlan static assets are rebuilt separately; watching them can EBUSY on Windows (.glb locks).
    watch: {
      ignored: ['**/public/openplan/**'],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:18002',
        changeOrigin: true,
      },
    },
  },
})
