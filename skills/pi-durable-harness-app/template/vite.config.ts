import { defineConfig } from 'vite'

import { foldkit } from '@foldkit/vite-plugin'

export default defineConfig({
  plugins: [foldkit()],
  optimizeDeps: { entries: ['src/client/entry.ts'] },
  // In dev, Vite serves the client and forwards the WebSocket to the Bun host.
  server: { proxy: { '/rpc': { target: 'ws://localhost:8787', ws: true } } },
})
