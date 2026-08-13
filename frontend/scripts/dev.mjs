import { createServer } from 'vite'
import react from '@vitejs/plugin-react'

const server = await createServer({
  // Must configure here: configFile:false ignores vite.config.js
  configFile: false,
  root: process.cwd(),
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Cloudflare Tunnel sends Host: erp.nexo-dev.com
    allowedHosts: true,
    proxy: {
      // Same-origin API from the tunnel domain → local FastAPI
      '/api': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
    },
  },
})

await server.listen()
server.printUrls()
