# Pi Extensions Reference

## Contents

- When to use an extension
- Locations
- Entry point shape
- Commands, tools, and events
- Extension implementation checklist

## When to Use an Extension

Use a Pi extension when the user needs:

- a custom slash command
- a custom tool callable by the model
- event interception around tool calls, sessions, or provider requests
- persistent session state
- custom TUI widgets, status lines, dialogs, or overlays

If a request is only about reusable instructions, prefer a skill or prompt template instead.

## Locations

Auto-discovered extension locations:

- `~/.pi/agent/extensions/*.ts`
- `~/.pi/agent/extensions/*/index.ts`
- `.pi/extensions/*.ts`
- `.pi/extensions/*/index.ts`

Settings can also point at explicit extension files or directories.

Project-local extensions are the default choice for repo-specific behavior.

## Entry Point Shape

Pi extensions export a default function that receives `ExtensionAPI`.

```ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("hello", {
    description: "Say hello",
    handler: async (args, ctx) => {
      ctx.ui.notify(`Hello ${args || "world"}!`, "info");
    },
  });
}
```

Extensions are loaded through `jiti`, so TypeScript works without a build step.

## Commands, Tools, and Events

Important extension APIs:

- `pi.registerCommand(...)`: add slash commands
- `pi.registerTool(...)`: add model-callable tools
- `pi.on(...)`: subscribe to lifecycle and tool events
- `pi.registerShortcut(...)`: add keyboard shortcuts
- `pi.registerFlag(...)`: add extension flags

Common events:

- `resources_discover`
- `session_start`
- `before_agent_start`
- `tool_call`
- `context`
- `before_provider_request`
- `session_shutdown`

Use `resources_discover` when the extension needs to contribute extra skill, prompt, or theme paths dynamically.

## Extension Implementation Checklist

1. Pick scope: `.pi/extensions/` for project-local, `~/.pi/agent/extensions/` for personal global behavior.
2. Add a nearby `package.json` only if dependencies are required.
3. Use `pi.registerCommand(...)` for slash commands instead of inventing a second command format.
4. Keep event handlers narrow and predictable.
5. If the extension blocks tool calls, include a clear reason for the user.
6. Reload with `/reload` after changes.

Minimal dependency guidance:

- Pi core extension packages should be peer dependencies when shipping a shareable Pi package.
- Ordinary npm libraries can go in `dependencies`.
