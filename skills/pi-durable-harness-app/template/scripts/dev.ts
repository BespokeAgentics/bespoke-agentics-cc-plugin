export {}
// Runs the Bun host (with --watch) and the Vite client together.
const procs = [
  Bun.spawn(['bun', '--watch', 'src/server/main.ts'], { stdout: 'inherit', stderr: 'inherit' }),
  Bun.spawn(['bunx', 'vite'], { stdout: 'inherit', stderr: 'inherit' }),
]
const stopAll = () => {
  for (const p of procs) p.kill('SIGINT')
  process.exit(0)
}
process.on("SIGINT", stopAll)
process.on("SIGTERM", stopAll)
await Promise.race(procs.map(p => p.exited))
stopAll()
