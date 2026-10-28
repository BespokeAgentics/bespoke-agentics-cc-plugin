// Proves recovery: start a job, kill -9 the host mid-job, start it again, expect the job done.
export {}
const PORT = 8899
const DB = `./data/crash-test-${Date.now()}.sqlite`
const env = { ...process.env, PORT: String(PORT), HARNESS_DB: DB }
const start = () => Bun.spawn(['bun', 'src/server/main.ts'], { env, stdout: 'ignore', stderr: 'inherit' })
const connect = async () => {
  for (let i = 0; i < 50; i++) {
    try {
      const ws = new WebSocket(`ws://localhost:${PORT}/rpc`)
      await new Promise((ok, fail) => ((ws.onopen = ok), (ws.onerror = fail)))
      return ws
    } catch {
      await Bun.sleep(100)
    }
  }
  throw new Error('host did not start')
}
const nextView = (ws: WebSocket, pred: (v: any) => boolean, ms = 10_000) =>
  new Promise<any>((ok, fail) => {
    const t = setTimeout(() => fail(new Error('timed out waiting for view')), ms)
    ws.addEventListener('message', e => {
      const r = JSON.parse(String(e.data))
      if (r._tag === 'view' && pred(r)) (clearTimeout(t), ok(r))
    })
  })

let host = start()
let ws = await connect()
const working = nextView(ws, v => v.jobs[0]?.stage === 'working')
ws.send(JSON.stringify({ _tag: 'act', id: '1', requestId: `crash-${Date.now()}`, command: 'job.start', label: 'Crash test' }))
const before = await working
console.log(`job #${before.jobs[0].id} is working; killing the host with SIGKILL`)
host.kill(9)
await host.exited
host = start()
ws = await connect()
const after = await nextView(ws, v => v.jobs[0]?.stage === 'done')
console.log(`after restart: job #${after.jobs[0].id} ${after.jobs[0].stage} (${after.jobs[0].detail})`)
host.kill('SIGINT')
await host.exited
console.log('PASS: the job survived a hard kill')
process.exit(0)
