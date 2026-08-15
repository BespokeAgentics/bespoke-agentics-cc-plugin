// Generator: scaffolds micros/<name>/ (contract, client, app, element, entry,
// styles, service trio, configs) with the next free port, tag `<name>-panel`.
// Refuses to overwrite an existing micro or reuse a claimed port.
// Fixture stub — the real workspace's generator is ~600 lines; evals only need
// the marker file and the CLI contract.
const microName = process.argv[2]
if (!microName || !/^[a-z][a-z0-9-]*$/.test(microName)) {
  console.error('usage: bun run new:micro <lower-kebab-name>')
  process.exit(1)
}
console.log(`would scaffold micros/${microName} (tag ${microName}-panel)`)
