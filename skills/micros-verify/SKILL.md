---
name: microdots-verify
description: Verify a change is actually done — typecheck, lint, test, build every micro-app bundle, then boot the system and confirm in a browser that the micro-apps render and poll their services. Use before reporting any change to this repo complete.
---

Green static checks are not sufficient in this repo. `Runtime.embed` runs the
Foldkit runtime in a forked fiber, so a startup defect produces a blank
micro-app with a clean console — typecheck, lint, tests and build have all
passed here while both micro-apps rendered nothing. The browser step is the
point of this skill; do not skip it.

## 1. Static checks

```bash
bun run check
```

Runs typecheck → lint → test. Fix anything that fails before continuing.

## 2. Build every bundle

```bash
bun run build
```

This proves each micro-app bundle and the host still compile. Watch for:

- a micro-app bundle that suddenly grows by hundreds of kB — usually a Node-only
  import leaking into the browser (`@kit/effect` is browser-only,
  `@kit/effect/service` is Node-only)
- the host bundle growing past ~20 kB — it must not contain micro-app code

## 3. Boot the system

```bash
bun run dev
```

Wait for the services to log `Listening on ...` and the host to log its URL.
If a port is already taken, find and stop the stale process rather than
switching ports.

## 4. Confirm in a browser

Open `http://localhost:5173` and check, for **each** micro-app:

- it rendered actual content (not an empty element)
- its value changes over time — it is polling its own service
- the host event log is receiving its events

Then exercise the wiring:

- change a host control and confirm the corresponding micro-app reacts
- unmount a micro-app and confirm the other is unaffected
- remount it and confirm it comes back live

Verify by inspecting the DOM and network activity, not just a screenshot.
Two failure modes are invisible to a naive check:

- **`Runtime.embed` replaces the container node**, so reading
  `container.innerHTML` inspects a detached element and always looks empty.
  Assert against the parent or `document.body.textContent`.
- **zero requests to a service port** means the runtime never started, even
  though `embed` returned a handle.

## 5. If a micro-app is blank

`embed` swallows the startup defect. Get the real error by running the program's
`start` effect directly and inspecting the `Exit` — the message is in
`cause.reasons[0].defect`. The most common cause is a mount container without an
`id`; everything must mount through `@kit/element`'s `mountPoint`.

## 6. Report honestly

State what passed and what you actually observed in the browser. If you could
not complete the browser step, say so explicitly rather than implying the change
is verified.
