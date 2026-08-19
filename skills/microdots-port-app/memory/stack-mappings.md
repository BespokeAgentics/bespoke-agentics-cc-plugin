# Stack mappings — the port ledger

Append-and-annotate only; rows are never deleted or rewritten. Protocol:
`references/memory-protocol.md`. Rows carry provenance `prior` when they enter
a port's optimization register; the `standard` framework mappings live in
`references/composition-and-port-map.md` §4 and do not belong here — this
ledger holds only what real ports established.

| ID  | Source pattern (fingerprint terms) | Target idiom | Default disposition | Confidence | First / last port | Notes |
| --- | ---------------------------------- | ------------ | ------------------- | ---------- | ----------------- | ----- |
