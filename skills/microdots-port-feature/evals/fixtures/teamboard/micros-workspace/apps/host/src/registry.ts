// The registry is the index of micros. apiUrlFor picks localPort vs
// deployedApiUrl at runtime by hostname — one build works everywhere.
export const registry = [
  {
    tag: 'pulse-panel',
    bundle: '/micros/pulse-panel.js',
    localPort: 3101,
    deployedApiUrl: 'https://effect-microapps-pulse.example.workers.dev',
    attributes: { label: 'default' },
  },
]
